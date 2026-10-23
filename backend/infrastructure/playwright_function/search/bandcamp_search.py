"""Read an artist site discovered by MusicBrainz; never crawl Bandcamp search."""
import json
import re
from time import monotonic
from urllib.parse import quote, urljoin, urlparse
from .http import page, amount, bandcamp_site
from .matching import match_rank, store_result, normalize
from .currency_converter import CurrencyConverter


def search_link(track, artist):
    return f'https://bandcamp.com/search?q={quote(f"{track} {artist}")}&item_type=t'


class BandcampSearch:
    def __init__(self, sites=()):
        self.sites = sites

    def search_song(self, track_name: str, artist_name: str) -> dict:
        fallback = store_result(url=search_link(track_name, artist_name))
        deadline = monotonic() + 9
        for site in self.sites[:1]:
            site = bandcamp_site(site)
            catalog = page(site + '/music', deadline)
            if not catalog.select_one('#music-grid, [data-tralbum]'):
                raise RuntimeError('Unrecognized Bandcamp artist page')
            links = []
            for anchor in catalog.select('a[href*="/track/"]'):
                if match_rank(artist_name, track_name, artist_name, anchor.get_text(' ', strip=True)) is not None:
                    links.append(urljoin(site, anchor['href']))
            # A title-derived path is only a candidate, never proof of identity.
            # This also reaches older tracks absent from the first catalog page.
            slug = re.sub(r'[^a-z0-9]+', '-', normalize(track_name)).strip('-')
            if slug:
                links.append(site + '/track/' + slug)
            for url in list(dict.fromkeys(links))[:2]:
                url = url.split("?", 1)[0].split("#", 1)[0]
                if bandcamp_site(url) != site or not re.fullmatch(r'/track/[a-zA-Z0-9_-]+/?', urlparse(url).path):
                    continue
                soup = page(url, deadline, missing_ok=True)
                if soup is None:
                    continue
                result = self.track_result(soup, url, track_name, artist_name)
                if result is not None:
                    return result
        return fallback

    @staticmethod
    def track_result(soup, url, track, artist):
        node = soup.select_one('[data-tralbum]')
        if not node:
            raise RuntimeError('Unrecognized Bandcamp track page')
        data = json.loads(node['data-tralbum'])
        current = data['current']
        credited = current.get('artist') or data.get('artist')
        title = current.get('title')
        if current.get('type') != 'track' or match_rank(artist, track, credited, title) is None:
            return None
        # Match the digital release's own ID, not album/CD/vinyl offers nearby.
        for script in soup.select('script[type="application/ld+json"]'):
            document = json.loads(script.string or script.get_text())
            def releases(value):
                if isinstance(value, dict):
                    yield value
                    for child in value.values():
                        yield from releases(child)
                elif isinstance(value, list):
                    for child in value:
                        yield from releases(child)
            for release in releases(document):
                if release.get('musicReleaseFormat') != 'DigitalFormat':
                    continue
                if release.get('@id', '').rstrip('/') != url.rstrip('/'):
                    continue
                offer = release.get('offers', {})
                if not isinstance(offer, dict) or 'price' not in offer:
                    continue
                price = amount(offer['price'])
                currency = offer.get('priceCurrency', '')
                if not re.fullmatch(r'[A-Z]{3}', currency):
                    raise RuntimeError('Missing Bandcamp currency')
                if currency != 'USD':
                    price = amount(CurrencyConverter.convert_to_usd(currency, price))
                return store_result(price, url, credited, title)
        # Recognized identity without a digital offer is not evidence of a price.
        raise RuntimeError('Missing Bandcamp digital track offer')
