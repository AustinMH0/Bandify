import requests
from urllib.parse import quote
from .matching import match_rank, store_result

class ItuneSearch:
    def __init__(self):
        pass

    @staticmethod
    def search_song(artistName: str, trackName: str) -> dict:
        parameters = f'{trackName} {artistName}'
        url = f'https://itunes.apple.com/search?term={quote(parameters)}&entity=musicTrack&attribute=mixTerm&explicit=Yes'
        try:
            response = requests.get(url, timeout=(2, 3))
            response.raise_for_status()
            jsResponse = response.json()

            matches = []
            for result in jsResponse.get('results', []):
                if result.get('kind') != 'song':
                    continue
                rank = match_rank(artistName, trackName,
                                  result.get('artistName', ''), result.get('trackName', ''))
                if rank is not None and result.get('trackViewUrl'):
                    matches.append((rank, result))
            if matches:
                result = min(matches, key=lambda item: item[0])[1]
                track_url = result['trackViewUrl']
                if 'music.apple.com' in track_url:
                    track_url = track_url.replace('music.apple.com', 'geo.itunes.apple.com')
                    track_url += '?ls=1&app=itunes'
                return store_result(result.get('trackPrice', -1), track_url,
                                    result['artistName'], result['trackName'])

        except requests.exceptions.RequestException as e:
            print(f'iTunes lookup failed: {type(e).__name__}')
            return {'price': -1, 'url': '', 'error': 'itunes'}

        #sleep(2)
        return store_result()
