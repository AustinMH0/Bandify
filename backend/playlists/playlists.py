from dotenv import load_dotenv

import os

from flask import Flask, session, redirect, url_for, request, jsonify
from flask_cors import CORS

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

# Enable CORS
CORS(app, supports_credentials=True)

# Spotify API credentials
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private playlist-read-collaborative'

# Set up Spotify auth
cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

# Global Spotify instance
sp = Spotify(auth_manager=sp_oauth, requests_timeout=10)

@app.route('/')
def home():
    """Redirect user to login if not authenticated"""
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))


@app.route('/callback')
def callback():
    """Handle Spotify OAuth callback"""
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists'))


@app.route('/get_playlists')
def get_playlists():
    """Fetch user's playlists"""
    token_info = cache_handler.get_cached_token()

    if not token_info or not sp_oauth.validate_token(token_info):
        return jsonify({"error": "Unauthorized"}), 401

    sp = Spotify(auth_manager=sp_oauth)
    
    playlists = sp.current_user_playlists()
    user_id = sp.me()['id']
    
    playlist_data = []
    
    for playlist in playlists['items']:
        if playlist['owner']['id'] == user_id:
            playlist_data.append({
                "id": playlist['id'],
                "name": playlist['name'],
                "total_tracks": playlist['tracks']['total']
            })

    return jsonify(playlist_data)


@app.route('/get_tracks/<playlist_id>')
def get_tracks(playlist_id):
    """Fetch tracks for a given playlist ID"""
    token_info = cache_handler.get_cached_token()

    if not token_info or not sp_oauth.validate_token(token_info):
        return jsonify({"error": "Unauthorized"}), 401

    sp = Spotify(auth_manager=sp_oauth)
    
    tracks = []
    results = sp.playlist_items(playlist_id, fields="items(track(name,artists(name))),next")

    while results:
        for item in results["items"]:
            track = item["track"]
            tracks.append({
                "name": track["name"],
                "artist": ", ".join(artist["name"] for artist in track["artists"])
            })
        
        results = sp.next(results) if results["next"] else None

    return jsonify(tracks)


@app.route('/logout')
def logout():
    """Clear session and log out user"""
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)