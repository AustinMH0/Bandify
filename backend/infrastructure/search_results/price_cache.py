"""Per-store validation and freshness; legacy rows are never trusted."""
import datetime
import os

from search.matching import MATCHER_VERSION, match_rank

STORES = ("itunes", "bandcamp", "beatport")
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60
PROVENANCE_FIELDS = ("matcher_version", "matched_artist", "matched_title", "validated_at")


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def cache_ttl():
    # Zero disables reuse. A malformed setting falls back to the documented default.
    try:
        return datetime.timedelta(seconds=max(0, int(os.environ.get(
            "PRICE_CACHE_TTL_SECONDS", DEFAULT_TTL_SECONDS))))
    except ValueError:
        return datetime.timedelta(seconds=DEFAULT_TTL_SECONDS)


def has_provenance(row, store, artist, title):
    if row.get(f"{store}_matcher_version") != MATCHER_VERSION:
        return False
    price, url = row.get(f"{store}_price"), row.get(f"{store}_url")
    credited = row.get(f"{store}_matched_artist")
    candidate = row.get(f"{store}_matched_title")
    # A completed no-match search has no matched identity. It can be cached, but
    # transport failures and old scraper responses carry no matcher version.
    if price == -1 and url == "" and not credited and not candidate:
        return True
    return price is not None and bool(url) and match_rank(artist, title, credited, candidate) is not None


def is_fresh(row, store, artist, title, now):
    validated_at = row.get(f"{store}_validated_at")
    if not isinstance(validated_at, datetime.datetime) or not has_provenance(row, store, artist, title):
        return False
    # SQLite and older TIMESTAMP columns return naive datetimes. All validation
    # timestamps written by this application are UTC.
    if validated_at.tzinfo is None:
        validated_at = validated_at.replace(tzinfo=datetime.timezone.utc)
    return datetime.timedelta(0) <= now - validated_at < cache_ttl()
