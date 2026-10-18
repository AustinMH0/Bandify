# Bandify

# Testing Workflow

# Spotify sign-in

"Login with Spotify" sends the browser to `<API>/login`, which redirects to Spotify. Spotify returns to `<API>/callback`, and the API sends the user back to the front end with an encrypted session in the URL fragment. The front end keeps it in `sessionStorage` and sends it as `Authorization: Bearer <session>` to `/get_playlists`, `/get_tracks/<playlist id>` and `/db_results` (GET and POST).

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

Foundation request controls: POST `/db_results` accepts exactly one track with
nonempty `name` and `artist` strings (at most 300 characters each, no control
characters) and a JSON body of at most 4 KiB. Price authentication validates the
existing seven-day encrypted session locally; it does not refresh Spotify.
Playlist discovery is shared across the page, including React StrictMode mounts.
Spotify item requests use 50-item pages and follow every `next` cursor. Access
errors (403/404) are returned without probing the deprecated tracks endpoint;
Spotify 429 responses preserve `Retry-After`.

Only iTunes/Apple Search API cache misses use the shared database-backed
admission slot across SearchResults instances, with at least six seconds between
Apple calls (at most ten per minute). Bandcamp and Beatport do not acquire the
slot and have no app-wide spacing: they retain their existing per-request
bounded parallelism and timeouts. A busy Apple slot returns available browser
prices immediately, with an `itunes_retry_after` delay on that track. The
existing UI shows those prices while keeping its ripple during up to two Apple
retries, then uses its existing retry message if Apple remains busy. Successful
browser-store results are cached, so Apple retries do not repeat them. Fully
cached results bypass all admission and store requests. No automatic prefetch or
background jobs run.

The first Apple cache miss creates the singleton `itunes_search_admission`
table in the existing database; the runtime role needs `CREATE TABLE` and
read/write access to that table. An operator can instead provision it ahead of
rollout using the DDL in `search_results/admission.py`. Leases expire after 60
seconds (longer than the 28-second coordinator deadline), survive Lambda
termination, and cannot be released by a previous owner. The slot releases as
soon as the Apple call settles; browser requests and timeouts never hold it.
Database transactions are closed during external searches. Apple admission fails
closed when the database is unavailable.

The scraper requires short-lived, payload-bound internal signatures from the
authenticated coordinator; public browser sessions cannot call it directly.
Both stacks use the existing `SESSION_SECRET`; the deployment
workflow passes it to the scraper as well. Release the scraper before
SearchResults. An older coordinator will see scraper authentication failures
during that rollout window and can retry afterward. No secret rotation or new
AWS resources are needed. Keep the coordinator timeout below the Apple admission
lease when changing deployment settings.
