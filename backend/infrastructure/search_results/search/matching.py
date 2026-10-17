"""Conservative store identity matching; keep both Lambda copies identical."""
import re
import unicodedata


def normalize(value):
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", value).split())


def artist_matches(requested, credited):
    """Match whole artist identities, never substrings (e.g. Weeknd tribute)."""
    def identity(value):
        return normalize(value).replace(" ", "")

    def credits(value):
        # Spotify uses commas; store credits also use feat., ft., &, and +.
        parts = re.split(r"\s*(?:,|&|\+|;|\b(?:feat(?:uring)?|ft)\b\.?|\band\b)\s*",
                         value, flags=re.IGNORECASE)
        return {identity(part) for part in parts if identity(part)}

    if not identity(requested) or not identity(credited):
        return False
    if identity(requested) == identity(credited):
        return True
    wanted = credits(requested)
    actual = credits(credited)
    # Preserve group names containing a separator when listed among credits.
    return identity(requested) in actual or (bool(wanted) and wanted <= actual)


def title_rank(requested, candidate):
    """Exact titles first; only tolerate the store's Original Mix suffix.

    No fuzzy/subtitle stripping: covers, remixes, karaoke, tribute and
    instrumental versions must be explicitly present in the requested title.
    """
    expected, actual = normalize(requested), normalize(candidate)
    if not expected or not actual:
        return None
    if expected == actual:
        return 0
    original = re.sub(r"\s+original mix$", "", actual)
    if original == expected:
        return 1
    return None


def match_rank(artist, title, credited_artist, candidate_title):
    if not artist_matches(artist, credited_artist):
        return None
    return title_rank(title, candidate_title)
