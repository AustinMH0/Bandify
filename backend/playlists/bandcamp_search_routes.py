from flask import jsonify, request, Blueprint
from concurrent.futures import ThreadPoolExecutor
from ..search import BandcampSearch

bandCampBlueprint = Blueprint('bandcamp_bp', __name__)

@bandCampBlueprint.route('/bandcamp_results', methods = ['POST'])
def get_bandcamp_prices():
    data = request.get_json()
    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No songs provided!'}), 400

    def process_track(track):
        artist = track.get('artist')
        songName = track.get('name')

        if not artist or not songName:
            return {'error': 'Missing artist or track name'}

        # firstArtist = artist.split(',')[0].strip() # This grabs the first artist, could have some issues when the artist has a ',' in their name
        bandSearch = BandcampSearch()

        try:
            search = bandSearch.search_song(songName, artist)
            price = search.get('price', -1)
            url = search.get('url', '')

            # print(f'song name is {songName}, artist is {firstArtist}, price is {price}')

            if price == -1:
                return {'name': songName, 'artist': artist, 'error': 'Track not found on Bandcamp'}
            else:
                return {'name': songName, 'artist': artist, 'price': price, 'url': url}
        except Exception as e:
            return {'name': songName, 'artist': artist, 'error': f'Error: {str(e)}'}

    # Use ThreadPoolExecutor to run searches concurrently
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_track, tracks))

    return jsonify(results)
            




