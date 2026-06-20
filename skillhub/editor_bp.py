"""Editor blueprint — read & write files inside a skill directory.

Safety contract (defence in depth):

* ``source`` is validated against the discoverable workspace list (or ``claude``).
* ``skill_name`` and relative path are resolved with
  :func:`skillhub.utils.resolve_skill_path` and :func:`skillhub.utils.safe_join`
  so the request can never escape the skill's root directory.
* Read/write are bounded by ``MAX_READ_BYTES`` / ``MAX_WRITE_BYTES``.
* Writes are restricted to ``ALLOWED_EXTENSIONS``.
* On overwrite we keep a sibling ``.bak`` via :func:`skillhub.utils.atomic_write`.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Blueprint, jsonify, request

from skillhub.utils import (
    ALLOWED_EXTENSIONS,
    MAX_READ_BYTES,
    MAX_WRITE_BYTES,
    atomic_write,
    resolve_skill_path,
    safe_join,
)

logger = logging.getLogger(__name__)

bp = Blueprint("editor", __name__, url_prefix="/api")


def _ext_of(path: str) -> str:
    return os.path.splitext(path)[1].lower()


@bp.get("/skills/<source>/<skill_name>/file")
def read_file(source: str, skill_name: str):
    skill_root = resolve_skill_path(source, skill_name)
    if skill_root is None:
        return jsonify({"error": "Skill not found"}), 404

    rel = request.args.get("path", "").strip()
    target = safe_join(skill_root, rel)
    if target is None or not os.path.isfile(target):
        return jsonify({"error": "Invalid path"}), 400

    size = os.path.getsize(target)
    if size > MAX_READ_BYTES:
        return jsonify({"error": "File too large to read in the editor", "size": size}), 413

    try:
        with open(target, "r", encoding="utf-8") as fh:
            content = fh.read()
    except UnicodeDecodeError:
        return jsonify({"error": "Binary file cannot be edited"}), 415
    except OSError as exc:
        logger.warning("read failed for %s: %s", target, exc)
        return jsonify({"error": "Read failed"}), 500

    return jsonify(
        {
            "path": rel.replace("\\", "/"),
            "content": content,
            "size": size,
            "editable": _ext_of(target) in ALLOWED_EXTENSIONS,
        }
    )


@bp.put("/skills/<source>/<skill_name>/file")
def write_file(source: str, skill_name: str):
    skill_root = resolve_skill_path(source, skill_name)
    if skill_root is None:
        return jsonify({"error": "Skill not found"}), 404

    rel = (request.json or {}).get("path", "").strip() if request.is_json else ""
    content = (request.json or {}).get("content", "") if request.is_json else ""
    if not rel:
        return jsonify({"error": "path required"}), 400

    target = safe_join(skill_root, rel)
    if target is None:
        return jsonify({"error": "Invalid path"}), 400

    ext = _ext_of(target)
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Extension {ext!r} is not editable"}), 415

    encoded_size = len(content.encode("utf-8"))
    if encoded_size > MAX_WRITE_BYTES:
        return jsonify({"error": "Content too large", "size": encoded_size}), 413

    try:
        atomic_write(target, content)
    except OSError as exc:
        logger.warning("write failed for %s: %s", target, exc)
        return jsonify({"error": "Write failed"}), 500

    backup_path = Path(target + ".bak")
    backup_exists = backup_path.exists()
    return jsonify(
        {
            "success": True,
            "path": rel.replace("\\", "/"),
            "size": encoded_size,
            "backup": str(backup_path) if backup_exists else None,
        }
    )
