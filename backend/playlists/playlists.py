from dotenv import load_dotenv

import os

from flask import Flask, session, redirect, url_for, request, jsonify
from flask_cors import CORS

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
CORS(app)

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private playlist-read-collaborative'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

sp = Spotify(auth_manager=sp_oauth, requests_timeout=10)

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists'))

# def show_tracks(results):
#     track_list = []
#     for i, item in enumerate(results['items']):
#         track = item['track']
#         track_list.append(f"{i+1}. {track['artists'][0]['name']} - {track['name']}")
#     return '<br>'.join(track_list)

@app.route('/get_playlists')
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return jsonify({"error": "Unauthorized"}), 401

    playlists = sp.current_user_playlists()
    user_id = sp.me()['id'] # gets the current authenticated Spotify user's profile information
    playlist_data = []

    for playlist in playlists['items']:
        if playlist['owner']['id'] == user_id:
            tracks = sp.playlist_items(playlist['id'], fields="items,next", additional_types=('track', ))

            track_list = []
            for item in tracks['items']:
                track = item['track']
                track_list.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name']
                })
            
            playlist_data.append({
                "id": playlist['id'],
                "name": playlist['name'],
                "total_tracks": playlist['tracks']['total'],
                "tracks": track_list
            })

    return jsonify(playlist_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)