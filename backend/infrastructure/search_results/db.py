from sqlalchemy import create_engine, MetaData, Table, and_
from sqlalchemy.orm import Session

metadata = MetaData()
track_table = None

def reflect_tables(engine):
    global track_table
    metadata.reflect(bind=engine, only=["track"])
    track_table = metadata.tables["track"]

def get_existing_tracks(session: Session, names=None, artists=None):
    if not track_table:
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
            (row["track_name"], row["artist"]): dict(row._mapping)
            for row in rows
        }
    else:
        return [dict(row._mapping) for row in rows]

def insert_tracks(session: Session, track_data):
    session.execute(track_table.insert(), track_data)
