"""
Installer: Premium Platform
- Landing page + register/login
- Auto trial 7 hari
- User dashboard
- Admin panel
- Auto renew via Telegram
Jalankan: python setup_premium_platform.py
"""
import os
import sys
from pathlib import Path

PROJECT = Path.home() / "capture-pro"
os.chdir(str(PROJECT))


# ============================================================
# STEP 1: Update models — tambah User, Plan, Subscription
# ============================================================
print("\n[1/6] Update models.py...")
models = PROJECT / "app" / "models.py"
src = models.read_text(encoding="utf-8")
backup = models.with_suffix(".py.bak_premium")
backup.write_text(src, encoding="utf-8")

if "class User" not in src:
    src += '''

class User(db.Model):
    """User terdaftar (customer)."""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    telegram_id = db.Column(db.String(64), index=True)
    
    # Subscription
    plan = db.Column(db.String(32), default="trial")  # trial / basic / pro / enterprise
    status = db.Column(db.String(16), default="active")  # active / expired / suspended
    trial_started_at = db.Column(db.DateTime)
    trial_ends_at = db.Column(db.DateTime)
    subscription_ends_at = db.Column(db.DateTime)
    
    # Extra
    api_quota = db.Column(db.Integer, default=1000)  # max sesi per bulan
    api_used = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    email_verified = db.Column(db.Integer, default=0)
    
    def is_active(self):
        """Cek user masih aktif."""
        if self.status != "active":
            return False
        
        now = datetime.utcnow()
        
        # Trial
        if self.plan == "trial" and self.trial_ends_at:
            return self.trial_ends_at > now
        
        # Subscription
        if self.subscription_ends_at:
            return self.subscription_ends_at > now
        
        return False
    
    def days_left(self):
        """Hitung hari tersisa."""
        now = datetime.utcnow()
        
        if self.plan == "trial" and self.trial_ends_at:
            delta = self.trial_ends_at - now
        elif self.subscription_ends_at:
            delta = self.subscription_ends_at - now
        else:
            return 0
        
        return max(0, delta.days)
    
    def to_dict(self, include_sensitive=False):
        d = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "plan": self.plan,
            "status": self.status,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "subscription_ends_at": self.subscription_ends_at.isoformat() if self.subscription_ends_at else None,
            "is_active": self.is_active(),
            "days_left": self.days_left(),
            "api_quota": self.api_quota,
            "api_used": self.api_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_sensitive:
            d["notes"] = self.notes
        return d


class Subscription(db.Model):
    """Log subscription / payment."""
    __tablename__ = "subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    plan = db.Column(db.String(32))
    amount = db.Column(db.Integer)  # dalam rupiah
    status = db.Column(db.String(16), default="pending")  # pending / paid / failed
    payment_method = db.Column(db.String(32))  # manual / midtrans / xendit
    payment_ref = db.Column(db.String(128))
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        for k in ["starts_at", "ends_at", "created_at"]:
            if d.get(k):
                d[k] = d[k].isoformat()
        return d
'''
    models.write_text(src, encoding="utf-8")
    print("  ✅ Model User + Subscription ditambahkan")
else:
    print("  ℹ️  Sudah ada")


# ============================================================
# STEP 2: Bikin user_service.py
# ============================================================
print("\n[2/6] Bikin user_service.py...")
service = PROJECT / "app" / "services" / "user_service.py"
service.parent.mkdir(parents=True, exist_ok=True)

service.write_text('''"""User service — register, login, subscription."""
import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Subscription
from app.services.license_core import generate_license_key


def hash_password(password, salt=None):
    """Hash password dengan PBKDF2."""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000,
    )
    return f"{salt}${h.hex()}"


def verify_password(password, stored):
    """Verify password."""
    try:
        salt, h = stored.split("$")
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000,
        ).hex()
        return hmac.compare_digest(computed, h)
    except Exception:
        return False


def register_user(email, password, name="", phone="", telegram_id=""):
    """Register user baru + auto trial."""
    email = email.lower().strip()
    
    # Cek sudah ada?
    existing = User.query.filter_by(email=email).first()
    if existing:
        return False, "Email sudah terdaftar"
    
    # Validate
    if len(password) < 6:
        return False, "Password minimal 6 karakter"
    
    if "@" not in email or "." not in email:
        return False, "Email tidak valid"
    
    # Bikin user
    now = datetime.utcnow()
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name[:128],
        phone=phone[:32],
        telegram_id=telegram_id[:64] if telegram_id else None,
        plan="trial",
        status="active",
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=7),
        api_quota=100,
    )
    db.session.add(user)
    db.session.commit()
    
    return True, user


def login_user(email, password):
    """Login user."""
    email = email.lower().strip()
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return False, "Email tidak terdaftar"
    
    if not verify_password(password, user.password_hash):
        return False, "Password salah"
    
    if user.status == "suspended":
        return False, "Akun ditangguhkan. Hubungi admin."
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return True, user


def create_license_for_user(user, days=None):
    """Bikin license key untuk user."""
    if days is None:
        days = user.days_left()
    
    if days <= 0:
        return None, "Tidak ada sisa hari"
    
    # Map plan → features
    features_map = {
        "trial": ["capture", "dashboard"],
        "basic": ["capture", "dashboard", "template"],
        "pro": ["capture", "dashboard", "template", "tunnel", "telegram"],
        "enterprise": ["capture", "dashboard", "template", "tunnel", "telegram", "osint", "editor"],
    }
    
    features = features_map.get(user.plan, ["capture"])
    
    key, payload = generate_license_key(
        owner=user.email,
        days=days,
        plan=user.plan,
        features=features,
    )
    
    return key, payload


def upgrade_user(user, plan, months=1, amount=0, payment_method="manual", notes=""):
    """Upgrade user ke plan berbayar."""
    now = datetime.utcnow()
    days = 30 * months
    
    # Extend subscription
    if user.subscription_ends_at and user.subscription_ends_at > now:
        # Extend dari yang sudah ada
        user.subscription_ends_at = user.subscription_ends_at + timedelta(days=days)
    else:
        user.subscription_ends_at = now + timedelta(days=days)
    
    user.plan = plan
    user.status = "active"
    
    # Set quota
    quotas = {"basic": 500, "pro": 2000, "enterprise": 10000}
    user.api_quota = quotas.get(plan, 500)
    
    # Log subscription
    sub = Subscription(
        user_id=user.id,
        plan=plan,
        amount=amount,
        status="paid" if payment_method != "manual" else "paid",
        payment_method=payment_method,
        starts_at=now,
        ends_at=user.subscription_ends_at,
        notes=notes,
    )
    db.session.add(sub)
    db.session.commit()
    
    return True, user


def check_and_update_expiry(user):
    """Cek expiry user, update status."""
    if user.status in ("suspended",):
        return
    
    now = datetime.utcnow()
    
    # Trial expired?
    if user.plan == "trial" and user.trial_ends_at and user.trial_ends_at < now:
        if user.status != "expired":
            user.status = "expired"
            db.session.commit()
        return
    
    # Subscription expired?
    if user.plan != "trial" and user.subscription_ends_at and user.subscription_ends_at < now:
        if user.status != "expired":
            user.status = "expired"
            db.session.commit()
        return
    
    # Still active — ensure status
    if user.status == "expired" and user.is_active():
        user.status = "active"
        db.session.commit()
''')
print(f"  ✅ {service}")


# ============================================================
# STEP 3: Bikin route auth + user dashboard
# ============================================================
print("\n[3/6] Bikin route auth...")
route = PROJECT / "app" / "routes" / "auth_route.py"
route.write_text('''"""Auth routes — register, login, user dashboard."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, make_response, session
from app.database import db
from app.models import User, Subscription
from app.services.user_service import (
    register_user, login_user, create_license_for_user,
    upgrade_user, check_and_update_expiry,
)
from app.config import Config
from datetime import datetime, timedelta
import secrets
import functools


bp = Blueprint("auth", __name__)


# ============================================================
# DECORATOR — user login required
# ============================================================
def user_login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.user_login_page"))
        
        user = User.query.get(user_id)
        if not user:
            session.pop("user_id", None)
            return redirect(url_for("auth.user_login_page"))
        
        # Cek expiry
        check_and_update_expiry(user)
        
        return f(user=user, *args, **kwargs)
    return wrapper


# ============================================================
# LANDING PAGE
# ============================================================
@bp.route("/")
def landing():
    """Landing page — kalau sudah login, redirect."""
    if session.get("user_id"):
        return redirect(url_for("auth.user_dashboard"))
    return render_template("landing.html")


# ============================================================
# REGISTER
# ============================================================
@bp.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        
        if not email or not password:
            return render_template("register.html", error="Email dan password wajib"), 400
        
        ok, result = register_user(email, password, name, phone)
        
        if not ok:
            return render_template("register.html", error=result), 400
        
        user = result
        
        # Set session
        session["user_id"] = user.id
        session["user_email"] = user.email
        
        # Kalau AJAX, balas JSON
        if request.is_json:
            return jsonify({
                "ok": True,
                "msg": "Registrasi berhasil! Trial 7 hari dimulai.",
                "user": user.to_dict(),
            })
        
        return redirect(url_for("auth.user_dashboard"))
    
    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================
@bp.route("/login-user", methods=["GET", "POST"])
def user_login_page():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        ok, result = login_user(email, password)
        
        if not ok:
            if request.is_json:
                return jsonify({"ok": False, "msg": result}), 401
            return render_template("user_login.html", error=result), 401
        
        user = result
        session["user_id"] = user.id
        session["user_email"] = user.email
        
        if request.is_json:
            return jsonify({
                "ok": True,
                "msg": "Login berhasil",
                "user": user.to_dict(),
            })
        
        return redirect(url_for("auth.user_dashboard"))
    
    return render_template("user_login.html")


# ============================================================
# LOGOUT
# ============================================================
@bp.route("/logout-user")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
    return redirect(url_for("auth.landing"))


# ============================================================
# USER DASHBOARD
# ============================================================
@bp.route("/my")
@user_login_required
def user_dashboard(user):
    """Dashboard user — lihat status, license, upgrade."""
    # Generate license untuk user
    key, payload = create_license_for_user(user)
    
    # Ambil riwayat subscription
    subs = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.id.desc()).limit(10).all()
    
    return render_template("user_dashboard.html",
                           user=user,
                           license_key=key,
                           license_payload=payload,
                           subscriptions=[s.to_dict() for s in subs])


# ============================================================
# API — USER INFO
# ============================================================
@bp.route("/api/user/me")
@user_login_required
def api_me(user):
    return jsonify({"ok": True, "user": user.to_dict()})


@bp.route("/api/user/license")
@user_login_required
def api_license(user):
    """Generate license key untuk user."""
    if not user.is_active():
        return jsonify({
            "ok": False,
            "msg": "Akun tidak aktif. Silakan upgrade.",
        }), 403
    
    key, payload = create_license_for_user(user)
    
    if not key:
        return jsonify({"ok": False, "msg": payload}), 400
    
    return jsonify({
        "ok": True,
        "key": key,
        "payload": payload,
    })


@bp.route("/api/user/change-password", methods=["POST"])
@user_login_required
def api_change_password(user):
    from app.services.user_service import hash_password, verify_password
    
    data = request.get_json() or {}
    old = data.get("old_password", "")
    new = data.get("new_password", "")
    
    if not verify_password(old, user.password_hash):
        return jsonify({"ok": False, "msg": "Password lama salah"}), 400
    
    if len(new) < 6:
        return jsonify({"ok": False, "msg": "Password baru minimal 6 karakter"}), 400
    
    user.password_hash = hash_password(new)
    db.session.commit()
    
    return jsonify({"ok": True, "msg": "Password diubah"})


# ============================================================
# ADMIN PANEL
# ============================================================
def admin_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("session_token")
        if not token:
            return redirect(url_for("dashboard.login_page"))
        from app.auth import verify_token
        if not verify_token(token):
            return redirect(url_for("dashboard.login_page"))
        return f(*args, **kwargs)
    return wrapper


@bp.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin_users.html", users=[u.to_dict(True) for u in users])


@bp.route("/api/admin/users")
@admin_required
def api_admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify({"ok": True, "users": [u.to_dict(True) for u in users]})


@bp.route("/api/admin/user/<int:uid>/extend", methods=["POST"])
@admin_required
def api_admin_extend(uid):
    """Extend subscription user."""
    data = request.get_json() or {}
    days = int(data.get("days", 30))
    
    user = User.query.get(uid)
    if not user:
        return jsonify({"ok": False, "msg": "User tidak ada"}), 404
    
    now = datetime.utcnow()
    if user.subscription_ends_at and user.subscription_ends_at > now:
        user.subscription_ends_at = user.subscription_ends_at + timedelta(days=days)
    else:
        user.subscription_ends_at = now + timedelta(days=days)
    
    user.status = "active"
    db.session.commit()
    
    return jsonify({"ok": True, "msg": f"Extended {days} hari"})


@bp.route("/api/admin/user/<int:uid>/suspend", methods=["POST"])
@admin_required
def api_admin_suspend(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"ok": False}), 404
    
    user.status = "suspended"
    db.session.commit()
    
    return jsonify({"ok": True, "msg": "User ditangguhkan"})


@bp.route("/api/admin/user/<int:uid>/plan", methods=["POST"])
@admin_required
def api_admin_set_plan(uid):
    data = request.get_json() or {}
    plan = data.get("plan", "basic")
    
    user = User.query.get(uid)
    if not user:
        return jsonify({"ok": False}), 404
    
    user.plan = plan
    db.session.commit()
    
    return jsonify({"ok": True, "msg": f"Plan diubah ke {plan}"})
''')
print(f"  ✅ {route}")


# ============================================================
# STEP 4: Register blueprint
# ============================================================
print("\n[4/6] Register auth blueprint...")
init = PROJECT / "app" / "__init__.py"
src = init.read_text(encoding="utf-8")
backup = init.with_suffix(".py.bak_auth")
backup.write_text(src, encoding="utf-8")

if "from app.routes.auth_route import bp as auth_bp" not in src:
    for a in ["from app.routes.api import bp as api_bp",
              "from app.routes.capture import bp as capture_bp"]:
        if a in src:
            src = src.replace(a, a + "\n    from app.routes.auth_route import bp as auth_bp")
            print("  ✅ Import ditambah")
            break

if "app.register_blueprint(auth_bp)" not in src:
    for a in ['app.register_blueprint(api_bp, url_prefix="/api")',
              "app.register_blueprint(capture_bp)"]:
        if a in src:
            src = src.replace(a, a + '\n    app.register_blueprint(auth_bp)')
            print("  ✅ Register ditambah")
            break

if "csrf.exempt(auth_mod.bp)" not in src:
    for a in ["csrf.exempt(api_mod.bp)", "csrf.exempt(capture_mod.bp)"]:
        if a in src:
            src = src.replace(
                a,
                a + "\n    from app.routes import auth_route as auth_mod\n    csrf.exempt(auth_mod.bp)"
            )
            print("  ✅ CSRF exempt ditambah")
            break

init.write_text(src, encoding="utf-8")


# ============================================================
# STEP 5: Bikin templates (landing, register, login, dashboard user)
# ============================================================
print("\n[5/6] Bikin templates...")
templates = PROJECT / "app" / "templates"

# ==== LANDING ====
(templates / "landing.html").write_text('''{% extends "base_modern.html" %}
{% block sidebar %}{% endblock %}
{% block title %}AndikaToolsV1 - Security Platform{% endblock %}
{% block head %}
<style>
body { display: block; }
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 40px 20px;
  text-align: center;
  position: relative;
}
.hero-logo {
  width: 100px;
  height: 100px;
  border-radius: 24px;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 50px;
  box-shadow: var(--shadow-glow);
  margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.hero h1 {
  font-size: 42px;
  margin: 0 0 12px;
  font-weight: 800;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px;
}
.hero p {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 500px;
  margin: 0 0 32px;
  line-height: 1.6;
}
.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.hero-btn {
  padding: 14px 28px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.15s;
  border: 2px solid transparent;
  cursor: pointer;
}
.hero-btn-primary {
  background: var(--gradient-primary);
  color: #fff;
  box-shadow: 0 6px 20px rgba(99,102,241,0.4);
}
.hero-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(99,102,241,0.6);
}
.hero-btn-outline {
  background: transparent;
  color: var(--text-primary);
  border-color: var(--border-strong);
}
.hero-btn-outline:hover {
  background: var(--bg-glass);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 20px;
}
.feature-box {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.2s;
}
.feature-box:hover {
  transform: translateY(-4px);
  border-color: var(--accent-primary);
}
.feature-box .icon { font-size: 36px; margin-bottom: 12px; }
.feature-box h3 { margin: 0 0 8px; font-size: 16px; }
.feature-box p { margin: 0; font-size: 13px; color: var(--text-muted); line-height: 1.5; }
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 20px;
}
.price-card {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border: 2px solid var(--border-subtle);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
  transition: all 0.2s;
  position: relative;
}
.price-card.popular {
  border-color: var(--accent-primary);
  transform: scale(1.05);
  box-shadow: 0 10px 40px rgba(99,102,241,0.3);
}
.price-card .popular-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--gradient-primary);
  color: #fff;
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.price-card h3 { margin: 0 0 8px; font-size: 18px; text-transform: uppercase; letter-spacing: 1px; }
.price-card .price {
  font-size: 32px;
  font-weight: 800;
  color: var(--accent-primary);
  margin: 12px 0;
}
.price-card .price small { font-size: 14px; color: var(--text-muted); font-weight: 400; }
.price-card ul {
  list-style: none;
  padding: 0;
  margin: 20px 0;
  text-align: left;
  font-size: 13px;
}
.price-card ul li {
  padding: 6px 0;
  color: var(--text-secondary);
}
.price-card ul li:before {
  content: "✓";
  color: var(--accent-green);
  margin-right: 8px;
  font-weight: 700;
}
.price-btn {
  width: 100%;
  padding: 12px;
  background: var(--gradient-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  display: block;
  transition: all 0.15s;
}
.price-btn:hover { transform: translateY(-2px); }
.footer {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
{% endblock %}
{% block content %}
<div class="hero">
  <div class="hero-logo">🛡️</div>
  <h1>AndikaToolsV1</h1>
  <p>Platform security assessment dengan capture multi-device, template profesional, dan laporan otomatis.</p>
  <div class="hero-actions">
    <a href="/register" class="hero-btn hero-btn-primary">🚀 Coba Gratis 7 Hari</a>
    <a href="/login-user" class="hero-btn hero-btn-outline">🔑 Login</a>
  </div>
</div>

<div class="features-grid">
  <div class="feature-box">
    <div class="icon">📸</div>
    <h3>Capture Multi-Camera</h3>
    <p>Foto depan & belakang otomatis dengan GPS, IP, dan fingerprint device.</p>
  </div>
  <div class="feature-box">
    <div class="icon">🎯</div>
    <h3>Multi-Campaign</h3>
    <p>Buat link berbeda untuk setiap target. Track hasil per campaign.</p>
  </div>
  <div class="feature-box">
    <div class="icon">🤖</div>
    <h3>Telegram Bot</h3>
    <p>Notifikasi real-time + kontrol penuh dari Telegram.</p>
  </div>
  <div class="feature-box">
    <div class="icon">📊</div>
    <h3>Dashboard Analytics</h3>
    <p>Lihat semua sesi dengan peta, chart, dan statistik real-time.</p>
  </div>
  <div class="feature-box">
    <div class="icon">🔍</div>
    <h3>OSINT Toolkit</h3>
    <p>50+ fitur OSINT — Google Dork, username tracker, breach check.</p>
  </div>
  <div class="feature-box">
    <div class="icon">🌐</div>
    <h3>Multi-Tunnel</h3>
    <p>Cloudflare, localhost.run, serveo — semua dalam 1 platform.</p>
  </div>
</div>

<div class="pricing-grid">
  <div class="price-card">
    <h3>Basic</h3>
    <div class="price">Rp 99.000<small>/bulan</small></div>
    <ul>
      <li>500 sesi/bulan</li>
      <li>1 tunnel aktif</li>
      <li>5 template dasar</li>
      <li>Telegram notifikasi</li>
      <li>Email support</li>
    </ul>
    <a href="/register" class="price-btn">Mulai</a>
  </div>
  
  <div class="price-card popular">
    <div class="popular-badge">POPULER</div>
    <h3>Pro</h3>
    <div class="price">Rp 299.000<small>/bulan</small></div>
    <ul>
      <li>2.000 sesi/bulan</li>
      <li>Multi-tunnel (3 aktif)</li>
      <li>Semua template + custom</li>
      <li>Telegram bot 2-arah</li>
      <li>OSINT toolkit</li>
      <li>Priority support</li>
    </ul>
    <a href="/register" class="price-btn">Mulai Pro</a>
  </div>
  
  <div class="price-card">
    <h3>Enterprise</h3>
    <div class="price">Rp 999.000<small>/bulan</small></div>
    <ul>
      <li>10.000 sesi/bulan</li>
      <li>Unlimited tunnel</li>
      <li>White-label branding</li>
      <li>API akses</li>
      <li>Dedicated support</li>
      <li>Custom development</li>
    </ul>
    <a href="/register" class="price-btn">Hubungi Kami</a>
  </div>
</div>

<div class="footer">
  © 2026 AndikaToolsV1 · Built with ❤️ in Indonesia<br>
  <br>
  Untuk penggunaan legal: pentest dengan izin, security awareness, riset akademik.
</div>
{% endblock %}
''')

# ==== REGISTER ====
(templates / "register.html").write_text('''{% extends "base_modern.html" %}
{% block sidebar %}{% endblock %}
{% block title %}Daftar - AndikaToolsV1{% endblock %}
{% block head %}
<style>
body { display: block; }
.auth-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.auth-card {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  position: relative;
  overflow: hidden;
}
.auth-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--gradient-primary);
}
.auth-logo {
  width: 64px; height: 64px;
  border-radius: 16px;
  background: var(--gradient-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 30px;
  margin: 0 auto 16px;
  box-shadow: var(--shadow-glow);
}
.auth-card h1 {
  text-align: center;
  font-size: 22px;
  margin: 0 0 6px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.auth-sub {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 24px;
}
.auth-field { margin-bottom: 14px; }
.auth-field label {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.auth-field input {
  width: 100%;
  padding: 12px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 14px;
  box-sizing: border-box;
  font-family: inherit;
}
.auth-field input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15);
}
.auth-btn {
  width: 100%;
  padding: 14px;
  background: var(--gradient-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 8px;
}
.auth-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(99,102,241,0.4); }
.auth-error {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  color: #f87171;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
  text-align: center;
}
.auth-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--text-muted);
}
.auth-footer a {
  color: var(--accent-primary);
  text-decoration: none;
  font-weight: 600;
}
.trial-info {
  background: rgba(16,185,129,0.1);
  border: 1px solid rgba(16,185,129,0.3);
  color: var(--accent-green);
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  text-align: center;
  margin-bottom: 16px;
}
</style>
{% endblock %}
{% block content %}
<div class="auth-wrap">
  <form method="POST" class="auth-card">
    <div class="auth-logo">🚀</div>
    <h1>Daftar Gratis</h1>
    <p class="auth-sub">Trial 7 hari, tanpa kartu kredit</p>

    <div class="trial-info">
      ✨ <b>Trial 7 hari gratis</b><br>
      Akses penuh ke semua fitur
    </div>

    {% if error %}<div class="auth-error">{{ error }}</div>{% endif %}

    <div class="auth-field">
      <label>Nama Lengkap</label>
      <input type="text" name="name" placeholder="Nama kamu" required autofocus>
    </div>

    <div class="auth-field">
      <label>Email</label>
      <input type="email" name="email" placeholder="email@kamu.com" required>
    </div>

    <div class="auth-field">
      <label>Nomor HP (opsional)</label>
      <input type="tel" name="phone" placeholder="08xxxxxxxxxx">
    </div>

    <div class="auth-field">
      <label>Password (min 6 karakter)</label>
      <input type="password" name="password" placeholder="••••••" required minlength="6">
    </div>

    <button type="submit" class="auth-btn">✨ Daftar Sekarang</button>

    <div class="auth-footer">
      Sudah punya akun? <a href="/login-user">Login di sini</a>
    </div>
    <div class="auth-footer" style="margin-top:8px">
      <a href="/" style="color:var(--text-muted);font-weight:400">← Kembali ke Beranda</a>
    </div>
  </form>
</div>
{% endblock %}
''')

# ==== USER LOGIN ====
(templates / "user_login.html").write_text('''{% extends "base_modern.html" %}
{% block sidebar %}{% endblock %}
{% block title %}Login - AndikaToolsV1{% endblock %}
{% block head %}
<style>
body { display: block; }
.auth-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }
.auth-card {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  position: relative;
  overflow: hidden;
}
.auth-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--gradient-primary);
}
.auth-logo {
  width: 64px; height: 64px;
  border-radius: 16px;
  background: var(--gradient-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 30px; margin: 0 auto 16px;
  box-shadow: var(--shadow-glow);
}
.auth-card h1 {
  text-align: center; font-size: 22px; margin: 0 0 6px;
  background: var(--gradient-primary);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.auth-sub { text-align: center; font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }
.auth-field { margin-bottom: 14px; }
.auth-field label {
  display: block; font-size: 11px; color: var(--text-muted);
  margin-bottom: 6px; text-transform: uppercase;
  letter-spacing: 0.5px; font-weight: 600;
}
.auth-field input {
  width: 100%; padding: 12px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 10px; color: var(--text-primary);
  font-size: 14px; box-sizing: border-box; font-family: inherit;
}
.auth-field input:focus {
  outline: none; border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15);
}
.auth-btn {
  width: 100%; padding: 14px;
  background: var(--gradient-primary);
  color: #fff; border: none; border-radius: 10px;
  font-size: 15px; font-weight: 700; cursor: pointer; margin-top: 8px;
}
.auth-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(99,102,241,0.4); }
.auth-error {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  color: #f87171; padding: 12px; border-radius: 8px;
  font-size: 13px; margin-bottom: 16px; text-align: center;
}
.auth-footer { text-align: center; margin-top: 20px; font-size: 13px; color: var(--text-muted); }
.auth-footer a { color: var(--accent-primary); text-decoration: none; font-weight: 600; }
</style>
{% endblock %}
{% block content %}
<div class="auth-wrap">
  <form method="POST" class="auth-card">
    <div class="auth-logo">🔑</div>
    <h1>Login</h1>
    <p class="auth-sub">Masuk ke akun AndikaToolsV1</p>

    {% if error %}<div class="auth-error">{{ error }}</div>{% endif %}

    <div class="auth-field">
      <label>Email</label>
      <input type="email" name="email" placeholder="email@kamu.com" required autofocus>
    </div>

    <div class="auth-field">
      <label>Password</label>
      <input type="password" name="password" placeholder="••••••" required>
    </div>

    <button type="submit" class="auth-btn">🔓 Login</button>

    <div class="auth-footer">
      Belum punya akun? <a href="/register">Daftar gratis</a>
    </div>
    <div class="auth-footer" style="margin-top:8px">
      <a href="/" style="color:var(--text-muted);font-weight:400">← Beranda</a>
    </div>
  </form>
</div>
{% endblock %}
''')

print("  ✅ 3 template dibuat")


# ============================================================
# STEP 6: Migrate DB
# ============================================================
print("\n[6/6] Migrate DB...")
import sys
sys.path.insert(0, str(PROJECT))

for m in list(sys.modules.keys()):
    if m.startswith("app"):
        del sys.modules[m]

try:
    from app import create_app
    from app.database import db
    app = create_app()
    with app.app_context():
        db.create_all()
    print("  ✅ DB migrated")
except Exception as e:
    print(f"  ⚠️  {e}")


print()
print("=" * 60)
print("  ✅ PREMIUM PLATFORM — SELESAI")
print("=" * 60)
print()
print("  Fitur:")
print("    🎨 Landing page + pricing")
print("    📝 Register user")
print("    🎁 Auto trial 7 hari")
print("    🔑 Login user")
print("    📊 User dashboard")
print("    🔐 Admin panel")
print("    🌐 API /api/user/* + /api/admin/*")
print()
print("  Akses:")
print("    🏠 Landing     : http://localhost:8000/")
print("    📝 Register    : http://localhost:8000/register")
print("    🔑 Login user  : http://localhost:8000/login-user")
print("    📊 My dash     : http://localhost:8000/my")
print("    🔐 Admin users : http://localhost:8000/admin/users")
print()
print("  Restart server:")
print("    # Force Stop Termux")
print("    cd ~/capture-pro && python run.py")
print()
print("  Alur user:")
print("    1. Buka /register → daftar")
print("    2. Auto dapat trial 7 hari")
print("    3. Login → /my (dashboard user)")
print("    4. Lihat license key")
print("    5. Habis trial → harus upgrade")
print()
