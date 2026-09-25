"""Control endpoint — restart, stop dari dalam."""
from flask import Blueprint, jsonify
from app.auth import login_required
import os
import threading
import time

bp = Blueprint("control", __name__)


@bp.route("/control/restart", methods=["POST"])
@login_required
def api_restart():
    def crash():
        time.sleep(2)
        os._exit(0)
    threading.Thread(target=crash, daemon=False).start()
    return jsonify({"ok": True, "msg": "Restarting...", "wait": 15})


@bp.route("/control/health")
def api_health():
    return jsonify({"ok": True, "pid": os.getpid()})
