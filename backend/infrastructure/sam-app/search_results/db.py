from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData, insert, tuple_

md = MetaData()
md.reflect(bind=None, only=['track']) 
base = automap_base(metadata=md)
base.prepare()
Track = base.classes.track

def get_existing_tracks(session, track_names, artists):
    query = session.query(Track).filter(tuple_(Track.track_name, Track.artist).in_(zip(track_names, artists)))
    results = query.all()

    return {
        (track.track_name, track.artist): {
            'itunes_price': track.itunes_price,
            'itunes_url': track.itunes_url,
            'bandcamp_price': track.bandcamp_price,
            'bandcamp_url': track.bandcamp_url,
            'beatport_price': track.beatport_price,
            'beatport_url': track.beatport_url
        } for track in results
    }

def insert_tracks(session, tracks):
    session.execute(insert(Track), tracks)
    session.commit()