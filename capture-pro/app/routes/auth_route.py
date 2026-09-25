"""Auth routes — register, login, user dashboard."""
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
