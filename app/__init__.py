"""Application factory for the Kadisco Procurement web app."""

from __future__ import annotations

from flask import Flask

from . import database
from .routes import bp

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

    # Ensure the Kadisco_Operations table exists before serving requests.
    database.init_db()
    app.register_blueprint(bp)
    app.jinja_env.filters["status_class"] = _status_class
    return app
