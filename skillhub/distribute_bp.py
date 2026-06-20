"""Distribute blueprint — copy selected skills into a project folder."""

from __future__ import annotations

import logging
import os
import shutil

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

bp = Blueprint("distribute", __name__, url_prefix="/api")


@bp.post("/distribute-skills")
def distribute_skills():
    data = request.json or {}
    skills = data.get("skills") or []
    target_folder = (data.get("targetFolder") or "").strip()

    if not target_folder:
        return jsonify({"success": False, "message": "请输入目标项目文件夹路径"}), 400
    if not skills:
        return jsonify({"success": False, "message": "请选择要分发的技能"}), 400

    target_folder = os.path.abspath(os.path.expanduser(target_folder))
    skills_root = os.path.join(target_folder, "skills")
    os.makedirs(skills_root, exist_ok=True)

    results: list[str] = []
    for skill in skills:
        skill_path = skill.get("path")
        skill_name = skill.get("name")
        if not skill_path or not skill_name:
            results.append("跳过无效条目")
            continue
        if not os.path.isdir(skill_path):
            results.append(f"跳过 {skill_name}: 源目录不存在")
            continue
        dest = os.path.join(skills_root, skill_name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(skill_path, dest)
        results.append(f"已分发 {skill_name} 到 {dest}")

    return jsonify({"success": True, "message": "\n".join(results)})


# Reserved for a future native folder picker; the Web UI uses a text input
# plus the OS dialog from a small client-side helper today.
@bp.post("/select-folder")
def select_folder():
    return jsonify({"success": True})
