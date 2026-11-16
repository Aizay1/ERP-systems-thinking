"""Application factory for the Kadisco Procurement web app."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory

from . import database
from .routes import bp

# Project-level folder that holds the Kadisco logo assets.
IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"

# Maps a department status value to a badge modifier class.
_STATUS_BADGE = {
    "Pending": "badge--pending",
    "Quoting": "badge--info",
    "Pending Approval": "badge--pending",
    "Approved": "badge--success",
    "PO Issued": "badge--info",
    "Goods Received": "badge--success",
    "Paid": "badge--success",
    "Completed": "badge--success",
}


def _status_class(value: str) -> str:
    return _STATUS_BADGE.get(value, "badge--neutral")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "kadisco-procurement-dev-key"

    # Ensure the Materials_Master and Kadisco_Operations tables exist.
    database.init_db()
    app.register_blueprint(bp)
    app.jinja_env.filters["status_class"] = _status_class

    @app.get("/images/<path:filename>")
    def images(filename: str):
        """Serve the Kadisco logo assets kept in the project's images/ folder."""
        return send_from_directory(IMAGES_DIR, filename)

    return app
