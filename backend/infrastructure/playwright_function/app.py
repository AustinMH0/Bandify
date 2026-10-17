import base64
import json
from concurrent.futures import ThreadPoolExecutor
from search import BandcampSearch, BeatportSearch

def lambda_handler(event, context):
    
    try:
        payload = event
        if "body" in event:
            body = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                body = base64.b64decode(body, validate=True).decode("utf-8")
            payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Expected an object")
    except (ValueError, UnicodeError, TypeError):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}

    artist = payload.get("artist")
    track_name = payload.get("track_name")

    if not artist or not track_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing artist or track_name"})
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
