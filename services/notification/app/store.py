"""Worker-private durable inbox. No access to Booking's database or credentials."""

import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from app.events import Event


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1}:
                raise ValueError("Unsupported delivery journal version")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS deliveries (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
                  booking_id TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL,
                  state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','sent')),
                  attempts INTEGER NOT NULL DEFAULT 0, next_at REAL NOT NULL DEFAULT 0,
                  sent_at REAL, last_error TEXT
                );
                CREATE INDEX IF NOT EXISTS deliveries_pending ON deliveries(state,next_at);
                CREATE INDEX IF NOT EXISTS deliveries_booking ON deliveries(booking_id,seq);
                PRAGMA user_version=1;
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        return db

    def accept(self, event: Event) -> bool:
        body = json.dumps(event.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(body.encode()).hexdigest()
        with closing(self.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT digest FROM deliveries WHERE event_id=?", (str(event.event_id),)
            ).fetchone()
            if previous and previous["digest"] != digest:
                raise ValueError("Conflicting event identity")
            if not previous:
                db.execute(
                    "INSERT INTO deliveries(event_id,booking_id,digest,payload) VALUES(?,?,?,?)",
                    (str(event.event_id), str(event.booking_id), digest, body),
                )
            db.commit()
        return previous is None

    def deliver_one(self, sender, now: float | None = None):
        now = time.time() if now is None else now
        with closing(self.connect()) as db:
            # One sender at a time; preserve created/cancelled order for each booking.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """SELECT d.* FROM deliveries d
                WHERE d.state='pending' AND d.next_at<=? AND NOT EXISTS(
                    SELECT 1 FROM deliveries earlier WHERE earlier.booking_id=d.booking_id
                    AND earlier.seq<d.seq AND earlier.state='pending') ORDER BY d.seq LIMIT 1""",
                (now,),
            ).fetchone()
            if row is None:
                db.rollback()
                return None
            attempts = row["attempts"] + 1
            try:
                sender(Event.model_validate_json(row["payload"]))
            except Exception as error:
                db.execute(
                    "UPDATE deliveries SET attempts=?,next_at=?,last_error=? WHERE seq=?",
                    (attempts, now + min(60, 2 ** min(attempts, 6)), type(error).__name__, row["seq"]),
                )
                state = "retry"
            else:
                db.execute(
                    "UPDATE deliveries SET state='sent',attempts=?,sent_at=?,last_error=NULL WHERE seq=?",
                    (attempts, now, row["seq"]),
                )
                state = "sent"
            db.commit()
            return {"event_id": row["event_id"], "state": state, "attempts": attempts}

    def ping(self):
        with closing(self.connect()) as db:
            db.execute("SELECT 1 FROM deliveries LIMIT 1")
