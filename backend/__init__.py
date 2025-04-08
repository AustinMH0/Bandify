from os import urandom
from flask import Flask
from .playlists.playlists import playlists_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = urandom(64)
    app.register_blueprint(playlists_bp)

    return app
