import requests
from urllib.parse import quote

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

            results = jsResponse.get('results', [])
            for result in results:
                if result['kind'] == 'song':
                    track_url = result['trackViewUrl']
                    if 'music.apple.com' in track_url:
                        track_url = track_url.replace('music.apple.com', 'geo.itunes.apple.com')
                        track_url += '?ls=1&app=itunes'
                        # print(f'Track URL: {track_url}')
                        
                    return {
                        'price': result.get('trackPrice', -1),
                        'url': track_url
                    }

        except requests.exceptions.RequestException as e:
            print(f'iTunes lookup failed: {type(e).__name__}')
            return {'price': -1, 'url': '', 'error': 'itunes'}

        #sleep(2)
        return {'price': -1, 'url': ''}
