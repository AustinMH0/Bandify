import json
import requests
from urllib.parse import quote
from time import sleep
from fake_useragent import UserAgent
from difflib import SequenceMatcher

class ItuneSearch:
    def __init__(self):
        pass

    @staticmethod
    def search_song(artistName: str, trackName: str) -> float:
        # Put track name first in search term
        parameters = f"{trackName} {artistName}"
        url = f"https://itunes.apple.com/search?term={quote(parameters)}&entity=musicTrack&attribute=mixTerm&explicit=Yes"
        
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            jsResponse = response.json()
            
            for result in jsResponse.get("results", []):
                if result.get("kind") == "song":
                    print(f"Found match: {result['trackName']} by {result['artistName']}")
                    return result.get("trackPrice", -1)
        except requests.exceptions.RequestException as e:
            print(f"iTunes error: {e}")
        
        return -1

