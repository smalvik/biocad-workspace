import re

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

CHILD = re.compile(r"wb08_[0-9a-f]{32}")


def isolated_parent(environment):
    if environment.get("APP_ENV") != "local" or environment.get("ALLOW_DATABASE_TESTS") != "1":
        raise RuntimeError("Race probe requires the isolated test runner")
    try:
        url = make_url(environment.get("DATABASE_URL", ""))
    except (ArgumentError, ValueError):
        raise RuntimeError("Race probe requires the fixed disposable PostgreSQL endpoint") from None
    if (
        url.drivername != "postgresql+asyncpg"
        or url.host != "postgres"
        or url.port not in {None, 5432}
        or url.username != "biocad"
        or url.password != "biocad-test-only"
        or url.database != "biocad"
        or url.query
    ):
        raise RuntimeError("Race probe refuses custom/persistent database credentials or endpoints")
    return url


def owned_child(name, marker, oid, expected_oid):
    if (
        not CHILD.fullmatch(name)
        or marker != "wb08-owned:" + name.removeprefix("wb08_")
        or type(oid) is not int
        or oid <= 0
        or oid != expected_oid
    ):
        raise RuntimeError("Race probe refuses a database without matching creation ownership")
