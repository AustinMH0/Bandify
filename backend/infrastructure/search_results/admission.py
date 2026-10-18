"""One shared, expiring iTunes search slot; no network I/O inside DB transactions.

All SearchResults instances use the existing database, including cold starts.
Six seconds between admissions allows at most ten iTunes calls/minute. The
60-second lease outlives the coordinator deadline if a Lambda is terminated.
Bandcamp and Beatport never acquire this slot.
"""
from contextlib import contextmanager
import math
import uuid

from sqlalchemy import text

SEARCH_INTERVAL = 6
LEASE_SECONDS = 60


class Busy(Exception):
    def __init__(self, retry_after):
        self.retry_after = max(1, math.ceil(retry_after))


def _now(connection):
    # Use the database clock so separate Lambda clocks cannot exceed the budget.
    expression = ("EXTRACT(EPOCH FROM clock_timestamp())" if connection.dialect.name == "postgresql"
                  else "(julianday('now') - 2440587.5) * 86400.0")
    return float(connection.execute(text(f"SELECT {expression}")).scalar_one())


@contextmanager
def itunes_slot(engine):
    owner = uuid.uuid4().hex
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            # Serialize the first CREATE across cold starts. IF NOT EXISTS
            # alone does not prevent Postgres catalog races on initial setup.
            connection.execute(text("SELECT pg_advisory_xact_lock(724619201)"))
        connection.execute(text("""CREATE TABLE IF NOT EXISTS itunes_search_admission (
            id INTEGER PRIMARY KEY, owner VARCHAR(32),
            lease_until DOUBLE PRECISION NOT NULL,
            next_allowed DOUBLE PRECISION NOT NULL)"""))
        connection.execute(text("""INSERT INTO itunes_search_admission
            (id, owner, lease_until, next_allowed) VALUES (1, NULL, 0, 0)
            ON CONFLICT (id) DO NOTHING"""))
        now = _now(connection)
        admitted = connection.execute(text("""UPDATE itunes_search_admission
            SET owner = :owner, lease_until = :lease, next_allowed = :next
            WHERE id = 1 AND lease_until <= :now AND next_allowed <= :now
            RETURNING id"""), {"owner": owner, "lease": now + LEASE_SECONDS,
                                 "next": now + SEARCH_INTERVAL, "now": now}).first()
        if not admitted:
            row = connection.execute(text("SELECT lease_until, next_allowed FROM itunes_search_admission WHERE id = 1")).one()
            raise Busy(max(row) - now)
    try:
        yield
    finally:
        with engine.begin() as connection:
            connection.execute(text("""UPDATE itunes_search_admission SET owner = NULL, lease_until = 0
                    WHERE id = 1 AND owner = :owner"""), {"owner": owner})
