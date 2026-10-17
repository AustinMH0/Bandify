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

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


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
    for name in ("app", "db", "spotify_auth", "search_tracks", "price_cache"):
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
    monkeypatch.delenv("PRICE_CACHE_TTL_SECONDS", raising=False)
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


def validated_prices(artist, title, stores=("itunes", "bandcamp", "beatport")):
    from price_cache import MATCHER_VERSION, utcnow

    now = utcnow()
    result = {"errors": [], "created_at": now}
    for store, price in [("itunes", 1.29), ("bandcamp", -1), ("beatport", 1.49)]:
        if store not in stores:
            continue
        result.update({
            f"{store}_price": price,
            f"{store}_url": "" if price == -1 else f"https://{store}.example/a",
            f"{store}_matcher_version": MATCHER_VERSION,
            f"{store}_matched_artist": None if price == -1 else artist,
            f"{store}_matched_title": None if price == -1 else title,
            f"{store}_validated_at": now,
        })
    return result


def test_price_lookup_reuses_validated_tracks_without_duplicates(app, track_db, monkeypatch):
    import datetime

    searched = []

    def fake_prices(artist, track_name, stores):
        searched.append((artist, track_name))
        return {
            **validated_prices(artist, track_name, stores),
            "itunes_price": 1.29, "itunes_url": "https://itunes.example/a",
            "bandcamp_price": -1, "bandcamp_url": "",
            "beatport_price": 1.49, "beatport_url": "https://beatport.example/a",
            "created_at": datetime.datetime(2026, 1, 1, 12, 0, 0),
        }

    monkeypatch.setattr(app, "get_api_prices", fake_prices)
    body = json.dumps({"tracks": [{"name": "Song A", "artist": "X"}]})

    first = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    # Reuse must survive a Lambda cold start, not just a warm process.
    app = load_modules()
    monkeypatch.setattr(app, "get_api_prices", fake_prices)
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


def test_new_track_crosses_scraper_http_boundary_and_is_committed(app, track_db, scraper, monkeypatch):
    import search_tracks
    from search.matching import store_result

    calls = []
    monkeypatch.setattr(search_tracks, "PLAYWRIGHT_API_URL", "https://scraper.example/playwright_function")
    monkeypatch.setattr(search_tracks.ItuneSearch, "search_song", lambda *args: store_result(1.29, "https://itunes.example/a", "X", "New Song"))

    def proxy_post(url, json, timeout):
        import json as json_module

        assert url == search_tracks.PLAYWRIGHT_API_URL
        assert timeout == (2, 16)
        calls.append(json)
        result = scraper.lambda_handler({"body": json_module.dumps(json), "httpMethod": "POST"}, None)
        return FakeResponse(json_module.loads(result["body"]), result["statusCode"])

    monkeypatch.setattr(search_tracks.requests, "post", proxy_post)
    body = json.dumps({"tracks": [{"name": "New Song", "artist": "X"}]})
    first = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert first["statusCode"] == 200
    row = json.loads(first["body"])[0]
    assert (row["itunes_price"], row["bandcamp_price"], row["beatport_price"]) == (1.29, 0.99, 1.49)
    assert row["errors"] == []

    # A fresh lookup uses persisted provider provenance without store traffic.
    second = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert second["statusCode"] == 200
    assert json.loads(second["body"])[0]["bandcamp_price"] == 0.99
    assert calls == [{"artist": "X", "track_name": "New Song", "stores": ["bandcamp", "beatport"]}]


def test_transport_failure_returns_partial_prices_without_poisoning_cache(app, track_db, monkeypatch):
    import search_tracks
    import requests
    from search.matching import store_result

    monkeypatch.setattr(search_tracks, "PLAYWRIGHT_API_URL", "https://scraper.example/playwright_function")
    monkeypatch.setattr(search_tracks.ItuneSearch, "search_song", lambda *args: store_result(0.99, "https://itunes.example/a", "X", "New Song"))
    calls = []

    def unavailable(*args, **kwargs):
        calls.append(1)
        raise requests.exceptions.ReadTimeout()

    monkeypatch.setattr(search_tracks.requests, "post", unavailable)
    body = json.dumps({"tracks": [{"name": "New Song", "artist": "X"}]})
    for _ in range(2):
        response = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
        assert response["statusCode"] == 200
        row = json.loads(response["body"])[0]
        assert row["itunes_price"] == 0.99
        assert row["errors"] == ["bandcamp", "beatport"]
    assert len(calls) == 2
    stored = app.lambda_handler(make_event("GET", "/db_results"), None)
    saved = json.loads(stored["body"])
    assert len(saved) == 1
    assert saved[0]["itunes_price"] == 0.99
    assert saved[0]["itunes_validated_at"]
    assert saved[0]["bandcamp_validated_at"] is None
    assert saved[0]["beatport_validated_at"] is None


def test_unknown_route_is_404(app):
    assert app.lambda_handler(make_event("GET", "/nope"), None)["statusCode"] == 404


@pytest.mark.parametrize("errors", [[], ["bandcamp"]])
def test_legacy_wrong_prices_are_rechecked_and_never_used_as_fallback(app, track_db, monkeypatch, errors):
    import datetime
    from sqlalchemy import MetaData, Table

    # The legacy row says The Weeknd because it copied the request, although its
    # Bandcamp URL/price actually came from vayd's cover. No stored field proves
    # a matched store identity, even for rows written during a rolling release.
    table = Table("track", MetaData(), autoload_with=track_db)
    with track_db.begin() as connection:
        connection.execute(table.insert().values(
            track_name="Blinding Lights", artist="The Weeknd",
            bandcamp_price=0, bandcamp_url="https://vayd.bandcamp.com/track/blinding-lights",
            created_at=datetime.datetime(2026, 10, 17),
        ))
    calls = []

    def prices(artist, name, stores):
        assert stores == ["itunes", "bandcamp", "beatport"]
        calls.append((artist, name))
        return {
            "itunes_price": 1.29, "itunes_url": "https://itunes.example/original",
            "beatport_price": 1.49, "beatport_url": "https://beatport.example/original",
            "bandcamp_price": -1, "bandcamp_url": "", "errors": errors,
            "created_at": datetime.datetime(2026, 10, 18),
        }

    monkeypatch.setattr(app, "get_api_prices", prices)
    body = json.dumps({"tracks": [{"name": "Blinding Lights", "artist": "The Weeknd"}]})
    result = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert result["statusCode"] == 200
    row = json.loads(result["body"])[0]
    assert calls == [("The Weeknd", "Blinding Lights")]
    assert row["bandcamp_price"] == -1
    assert row["bandcamp_url"] == ""
    assert row["itunes_price"] == 1.29
    with track_db.connect() as connection:
        stored = connection.execute(table.select()).mappings().all()
    assert len(stored) == 1
    # A failed provider does not overwrite stored data, which is never trusted
    # on POST; successful N/A replaces the stale cover in the historical row.
    assert stored[0]["bandcamp_price"] == (0 if errors else -1)


@pytest.mark.parametrize("store", ["itunes", "bandcamp", "beatport"])
@pytest.mark.parametrize("invalid", ["expired", "old_matcher", "unvalidated", "wrong_identity", "future"])
def test_only_invalid_store_is_rechecked(app, track_db, monkeypatch, store, invalid):
    import datetime
    from sqlalchemy import MetaData, Table
    from price_cache import utcnow

    calls = []

    def prices(artist, title, stores):
        calls.append(stores)
        return validated_prices(artist, title, stores)

    monkeypatch.setattr(app, "get_api_prices", prices)
    body = json.dumps({"tracks": [{"name": "Song A", "artist": "X"}]})
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    table = Table("track", MetaData(), autoload_with=track_db)
    invalid_fields = {
        "expired": {f"{store}_validated_at": utcnow() - datetime.timedelta(days=8)},
        "old_matcher": {f"{store}_matcher_version": "older-matcher"},
        "unvalidated": {f"{store}_validated_at": None},
        "wrong_identity": {f"{store}_matched_artist": "Cover Artist"},
        "future": {f"{store}_validated_at": utcnow() + datetime.timedelta(days=1)},
    }
    with track_db.begin() as connection:
        connection.execute(table.update().values(**invalid_fields[invalid]))
        before = dict(connection.execute(table.select()).mappings().one())
    response = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert response["statusCode"] == 200
    assert calls == [["itunes", "bandcamp", "beatport"], [store]]
    assert json.loads(response["body"])[0]["errors"] == []
    with track_db.connect() as connection:
        after = connection.execute(table.select()).mappings().one()
    for other in ("itunes", "bandcamp", "beatport"):
        if other != store:
            assert before[f"{other}_validated_at"] == after[f"{other}_validated_at"]
    # Revalidated matches and no-match results are reusable immediately.
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert len(calls) == 2


def test_freshness_window_setting_and_expiry_boundary(app, track_db, monkeypatch):
    import datetime
    from sqlalchemy import MetaData, Table
    from price_cache import utcnow

    now = utcnow()
    monkeypatch.setattr(app, "utcnow", lambda: now)
    monkeypatch.setenv("PRICE_CACHE_TTL_SECONDS", "60")
    calls = []

    def prices(artist, title, stores):
        calls.append(stores)
        return validated_prices(artist, title, stores)

    monkeypatch.setattr(app, "get_api_prices", prices)
    body = json.dumps({"tracks": [{"name": "Song A", "artist": "X"}]})
    # Pin service timestamps to the same clock as the lookup.
    def pinned_prices(artist, title, stores):
        result = prices(artist, title, stores)
        for store in stores:
            result[f"{store}_validated_at"] = now
        return result

    monkeypatch.setattr(app, "get_api_prices", pinned_prices)
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    table = Table("track", MetaData(), autoload_with=track_db)
    with track_db.begin() as connection:
        connection.execute(table.update().values(
            itunes_validated_at=now - datetime.timedelta(seconds=60),
            beatport_validated_at=now - datetime.timedelta(seconds=59),
        ))
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert calls[-1] == ["itunes"]
    monkeypatch.setenv("PRICE_CACHE_TTL_SECONDS", "0")
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert calls[-1] == ["itunes", "bandcamp", "beatport"]


def test_partial_store_failure_saves_successes_and_retries_only_failure(app, track_db, scraper, monkeypatch):
    import datetime
    import search_tracks
    from sqlalchemy import MetaData, Table
    from search.matching import store_result

    monkeypatch.setattr(search_tracks, "PLAYWRIGHT_API_URL", "https://scraper.example")
    itunes_calls = []

    def itunes(artist, title):
        itunes_calls.append((artist, title))
        return store_result(1.29, "https://itunes.example/a", artist, title)

    monkeypatch.setattr(search_tracks.ItuneSearch, "search_song", itunes)
    calls = []
    fail = False

    def bandcamp(self, title, artist):
        if fail:
            raise TimeoutError("provider unavailable")
        return store_result(0.99, "https://bandcamp.example/a", artist, title)

    monkeypatch.setattr(scraper.BandcampSearch, "search_song", bandcamp)

    def proxy_post(url, json, timeout):
        import json as json_module

        calls.append(json["stores"])
        response = scraper.lambda_handler({"body": json_module.dumps(json)}, None)
        return FakeResponse(json_module.loads(response["body"]), response["statusCode"])

    monkeypatch.setattr(search_tracks.requests, "post", proxy_post)
    body = json.dumps({"tracks": [{"name": "Song A", "artist": "X"}]})
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    table = Table("track", MetaData(), autoload_with=track_db)
    stale = datetime.datetime(2020, 1, 1)
    with track_db.begin() as connection:
        connection.execute(table.update().values(bandcamp_validated_at=stale, beatport_validated_at=stale))
    fail = True
    response = app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    row = json.loads(response["body"])[0]
    assert row["errors"] == ["bandcamp"]
    assert (row["itunes_price"], row["beatport_price"], row["bandcamp_price"]) == (1.29, 1.49, -1)
    assert row["bandcamp_url"] == ""
    with track_db.connect() as connection:
        saved = connection.execute(table.select()).mappings().one()
    assert saved["bandcamp_validated_at"] == stale
    assert float(saved["bandcamp_price"]) == 0.99
    assert saved["beatport_validated_at"] > stale
    # Recovery only queries the failing store, then all stores are cache hits.
    fail = False
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    app.lambda_handler(make_event("POST", "/db_results", body=body), None)
    assert calls == [["bandcamp", "beatport"], ["bandcamp", "beatport"], ["bandcamp"]]
    assert itunes_calls == [("X", "Song A")]


def test_migration_is_idempotent_and_does_not_validate_legacy_rows(app, track_db):
    import db
    from sqlalchemy import MetaData, Table, inspect

    table = Table("track", MetaData(), autoload_with=track_db)
    with track_db.begin() as connection:
        connection.execute(table.insert().values(track_name="Song A", artist="X", itunes_price=1.29))
    db.reflect_tables(track_db)
    db.reflect_tables(track_db)
    columns = {column["name"] for column in inspect(track_db).get_columns("track")}
    for store in ("itunes", "bandcamp", "beatport"):
        assert {f"{store}_{field}" for field in (
            "matcher_version", "matched_artist", "matched_title", "validated_at")} <= columns
    with track_db.connect() as connection:
        row = connection.execute(db.track_table.select()).mappings().one()
    assert float(row["itunes_price"]) == 1.29
    assert row["itunes_validated_at"] is None
    assert row["itunes_matcher_version"] is None


def test_old_scraper_cannot_certify_current_cache(app, track_db, monkeypatch):
    import search_tracks
    from search.matching import store_result

    monkeypatch.setattr(search_tracks, "PLAYWRIGHT_API_URL", "https://old-scraper.example")
    monkeypatch.setattr(search_tracks.ItuneSearch, "search_song", lambda *args: store_result())
    calls = []

    def old_scraper(url, json, timeout):
        calls.append(json["stores"])
        return FakeResponse({store: {"price": -1, "url": ""} for store in json["stores"]})

    monkeypatch.setattr(search_tracks.requests, "post", old_scraper)
    body = json.dumps({"tracks": [{"name": "Song A", "artist": "X"}]})
    for _ in range(2):
        assert app.lambda_handler(make_event("POST", "/db_results", body=body), None)["statusCode"] == 200
    saved = json.loads(app.lambda_handler(make_event("GET", "/db_results"), None)["body"])[0]
    assert saved["itunes_validated_at"]
    assert saved["bandcamp_validated_at"] is None
    assert saved["beatport_validated_at"] is None
    assert calls == [["bandcamp", "beatport"], ["bandcamp", "beatport"]]
