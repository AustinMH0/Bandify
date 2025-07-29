from search import BandcampSearch, BeatportSearch, ItuneSearch
import datetime

def get_api_prices(artist, track_name):
    timestamp = datetime.datetime.now()

    bandcamp_data = BandcampSearch().search_song(track_name, artist)
    beatport_data = BeatportSearch().search_song(track_name, artist)
    itunes_data = ItuneSearch.search_song(artist, track_name)

    return {
        'itunes_price': itunes_data['price'],
        'itunes_url': itunes_data['url'],
        'bandcamp_price': bandcamp_data['price'],
        'bandcamp_url': bandcamp_data['url'],
        'beatport_price': beatport_data['price'],
        'beatport_url': beatport_data['url'],
        'created_at': timestamp
    }
