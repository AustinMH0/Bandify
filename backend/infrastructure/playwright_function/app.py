import base64
import json
import hashlib
import hmac
import os
import time
from concurrent.futures import ThreadPoolExecutor
from search import BandcampSearch, BeatportSearch

def lambda_handler(event, context):
    # This endpoint is internal to SearchResults. A browser session alone cannot
    # bypass its app-wide admission gate by calling the scraper directly.
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    credential = headers.get("authorization", "")
    secret = os.environ.get("SESSION_SECRET", "")
    if not secret or not credential.startswith("Bearer "):
        return {"statusCode": 401, "body": json.dumps({"error": "Unauthorized"})}
    try:
        payload = {key: value for key, value in event.items() if key != "headers"}
        if "body" in event:
            body = event.get("body") or "{}"
            if not isinstance(body, str) or len(body.encode("utf-8")) > 4096:
                return {"statusCode": 413, "body": json.dumps({"error": "Request too large"})}
            if event.get("isBase64Encoded"):
                body = base64.b64decode(body, validate=True).decode("utf-8")
            payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Expected an object")
    except (ValueError, UnicodeError, TypeError):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}

    try:
        timestamp, signature = credential[7:].split(".", 1)
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        message = f"bandify-scraper-v1\n{timestamp}\n{body}".encode()
        expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        valid = abs(time.time() - int(timestamp)) <= 30 and hmac.compare_digest(expected, signature)
    except (ValueError, TypeError):
        valid = False
    if not valid:
        return {"statusCode": 401, "body": json.dumps({"error": "Unauthorized"})}

    artist = payload.get("artist")
    track_name = payload.get("track_name")

    if any(not isinstance(value, str) or not value.strip() or len(value) > 300
           or any(ord(c) < 32 or 0x7f <= ord(c) <= 0x9f or 0xd800 <= ord(c) <= 0xdfff for c in value) for value in (artist, track_name)):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid artist or track_name"})
        }

    stores = payload.get("stores", ["bandcamp", "beatport"])
    if not isinstance(stores, list) or not stores or any(
        store not in ("bandcamp", "beatport") for store in stores
    ):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid stores"})}

    results = {}
    errors = []
    # Each provider owns its browser in its own thread. One store failing must
    # neither discard another store's price nor serialize both browser waits.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            name: pool.submit(search().search_song, track_name, artist)
            for name, search in [("bandcamp", BandcampSearch), ("beatport", BeatportSearch)]
            if name in stores
        }
        for name, future in futures.items():
            try:
                results[name] = future.result()
            except Exception as exc:
                print(f"{name} lookup failed: {type(exc).__name__}")
                results[name] = {"price": -1, "url": ""}
                errors.append(name)
    results["errors"] = errors
    return {"statusCode": 200, "body": json.dumps(results)}
