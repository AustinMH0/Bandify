import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db import get_existing_tracks, insert_tracks, reflect_tables
from search_tracks import get_api_prices

engine = create_engine(os.environ['DB_URL'])
reflect_tables(engine)

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "https://groovonomy.com",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
    }

    path = event.get("path", "")
    method = event.get("httpMethod", "")

    if path == "/get_playlists" and method == "GET":
        try:
            with Session(engine) as session:
                db_tracks = get_existing_tracks(session)  # no filters
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps(db_tracks)
                }
        except Exception as e:
            print("Error in /get_playlists:", str(e))
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({"message": "Internal server error"})
            }

    # existing search route
    if method == "POST":
        body = json.loads(event['body'])
        tracks = body.get('tracks', [])

        if not tracks:
            return {
                "statusCode": 400,
                "headers": headers,
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
            "headers": headers,
            "body": json.dumps(final_data)
        }

    return {
        "statusCode": 404,
        "headers": headers,
        "body": json.dumps({"error": "Not found"})
    }
