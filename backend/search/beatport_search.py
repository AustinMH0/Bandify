import requests
from urllib.parse import quote
from time import sleep
from fake_useragent import UserAgent

import concurrent.futures
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import quote

class BeatportSearch:
    def __init__(self):
        pass

    def search_song(self, track_name: str, artist_name: str) -> dict:
        query = f"{track_name} {artist_name}"
        search_url = f"https://www.beatport.com/search?q={quote(query)}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(search_url, timeout=0)

            page.wait_for_timeout(100)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        titles = soup.find_all("span", class_=lambda c: c and "ReleaseName" in c)
        prices = soup.find_all("span", class_="price")

        # print(f"Found {len(titles)} titles and {len(prices)} prices for {track_name} by {artist_name}")

        for title, price in zip(titles, prices):
            title_text = title.get_text(strip=True).lower()
            price_text = price.get_text(strip=True).replace("$", "")

            if track_name.lower() in title_text:
                # Try to get parent anchor tag
                parent_link = title.find_parent("a")
                track_href = parent_link["href"] if parent_link and parent_link.has_attr("href") else None
                track_url = f"https://www.beatport.com{track_href}" if track_href else search_url

                try:
                    return {
                        "price": float(price_text),
                        "url": track_url
                    }
                except ValueError:
                    continue

        return {"price": -1, "url": search_url}

    def search_multiple_tracks(self, tracks: list) -> list:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.search_song, track['name'], track['artist']): track for track in tracks}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        return results

# # Example of how to use it
# if __name__ == "__main__":
#     bp = BeatportSearch()

#     # Example list of tracks to search for
#     tracks_to_search = [
#         {"name": "Blood", "artist": "Boneless"},
#         {"name": "Hypnotized", "artist": "AVOR"},
#         {"name": "Clear Cut", "artist": "GLM"}
#     ]

#     # Get the results for all tracks
#     results = bp.search_song("Blood", "Boneless")

#     # Print the results
#     print(results)
