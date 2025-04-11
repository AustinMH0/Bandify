from flask import Blueprint, request, jsonify
from flask_cors import CORS
# import json
import threading
import queue

from ..search import ItuneSearch

def search_for_songs(songsQueue, resultingPrices):
    while not songsQueue.empty():
        try:
            artist, song = songsQueue.get(timeout = 1)
        except queue.Empty:
            print("Queue empty")
            return
        iSearch = ItuneSearch.search_song(artist, song)
        resultingPrices.put({
            "name": song,
            "artist": artist,
            "price": iSearch["price"],
            "url": iSearch["url"],
            "error": "Track not found on iTunes" if iSearch["price"] == -1 else "",
        })
        songsQueue.task_done()

itunes_bp = Blueprint('itunes_bp', __name__)

@itunes_bp.route('/itunes_result', methods=['POST'])
def get_itunes_result():
    data = request.get_json()

    songsQueue = queue.Queue()

    tracks = data.get('tracks')
    if not tracks:
        return jsonify({'error': 'No tracks provided'}), 400

    itunes_prices = queue.Queue() # Holds track price and URL

    for track in tracks:
        artist = track.get('artist')
        name = track.get('name')

        # print(f"\nOriginal artist: {artist}")
        # print(f"Track name: {name}")

        if not artist or not name:
            print("Missing artist/name")
            continue

        main_artist = artist.split(',')[0].strip()
        # print(f"Using main_artist: {main_artist}")

        songsQueue.put((main_artist, name))    
        
        

    
        # try:
        #     main_artist, name = songsQueue.get(timeout= 2)
        #     if queue.Empty:
        #         return
            
        #     search = iSearch.search_song(main_artist, name)
        #     price = search.get("price", -1)
        #     url = search.get("url", "")

        #     # search = iSearch.search_song(main_artist, name)
        #     # price = search.get("price", -1)
        #     # url = search.get("url", "")

        #     print(f"Price from iTunes: {price}")
        #     print(f"Track URL: {url}")

        # #     if price == -1:
        # #         result.append({'name': name, 'artist': artist, 'error': 'Track not found on iTunes'})
        # #     else:
        # #         result.append({'name': name, 'artist': artist, 'price': price, 'url': url})
        # # except Exception as e:
        # #     result.append({'name': name, 'artist': artist, 'error': f'Error: {str(e)}'})
    # print("starting search")

    for i in range(8):
        t = threading.Thread(target=search_for_songs, args =(songsQueue, itunes_prices), daemon=True)
        t.start()

    songsQueue.join()
    
    

    return jsonify(list(itunes_prices.queue))
