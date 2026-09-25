from flask import Blueprint, jsonify, request
from app.auth import login_required
import subprocess
import os

bp = Blueprint("tunnel", __name__)

SCRIPT = os.path.expanduser("~/capture-pro/tunnel_service.sh")
LOG_FILE = os.path.expanduser("~/capture-pro/tunnel.log")


def _run(args):
    """Jalankan tunnel_service.sh dengan argumen."""
    if not os.path.isfile(SCRIPT):
        return "ERROR: tunnel_service.sh tidak ditemukan"
    try:
        result = subprocess.run(
            ["bash", SCRIPT] + args,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


@bp.route("/tunnel/start", methods=["POST"])
@login_required
def tunnel_start():
    out = _run(["start"])
    return jsonify({"ok": True, "msg": out})


@bp.route("/tunnel/stop", methods=["POST"])
@login_required
def tunnel_stop():
    out = _run(["stop"])
    return jsonify({"ok": True, "msg": out})


@bp.route("/tunnel/restart", methods=["POST"])
@login_required
def tunnel_restart():
    out = _run(["restart"])
    return jsonify({"ok": True, "msg": out})


@bp.route("/tunnel/status", methods=["GET"])
@login_required
def tunnel_status():
    out = _run(["status"])
    parts = out.split("|")
    running = (parts[0].strip() == "RUNNING") if parts else False
    pid = parts[1].strip() if len(parts) > 1 else "0"
    url = parts[2].strip() if len(parts) > 2 else ""
    return jsonify({
        "ok": True,
        "running": running,
        "pid": pid,
        "url": url,
    })


@bp.route("/tunnel/url", methods=["GET"])
@login_required
def tunnel_url():
    out = _run(["url"])
    return jsonify({"ok": True, "url": out})


@bp.route("/tunnel/log", methods=["GET"])
@login_required
def tunnel_log():
    try:
        if os.path.isfile(LOG_FILE):
            with open(LOG_FILE, "r", errors="ignore") as f:
                lines = f.readlines()[-60:]
            return jsonify({"ok": True, "log": "".join(lines)})
        return jsonify({"ok": True, "log": "Belum ada log"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})
