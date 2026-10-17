from bs4 import BeautifulSoup
from urllib.parse import quote
from time import monotonic
from .browser import page_html
from .matching import match_rank
import re
from .currency_converter import CurrencyConverter


class BandcampSearch:
    def search_song(self, track_name: str, artist_name: str) -> dict:
        deadline = monotonic() + 9
        query = f'{track_name} {artist_name}'
        search_url = f'https://bandcamp.com/search?q={quote(query)}&item_type=t'
        soup = BeautifulSoup(page_html(search_url, deadline), 'html.parser')
        matches = []
        for row in soup.select('li.searchresult'):
            heading = row.select_one('.heading a')
            subhead = row.select_one('.subhead')
            if not heading or not heading.get('href') or not subhead:
                continue
            credited = re.sub(r'^by\s+', '', subhead.get_text(" ", strip=True), flags=re.I)
            rank = match_rank(artist_name, track_name, credited, heading.get_text(" ", strip=True))
            if rank is not None:
                matches.append((rank, heading['href']))
        if not matches:
            return {'price': -1, 'url': ''}

        track_url = min(matches, key=lambda item: item[0])[1]
        track_soup = BeautifulSoup(page_html(track_url, deadline), 'html.parser')
        # Search snippets may be stale: confirm identity on the purchase page too.
        title = track_soup.select_one('h2.trackTitle')
        artist = track_soup.select_one('#name-section h3 a')
        if not title or not artist or match_rank(
            artist_name, track_name, artist.get_text(" ", strip=True), title.get_text(" ", strip=True)
        ) is None:
            return {'price': -1, 'url': ''}

        price = -1
        buy_item = track_soup.select_one('li.buyItem:has(h4:-soup-contains("Buy Digital Track"))')
        if buy_item:
            nyp = buy_item.find('span', string=lambda text: text and 'name your price' in text.lower())
            price_span = buy_item.select_one('span.base-text-color')
            if nyp:
                price = 0.0
            elif price_span:
                match = re.match(r'([^\d]+)?([\d.]+)', price_span.get_text(strip=True))
                if match:
                    symbol = match.group(1).strip() if match.group(1) else '$'
                    amount = float(match.group(2))
                    currency = {'€': 'EUR', '£': 'GBP', '$': 'USD', '¥': 'JPY'}.get(symbol)
                    if currency and currency != 'USD':
                        price = CurrencyConverter.convert_to_usd(currency, amount)
                    elif currency == 'USD':
                        price = round(amount, 2)
        return {'price': price, 'url': track_url}
