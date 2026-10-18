import os
import hashlib
import hmac
import json
import time
import math
import requests
from search import ItuneSearch
from admission import Busy, itunes_slot
from db import get_engine
from price_cache import STORES, PROVENANCE_FIELDS, has_provenance, utcnow

PLAYWRIGHT_API_URL = os.environ.get("PLAYWRIGHT_API_URL")


def get_api_prices(artist, track_name, stores=STORES):
    """Search only requested stores and retain each provider's own provenance."""
    results = {}
    errors = []
    retry_after = None
    if "itunes" in stores:
        try:
            with itunes_slot(get_engine()):
                results["itunes"] = ItuneSearch.search_song(artist, track_name)
            if results["itunes"].get("error"):
                errors.append("itunes")
        except Busy as busy:
            # Apple capacity must never prevent the browser stores from running.
            errors.append("itunes")
            retry_after = time.monotonic() + busy.retry_after

    browser_stores = [store for store in stores if store in ("bandcamp", "beatport")]
    if browser_stores:
        if PLAYWRIGHT_API_URL:
            try:
                response = requests.post(
                    PLAYWRIGHT_API_URL,
                    json={"artist": artist, "track_name": track_name, "stores": browser_stores},
                    headers=scraper_headers({"artist": artist, "track_name": track_name, "stores": browser_stores}),
                    timeout=(2, 16),
                )
                response.raise_for_status()
                data = response.json()
                for store in browser_stores:
                    if not isinstance(data.get(store), dict) or store in data.get("errors", []):
                        errors.append(store)
                    else:
                        results[store] = data[store]
            except Exception as exc:
                print(f"Playwright lookup failed: {type(exc).__name__}")
                errors.extend(browser_stores)
        else:
            errors.extend(browser_stores)

    timestamp = utcnow()
    prices = {"errors": errors, "created_at": timestamp}
    if retry_after is not None:
        # Browser work may have already consumed Apple's cooldown.
        prices["itunes_retry_after"] = max(0, math.ceil(retry_after - time.monotonic()))
    for store in stores:
        result = results.get(store, {}) if store not in errors else {}
        prices[f"{store}_price"] = result.get("price", -1)
        prices[f"{store}_url"] = result.get("url", "")
        for field in PROVENANCE_FIELDS:
            prices[f"{store}_{field}"] = result.get(field) if field != "validated_at" else None
        if store not in errors and has_provenance(prices, store, artist, track_name):
            prices[f"{store}_validated_at"] = timestamp
    return prices


def scraper_headers(payload):
    # Only the authenticated coordinator signs scraper calls.
    # Bind the short-lived signature to the entire payload, using a distinct
    # purpose from the Fernet session key. Never return this credential to clients.
    timestamp = str(int(time.time()))
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"bandify-scraper-v1\n{timestamp}\n{body}".encode()
    signature = hmac.new(os.environ["SESSION_SECRET"].encode(), message, hashlib.sha256).hexdigest()
    return {"Authorization": f"Bearer {timestamp}.{signature}"}
