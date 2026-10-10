import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken

AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1"
SCOPE = "playlist-read-private playlist-read-collaborative"

STATE_COOKIE = "groovonomy_oauth_state"
STATE_MAX_AGE = 600
# How long a sign-in lasts before the user has to log in again
SESSION_MAX_AGE = 7 * 24 * 60 * 60
REQUEST_TIMEOUT = 8
MAX_PAGES = 50

REQUIRED_SETTINGS = ("CLIENT_ID", "CLIENT_SECRET", "SESSION_SECRET")


class AuthError(Exception):
    """The caller is not signed in (or the session can no longer be used)."""


class ConfigError(Exception):
    """A required setting is missing from the function's environment."""


class SpotifyError(Exception):
    """Spotify answered with something we cannot use."""


def check_config():
    missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
    if missing:
        raise ConfigError("Missing settings: " + ", ".join(missing))
    if len(os.environ["SESSION_SECRET"]) < 32:
        raise ConfigError("SESSION_SECRET must be at least 32 characters")


def redirect_uri(event):
    # Must match the redirect URI registered in the Spotify dashboard exactly
    override = os.environ.get("SPOTIFY_REDIRECT_URI")
    if override:
        return override
    ctx = event.get("requestContext") or {}
    return f"https://{ctx['domainName']}/{ctx['stage']}/callback"


def _fernet():
    # The key comes from configuration, so every Lambda instance reads the same sessions
    digest = hashlib.sha256(os.environ["SESSION_SECRET"].encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def create_session(token_info):
    payload = {
        "access_token": token_info["access_token"],
        "refresh_token": token_info.get("refresh_token"),
        "expires_at": int(time.time()) + int(token_info.get("expires_in", 3600)),
    }
    return _fernet().encrypt(json.dumps(payload).encode()).decode()


def read_session(session_token):
    try:
        raw = _fernet().decrypt(session_token.encode(), ttl=SESSION_MAX_AGE)
        return json.loads(raw)
    except (InvalidToken, ValueError):
        raise AuthError("Invalid or expired session")


def _cookie(value, max_age):
    return f"{STATE_COOKIE}={value}; Max-Age={max_age}; Path=/; Secure; HttpOnly; SameSite=Lax"


def _read_state_cookie(headers):
    for part in headers.get("cookie", "").split(";"):
        name, _, value = part.strip().partition("=")
        if name == STATE_COOKIE:
            return value
    return None


def login(event):
    """Returns (location, set_cookie) for the redirect to Spotify's authorize page."""
    check_config()
    state = secrets.token_urlsafe(24)
    query = urlencode({
        "client_id": os.environ["CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": redirect_uri(event),
        "scope": SCOPE,
        "state": state,
        "show_dialog": "true",
    })
    return f"{AUTHORIZE_URL}?{query}", _cookie(state, STATE_MAX_AGE)


def _token_request(data):
    try:
        response = requests.post(
            TOKEN_URL,
            data=data,
            auth=(os.environ["CLIENT_ID"], os.environ["CLIENT_SECRET"]),
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as e:
        raise SpotifyError(f"Could not reach Spotify: {type(e).__name__}")
    if response.status_code != 200:
        raise SpotifyError(f"Spotify token endpoint returned {response.status_code}")
    return response.json()


def callback(event, headers):
    """Returns (session_token, set_cookie); raises AuthError if sign-in did not complete."""
    check_config()
    params = event.get("queryStringParameters") or {}
    expected = _read_state_cookie(headers)
    state = params.get("state")
    if not expected or not state or not hmac.compare_digest(expected, state):
        raise AuthError("state_mismatch")
    if params.get("error") or not params.get("code"):
        raise AuthError(params.get("error") or "missing_code")

    token_info = _token_request({
        "grant_type": "authorization_code",
        "code": params["code"],
        "redirect_uri": redirect_uri(event),
    })
    return create_session(token_info), _cookie("", 0)


def access_token(headers):
    """Returns a usable Spotify access token for the signed-in caller."""
    check_config()
    scheme, _, session_token = headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not session_token.strip():
        raise AuthError("Not signed in")

    session = read_session(session_token.strip())
    if session["expires_at"] - 60 > time.time():
        return session["access_token"]
    if not session.get("refresh_token"):
        raise AuthError("Session expired")
    try:
        refreshed = _token_request({
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
        })
    except SpotifyError:
        raise AuthError("Session expired")
    return refreshed["access_token"]


def _get(token, url, params=None):
    try:
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as e:
        raise SpotifyError(f"Could not reach Spotify: {type(e).__name__}")
    if response.status_code == 401:
        raise AuthError("Spotify rejected the session")
    if response.status_code != 200:
        error = SpotifyError(f"Spotify returned {response.status_code}")
        error.status_code = response.status_code
        raise error
    return response.json()


def _pages(token, url, params):
    page = _get(token, url, params)
    for _ in range(MAX_PAGES):
        yield page
        next_url = page.get("next")
        if not next_url or not next_url.startswith(API_URL + "/"):
            return
        page = _get(token, next_url)


def get_playlists(token):
    user_info = _get(token, f"{API_URL}/me")
    images = user_info.get("images") or []

    playlists = []
    for page in _pages(token, f"{API_URL}/me/playlists", {"limit": 50}):
        for playlist in page.get("items") or []:
            if not playlist:
                continue
            playlist_images = playlist.get("images") or []
            owner = playlist.get("owner") or {}
            # Spotify renamed the playlist's "tracks" field to "items" in February 2026
            contents = playlist.get("items") or playlist.get("tracks") or {}
            playlists.append({
                "id": playlist["id"],
                "name": playlist.get("name"),
                "total_tracks": contents.get("total", 0),
                "image": playlist_images[0]["url"] if playlist_images else None,
                "owner": {
                    "id": owner.get("id"),
                    "display_name": owner.get("display_name"),
                },
            })

    return {
        "id": user_info["id"],
        "display_name": user_info.get("display_name"),
        "profile_picture": images[0]["url"] if images else None,
        "playlists": playlists,
    }


def get_tracks(token, playlist_id):
    if not re.fullmatch(r"[A-Za-z0-9]+", playlist_id or ""):
        raise SpotifyError("Invalid playlist id")

    params = {"limit": 100}
    try:
        pages = list(_pages(token, f"{API_URL}/playlists/{playlist_id}/items", params))
    except SpotifyError as e:
        if getattr(e, "status_code", None) != 404:
            raise
        # Endpoint name before Spotify's February 2026 API change
        pages = list(_pages(token, f"{API_URL}/playlists/{playlist_id}/tracks", params))

    tracks = []
    for page in pages:
        for entry in page.get("items") or []:
            track = (entry or {}).get("item") or (entry or {}).get("track")
            if not track or not track.get("name"):
                continue
            tracks.append({
                "name": track["name"],
                "artist": ", ".join(a["name"] for a in track.get("artists") or [] if a.get("name")),
            })
    return tracks
