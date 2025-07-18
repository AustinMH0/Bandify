from os import urandom
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix


from .playlists.playlists import playlists_bp
from .playlists.itunes_search_routes import itunes_bp
from .playlists.bandcamp_search_routes import bandCampBlueprint
from .playlists.beatport_search_routes import beatport_bp
from .playlists.server import server_bp


def create_app():
    app = Flask(__name__)

    # Make sure flask verifies proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    CORS(app, supports_credentials=True, origins=[
        "http://localhost:5173", 
        "https:groovonomy.com"
        ])
    app.config['SECRET_KEY'] = urandom(64)
    app.config['SESSION_COOKIE_NAME'] = 'groovonomy_session'
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True 
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    app.register_blueprint(playlists_bp)
    app.register_blueprint(itunes_bp)
    app.register_blueprint(bandCampBlueprint)
    app.register_blueprint(beatport_bp)
    app.register_blueprint(server_bp)

    return app
