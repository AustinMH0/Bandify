from os import urandom
from flask import Flask
from flask_cors import CORS

from .playlists.playlists import playlists_bp
from .playlists.itunes_search_routes import itunes_bp
from .playlists.bandcamp_search_routes import bandCampBlueprint
from .playlists.beatport_search_routes import beatport_bp

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config['SECRET_KEY'] = urandom(64)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(itunes_bp)
    app.register_blueprint(bandCampBlueprint)
    app.register_blueprint(beatport_bp)

    return app
