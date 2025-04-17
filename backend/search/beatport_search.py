from urllib.parse import quote
import concurrent.futures
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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

        result_row = soup.find("div", class_=lambda c: c and "TableRow" in c)
        price = -1
        full_track_url = ""

        if result_row:
            anchor = result_row.find("a", href=True, title=True)
            price_span = result_row.find("span", class_="price")

            if anchor:
                full_track_url = f"https://www.beatport.com{anchor['href']}"
            if price_span:
                price_text = price_span.get_text(strip=True).replace("$", "")
                try:
                    price = float(price_text)
                except ValueError:
                    price = -1

        return {"price": price, "url": full_track_url}

    # def search_multiple_tracks(self, tracks: list) -> list:
    #     results = []
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    #         futures = {executor.submit(self.search_song, track['name'], track['artist']): track for track in tracks}
    #         for future in concurrent.futures.as_completed(futures):
    #             result = future.result()
    #             results.append(result)
    #     return results

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
