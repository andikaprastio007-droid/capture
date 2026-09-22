from flask import Blueprint, request, jsonify
import base64, os
from app.config import Config
from app.database import db
from app.models import BurstPhoto, Session

bp = Blueprint("burst", __name__)


def decode_data_url(d):
    if not d or "," not in d:
        return b""
    try:
        return base64.b64decode(d.split(",", 1)[1])
    except Exception:
        return b""


@bp.route("/upload", methods=["POST"])
def upload_burst():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    frame = p.get("frame_num", 0)
    img = decode_data_url(p.get("image", ""))
    if not ts or not img:
        return jsonify({"ok": False}), 400
    fname = ts + "_burst_" + str(frame).zfill(3) + ".png"
    with open(os.path.join(Config.BURST_DIR, fname), "wb") as f:
        f.write(img)
    db.session.add(BurstPhoto(session_ts=ts, filename=fname, frame_num=frame))
    s = Session.query.filter_by(ts=ts).first()
    if s:
        s.burst_count = (s.burst_count or 0) + 1
    db.session.commit()
    return jsonify({"ok": True, "filename": fname})
