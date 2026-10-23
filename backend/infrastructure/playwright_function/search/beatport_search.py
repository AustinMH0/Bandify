import json
from time import monotonic
from urllib.parse import quote
from .http import page, amount, DESKTOP_AGENT
from .matching import match_rank, store_result, normalize


class BeatportSearch:
    def search_song(self, track_name: str, artist_name: str) -> dict:
        url = f'https://www.beatport.com/search?q={quote(f"{track_name} {artist_name}")}'
        soup = page(url, monotonic() + 9, DESKTOP_AGENT)
        node = soup.select_one('script#__NEXT_DATA__')
        if not node:
            raise RuntimeError('Unrecognized Beatport search page')
        data = json.loads(node.get_text())
        queries = data['props']['pageProps']['dehydratedState']['queries']
        rows = None
        for query in queries:
            payload = query.get('state', {}).get('data', {})
            if isinstance(payload, dict) and isinstance(payload.get('tracks'), dict):
                rows = payload['tracks'].get('data')
                break
        if not isinstance(rows, list):
            raise RuntimeError('Missing Beatport search results')
        matches = []
        for row in rows:
            credited = ', '.join(a['artist_name'] for a in row['artists'])
            title = row['track_name']
            mix = row.get('mix_name')
            if not isinstance(mix, str) or not mix.strip():
                raise RuntimeError('Missing Beatport mix identity')
            # Do not silently drop remix identity, even when the base title matches.
            candidate = title if normalize(title).endswith(normalize(mix)) else f'{title} ({mix})'
            rank = match_rank(artist_name, track_name, credited, candidate)
            if rank is None:
                continue
            price = row['price']
            if price.get('code') != 'USD':
                raise RuntimeError('Beatport did not return USD prices')
            track_id = row['track_id']
            if isinstance(track_id, bool) or not isinstance(track_id, int) or track_id <= 0:
                raise ValueError('Invalid Beatport track ID')
            slug = '-'.join(normalize(title).split())
            matches.append((rank, store_result(amount(price['value']),
                f'https://www.beatport.com/track/{quote(slug)}/{track_id}', credited, candidate)))
        return min(matches, key=lambda item: item[0])[1] if matches else store_result()
