import os

from sqlalchemy import create_engine, MetaData, and_, or_
from sqlalchemy.orm import Session

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
    metadata.reflect(bind=engine, only=["track"])
    track_table = metadata.tables["track"]

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
