"""Regressions for the real scraper HTTP boundary and provider failures."""
import base64
import json
import time

import pytest


def authenticated_event(payload):
    from search_tracks import scraper_headers
    if "body" in payload:
        raw = payload.get("body") or "{}"
        try:
            if payload.get("isBase64Encoded"):
                raw = base64.b64decode(raw, validate=True).decode()
            body = json.loads(raw)
        except (ValueError, UnicodeError):
            body = {}
    else:
        body = payload
    return {**payload, "headers": scraper_headers(body)}


def test_scraper_accepts_the_api_gateway_proxy_event(scraper):
    payload = {"artist": "X", "track_name": "New Song"}
    # The exact JSON sent by requests.post becomes event.body in a REST API.
    response = scraper.lambda_handler(authenticated_event({
        "httpMethod": "POST", "body": json.dumps(payload), "isBase64Encoded": False,
    }), None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["bandcamp"]["price"] == 0.99


def test_direct_payload_counterfactual(scraper):
    response = scraper.lambda_handler(authenticated_event({"artist": "X", "track_name": "New Song"}), None)
    assert response["statusCode"] == 200


def test_scraper_accepts_base64_proxy_body(scraper):
    body = base64.b64encode(json.dumps({"artist": "X", "track_name": "New Song"}).encode()).decode()
    response = scraper.lambda_handler(authenticated_event({"body": body, "isBase64Encoded": True}), None)
    assert response["statusCode"] == 200


@pytest.mark.parametrize("event", [
    {"body": "not json"}, {"body": "[]"}, {"body": "null"},
    {"body": "{}"}, {}, {"artist": "X"},
    {"body": "invalid base64", "isBase64Encoded": True},
])
def test_scraper_rejects_invalid_requests(scraper, event):
    assert scraper.lambda_handler(authenticated_event(event), None)["statusCode"] == 400


def test_one_store_failure_preserves_the_other_price(scraper, monkeypatch):
    def unavailable(*args):
        raise TimeoutError("store unavailable")

    monkeypatch.setattr(scraper.BandcampSearch, "search_song", unavailable)
    response = scraper.lambda_handler(authenticated_event({"artist": "X", "track_name": "New Song"}), None)
    data = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert data["bandcamp"]["price"] == -1
    assert data["beatport"]["price"] == 1.49
    assert data["errors"] == ["bandcamp"]


def test_scraper_skips_fresh_store(scraper, monkeypatch):
    def must_not_search(*args):
        raise AssertionError("Fresh store must not be queried")

    monkeypatch.setattr(scraper.BandcampSearch, "search_song", must_not_search)
    response = scraper.lambda_handler(authenticated_event({"artist": "X", "track_name": "New Song", "stores": ["beatport"]}), None)
    data = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert "bandcamp" not in data
    assert data["beatport"]["price"] == 1.49
    assert data["errors"] == []


@pytest.mark.parametrize("stores", [[], "beatport", ["itunes"], None])
def test_scraper_rejects_invalid_store_selection(scraper, stores):
    response = scraper.lambda_handler(authenticated_event({"artist": "X", "track_name": "New Song", "stores": stores}), None)
    assert response["statusCode"] == 400


def test_scraper_rejects_unsigned_and_browser_sessions(scraper, monkeypatch):
    def no_search(*args):
        pytest.fail("Unauthorized requests must not search stores")
    monkeypatch.setattr(scraper.BandcampSearch, "search_song", no_search)
    monkeypatch.setattr(scraper.BeatportSearch, "search_song", no_search)
    for headers in ({}, {"Authorization": "Bearer fake-browser-session"}):
        response = scraper.lambda_handler({"body": json.dumps({"artist": "X", "track_name": "Song"}),
                                           "headers": headers}, None)
        assert response["statusCode"] == 401


def test_scraper_signature_expires_and_binds_payload(scraper, monkeypatch):
    event = authenticated_event({"body": json.dumps({"artist": "X", "track_name": "Song"})})
    tampered = {**event, "body": json.dumps({"artist": "Y", "track_name": "Song"})}
    assert scraper.lambda_handler(tampered, None)["statusCode"] == 401
    now = time.time()
    monkeypatch.setattr(scraper.time, "time", lambda: now + 31)
    assert scraper.lambda_handler(event, None)["statusCode"] == 401
