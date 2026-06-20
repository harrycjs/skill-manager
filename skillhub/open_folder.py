"""Open-folder helper — launches the OS file explorer at a given path.

Centralised so the same cross-platform logic is used by every blueprint
that exposes an "open in file explorer" button.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)


def open_in_file_manager(path: str) -> tuple[bool, str]:
    """Open ``path`` (a directory) in the host OS file explorer.

    Returns ``(success, message)``. Never raises — callers can treat
    failures as user-facing errors.
    """
    if not path or not os.path.isdir(path):
        return False, f"目录不存在: {path}"

    try:
        if sys.platform == "win32":
            # ``os.startfile`` understands folders natively on Windows and
            # launches Explorer pointed at the path.
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False, timeout=10)
        else:
            subprocess.run(["xdg-open", path], check=False, timeout=10)
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
        logger.warning("Failed to open %s: %s", path, exc)
        return False, f"打开失败: {exc}"

    return True, "已请求系统文件管理器"


__all__ = ["open_in_file_manager"]
