"""Create, mutate, restore and destroy only a newly owned disposable child database."""

import asyncio
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from race_probe.guard import isolated_parent, owned_child

OWNERSHIP = "SELECT oid, shobj_description(oid,'pg_database') FROM pg_database WHERE datname=:name"
DEFINITION = """SELECT pg_get_constraintdef(oid) FROM pg_constraint
    WHERE conrelid='bookings'::regclass AND conname='bookings_no_overlap'"""


class Experiment:
    def __init__(self, output: Path):
        self.parent_url = isolated_parent(os.environ)
        self.name = "wb08_" + uuid4().hex
        self.marker = "wb08-owned:" + self.name.removeprefix("wb08_")
        self.oid = None
        self.output = output
        self.processes = []
        self.files = []
        self.urls = []
        self.env = {
            **os.environ,
            "DATABASE_URL": self.parent_url.set(database=self.name).render_as_string(hide_password=False),
            "NOTIFICATIONS_ENABLED": "false",
            "WB08_PROBE": "1",
        }

    async def ownership(self, connection):
        row = (await connection.execute(text(OWNERSHIP), {"name": self.name})).one()
        owned_child(self.name, row[1], row[0], self.oid)

    def command(self, name, *argv, environment=None, timeout=120):
        result = subprocess.run(
            argv, env=environment or self.env, capture_output=True, text=True, timeout=timeout
        )
        (self.output / (name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        return result.returncode

    def spawn_servers(self):
        for index in range(2):
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                listener.listen()
                self.urls.append("http://127.0.0.1:" + str(listener.getsockname()[1]))
                log = (self.output / f"http-process-{index}.log").open("w", encoding="utf-8")
                self.files.append(log)
                self.processes.append(
                    subprocess.Popen(
                        [sys.executable, "-m", "race_probe.server", str(listener.fileno())],
                        env=self.env,
                        pass_fds=(listener.fileno(),),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                )

    async def start_servers(self):
        await asyncio.to_thread(self.spawn_servers)
        async with httpx.AsyncClient(timeout=2) as client:
            async with asyncio.timeout(30):
                for url in self.urls:
                    while True:
                        if any(process.poll() is not None for process in self.processes):
                            raise RuntimeError("A probe HTTP process exited during startup")
                        try:
                            if (await client.get(url + "/api/v1/readyz")).status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.05)

    def stop_servers(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
        for process in self.processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for stream in self.files:
            stream.close()

    async def phase(self, name):
        folder = self.output / name
        folder.mkdir()
        env = {**self.env, "WB08_PHASE": name, "WB08_URLS": json.dumps(self.urls), "WB08_OUTPUT": str(folder)}
        argv = [sys.executable, "-m", "pytest", "-q", "race_probe/invariant.py", "--alluredir=" + str(folder)]
        if name == "red":
            argv.extend(["-k", "two_process_confirmations"])
        code = await asyncio.to_thread(self.command, name, *argv, environment=env)
        results = [json.loads(path.read_text()) for path in folder.glob("*-result.json")]
        observations = []
        for resource in ("D-15", "M-03"):
            path = folder / (resource + ".json")
            observations.append(
                json.loads(path.read_text())
                if path.exists()
                else {"resource": resource, "error": "Observation was not written; inspect raw pytest log"}
            )
        return {
            "exit_code": code,
            "results": results,
            "observations": observations,
            "oracle_source_sha256": hashlib.sha256(Path("race_probe/invariant.py").read_bytes()).hexdigest(),
        }

    async def run(self):
        parent = create_async_engine(self.parent_url, isolation_level="AUTOCOMMIT")
        child = None
        created = False
        report = {
            "database": self.name,
            "source_sha": os.getenv("GIT_SHA", "dev"),
            "working_tree": os.getenv("WORKING_TREE", "unknown"),
            "http_process_count": 2,
        }
        try:
            async with parent.connect() as control:
                await control.execute(text(f'CREATE DATABASE "{self.name}"'))
                created = True
                # Capture creation identity before any destructive operation is allowed.
                self.oid = await control.scalar(
                    text("SELECT oid FROM pg_database WHERE datname=:name"), {"name": self.name}
                )
                await control.execute(text(f"COMMENT ON DATABASE {self.name} IS '{self.marker}'"))
                await self.ownership(control)
            for label, command in (
                ("migrations", ["alembic", "upgrade", "head"]),
                ("seed", [sys.executable, "-m", "app.seed"]),
            ):
                if await asyncio.to_thread(self.command, label, *command):
                    raise RuntimeError("Probe child database preparation failed: " + label)
            child = create_async_engine(self.env["DATABASE_URL"])
            async with child.begin() as connection:
                await self.ownership(connection)
                original = await connection.scalar(text(DEFINITION))
                assert original and original.startswith("EXCLUDE USING gist") and "confirmed" in original
                await connection.execute(
                    text("""CREATE FUNCTION wb08_insert_gate() RETURNS trigger LANGUAGE plpgsql AS $$
                  BEGIN IF NEW.idempotency_key LIKE 'wb08:%' THEN
                    PERFORM pg_advisory_xact_lock_shared(841008); END IF; RETURN NEW; END $$""")
                )
                await connection.execute(
                    text(
                        "CREATE TRIGGER wb08_insert_gate BEFORE INSERT ON bookings "
                        "FOR EACH ROW EXECUTE FUNCTION wb08_insert_gate()"
                    )
                )
            await self.start_servers()
            async with child.begin() as connection:
                await self.ownership(connection)
                await connection.execute(text("ALTER TABLE bookings DROP CONSTRAINT bookings_no_overlap"))
                assert (
                    await connection.scalar(
                        text("""SELECT count(*) FROM pg_constraint
                    WHERE conrelid='bookings'::regclass AND conname='bookings_no_overlap'""")
                    )
                    == 0
                )
                report["constraint_removed_for_red"] = True
            try:
                report["red"] = await self.phase("red")
            finally:
                # Only rows created by this probe in its newly owned database are removed.
                async with child.begin() as connection:
                    await self.ownership(connection)
                    await connection.execute(
                        text(
                            "DELETE FROM outbox_events WHERE aggregate_id IN "
                            "(SELECT id FROM bookings WHERE idempotency_key LIKE 'wb08:red:%')"
                        )
                    )
                    await connection.execute(
                        text("DELETE FROM bookings WHERE idempotency_key LIKE 'wb08:red:%'")
                    )
                    await connection.execute(
                        text("ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap " + original)
                    )
            async with child.connect() as connection:
                restored = await connection.scalar(text(DEFINITION))
                assert restored == original
            report["original_constraint"] = original
            report["restored_constraint"] = restored
            report["green"] = await self.phase("green")
            red, green = report["red"], report["green"]
            assert red["oracle_source_sha256"] == green["oracle_source_sha256"]
            assert red["exit_code"] == 1 and len(red["results"]) == 2
            assert all(
                row["status"] == "failed" and "NONOVERLAP_INVARIANT" in row["statusDetails"]["message"]
                for row in red["results"]
            )
            assert all(
                row["http_statuses"] == [201, 201]
                and row["committed_confirmed"] == row["outbox_events"] == 2
                and row["blocked_insert_transactions"] == 2
                for row in red["observations"]
            )
            assert green["exit_code"] == 0 and len(green["results"]) == 3
            assert all(row["status"] == "passed" for row in green["results"])
            assert all(
                row["http_statuses"] == [201, 409]
                and row["committed_confirmed"] == row["outbox_events"] == 1
                and row["blocked_insert_transactions"] == 2
                for row in green["observations"]
            )
            report["status"] = "passed"
        finally:
            await asyncio.to_thread(self.stop_servers)
            if child is not None:
                await child.dispose()
            if created:
                async with parent.connect() as control:
                    await self.ownership(control)
                    await control.execute(text(f'DROP DATABASE "{self.name}" WITH (FORCE)'))
                    assert (
                        await control.scalar(
                            text("SELECT count(*) FROM pg_database WHERE datname=:name"), {"name": self.name}
                        )
                        == 0
                    )
                    report["owned_database_removed"] = True
            await parent.dispose()
            (self.output / "proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
