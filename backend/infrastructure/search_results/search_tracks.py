import datetime
import os
import requests
from search import ItuneSearch

PLAYWRIGHT_API_URL = os.environ.get("PLAYWRIGHT_API_URL")

def get_api_prices(artist, track_name):
    timestamp = datetime.datetime.now()


    itunes_data = ItuneSearch.search_song(artist, track_name)


    bandcamp_data = {"price": -1, "url": ""}
    beatport_data = {"price": -1, "url": ""}

    # Call the Playwright Lambda for Bandcamp & Beatport
    if PLAYWRIGHT_API_URL:
        try:
            response = requests.post(
                f"{PLAYWRIGHT_API_URL}",
                json={"artist": artist, "track_name": track_name},
                timeout=25
            )
            if response.status_code == 200:
                data = response.json()
                bandcamp_data = data.get("bandcamp", bandcamp_data)
                beatport_data = data.get("beatport", beatport_data)
            else:
                print(f"Playwright Lambda returned {response.status_code}")
        except Exception as e:
            print(f"Error calling Playwright Lambda: {e}")

    return {
        "itunes_price": itunes_data.get("price"),
        "itunes_url": itunes_data.get("url"),
        "bandcamp_price": bandcamp_data.get("price"),
        "bandcamp_url": bandcamp_data.get("url"),
        "beatport_price": beatport_data.get("price"),
        "beatport_url": beatport_data.get("url"),
        "created_at": timestamp
    }
