import json
import requests
from urllib.parse import quote


class ItuneSearch:


    def __init__(self):
        pass

    @staticmethod   
    def search_song(artistName, trackName) -> float:

        parameters = f"{artistName} {trackName}" #itunes search terms

        url = f"https://itunes.apple.com/search?term={quote(parameters)}&entity=musicTrack&attribute=mixTerm&explicit=Yes"
        response = requests.get(url) # fetch json object
        response.raise_for_status()
        
        jsResponse = json.loads(response.text) # convert response content to dictionary
        
        results = jsResponse["results"]
        for result in results:
            if result["kind"] == "song" and result["trackName"] == trackName:
                return result["trackPrice"] # return track price (assumes that first track in "results" that has a matching name is the one we want)
        
        return -1 # if not found return -1    
        
        # print(url)
        # print(parameters)






