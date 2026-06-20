"""Skill Manager — Flask application factory.

A web UI to browse, install, distribute, view, and edit Claude Code /
OpenCLAW skills locally. Architecture uses Flask Blueprints; the package
``skillhub`` is intentionally framework-aware (Flask) but the helpers in
:mod:`skillhub.utils` are pure stdlib so they can later back a CLI/TUI.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask


def create_app() -> Flask:
    """Application factory used by both ``app.py`` and the test suite."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )

    _configure_logging(app)
    _register_context_processors(app)

    # Register blueprints
    from skillhub.skills_bp import bp as skills_bp
    from skillhub.install_bp import bp as install_bp
    from skillhub.distribute_bp import bp as distribute_bp
    from skillhub.editor_bp import bp as editor_bp

    app.register_blueprint(skills_bp)
    app.register_blueprint(install_bp)
    app.register_blueprint(distribute_bp)
    app.register_blueprint(editor_bp)

    @app.route("/")
    def index():
        from flask import render_template

        return render_template("index.html")

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


def _configure_logging(app: Flask) -> None:
    level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(level)


def _register_context_processors(app: Flask) -> None:
    """Inject global template variables (e.g. Skillhub marketplace URL).

    The Flask app config takes precedence over the environment variable
    so deployment manifests can override it without touching code.
    """
    from skillhub.utils import SKILLHUB_WEBSITE_URL

    @app.context_processor
    def inject_globals() -> dict:
        return {
            "skillhub_website_url": app.config.get(
                "SKILLHUB_WEBSITE_URL", SKILLHUB_WEBSITE_URL
            ),
        }


__all__ = ["create_app"]
