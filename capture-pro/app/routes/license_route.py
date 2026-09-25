"""License API — verify dari klien."""
from flask import Blueprint, jsonify, request
from app.database import db
from app.models import License, Activation
from app.services.license_core import verify_license_key
import json
from datetime import datetime


bp = Blueprint("license", __name__)


@bp.route("/api/license/verify", methods=["POST"])
def verify():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or "").strip()
    device_id = (data.get("device_id") or "unknown").strip()
    
    if not key:
        return jsonify({"ok": False, "msg": "License key kosong"}), 400
    
    valid, payload = verify_license_key(key)
    if not valid:
        return jsonify({"ok": False, "msg": payload}), 400
    
    lic = License.query.filter_by(key=key).first()
    if not lic:
        # Auto register
        try:
            from datetime import datetime as _dt
            lic = License(
                key=key,
                owner=payload.get("owner", ""),
                plan=payload.get("plan", "basic"),
                expires_at=_dt.fromtimestamp(payload["expires_at"]),
                max_devices=3,
            )
            db.session.add(lic)
            db.session.commit()
        except Exception as e:
            return jsonify({"ok": False, "msg": f"DB error: {e}"}), 500
    elif lic.status != "active":
        return jsonify({"ok": False, "msg": f"License {lic.status}"}), 403
    
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    client_ip = client_ip.split(",")[0].strip()
    
    try:
        act = Activation(
            license_key=key,
            device_id=device_id,
            ip=client_ip,
            user_agent=request.headers.get("User-Agent"),
        )
        db.session.add(act)
        lic.last_seen = datetime.utcnow()
        lic.activation_count = (lic.activation_count or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    return jsonify({
        "ok": True,
        "msg": "License valid",
        "owner": lic.owner,
        "plan": lic.plan,
        "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        "features": payload.get("features", []),
    })


@bp.route("/api/license/check", methods=["GET"])
def check():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"ok": False, "msg": "Key kosong"}), 400
    
    valid, payload = verify_license_key(key)
    if not valid:
        return jsonify({"ok": False, "msg": payload}), 400
    
    return jsonify({"ok": True, "msg": "Valid", "payload": payload})
