from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from time import monotonic
from .browser import page_html
from .matching import match_rank, store_result


class BeatportSearch:
    def search_song(self, track_name: str, artist_name: str) -> dict:
        query = f'{track_name} {artist_name}'
        search_url = f'https://www.beatport.com/search?q={quote(query)}'
        soup = BeautifulSoup(page_html(search_url, monotonic() + 9), 'html.parser')
        matches = []
        for row in soup.find_all('div', class_=lambda c: c and 'TableRow' in c):
            artists = row.find('div', class_=lambda c: c and 'ArtistNames' in c)
            title = row.find('span', class_=lambda c: c and 'ReleaseName' in c)
            if not artists or not title:
                continue
            credited = ', '.join(a.get('title') or a.get_text(" ", strip=True)
                                 for a in artists.find_all('a'))
            # Include separately rendered mix labels instead of silently accepting
            # a remix whose base title happens to match the Spotify track.
            mix = row.find('span', class_=lambda c: c and 'TrackName' in c)
            candidate = title.get_text(" ", strip=True)
            if mix and mix is not title:
                candidate += ' ' + mix.get_text(" ", strip=True)
            rank = match_rank(artist_name, track_name, credited, candidate)
            anchor = row.select_one('a[href*="/track/"]')
            if rank is not None and anchor:
                matches.append((rank, row, anchor['href'], credited, candidate))
        if not matches:
            return store_result()

        _, row, href, credited, candidate = min(matches, key=lambda item: item[0])
        price_span = row.find('span', class_='price')
        try:
            price = float(price_span.get_text(strip=True).replace('$', '')) if price_span else -1
        except ValueError:
            price = -1
        return store_result(price, urljoin('https://www.beatport.com', href), credited, candidate)
