import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class BeatportSearch:
    def __init__(self):
        pass

    def clean_track_name(self, name: str) -> str:
        # Ensure ' original mix' is removed cleanly, including spacing
        name = re.sub(r'\s*\(original mix\)', '', name, flags=re.IGNORECASE)  # for '(Original Mix)'
        name = re.sub(r'\s*original mix', '', name, flags=re.IGNORECASE)      # for 'Original Mix' with or without space
        name = re.sub(r'\s+', ' ', name)  # normalize spaces
        return name.strip().lower()

    def search_song(self, track_name: str, artist_name: str) -> dict:
        query = f'{track_name} {artist_name}'
        search_url = f'https://www.beatport.com/search?q={quote(query)}'

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(search_url, timeout=0)
            page.wait_for_timeout(500)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')

        result_row = soup.find('div', class_=lambda c: c and 'TableRow' in c)
        if not result_row:
            return {'price': -1, 'url': ''}

        # Extract artist
        artist_div = result_row.find('div', class_=lambda c: c and 'ArtistNames' in c)
        scraped_artist = ''
        if artist_div:
            artist_tag = artist_div.find('a', title=True)
            if artist_tag:
                scraped_artist = artist_tag['title'].strip().lower()

        # Extract track
        track_span = result_row.find('span', class_=lambda c: c and 'ReleaseName' in c)
        scraped_track = track_span.get_text(strip=True).lower() if track_span else ''

        expected_artist = artist_name.strip().lower()
        expected_track = track_name.strip().lower()

        # print(f'\nScraped track: {scraped_track}')
        # print(f'Scraped artist: {scraped_artist}')
        # print(f'Expected track: {expected_track}')
        # print(f'Expected artist: {expected_artist}')

        if self.clean_track_name(scraped_track) != expected_track or scraped_artist != expected_artist:
            return {'price': -1, 'url': ''}

        # Get price and URL
        anchor = result_row.find('a', href=True, title=True)
        full_track_url = f"https://www.beatport.com{anchor['href']}" if anchor else ''

        price_span = result_row.find('span', class_='price')
        price = -1
        if price_span:
            price_text = price_span.get_text(strip=True).replace('$', '')
            try:
                price = float(price_text)
            except ValueError:
                price = -1

        return {'price': price, 'url': full_track_url}