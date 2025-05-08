from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from sqlalchemy import MetaData, insert, tuple_
from sqlalchemy.ext.automap import automap_base
from flask import jsonify, request, Blueprint
from itertools import chain

import datetime
from ..search import BeatportSearch
from ..search import BandcampSearch
from ..search import ItuneSearch
from .engine import engine

# Function used to grab search API prices given track name and artist name
def getApiPrices(artist, trackName):


    #create timestamp for songs
    time_stamp = datetime.datetime.now()

    #band_search = BandcampSearch()
    #beatport_search = BeatportSearch()
    itunes_data = ItuneSearch.search_song(artist, trackName)
    bandcamp_data = {'price': .99, 'url': "youtube.com"}
    beatport_data = {'price': .69, 'url': "google.com"}


    itunes_price = itunes_data['price']
    itunes_url = itunes_data['url']
    bandcamp_price = bandcamp_data['price']
    bandcamp_url = bandcamp_data['url']
    beatport_price = beatport_data['price']
    beatport_url = beatport_data['url']

    return {'itunes_price': itunes_price, 'itunes_url': itunes_url, 'bandcamp_price': bandcamp_price, 'bandcamp_url': bandcamp_url, 'beatport_price': beatport_price, 'beatport_url': beatport_url, 'created_at': time_stamp}



server_bp = Blueprint('server_bp', __name__)

@server_bp.route('/db_results', methods=['POST'])
def get_db_result():

    data = request.get_json()

    # Grab all tracks
    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400
    
    print(tracks)
    print("=" * 50)
    # Grab track names and artists
    song_names = []
    artists = []
    for track in tracks:
        song_names.append(track['name'])
        artists.append(track['artist'])


    # Query bandify db to see if they exist, otherwise API search and add to db

    final_data = []
    db_dict = dict()

    # Create table Track 'object' with SQLAlchemy for later use with "insert()"
    md = MetaData()
    md.reflect(engine, only = ['track'])
    base = automap_base(metadata = md)
    base.prepare()
    Track=base.classes.track
    

    # Query bandify db, if song exists return song data, else API search and insert()
    with engine.connect() as con:

        print(list(chain.from_iterable(zip(song_names, artists))))
        print("=" * 50)
        print(song_names)
        print("=" * 50)
        print(artists)
        print("=" * 50)
        # "results" holds the query results
        with Session(engine) as sesh, sesh.begin():
            query = sesh.query(Track).filter(tuple_(Track.artist, Track.track_name).in_(zip(artists, song_names)))

        # create tuple to loop through
            for track in query.all():
                db_dict[(track.track_name, track.artist)] = {
                    'itunes_price': track.itunes_price,
                    'itunes_url': track.itunes_url,
                    'bandcamp_price': track.bandcamp_price,
                    'bandcamp_url': track.bandcamp_url,
                    'beatport_price': track.beatport_price,
                    'beatport_url': track.beatport_url}

            final_data = []
            new_song_data = []


            for song in tracks:

                artist, track_name = song['artist'], song['name']
                songData = db_dict.get((track_name, artist), None)

                if songData is None:
                    songData = getApiPrices(artist, track_name)
                    new_song_data.append(songData)

                # SongData dict in new_song_data dict is being updated due to reference 
                songData['track_name'], songData['artist'] = track_name, artist
                final_data.append(songData)

        if new_song_data:
            print(new_song_data)
            sesh.execute(insert(Track), new_song_data)
            sesh.commit()
    
    print(list(final_data))

    return jsonify(list(final_data))





