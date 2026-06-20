"""Entry point — ``python app.py`` to start the dev server.

For production, prefer ``flask --app skillhub run`` or any WSGI server
(``gunicorn`` / ``waitress``) pointed at ``skillhub:create_app()``.
"""

from __future__ import annotations

import logging

from skillhub import create_app
from skillhub.install_bp import ensure_skillhub_installed

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Checking Skillhub CLI...")
    ensure_skillhub_installed()
    app = create_app()
    logger.info("Starting server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
