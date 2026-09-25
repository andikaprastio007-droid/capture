"""Web Code Editor — dengan secret key protection."""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, make_response
from app.auth import login_required
from app.config import Config
from app.services.editor import (
    list_files, read_file, write_file, delete_file,
    run_command, restart_server, search_files,
)

bp = Blueprint("editor", __name__)


# ============================================================
# SECRET KEY PROTECTION
# ============================================================
def check_editor_access():
    """Cek apakah user punya akses ke editor.
    
    Akses diberikan kalau:
    1. Ada cookie 'editor_access' valid (dari session sebelumnya), ATAU
    2. Ada query param ?key=SECRET yang cocok
    
    Return: True kalau boleh, False kalau tidak.
    """
    # Cek cookie
    cookie_token = request.cookies.get("editor_access")
    if cookie_token and Config.EDITOR_SECRET_KEY:
        # Cookie menyimpan hash dari secret
        import hashlib
        expected = hashlib.sha256(Config.EDITOR_SECRET_KEY.encode()).hexdigest()[:32]
        if cookie_token == expected:
            return True
    
    # Cek query param
    key = request.args.get("key", "").strip()
    if key and Config.EDITOR_SECRET_KEY and key == Config.EDITOR_SECRET_KEY:
        return True
    
    return False


def require_editor_access(f):
    """Decorator: butuh akses editor."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not check_editor_access():
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "msg": "Editor access denied"}), 403
            # Halaman: tampilkan 404 biar tidak kelihatan ada editor
            return "404 Not Found", 404
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# PAGE
# ============================================================
@bp.route("/editor")
@login_required
@require_editor_access
def editor_page():
    """Halaman editor — butuh secret key."""
    import hashlib
    resp = make_response(render_template("editor.html"))
    
    # Set cookie kalau belum ada (biar tidak perlu ketik key terus)
    expected = hashlib.sha256(Config.EDITOR_SECRET_KEY.encode()).hexdigest()[:32]
    if request.cookies.get("editor_access") != expected:
        resp.set_cookie(
            "editor_access",
            expected,
            httponly=True,
            samesite="Lax",
            max_age=1800,  # 30 menit
        )
    return resp


# ============================================================
# API ENDPOINTS — semua butuh editor access
# ============================================================
@bp.route("/api/editor/files")
@login_required
@require_editor_access
def api_files():
    return jsonify({"ok": True, "files": list_files()})


@bp.route("/api/editor/read")
@login_required
@require_editor_access
def api_read():
    path = request.args.get("path", "")
    return jsonify(read_file(path))


@bp.route("/api/editor/write", methods=["POST"])
@login_required
@require_editor_access
def api_write():
    data = request.get_json(force=True, silent=True) or {}
    path = data.get("path", "")
    content = data.get("content", "")
    if not path:
        return jsonify({"ok": False, "msg": "Path kosong"}), 400
    return jsonify(write_file(path, content))


@bp.route("/api/editor/delete", methods=["POST"])
@login_required
@require_editor_access
def api_delete():
    data = request.get_json(force=True, silent=True) or {}
    path = data.get("path", "")
    if not path:
        return jsonify({"ok": False, "msg": "Path kosong"}), 400
    return jsonify(delete_file(path))


@bp.route("/api/editor/run", methods=["POST"])
@login_required
@require_editor_access
def api_run():
    data = request.get_json(force=True, silent=True) or {}
    cmd = data.get("cmd", "").strip()
    if not cmd:
        return jsonify({"ok": False, "msg": "Command kosong"}), 400
    return jsonify(run_command(cmd))


@bp.route("/api/editor/restart", methods=["POST"])
@login_required
@require_editor_access
def api_restart():
    return jsonify(restart_server())


@bp.route("/api/editor/search")
@login_required
@require_editor_access
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"ok": False, "msg": "Query kosong"}), 400
    ext = request.args.get("ext") or None
    return jsonify({"ok": True, "results": search_files(q, ext)})


# ============================================================
# LOGOUT dari editor
# ============================================================
@bp.route("/editor/logout")
@login_required
def editor_logout():
    resp = make_response(redirect(url_for("dashboard.index")))
    resp.delete_cookie("editor_access")
    return resp
