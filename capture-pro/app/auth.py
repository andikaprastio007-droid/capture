import hmac, hashlib, time, base64, json
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
