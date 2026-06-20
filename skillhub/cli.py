"""CLI entry point — reserved for a future release.

Currently the project is web-only. This stub keeps ``pyproject.toml``'s
``[project.scripts]`` entry valid so that installing the package does
not fail, and so the import-time wiring is ready when the CLI lands.
"""

from __future__ import annotations

import sys


def main() -> int:
    """Print a friendly message; a real CLI will replace this in 0.3.0."""
    print(
        "skill-manager CLI is not implemented yet. "
        "Run `python app.py` to start the web UI.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
