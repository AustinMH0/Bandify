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
