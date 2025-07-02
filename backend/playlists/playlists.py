from dotenv import load_dotenv

import os

from flask import Blueprint, session, redirect, url_for, request, jsonify
from flask_cors import CORS

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

load_dotenv()

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

playlists_bp = Blueprint('playlists_bp', __name__)
CORS(playlists_bp, origins=["https://groovonomy.com"], supports_credentials=True)

# Spotify config
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')
scope = 'playlist-read-private playlist-read-collaborative'

# Auth handler
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


@playlists_bp.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('playlists.get_playlists'))


@playlists_bp.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        sp_oauth.get_access_token(code)

    # Redirect back to frontend
    return redirect(FRONTEND_URL)


@playlists_bp.route('/get_playlists')
def get_playlists():
    token_info = cache_handler.get_cached_token()
    if not token_info or not sp_oauth.validate_token(token_info):
        # Now returns 401 JSON instead of redirect
        return jsonify({'error': 'Unauthorized'}), 401

    playlists = sp.current_user_playlists()
    user_info = sp.me()
    user_id = user_info['id']
    profile_pic = user_info['images'][0]['url'] if user_info['images'] else None

    result = [
        {
            'id': playlist['id'],
            'name': playlist['name'],
            'total_tracks': playlist['tracks']['total'],
            'image': playlist['images'][0]['url'] if playlist['images'] else None,
            'owner': {
                'id': playlist['owner']['id'],
                'display_name': playlist['owner']['display_name']
            }
        }
        for playlist in playlists['items']
    ]

    return jsonify({
        'id': user_id,
        'display_name': user_info['display_name'],
        'profile_picture': profile_pic,
        'playlists': result
    })


@playlists_bp.route('/get_tracks/<playlist_id>')
def get_tracks(playlist_id):
    token_info = cache_handler.get_cached_token()

    if not token_info or not sp_oauth.validate_token(token_info):
        return jsonify({'error': 'Unauthorized'}), 401

    sp = Spotify(auth_manager=sp_oauth)
    
    tracks = []
    results = sp.playlist_items(playlist_id, fields='items(track(name,artists(name))),next')

    while results:
        for item in results['items']:
            track = item['track']
            tracks.append({
                'name': track['name'],
                'artist': ', '.join(artist['name'] for artist in track['artists'])
            })
        
        results = sp.next(results) if results['next'] else None

    return jsonify(tracks)



@playlists_bp.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@playlists_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('playlists.home'))
