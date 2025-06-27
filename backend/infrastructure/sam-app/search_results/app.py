import json
from db import get_existing_tracks, insert_tracks
from search import get_api_prices
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine(os.environ['DB_URL'])

def lambda_handler(event, context):
    body = json.loads(event['body'])
    tracks = body.get('tracks', [])
    
    if not tracks:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No tracks provided"})
        }

    song_names = [t['name'] for t in tracks]
    artists = [t['artist'] for t in tracks]

    with Session(engine) as session:
        db_dict = get_existing_tracks(session, song_names, artists)

        final_data = []
        new_data = []

        for track in tracks:
            key = (track['name'], track['artist'])
            song_data = db_dict.get(key)
            if not song_data:
                song_data = get_api_prices(track['artist'], track['name'])
                new_data.append(song_data)

            song_data['track_name'] = track['name']
            song_data['artist'] = track['artist']
            final_data.append(song_data)

        if new_data:
            insert_tracks(session, new_data)

    return {
        "statusCode": 200,
        "body": json.dumps(final_data)
    }