import os

from sqlalchemy import create_engine, MetaData, and_, or_, inspect, text
from sqlalchemy.orm import Session

from price_cache import STORES

# Seconds to wait for the Postgres TCP connect before giving up
DB_CONNECT_TIMEOUT = 5

metadata = MetaData()
track_table = None
_engine = None

def get_engine():
    # Created on first use so a cold start never waits on the database
    global _engine
    if _engine is None:
        url = os.environ['DB_URL']
        connect_args = {"connect_timeout": DB_CONNECT_TIMEOUT} if url.startswith("postgres") else {}
        _engine = create_engine(url, connect_args=connect_args)
    if track_table is None:
        reflect_tables(_engine)
    return _engine

def reflect_tables(engine):
    global track_table
    migrate_price_validation(engine)
    metadata.clear()
    metadata.reflect(bind=engine, only=["track"])
    track_table = metadata.tables["track"]

def migrate_price_validation(engine):
    """Add nullable provenance on first DB use; never certify legacy prices.

    Postgres IF NOT EXISTS handles simultaneous Lambda cold starts. Migration
    runs before reflection and only once per initialized application instance.
    """
    with engine.begin() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("track")}
        timestamp_type = "TIMESTAMP WITH TIME ZONE" if engine.dialect.name == "postgresql" else "TIMESTAMP"
        for store in STORES:
            for field, column_type in (("matcher_version", "TEXT"), ("matched_artist", "TEXT"),
                                       ("matched_title", "TEXT"), ("validated_at", timestamp_type)):
                name = f"{store}_{field}"
                if name not in columns:
                    guard = "IF NOT EXISTS " if engine.dialect.name == "postgresql" else ""
                    connection.execute(text(f"ALTER TABLE track ADD COLUMN {guard}{name} {column_type}"))

def get_existing_tracks(session: Session, names=None, artists=None):
    if track_table is None:
        raise Exception("track_table not initialized")

    if names and artists:
        conditions = [
            and_(
                track_table.c.track_name == name,
                track_table.c.artist == artist
            )
            for name, artist in zip(names, artists)
        ]
        query = track_table.select().where(or_(*conditions))
    else:
        query = track_table.select()

    result = session.execute(query)
    rows = result.fetchall()

    if names and artists:
        return {
            (row._mapping["track_name"], row._mapping["artist"]): dict(row._mapping)
            for row in rows
        }
    else:
        return [dict(row._mapping) for row in rows]

def insert_tracks(session: Session, track_data):
    # Refresh in place, including pre-validation rows. Never accumulate stale
    # duplicates or keep a wrong price when a new search returns not found.
    for data in track_data:
        condition = and_(track_table.c.track_name == data["track_name"],
                         track_table.c.artist == data["artist"])
        updated = session.execute(track_table.update().where(condition).values(**data))
        if not updated.rowcount:
            session.execute(track_table.insert(), data)
    session.commit()
