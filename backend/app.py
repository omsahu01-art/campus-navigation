"""Flask application factory for CampusNav."""

from pathlib import Path

from flask import Flask, url_for

from config.config import (APP_NAME, APP_TAGLINE, APP_VERSION, STATIC_DIR, TEMPLATES_DIR)
from database import campus_data
from database.campus_db import initialize_database, load_graph_data
from navigation.graph import build_graph
from navigation.locations import LocationService


def create_app():
    app = Flask(__name__, template_folder=str(TEMPLATES_DIR),
                static_folder=str(STATIC_DIR), static_url_path="/static")
    app.config["JSON_SORT_KEYS"] = False
    app.json.sort_keys = False

    rebuilt = initialize_database()
    nodes, edges = load_graph_data()
    graph = build_graph(nodes, edges)
    views = campus_data.VIEWS
    locations = LocationService(nodes, views)

    app.config.update(CAMPUS_GRAPH=graph, LOCATION_SERVICE=locations, CAMPUS_VIEWS=views,
                      APP_NAME=APP_NAME, APP_TAGLINE=APP_TAGLINE, APP_VERSION=APP_VERSION,
                      DB_REBUILT=rebuilt)

    @app.context_processor
    def asset_helpers():
        def asset(filename):
            """static URL with a cache-busting version (file modification time)."""
            path = Path(STATIC_DIR) / filename
            version = int(path.stat().st_mtime) if path.exists() else APP_VERSION
            return url_for("static", filename=filename, v=version)
        return {"asset": asset, "app_name": APP_NAME, "app_tagline": APP_TAGLINE,
                "app_version": APP_VERSION}

    from backend.api import api_bp
    from backend.routes import pages_bp
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)
    return app


app = create_app()
