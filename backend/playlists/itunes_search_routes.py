from flask import Blueprint, request, jsonify
from flask_cors import CORS
# import json

from ..search import ItuneSearch

itunes_bp = Blueprint('itunes_bp', __name__)

@itunes_bp.route('/itunes_result', methods=['POST'])
def get_itunes_result():
    data = request.get_json()

    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400

    result = [] # Holds track price and URL

    for track in tracks:
        artist = track.get('artist')
        name = track.get('name')

        # print(f"\nOriginal artist: {artist}")
        # print(f"Track name: {name}")

        if not artist or not name:
            result.append({'error': 'Missing artist or track name'})
            continue

        main_artist = artist.split(',')[0].strip()
        print(f"Using main_artist: {main_artist}")

        iSearch = ItuneSearch()

        try:
            search = iSearch.search_song(main_artist, name)
            price = search.get("price", -1)
            url = search.get("url", "")

            # print(f"Price from iTunes: {price}")
            # print(f"Track URL: {url}")

            if price == -1:
                result.append({'name': name, 'artist': artist, 'error': 'Track not found on iTunes'})
            else:
                result.append({'name': name, 'artist': artist, 'price': price, 'url': url})
        except Exception as e:
            result.append({'name': name, 'artist': artist, 'error': f'Error: {str(e)}'})

    return jsonify(result)
