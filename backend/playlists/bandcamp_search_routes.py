from flask import jsonify, request, Blueprint
from flask_cors import CORS

from ..search import BandcampSearch


bandCampBlueprint = Blueprint('bandcamp_bp', __name__)

@bandCampBlueprint.route('/bandcamp_results', methods = ["POST"])
def get_bandcamp_prices():
    
    data = request.get_json()

    tracks = data.get('tracks')
    

    if not tracks:
        return jsonify({'error': "No songs provided!"}), 400
    
    prices = [] # List to hold song price

    for track in tracks:
        artists = track.get('artist')
        songName = track.get('name')


        if not artists or not songName:
            prices.append("error: no artist or song name found")
            continue

        firstArtist = artists.split(',')[0].strip() # This grabs the first artist, could have some issues when the artist has a ',' in their name

        bandSearch = BandcampSearch(songName, firstArtist)

        try:
            search = bandSearch.get_track_price()
            price = search.get("price", -1)
            url = search.get("url", "")

            print(f"song name is {songName}, artist is {firstArtist}, price is {price}")

            if price == -1: 
                prices.append({'name': songName, 'artist': firstArtist, 'error': "Track not found on Beatport"})
            else:
                prices.append({'name': songName, 'artist': firstArtist, 'price': price, 'url': url}) 

        except Exception as e:
            prices.append({'name': songName, 'artist': firstArtist, 'error': f'Error: {str(e)}'})

        return jsonify(prices)
            




