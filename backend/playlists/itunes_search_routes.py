from flask import Blueprint, request, jsonify
from flask_cors import CORS
# import json

from ..search import ItuneSearch

itunes_bp = Blueprint('itunes_bp', __name__)

@itunes_bp.route('/itunes_prices', methods=['POST'])
def get_itunes_prices():
    data = request.get_json()  # Get the posted JSON data

    # Log the incoming data to verify the request
    # print(f'Received data: {data}')

    tracks = data.get('tracks')  # Extract the list of tracks

    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400

    prices = []  # List to hold prices for each track

    for track in tracks:
        artist = track.get('artist')
        name = track.get('name')

        print(f"\nOriginal artist: {artist}")
        print(f"Track name: {name}")

        if not artist or not name:
            prices.append({'error': 'Missing artist or track name'})
            continue

        # Try just the first artist
        main_artist = artist.split(',')[0].strip()
        print(f"Using main_artist: {main_artist}")

        iSearch = ItuneSearch()

        try:
            price = iSearch.search_song(main_artist, name)
            print(f"Price from iTunes: {price}")

            if price == -1:
                prices.append({'artist': artist, 'name': name, 'error': 'Track not found on iTunes'})
            else:
                prices.append({'artist': artist, 'name': name, 'price': price})
        except Exception as e:
            prices.append({'artist': artist, 'name': name, 'error': f'Error: {str(e)}'})

    # print('\n')
    # print(json.dumps(prices, indent=4))
    return jsonify(prices)