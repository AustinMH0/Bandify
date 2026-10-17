# Bandify

# Testing Workflow

# Spotify sign-in

"Login with Spotify" sends the browser to `<API>/login`, which redirects to Spotify. Spotify returns to `<API>/callback`, and the API sends the user back to the front end with an encrypted session in the URL fragment. The front end keeps it in `sessionStorage` and sends it as `Authorization: Bearer <session>` to `/get_playlists` and `/get_tracks/<playlist id>`.

Settings the deploy workflow needs as GitHub Actions secrets:

| Secret | What it is |
| --- | --- |
| `SPOTIFY_CLIENT_ID` | Client ID of the Spotify app |
| `SPOTIFY_CLIENT_SECRET` | Client secret of the Spotify app |
| `SESSION_SECRET` | Random string of at least 32 characters, e.g. `openssl rand -base64 48`. Keep it fixed: changing it signs everyone out |

The redirect URI registered in the Spotify developer dashboard must be exactly `<API>/callback` (the `SpotifyRedirectUri` output of `searchresults-stack`).

Backend tests: `pip install -r backend/infrastructure/search_results/requirements.txt pytest`, then `pytest backend/infrastructure/tests/unit`.

Price-search UI checks: `cd frontend && npm ci && npx playwright install chromium`,
then `npm run test:e2e`. These headless tests use fake Spotify/store responses and
need no credentials. `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` can select an existing
Chromium, and `PLAYWRIGHT_OUTPUT_DIR` can redirect test artifacts (default: `/tmp/bandify-playwright-results`).

Store matching requires matching artist credits and an exact normalized title
(or the store's `Original Mix` suffix). Unrequested cover/remix/karaoke/tribute/
instrumental versions return N/A. POST price lookups reuse each store's saved
price only when its matched identity and matcher version are validated and its
validation timestamp is fresh. `PRICE_CACHE_TTL_SECONDS` on SearchResults sets
the freshness window (default `604800`, seven days; `0` disables reuse). Completed
no-match searches also expire after this window. Failed stores are retried on
the next lookup; successful stores are saved independently. Stale or unvalidated
prices are never returned as a fallback when a store fails.

On deploy, release the Playwright scraper before SearchResults (the existing
workflow already uses this order). On its first database access, SearchResults'
existing lazy DB setup runs an idempotent migration adding nullable
`<store>_matcher_version`, `<store>_matched_artist`, `<store>_matched_title` and
`<store>_validated_at` columns to `track` for iTunes, Bandcamp and Beatport. The
database role must own `track` or otherwise be permitted to `ALTER TABLE`; if
the runtime role cannot migrate, an operator must run
`python -c 'import db; db.get_engine()'` using a migration-capable `DB_URL`
from the SearchResults source directory before rollout. No price rows are
backfilled as validated: legacy rows and older scraper responses are rechecked.
PostgreSQL timestamps use UTC with time zone. Bump `MATCHER_VERSION` in both
identical `search/matching.py` copies when matching rules or provider identity
extraction change. No frontend migration is needed.
