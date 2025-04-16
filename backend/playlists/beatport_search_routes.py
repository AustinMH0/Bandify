from flask import Blueprint, request, jsonify

from ..search import BeatportSearch

beatport_bp = Blueprint('beatport_bp', __name__)

@beatport_bp.route('/beatport_result', methods=['POST'])
def get_beatport_result():
    data = request.get_json()

    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400

    result = []

    for track in tracks:
        artist = track.get('artist')
        name = track.get('name')

        print(f"\nOriginal artist: {artist}")
        print(f"Track name: {name}")

        if not artist or not name:
            result.append({'error': 'Missing artist or track name'})
            continue

        main_artist = artist.split(',')[0].strip()
        print(f"Using main_artist: {main_artist}")

        bpSearch = BeatportSearch()

        try:
            search = bpSearch.search_song(name, main_artist)
            price = search.get("price", -1)
            url = search.get("url", "")

            # print(f"Price from Beatport: {price}")
            # print(f"Track URL: {url}")

            if price == -1:
                result.append({'name': name, 'artist': artist, 'error': 'Track not found on iTunes'})
            else:
                result.append({'name': name, 'artist': artist, 'price': price, 'url': url})
        except Exception as e:
            result.append({'name': name, 'artist': artist, 'error': f'Error: {str(e)}'})

    return jsonify(result)
