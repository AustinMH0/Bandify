import importlib
import json
import os
import sys
import time
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "search_results"))

API_HOST = "abc123.execute-api.us-west-1.amazonaws.com"
REDIRECT_URI = f"https://{API_HOST}/Prod/callback"
FRONTEND = "https://groovonomy.com"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def make_event(method, path, headers=None, query=None, body=None):
    return {
        "httpMethod": method,
        "path": path,
        "headers": headers or {},
        "queryStringParameters": query,
        "body": body,
        "requestContext": {"domainName": API_HOST, "stage": "Prod"},
    }


def load_modules():
    """Imports the handler the way a new Lambda instance would."""
    for name in ("app", "db", "spotify_auth", "search_tracks"):
        sys.modules.pop(name, None)
    return importlib.import_module("app")


@pytest.fixture()
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("CLIENT_ID", "test-client-id")
    monkeypatch.setenv("CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("SESSION_SECRET", "s" * 40)
    monkeypatch.setenv("FRONTEND_URL", FRONTEND)
    monkeypatch.delenv("SPOTIFY_REDIRECT_URI", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_API_URL", raising=False)
    return load_modules()


def sign_in(app, monkeypatch, expires_in=3600):
    """Runs /login and /callback and returns the session the front end would receive."""
    import spotify_auth

    login = app.lambda_handler(make_event("GET", "/login"), None)
    state = parse_qs(urlparse(login["headers"]["Location"]).query)["state"][0]
    cookie = login["headers"]["Set-Cookie"].split(";")[0]

    def fake_post(url, data=None, auth=None, timeout=None):
        assert url == spotify_auth.TOKEN_URL
        assert auth == ("test-client-id", "test-client-secret")
        assert data["redirect_uri"] == REDIRECT_URI
        return FakeResponse({"access_token": "access-1", "refresh_token": "refresh-1", "expires_in": expires_in})

    monkeypatch.setattr(spotify_auth.requests, "post", fake_post)
    response = app.lambda_handler(
        make_event("GET", "/callback", headers={"Cookie": cookie}, query={"code": "abc", "state": state}),
        None,
    )
    assert response["statusCode"] == 302
    location = response["headers"]["Location"]
    assert location.startswith(f"{FRONTEND}/#session=")
    return location.split("#session=")[1]


# --- the reported timeout: sign-in must not depend on the database ---

def test_import_and_login_do_not_touch_the_database(app, monkeypatch):
    # Regression: the handler used to connect to Postgres at import, so an
    # unreachable database timed out every request, including sign-in.
    monkeypatch.setenv("DB_URL", "postgresql+psycopg2://user:pw@10.255.255.1:5432/db")
    started = time.time()
    app = load_modules()
    response = app.lambda_handler(make_event("GET", "/login"), None)

    assert time.time() - started < 2
    assert response["statusCode"] == 302
    assert response["headers"]["Location"].startswith("https://accounts.spotify.com/authorize?")


def test_unreachable_database_returns_json_error_quickly(app, monkeypatch):
    # Nothing listens on port 1, so the connection is refused straight away
    monkeypatch.setenv("DB_URL", "postgresql+psycopg2://user:pw@127.0.0.1:1/db")
    app = load_modules()
    started = time.time()
    response = app.lambda_handler(make_event("GET", "/db_results"), None)

    assert time.time() - started < 10
    assert response["statusCode"] == 503
    assert json.loads(response["body"]) == {"error": "Database unavailable"}
    assert response["headers"]["Access-Control-Allow-Origin"] == FRONTEND


def test_database_connect_timeout_is_short(app, monkeypatch):
    import db

    captured = {}

    def fake_create_engine(url, **kwargs):
        captured.update(kwargs)
        raise RuntimeError("stop before connecting")

    monkeypatch.setenv("DB_URL", "postgresql+psycopg2://user:pw@db.example.com:5432/db")
    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    with pytest.raises(RuntimeError):
        db.get_engine()
    assert captured["connect_args"] == {"connect_timeout": 5}


# --- Spotify sign-in ---

def test_login_redirects_to_spotify_with_state_cookie(app):
    response = app.lambda_handler(make_event("GET", "/login"), None)

    location = urlparse(response["headers"]["Location"])
    query = parse_qs(location.query)
    assert (location.netloc, location.path) == ("accounts.spotify.com", "/authorize")
    assert query["client_id"] == ["test-client-id"]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert query["response_type"] == ["code"]
    cookie = response["headers"]["Set-Cookie"]
    assert cookie.startswith(f"groovonomy_oauth_state={query['state'][0]};")
    assert "Secure" in cookie and "HttpOnly" in cookie


def test_login_reports_missing_configuration(app, monkeypatch):
    monkeypatch.delenv("CLIENT_SECRET")
    response = app.lambda_handler(make_event("GET", "/login"), None)

    assert response["statusCode"] == 500
    assert "CLIENT_SECRET" in json.loads(response["body"])["detail"]


def test_callback_rejects_wrong_state(app, monkeypatch):
    import spotify_auth

    def fail_post(*args, **kwargs):
        raise AssertionError("must not exchange a code when the state does not match")

    monkeypatch.setattr(spotify_auth.requests, "post", fail_post)
    response = app.lambda_handler(
        make_event(
            "GET", "/callback",
            headers={"Cookie": "groovonomy_oauth_state=expected"},
            query={"code": "abc", "state": "something-else"},
        ),
        None,
    )
    assert response["statusCode"] == 302
    assert response["headers"]["Location"] == f"{FRONTEND}/#login_error=sign_in_failed"


def test_callback_handles_user_denying_access(app):
    response = app.lambda_handler(
        make_event(
            "GET", "/callback",
            headers={"cookie": "groovonomy_oauth_state=st"},
            query={"error": "access_denied", "state": "st"},
        ),
        None,
    )
    assert response["headers"]["Location"] == f"{FRONTEND}/#login_error=sign_in_failed"


def test_session_survives_a_new_lambda_instance(app, monkeypatch):
    session = sign_in(app, monkeypatch)
    assert "access-1" not in session and "refresh-1" not in session

    # A different instance has nothing in memory, only the configured SESSION_SECRET
    fresh_app = load_modules()
    import spotify_auth

    seen = []

    def fake_get(url, params=None, headers=None, timeout=None):
        seen.append((url, headers["Authorization"]))
        if url.endswith("/me"):
            return FakeResponse({"id": "user1", "display_name": "Test User", "images": [{"url": "pic.jpg"}]})
        return FakeResponse({
            "items": [
                {"id": "p1", "name": "Old shape", "tracks": {"total": 3}, "images": [{"url": "a.jpg"}],
                 "owner": {"id": "user1", "display_name": "Test User"}},
                {"id": "p2", "name": "New shape", "items": {"total": 7}, "images": None,
                 "owner": {"id": "other", "display_name": None}},
            ],
            "next": None,
        })

    monkeypatch.setattr(spotify_auth.requests, "get", fake_get)
    response = fresh_app.lambda_handler(
        make_event("GET", "/get_playlists", headers={"Authorization": f"Bearer {session}"}), None
    )

    assert response["statusCode"] == 200
    assert all(auth == "Bearer access-1" for _, auth in seen)
    assert json.loads(response["body"]) == {
        "id": "user1",
        "display_name": "Test User",
        "profile_picture": "pic.jpg",
        "playlists": [
            {"id": "p1", "name": "Old shape", "total_tracks": 3, "image": "a.jpg",
             "owner": {"id": "user1", "display_name": "Test User"}},
            {"id": "p2", "name": "New shape", "total_tracks": 7, "image": None,
             "owner": {"id": "other", "display_name": None}},
        ],
    }


def test_session_from_another_key_is_rejected(app, monkeypatch):
    session = sign_in(app, monkeypatch)
    monkeypatch.setenv("SESSION_SECRET", "t" * 40)
    response = app.lambda_handler(
        make_event("GET", "/get_playlists", headers={"Authorization": f"Bearer {session}"}), None
    )
    assert response["statusCode"] == 401


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-session"}, {"Authorization": "Basic abc"}])
def test_playlists_require_sign_in(app, headers):
    response = app.lambda_handler(make_event("GET", "/get_playlists", headers=headers), None)

    assert response["statusCode"] == 401
    assert json.loads(response["body"]) == {"error": "Unauthorized"}
    assert response["headers"]["Access-Control-Allow-Origin"] == FRONTEND


def test_expired_access_token_is_refreshed(app, monkeypatch):
    import spotify_auth

    session = sign_in(app, monkeypatch, expires_in=0)

    def fake_post(url, data=None, auth=None, timeout=None):
        assert data == {"grant_type": "refresh_token", "refresh_token": "refresh-1"}
        return FakeResponse({"access_token": "access-2", "expires_in": 3600})

    used = []

    def fake_get(url, params=None, headers=None, timeout=None):
        used.append(headers["Authorization"])
        if url.endswith("/me"):
            return FakeResponse({"id": "user1", "display_name": "Test User", "images": []})
        return FakeResponse({"items": [], "next": None})

    monkeypatch.setattr(spotify_auth.requests, "post", fake_post)
    monkeypatch.setattr(spotify_auth.requests, "get", fake_get)
    response = app.lambda_handler(
        make_event("GET", "/get_playlists", headers={"authorization": f"Bearer {session}"}), None
    )

    assert response["statusCode"] == 200
    assert set(used) == {"Bearer access-2"}


def test_get_tracks_follows_pages_and_both_item_shapes(app, monkeypatch):
    import spotify_auth

    session = sign_in(app, monkeypatch)
    second_page = "https://api.spotify.com/v1/playlists/p1/items?offset=100"

    def fake_get(url, params=None, headers=None, timeout=None):
        if url == second_page:
            return FakeResponse({
                "items": [{"track": {"name": "Song C", "artists": [{"name": "Z"}]}}, {"track": None}],
                "next": None,
            })
        assert url == "https://api.spotify.com/v1/playlists/p1/items"
        return FakeResponse({
            "items": [
                {"item": {"name": "Song A", "artists": [{"name": "X"}, {"name": "Y"}]}},
                {"item": {"name": "Song B", "artists": [{"name": "X"}]}},
            ],
            "next": second_page,
        })

    monkeypatch.setattr(spotify_auth.requests, "get", fake_get)
    response = app.lambda_handler(
        make_event("GET", "/get_tracks/p1", headers={"Authorization": f"Bearer {session}"}), None
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == [
        {"name": "Song A", "artist": "X, Y"},
        {"name": "Song B", "artist": "X"},
        {"name": "Song C", "artist": "Z"},
    ]


def test_get_tracks_falls_back_to_older_endpoint(app, monkeypatch):
    import spotify_auth

    session = sign_in(app, monkeypatch)

    def fake_get(url, params=None, headers=None, timeout=None):
        if url.endswith("/items"):
            return FakeResponse({}, status_code=404)
        assert url == "https://api.spotify.com/v1/playlists/p1/tracks"
        return FakeResponse({"items": [{"track": {"name": "Song A", "artists": [{"name": "X"}]}}], "next": None})

    monkeypatch.setattr(spotify_auth.requests, "get", fake_get)
    response = app.lambda_handler(
        make_event("GET", "/get_tracks/p1", headers={"Authorization": f"Bearer {session}"}), None
    )
    assert json.loads(response["body"]) == [{"name": "Song A", "artist": "X"}]


def test_get_tracks_rejects_odd_playlist_ids(app, monkeypatch):
    import spotify_auth

    session = sign_in(app, monkeypatch)

    def fail_get(*args, **kwargs):
        raise AssertionError("must not call Spotify with an unchecked id")

    monkeypatch.setattr(spotify_auth.requests, "get", fail_get)
    response = app.lambda_handler(
        make_event("GET", "/get_tracks/..%2Fme", headers={"Authorization": f"Bearer {session}"}), None
    )
    assert response["statusCode"] == 502


def test_preflight_allows_the_front_end(app):
    response = app.lambda_handler(make_event("OPTIONS", "/db_results"), None)

    assert response["statusCode"] == 204
    assert response["headers"]["Access-Control-Allow-Origin"] == FRONTEND
    assert "Authorization" in response["headers"]["Access-Control-Allow-Headers"]
    assert "POST" in response["headers"]["Access-Control-Allow-Methods"]


# --- price lookup ---

@pytest.fixture()
def track_db(app):
    from sqlalchemy import Column, DateTime, Integer, MetaData, Numeric, String, Table, create_engine

    engine = create_engine(os.environ["DB_URL"])
    md = MetaData()
    Table(
        "track", md,
        Column("id", Integer, primary_key=True),
        Column("track_name", String), Column("artist", String),
        Column("itunes_price", Numeric(6, 2)), Column("itunes_url", String),
        Column("bandcamp_price", Numeric(6, 2)), Column("bandcamp_url", String),
        Column("beatport_price", Numeric(6, 2)), Column("beatport_url", String),
        Column("created_at", DateTime),
    )
    md.create_all(engine)
    return engine


def test_price_lookup_stores_new_tracks_and_reuses_them(app, track_db, monkeypatch):
    import datetime

    searched = []

    def fake_prices(artist, track_name):
        searched.append((artist, track_name))
        return {
            "itunes_price": 1.29, "itunes_url": "https://itunes.example/a",
            "bandcamp_price": -1, "bandcamp_url": "",
            "beatport_price": 1.49, "beatport_url": "https://beatport.example/a",
            "created_at": datetime.datetime(2026, 1, 1, 12, 0, 0),
        }

    monkeypatch.setattr(app, "get_api_prices", fake_prices)
    body = json.dumps({"tracks": [{"name": "Song A", "artist": "X"}]})

    first = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    second = app.lambda_handler(make_event("POST", "/db_results", body=body), None)

    assert first["statusCode"] == 200 and second["statusCode"] == 200
    assert searched == [("X", "Song A")]
    stored = json.loads(second["body"])[0]
    assert (stored["track_name"], stored["artist"]) == ("Song A", "X")
    assert stored["itunes_price"] == 1.29
    assert stored["beatport_url"] == "https://beatport.example/a"

    everything = app.lambda_handler(make_event("GET", "/db_results"), None)
    assert len(json.loads(everything["body"])) == 1


def test_price_lookup_requires_tracks(app):
    response = app.lambda_handler(make_event("POST", "/db_results", body=json.dumps({"tracks": []})), None)
    assert response["statusCode"] == 400


def test_unknown_route_is_404(app):
    assert app.lambda_handler(make_event("GET", "/nope"), None)["statusCode"] == 404
