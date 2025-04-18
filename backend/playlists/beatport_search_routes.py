from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from ..search import BeatportSearch

beatport_bp = Blueprint('beatport_bp', __name__)

@beatport_bp.route('/beatport_results', methods=['POST'])
def get_beatport_result():
    data = request.get_json()
    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400

    def process_track(track):
        artist = track.get('artist')
        name = track.get('name')

        if not artist or not name:
            return {'error': 'Missing artist or track name'}

        main_artist = artist.split(',')[0].strip()
        bpSearch = BeatportSearch()

        try:
            search = bpSearch.search_song(name, main_artist)
            price = search.get('price', -1)
            url = search.get('url', '')

            if price == -1:
                return {'name': name, 'artist': artist, 'error': 'Track not found on Beatport'}
            else:
                return {'name': name, 'artist': artist, 'price': price, 'url': url}
        except Exception as e:
            return {'name': name, 'artist': artist, 'error': f'Error: {str(e)}'}

    # Use ThreadPoolExecutor to run searches concurrently
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_track, tracks))

    return jsonify(results)
