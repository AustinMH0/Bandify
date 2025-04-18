from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS

from ..search import ItuneSearch

itunes_bp = Blueprint('itunes_bp', __name__)

@itunes_bp.route('/itunes_result', methods=['POST'])
def get_itunes_result():
    data = request.get_json()

    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400

    def process_track(track):
        artist = track.get('artist')
        name = track.get('name')

        # print(f'\nOriginal artist: {artist}')
        # print(f'Track name: {name}')

        if not artist or not name:
            return {'error': 'Missing artist or track name'}
            
        main_artist = artist.split(',')[0].strip()
        # print(f'Using main_artist: {main_artist}')

        iSearch = ItuneSearch()

        try:
            search = iSearch.search_song(main_artist, name)
            price = search.get('price', -1)
            url = search.get('url', '')

            # print(f'Price from iTunes: {price}')
            # print(f'Track URL: {url}')

            if price == -1:
                return {'name': name, 'artist': artist, 'error': 'Track not found on iTunes'}
            else:
                return {'name': name, 'artist': artist, 'price': price, 'url': url}
        except Exception as e:
            return {'name': name, 'artist': artist, 'error': f'Error: {str(e)}'}

        # Use ThreadPoolExecutor to run searches concurrently
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_track, tracks))

    return jsonify(results)