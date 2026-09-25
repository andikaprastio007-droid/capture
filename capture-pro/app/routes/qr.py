"""QR Code generator — minimal."""
from flask import Blueprint, jsonify, request, render_template, send_file
from app.auth import login_required
import io

bp = Blueprint("qr", __name__)


@bp.route("/qr-page")
@login_required
def qr_page():
    return render_template("qr_page.html")


@bp.route("/api/qr/generate", methods=["POST"])
@login_required
def api_qr():
    data = request.get_json() or {}
    url = data.get("url", "")
    if not url:
        return jsonify({"ok": False, "msg": "URL kosong"}), 400
    try:
        import qrcode
        img = qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
    except ImportError:
        return jsonify({"ok": False, "msg": "Install: pip install qrcode[pil]"}), 500
