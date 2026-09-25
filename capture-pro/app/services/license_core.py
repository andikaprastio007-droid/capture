"""License Core — generate & verify license key."""
import os
import json
import hmac
import hashlib
import base64
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
LICENSE_SECRET = os.environ.get("LICENSE_SECRET", "ANDIKA-2026-CHANGE-ME-xyz123")


def _sign(data: bytes) -> str:
    return hmac.new(LICENSE_SECRET.encode(), data, hashlib.sha256).hexdigest()


def generate_license_key(owner, days=365, plan="pro", features=None):
    if features is None:
        features = ["capture", "dashboard", "template", "tunnel", "telegram"]
    
    payload = {
        "owner": owner,
        "plan": plan,
        "features": features,
        "issued_at": int(time.time()),
        "expires_at": int(time.time()) + days * 86400,
        "license_id": hashlib.sha256(
            f"{owner}{time.time()}{os.urandom(8)}".encode()
        ).hexdigest()[:12],
    }
    
    raw = json.dumps(payload, sort_keys=True).encode()
    b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    sig = _sign(raw)[:32]
    
    return f"ATV1-{b64}-{sig}", payload


def verify_license_key(key):
    if not key or not key.startswith("ATV1-"):
        return False, "Format license tidak valid"
    try:
        parts = key.split("-", 2)
        if len(parts) != 3:
            return False, "Format rusak"
        _, b64, sig = parts
        b64 += "=" * (-len(b64) % 4)
        raw = base64.urlsafe_b64decode(b64)
        expected_sig = _sign(raw)[:32]
        if not hmac.compare_digest(expected_sig, sig):
            return False, "Signature tidak valid"
        payload = json.loads(raw)
        if payload.get("expires_at", 0) < time.time():
            return False, "License kadaluarsa"
        return True, payload
    except Exception as e:
        return False, f"Error: {e}"
