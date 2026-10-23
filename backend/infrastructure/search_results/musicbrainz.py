"""Artist-to-Bandcamp discovery under a shared one-request/second budget."""
from time import sleep
from urllib.parse import urlparse
from uuid import UUID
import requests
from admission import musicbrainz_slot
from search.matching import normalize

AGENT = 'Groovonomy/1.0 (https://groovonomy.com; https://github.com/AustinMH0/Bandify)'
BASE = 'https://musicbrainz.org/ws/2/artist/'


def _get(url, params):
    response = requests.get(url, params={**params, 'fmt': 'json'},
                            headers={'User-Agent': AGENT}, timeout=(1, 2),
                            allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError('Unexpected MusicBrainz response')
    return response.json()


def discover_bandcamp_sites(artist, engine):
    with musicbrainz_slot(engine):
        escaped = artist.replace('\\', '\\\\').replace('"', '\\"')
        data = _get(BASE, {'query': f'artist:"{escaped}"', 'limit': 5})
        artists = data['artists']
        if not isinstance(artists, list):
            raise RuntimeError('Unrecognized MusicBrainz search')
        exact = [a for a in artists if normalize(a.get('name')) == normalize(artist)]
        # Same-name artists cannot safely be disambiguated from Spotify text alone.
        if len(exact) != 1:
            return []
        artist_id = str(UUID(exact[0]['id']))
        sleep(1.1)
        data = _get(BASE + artist_id, {'inc': 'url-rels'})
        if data.get('id') != artist_id or normalize(data.get('name')) != normalize(artist):
            raise RuntimeError('MusicBrainz artist identity mismatch')
        sites = []
        for relation in data['relations']:
            if relation.get('type') != 'bandcamp' or relation.get('ended'):
                continue
            url = urlparse(relation.get('url', {}).get('resource', ''))
            host = url.hostname or ''
            if (url.scheme == 'https' and not url.username and not url.password and not url.port
                    and host.endswith('.bandcamp.com') and host.count('.') == 2
                    and host not in ('www.bandcamp.com', 'daily.bandcamp.com')):
                sites.append(f'https://{host}')
        # Multiple artist storefronts are ambiguous; do not guess.
        sites = sorted(set(sites))
        return sites if len(sites) == 1 else []
