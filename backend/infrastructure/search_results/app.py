import datetime
import decimal
import json
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import spotify_auth
from db import get_engine, get_existing_tracks, insert_tracks
from search_tracks import get_api_prices
from price_cache import STORES, PROVENANCE_FIELDS, is_fresh, utcnow

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://groovonomy.com").rstrip("/")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": FRONTEND_URL,
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
    "Access-Control-Max-Age": "600",
    "Cache-Control": "no-store",
}

def json_default(value):
    # Postgres NUMERIC and TIMESTAMP columns come back as Decimal and datetime
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, datetime.datetime):
        # Validation columns may return naive datetimes; they are stored in UTC.
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc).isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

def respond(status, body):
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=json_default)
    }

def redirect(location, set_cookie=None):
    headers = {"Location": location, "Cache-Control": "no-store"}
    if set_cookie:
        headers["Set-Cookie"] = set_cookie
    return {"statusCode": 302, "headers": headers, "body": ""}

def lambda_handler(event, context):
    path = event.get("path", "").rstrip("/")
    method = event.get("httpMethod", "")
    request_headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}

    # CORS preflight, e.g. for the JSON POST to /db_results
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}

    try:
        return route(event, path, method, request_headers)
    except spotify_auth.AuthError:
        return respond(401, {"error": "Unauthorized"})
    except spotify_auth.ConfigError as e:
        print("Configuration error:", str(e))
        return respond(500, {"error": "Spotify sign-in is not configured", "detail": str(e)})
    except spotify_auth.SpotifyError as e:
        print("Spotify error:", str(e))
        return respond(502, {"error": "Spotify request failed", "detail": str(e)})
    except SQLAlchemyError as e:
        print("Database error:", str(e))
        return respond(503, {"error": "Database unavailable"})

def route(event, path, method, request_headers):
    # Spotify sign-in: /login -> Spotify -> /callback -> back to the front end
    if path == "/login" and method == "GET":
        location, cookie = spotify_auth.login(event)
        return redirect(location, cookie)

    if path == "/callback" and method == "GET":
        try:
            session_token, cookie = spotify_auth.callback(event, request_headers)
        except spotify_auth.AuthError as e:
            print("Sign-in did not complete:", str(e))
            return redirect(f"{FRONTEND_URL}/#login_error=sign_in_failed")
        except spotify_auth.SpotifyError as e:
            print("Spotify error during sign-in:", str(e))
            return redirect(f"{FRONTEND_URL}/#login_error=spotify_unavailable")
        # The fragment never reaches a server, so the session stays out of access logs
        return redirect(f"{FRONTEND_URL}/#session={session_token}", cookie)

    # The signed-in user's playlists
    if path == "/get_playlists" and method == "GET":
        token = spotify_auth.access_token(request_headers)
        return respond(200, spotify_auth.get_playlists(token))

    if path.startswith("/get_tracks/") and method == "GET":
        token = spotify_auth.access_token(request_headers)
        playlist_id = path[len("/get_tracks/"):]
        return respond(200, spotify_auth.get_tracks(token, playlist_id))

    # every track price already stored in the database
    if path == "/db_results" and method == "GET":
        with Session(get_engine()) as session:
            db_tracks = get_existing_tracks(session)  # no filters
        return respond(200, db_tracks)

    # existing search route
    if path == "/db_results" and method == "POST":
        try:
            body = json.loads(event.get('body') or '{}')
        except ValueError:
            return respond(400, {"error": "Invalid JSON body"})
        tracks = body.get('tracks', [])

        if not tracks:
            return respond(400, {"error": "No tracks provided"})

        with Session(get_engine()) as session:
            final_data = []
            new_data = []
            existing = get_existing_tracks(session, [track['name'] for track in tracks],
                                           [track['artist'] for track in tracks])

            for track in tracks:
                artist, title = track['artist'], track['name']
                saved = existing.get((title, artist), {})
                now = utcnow()
                pending = [store for store in STORES if not is_fresh(saved, store, artist, title, now)]
                song_data = {'track_name': title, 'artist': artist, 'errors': [],
                             'created_at': saved.get('created_at')}
                for store in STORES:
                    song_data[f'{store}_price'] = saved.get(f'{store}_price', -1) if store not in pending else -1
                    song_data[f'{store}_url'] = saved.get(f'{store}_url', '') if store not in pending else ''
                    song_data[f'{store}_validated_at'] = saved.get(f'{store}_validated_at') if store not in pending else None

                if pending:
                    fresh = get_api_prices(artist, title, stores=pending)
                    song_data['errors'] = fresh.get('errors', [])
                    song_data['created_at'] = fresh.get('created_at')
                    successful = [store for store in pending if store not in song_data['errors']]
                    update = {'track_name': title, 'artist': artist}
                    for store in pending:
                        for field in ('price', 'url'):
                            key = f'{store}_{field}'
                            song_data[key] = fresh.get(key, -1 if field == 'price' else '')
                        # Preserve failed stores in storage, but never return their
                        # stale prices. Save successful providers independently.
                        if store in successful:
                            song_data[f'{store}_validated_at'] = fresh.get(f'{store}_validated_at')
                            for field in ('price', 'url', *PROVENANCE_FIELDS):
                                key = f'{store}_{field}'
                                update[key] = fresh.get(key)
                    if successful:
                        update['created_at'] = fresh.get('created_at')
                        new_data.append(update)
                        existing[(title, artist)] = {**saved, **update}
                final_data.append(song_data)


            if new_data:
                insert_tracks(session, new_data)

        return respond(200, final_data)

    return respond(404, {"error": "Not found"})
