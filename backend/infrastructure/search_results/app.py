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
    "Access-Control-Expose-Headers": "Retry-After",
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

def respond(status, body, headers=None):
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, **(headers or {})},
        "body": json.dumps(body, default=json_default)
    }

def redirect(location, set_cookie=None):
    headers = {"Location": location, "Cache-Control": "no-store"}
    if set_cookie:
        headers["Set-Cookie"] = set_cookie
    return {"statusCode": 302, "headers": headers, "body": ""}

def cached_projection(saved, artist, title):
    pending = [store for store in STORES if not is_fresh(saved, store, artist, title, utcnow())]
    song_data = {'track_name': title, 'artist': artist, 'errors': [],
                 'created_at': saved.get('created_at')}
    for store in STORES:
        song_data[f'{store}_price'] = saved.get(f'{store}_price', -1) if store not in pending else -1
        song_data[f'{store}_url'] = saved.get(f'{store}_url', '') if store not in pending else ''
        song_data[f'{store}_validated_at'] = saved.get(f'{store}_validated_at') if store not in pending else None

    return song_data, pending


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
        headers = {"Retry-After": e.retry_after} if e.retry_after else None
        return respond(e.status_code, {"error": "Spotify request failed", "detail": str(e)}, headers)
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
        spotify_auth.require_session(request_headers)
        with Session(get_engine()) as session:
            db_tracks = get_existing_tracks(session)  # no filters
        return respond(200, db_tracks)

    # existing search route
    if path == "/db_results" and method == "POST":
        spotify_auth.require_session(request_headers)
        raw = event.get('body') or '{}'
        if not isinstance(raw, str) or len(raw.encode('utf-8')) > 4096:
            return respond(413, {"error": "Price request body is too large"})
        try:
            body = json.loads(raw)
        except ValueError:
            return respond(400, {"error": "Invalid JSON body"})
        tracks = body.get('tracks') if isinstance(body, dict) else None
        if not isinstance(tracks, list) or len(tracks) != 1:
            return respond(400, {"error": "Provide exactly one track per request"})
        track = tracks[0]
        if not isinstance(track, dict) or any(
            not isinstance(track.get(key), str) or not track[key].strip()
            or len(track[key]) > 300 or any(ord(c) < 32 or 0x7f <= ord(c) <= 0x9f or 0xd800 <= ord(c) <= 0xdfff for c in track[key])
            for key in ('name', 'artist')
        ):
            return respond(400, {"error": "Track name and artist must be nonempty strings of at most 300 characters"})

        engine = get_engine()
        artist, title = track['artist'], track['name']
        with Session(engine) as session:
            saved = get_existing_tracks(session, [title], [artist]).get((title, artist), {})
        song_data, pending = cached_projection(saved, artist, title)

        if pending:
            fresh = get_api_prices(artist, title, stores=pending)
            song_data['errors'] = fresh.get('errors', [])
            song_data['created_at'] = fresh.get('created_at')
            if fresh.get('itunes_retry_after') is not None:
                song_data['itunes_retry_after'] = fresh['itunes_retry_after']
            successful = [store for store in pending if store not in song_data['errors']]
            update = {'track_name': title, 'artist': artist}
            for store in pending:
                for field in ('price', 'url'):
                    key = f'{store}_{field}'
                    song_data[key] = fresh.get(key, -1 if field == 'price' else '')
                # Failed stores remain in storage but their stale prices are
                # withheld. Save successful providers independently.
                if store in successful:
                    song_data[f'{store}_validated_at'] = fresh.get(f'{store}_validated_at')
                    for field in ('price', 'url', *PROVENANCE_FIELDS):
                        key = f'{store}_{field}'
                        update[key] = fresh.get(key)
            if successful:
                update['created_at'] = fresh.get('created_at')
                with Session(engine) as session:
                    insert_tracks(session, [update])

        return respond(200, [song_data])

    return respond(404, {"error": "Not found"})
