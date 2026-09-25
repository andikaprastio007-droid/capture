"""
Paket 1: Reports Suite Installer
- PDF Report Generator
- Session Replay (slider)
- Click Heatmap
- Funnel Analytics
- Screenshot Watermark
Jalankan: python setup_paket1_reports.py
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT = Path.home() / "capture-pro"
HOME = Path.home()

if not PROJECT.exists():
    print(f"❌ Folder {PROJECT} tidak ada.")
    sys.exit(1)


# ============================================================
# STEP 0: Install dependencies
# ============================================================
print("\n[0/7] Install dependencies...")
pkgs = ["Pillow", "python-dateutil"]
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + pkgs)
    print("      OK — Pillow + dateutil")
except Exception as e:
    print(f"      WARN: {e}")

# WeasyPrint optional
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "weasyprint"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("      OK — WeasyPrint (PDF)")
    HAS_PDF = True
except Exception:
    print("      WARN — WeasyPrint gagal install, PDF akan fallback ke HTML")
    HAS_PDF = False


# ============================================================
# STEP 1: Bikin folder services
# ============================================================
print("\n[1/7] Bikin folder & file services...")
services_dir = PROJECT / "app" / "services"
services_dir.mkdir(parents=True, exist_ok=True)

# __init__.py kalau belum ada
(services_dir / "__init__.py").touch(exist_ok=True)

# ---------- watermark.py ----------
watermark_py = services_dir / "watermark.py"
watermark_py.write_text('''"""Auto-annotate screenshot dengan IP + waktu + device."""
import os
from datetime import datetime
from app.config import Config

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def add_watermark(input_path, output_path=None, session_info=None):
    """Tambah watermark ke screenshot.

    session_info: dict {ip, city, device, ts}
    """
    if not HAS_PIL:
        # Fallback: return path as-is
        return input_path

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = base + "_wm" + ext

    try:
        img = Image.open(input_path).convert("RGBA")
        W, H = img.size

        # Overlay semi-transparan
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Font (fallback default kalau tidak ada TTF)
        try:
            font_size = max(12, W // 60)
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        # Text content
        info = session_info or {}
        ts = info.get("ts", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ip = info.get("ip", "-")
        city = info.get("city", "-")
        device = info.get("device", "-")

        lines = [
            f"ReconPro Evidence",
            f"Time   : {ts}",
            f"IP     : {ip}",
            f"Location: {city}",
            f"Device : {device}",
        ]

        # Bikin kotak background di kiri atas
        padding = max(8, W // 100)
        line_h = max(16, W // 50)
        box_w = max(220, W // 3)
        box_h = padding * 2 + line_h * len(lines)

        draw.rectangle([0, 0, box_w, box_h], fill=(0, 0, 0, 140))
        draw.rectangle([0, 0, box_w, box_h], outline=(88, 166, 255, 220), width=2)

        for i, line in enumerate(lines):
            y = padding + i * line_h
            color = (88, 166, 255, 255) if i == 0 else (230, 237, 243, 240)
            draw.text((padding + 4, y), line, fill=color, font=font)

        # Composite
        out = Image.alpha_composite(img, overlay)

        # Simpan (sesuaikan format)
        if output_path.lower().endswith(".png"):
            out.convert("RGB").save(output_path, "PNG", optimize=True)
        else:
            out.convert("RGB").save(output_path, "JPEG", quality=80)

        return output_path
    except Exception as e:
        print(f"[watermark] error: {e}")
        return input_path


def add_watermark_to_session(session_row):
    """Watermark screenshot milik satu sesi."""
    from app.models import Session as SessionModel
    ts = session_row.ts
    screenshot_path = os.path.join(Config.SCREENSHOT_DIR, ts + "_screenshot.png")
    if not os.path.isfile(screenshot_path):
        return None
    info = {
        "ts": session_row.waktu or ts,
        "ip": session_row.ip_publik or session_row.ip_koneksi or "-",
        "city": (session_row.city or "-") + ", " + (session_row.region or "-"),
        "device": session_row.device_type or "-",
    }
    return add_watermark(screenshot_path, session_info=info)
''')
print(f"      OK  {watermark_py}")


# ---------- funnel.py ----------
funnel_py = services_dir / "funnel.py"
funnel_py.write_text('''"""Funnel Analytics - drop-off analysis."""
from app.database import db
from app.models import Session as SessionModel, Event


def campaign_funnel(campaign=None):
    """Hitung funnel: opened -> with_photo -> with_gps -> with_screenshot."""
    q = SessionModel.query
    if campaign and campaign != "all":
        q = q.filter_by(campaign=campaign)

    total = q.count()
    with_photo = q.filter(
        (SessionModel.has_depan == 1) | (SessionModel.has_belakang == 1)
    ).count()
    with_gps = q.filter(SessionModel.lat.isnot(None)).count()
    with_screenshot = q.filter(SessionModel.has_screenshot == 1).count()

    steps = [
        {"name": "Halaman dibuka", "count": total, "icon": "eye"},
        {"name": "Izin kamera + foto", "count": with_photo, "icon": "camera"},
        {"name": "Izin GPS", "count": with_gps, "icon": "map"},
        {"name": "Screenshot tersimpan", "count": with_screenshot, "icon": "image"},
    ]

    # Hitung conversion rate antar step
    for i, s in enumerate(steps):
        if i == 0:
            s["rate"] = 100.0
            s["drop"] = 0
        else:
            prev = steps[i - 1]["count"]
            s["rate"] = (s["count"] / prev * 100) if prev > 0 else 0
            s["drop"] = prev - s["count"]

    overall = (with_screenshot / total * 100) if total > 0 else 0

    return {
        "campaign": campaign or "all",
        "steps": steps,
        "total": total,
        "overall_conversion": round(overall, 1),
    }


def all_campaigns_funnel():
    """Funnel untuk semua campaign."""
    rows = db.session.query(SessionModel.campaign).distinct().all()
    return [campaign_funnel(r[0]) for r in rows]
''')
print(f"      OK  {funnel_py}")


# ---------- pdf_report.py ----------
pdf_report_py = services_dir / "pdf_report.py"
pdf_report_py.write_text('''"""PDF Report Generator - WeasyPrint atau HTML fallback."""
import os
from datetime import datetime
from app.config import Config

try:
    from weasyprint import HTML as WeasyHTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

try:
    from app.services.watermark import add_watermark
    HAS_WATERMARK = True
except ImportError:
    HAS_WATERMARK = False


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: 1.5cm; }
  * { box-sizing: border-box; }
  body { font-family: Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.5; font-size: 11pt; }
  h1 { color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 8px; margin-top: 0; font-size: 22pt; }
  h2 { color: #2a5298; margin-top: 24px; border-bottom: 1px solid #ccc; padding-bottom: 4px; font-size: 14pt; }
  h3 { color: #333; font-size: 12pt; margin-top: 16px; }
  .meta { color: #666; font-size: 10pt; margin-bottom: 20px; }
  .meta b { color: #333; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  th, td { padding: 7px 10px; text-align: left; border-bottom: 1px solid #eee; font-size: 10pt; vertical-align: top; }
  th { background: #f5f7fa; color: #1e3c72; font-weight: 600; }
  .stat-grid { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }
  .stat { background: #f5f7fa; padding: 14px 20px; border-radius: 6px; flex: 1; min-width: 120px; }
  .stat .num { font-size: 22pt; font-weight: bold; color: #1e3c72; line-height: 1; }
  .stat .lbl { font-size: 9pt; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 9pt; font-weight: bold; }
  .badge.high { background: #ffebee; color: #c62828; }
  .badge.low { background: #e8f5e9; color: #2e7d32; }
  .badge.med { background: #fff8e1; color: #f57c00; }
  .evidence { background: #f8f9fa; padding: 10px 14px; border-left: 3px solid #2a5298; margin: 10px 0; font-size: 10pt; }
  .screenshot { max-width: 100%; max-height: 200px; border: 1px solid #ddd; border-radius: 4px; margin-top: 8px; }
  .footer { margin-top: 40px; padding-top: 12px; border-top: 1px solid #eee; text-align: center; color: #999; font-size: 9pt; }
  .page-break { page-break-before: always; }
  .no-break { page-break-inside: avoid; }
</style>
</head>
<body>
<h1>Security Assessment Report</h1>
<div class="meta">
  <b>Generated:</b> {generated}<br>
  <b>Scope:</b> {title}<br>
  <b>Total Sessions:</b> {total_sessions}<br>
  <b>Assessment ID:</b> {assessment_id}
</div>

<h2>Executive Summary</h2>
<p>Laporan ini menyajikan hasil security assessment terhadap target <b>{title}</b>.
Selama periode pengujian, terdeteksi <b>{total_sessions}</b> sesi yang berhasil dicatat,
dengan <b>{with_photo}</b> sesi yang memberikan bukti foto dan <b>{with_gps}</b> sesi dengan data lokasi GPS.</p>

<div class="stat-grid">
  <div class="stat"><div class="num">{total_sessions}</div><div class="lbl">Total Sessions</div></div>
  <div class="stat"><div class="num">{with_photo}</div><div class="lbl">With Photo</div></div>
  <div class="stat"><div class="num">{with_gps}</div><div class="lbl">With GPS</div></div>
  <div class="stat"><div class="num">{with_vpn}</div><div class="lbl">VPN Detected</div></div>
</div>

<h2>Risk Assessment</h2>
<table>
<tr><th>Risk</th><th>Level</th><th>Description</th></tr>
<tr><td>Information Disclosure</td><td><span class="badge high">HIGH</span></td><td>Website meminta data sensitif tanpa verifikasi identitas</td></tr>
<tr><td>Insecure Direct Object Reference</td><td><span class="badge high">HIGH</span></td><td>URL tidak menggunakan token unik per sesi</td></tr>
<tr><td>Missing Rate Limiting</td><td><span class="badge med">MEDIUM</span></td><td>Endpoint upload tidak dibatasi dengan baik</td></tr>
<tr><td>Weak Session Management</td><td><span class="badge med">MEDIUM</span></td><td>Session ID tidak di-rotate secara berkala</td></tr>
</table>

<h2>Detailed Findings</h2>
<table>
<tr>
  <th>#</th>
  <th>Timestamp</th>
  <th>IP Address</th>
  <th>Location</th>
  <th>Device</th>
  <th>VPN</th>
  <th>Evidence</th>
</tr>
{rows}
</table>

<h2>Evidence Details</h2>
{evidence}

<h2>Recommendations</h2>
<ol>
  <li><b>Implementasi CAPTCHA</b> pada endpoint publik yang meminta data sensitif.</li>
  <li><b>Rate limiting ketat</b> per IP — maksimal 10 request per menit.</li>
  <li><b>Validasi input server-side</b> — jangan percaya data dari client.</li>
  <li><b>Audit permission API</b> — minimal permission untuk setiap endpoint.</li>
  <li><b>Content Security Policy (CSP)</b> yang ketat — cegah XSS.</li>
  <li><b>HTTPS wajib</b> dengan HSTS — cegah MITM.</li>
  <li><b>Edukasi pengguna</b> — tentang bahaya phishing dan social engineering.</li>
</ol>

<div class="footer">
  Generated by <b>ReconPro Professional Edition</b><br>
  Laporan ini dibuat untuk keperluan security assessment dengan izin tertulis.<br>
  Dokumen ini bersifat CONFIDENTIAL.
</div>
</body>
</html>
"""


def _evidence_block(s, idx):
    """Bikin blok evidence per sesi (dengan screenshot kalau ada)."""
    parts = [f'<div class="no-break"><h3>#{idx} — Session {s.ts}</h3>']
    parts.append('<div class="evidence">')
    parts.append(f'<b>Waktu:</b> {s.waktu}<br>')
    parts.append(f'<b>IP:</b> {s.ip_publik or s.ip_koneksi or "-"}<br>')
    if s.ip_lokal:
        parts.append(f'<b>IP Lokal:</b> {s.ip_lokal}<br>')
    parts.append(f'<b>Lokasi:</b> {s.city or "-"}, {s.region or "-"}<br>')
    if s.lat and s.lon:
        parts.append(f'<b>GPS:</b> {s.lat:.5f}, {s.lon:.5f}<br>')
    if s.alamat:
        parts.append(f'<b>Alamat:</b> {s.alamat[:200]}<br>')
    parts.append(f'<b>ISP:</b> {s.isp or "-"}<br>')
    parts.append(f'<b>Device:</b> {s.device_type or "-"} ({s.os_type or "-"})<br>')
    if s.is_vpn:
        parts.append('<b>VPN:</b> <span class="badge high">YES</span><br>')

    # Path screenshot
    ss_path = os.path.join(Config.SCREENSHOT_DIR, s.ts + "_screenshot.png")
    if os.path.isfile(ss_path):
        # Convert ke file:// URL untuk WeasyPrint
        parts.append(f'<b>Bukti:</b><br><img src="file://{ss_path}" class="screenshot">')

    parts.append('</div></div>')
    return "".join(parts)


def generate_pdf_report(single_session=None, sessions=None, title="Assessment"):
    """Generate PDF report. Return path."""
    if single_session is not None:
        sessions = [single_session]
        title = f"Session {single_session.ts}"
    if sessions is None:
        sessions = []

    total = len(sessions)
    with_photo = sum(1 for s in sessions if s.has_depan or s.has_belakang)
    with_gps = sum(1 for s in sessions if s.lat)
    with_vpn = sum(1 for s in sessions if s.is_vpn)

    rows = ""
    for i, s in enumerate(sessions, 1):
        evidence_tags = []
        if s.has_depan: evidence_tags.append("foto-depan")
        if s.has_belakang: evidence_tags.append("foto-belakang")
        if s.has_screenshot: evidence_tags.append("screenshot")

        vpn_badge = '<span class="badge high">YES</span>' if s.is_vpn else '<span class="badge low">NO</span>'

        rows += f"""<tr>
  <td>{i}</td>
  <td>{s.ts}</td>
  <td>{s.ip_publik or s.ip_koneksi or "-"}</td>
  <td>{s.city or "-"}, {s.region or "-"}</td>
  <td>{s.device_type or "-"}</td>
  <td>{vpn_badge}</td>
  <td>{", ".join(evidence_tags) or "-"}</td>
</tr>"""

    # Evidence blocks (maks 10 sesi biar PDF tidak kepanjangan)
    evidence = ""
    for i, s in enumerate(sessions[:10], 1):
        evidence += _evidence_block(s, i)
    if len(sessions) > 10:
        evidence += f"<p><i>... dan {len(sessions) - 10} sesi lainnya (lihat CSV export).</i></p>"

    assessment_id = datetime.now().strftime("ASMT-%Y%m%d-%H%M%S")

    html = HTML_TEMPLATE.format(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        title=title,
        total_sessions=total,
        with_photo=with_photo,
        with_gps=with_gps,
        with_vpn=with_vpn,
        rows=rows,
        evidence=evidence,
        assessment_id=assessment_id,
    )

    ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")

    if HAS_WEASYPRINT:
        out_path = os.path.join(Config.REPORT_DIR, f"report_{ts_file}.pdf")
        try:
            WeasyHTML(string=html, base_url="/").write_pdf(out_path)
            return out_path, "pdf"
        except Exception as e:
            print(f"[pdf] WeasyPrint error: {e}, fallback to HTML")

    # Fallback: HTML
    out_path = os.path.join(Config.REPORT_DIR, f"report_{ts_file}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path, "html"
''')
print(f"      OK  {pdf_report_py}")


# ============================================================
# STEP 2: Bikin routes
# ============================================================
print("\n[2/7] Bikin routes (reports, replay, heatmap, funnel)...")
routes_dir = PROJECT / "app" / "routes"

# ---------- reports.py ----------
reports_py = routes_dir / "reports.py"
reports_py.write_text('''"""Reports - PDF generator endpoints."""
from flask import Blueprint, send_file, render_template, jsonify, abort
from app.auth import login_required
from app.config import Config
from app.models import Session as SessionModel
from app.services.pdf_report import generate_pdf_report
from app.services.watermark import add_watermark_to_session, add_watermark
from app.services.funnel import campaign_funnel, all_campaigns_funnel
import os

bp = Blueprint("reports", __name__)


@bp.route("/reports/session/<ts>")
@login_required
def session_report(ts):
    s = SessionModel.query.filter_by(ts=ts).first()
    if not s:
        abort(404)
    # Watermark screenshot dulu
    try:
        add_watermark_to_session(s)
    except Exception as e:
        print(f"[watermark] {e}")
    path, fmt = generate_pdf_report(single_session=s)
    mimetype = "application/pdf" if fmt == "pdf" else "text/html"
    ext = "pdf" if fmt == "pdf" else "html"
    return send_file(path, mimetype=mimetype, as_attachment=True,
                     download_name=f"report_{ts}.{ext}")


@bp.route("/reports/campaign/<campaign>")
@login_required
def campaign_report(campaign):
    sessions = SessionModel.query.filter_by(campaign=campaign).order_by(SessionModel.id.desc()).all()
    if not sessions:
        abort(404)
    path, fmt = generate_pdf_report(sessions=sessions, title=f"Campaign: {campaign}")
    mimetype = "application/pdf" if fmt == "pdf" else "text/html"
    ext = "pdf" if fmt == "pdf" else "html"
    return send_file(path, mimetype=mimetype, as_attachment=True,
                     download_name=f"report_{campaign}.{ext}")


@bp.route("/reports/all")
@login_required
def all_report():
    sessions = SessionModel.query.order_by(SessionModel.id.desc()).all()
    if not sessions:
        abort(404)
    path, fmt = generate_pdf_report(sessions=sessions, title="All Sessions")
    mimetype = "application/pdf" if fmt == "pdf" else "text/html"
    ext = "pdf" if fmt == "pdf" else "html"
    return send_file(path, mimetype=mimetype, as_attachment=True,
                     download_name=f"report_all.{ext}")


@bp.route("/reports/preview/<ts>")
@login_required
def preview_report(ts):
    """Preview report di browser (HTML view)."""
    s = SessionModel.query.filter_by(ts=ts).first()
    if not s:
        abort(404)
    path, fmt = generate_pdf_report(single_session=s)
    if fmt == "html":
        return send_file(path, mimetype="text/html")
    return send_file(path, mimetype="application/pdf")
''')
print(f"      OK  {reports_py}")


# ---------- replay.py (heatmap + replay) ----------
replay_py = routes_dir / "replay.py"
replay_py.write_text('''"""Session Replay + Click Heatmap endpoints."""
from flask import Blueprint, jsonify, send_from_directory
from app.auth import login_required
from app.config import Config
from app.models import Session as SessionModel, Event
from app.services.watermark import add_watermark_to_session
import json
import os

bp = Blueprint("replay", __name__)


@bp.route("/api/session/<ts>/replay")
@login_required
def session_replay(ts):
    """Ambil semua screenshot frames untuk replay.

    Karena kita tidak simpan frame terus-menerus, kita pakai:
    - Screenshot utama
    - Burst photos (kalau ada)
    - Event timeline
    """
    s = SessionModel.query.filter_by(ts=ts).first()
    if not s:
        return jsonify({"ok": False, "msg": "not found"}), 404

    frames = []

    # 1. Screenshot utama
    screenshot_path = os.path.join(Config.SCREENSHOT_DIR, ts + "_screenshot.png")
    if os.path.isfile(screenshot_path):
        # Watermark dulu
        try:
            wm_path = add_watermark_to_session(s)
            if wm_path:
                frames.append({"type": "screenshot", "filename": os.path.basename(wm_path), "label": "Screenshot"})
        except Exception:
            pass
        if not frames or frames[-1].get("filename") != os.path.basename(screenshot_path):
            frames.append({"type": "screenshot", "filename": ts + "_screenshot.png", "label": "Screenshot"})

    # 2. Foto depan
    depan_path = os.path.join(Config.UPLOAD_DIR, ts + "_depan.png")
    if os.path.isfile(depan_path):
        frames.append({"type": "photo", "filename": ts + "_depan.png", "label": "Foto Depan"})

    # 3. Foto belakang
    belakang_path = os.path.join(Config.UPLOAD_DIR, ts + "_belakang.png")
    if os.path.isfile(belakang_path):
        frames.append({"type": "photo", "filename": ts + "_belakang.png", "label": "Foto Belakang"})

    # 4. Burst photos (kalau ada)
    if os.path.isdir(Config.BURST_DIR):
        burst_files = sorted([f for f in os.listdir(Config.BURST_DIR) if f.startswith(ts + "_burst_")])
        for bf in burst_files:
            frames.append({"type": "burst", "filename": bf, "label": "Burst"})

    # 5. Event timeline
    events = Event.query.filter_by(session_ts=ts).order_by(Event.id).limit(200).all()
    timeline = [{"type": e.event_type, "data": e.data, "time": e.created_at.isoformat() if e.created_at else None}
                for e in events]

    return jsonify({
        "ok": True,
        "frames": frames,
        "timeline": timeline,
        "session": s.to_dict(),
    })


@bp.route("/api/heatmap/<ts>")
@login_required
def click_heatmap(ts):
    """Aggregate click events untuk heatmap."""
    rows = Event.query.filter_by(session_ts=ts, event_type="click").all()
    clicks = []
    for r in rows:
        try:
            d = json.loads(r.data)
            x = d.get("x")
            y = d.get("y")
            vw = d.get("vw") or 1
            vh = d.get("vh") or 1
            if x is not None and y is not None:
                # Normalize ke 0-100%
                clicks.append({
                    "x": round(x / vw * 100, 2),
                    "y": round(y / vh * 100, 2),
                    "raw_x": x,
                    "raw_y": y,
                    "vw": vw,
                    "vh": vh,
                })
        except Exception:
            pass

    # Ambil screenshot untuk background heatmap
    screenshot_url = None
    screenshot_path = os.path.join(Config.SCREENSHOT_DIR, ts + "_screenshot.png")
    if os.path.isfile(screenshot_path):
        screenshot_url = "/api/file/" + ts + "_screenshot.png"

    return jsonify({
        "ok": True,
        "clicks": clicks,
        "total": len(clicks),
        "screenshot_url": screenshot_url,
    })


@bp.route("/api/funnel/<campaign>")
@login_required
def funnel_api(campaign):
    from app.services.funnel import campaign_funnel
    return jsonify(campaign_funnel(campaign if campaign != "all" else None))


@bp.route("/api/funnel-all")
@login_required
def funnel_all():
    from app.services.funnel import all_campaigns_funnel
    return jsonify(all_campaigns_funnel())
''')
print(f"      OK  {replay_py}")


# ============================================================
# STEP 3: Patch app/__init__.py
# ============================================================
print("\n[3/7] Patch app/__init__.py...")
init_file = PROJECT / "app" / "__init__.py"
if init_file.exists():
    content = init_file.read_text(encoding="utf-8")
    backup = init_file.with_suffix(".py.bak_report")
    backup.write_text(content, encoding="utf-8")

    # Tambah import reports + replay
    if "from app.routes.reports import bp as reports_bp" not in content:
        if "from app.routes.api import bp as api_bp" in content:
            content = content.replace(
                "from app.routes.api import bp as api_bp",
                "from app.routes.api import bp as api_bp\n    from app.routes.reports import bp as reports_bp\n    from app.routes.replay import bp as replay_bp"
            )

    # Register blueprint
    if "app.register_blueprint(reports_bp)" not in content:
        if 'app.register_blueprint(api_bp, url_prefix="/api")' in content:
            content = content.replace(
                'app.register_blueprint(api_bp, url_prefix="/api")',
                'app.register_blueprint(api_bp, url_prefix="/api")\n    app.register_blueprint(reports_bp)\n    app.register_blueprint(replay_bp, url_prefix="/api")'
            )

    # csrf.exempt untuk replay (POST endpoints)
    if "csrf.exempt(replay_mod.bp)" not in content:
        if "from app.routes import tunnel as tunnel_mod" in content:
            content = content.replace(
                "from app.routes import tunnel as tunnel_mod\n    csrf.exempt(tunnel_mod.bp)",
                "from app.routes import tunnel as tunnel_mod\n    csrf.exempt(tunnel_mod.bp)\n\n    from app.routes import replay as replay_mod\n    csrf.exempt(replay_mod.bp)"
            )

    init_file.write_text(content, encoding="utf-8")
    print(f"      OK  {init_file} (backup: {backup.name})")
else:
    print(f"      SKIP")


# ============================================================
# STEP 4: Patch dashboard.html - tombol baru
# ============================================================
print("\n[4/7] Patch dashboard.html...")
dash_file = PROJECT / "app" / "templates" / "dashboard.html"
if dash_file.exists():
    content = dash_file.read_text(encoding="utf-8")
    backup = dash_file.with_suffix(".html.bak_report")
    backup.write_text(content, encoding="utf-8")

    # Tambah tombol "PDF Report" di header
    if 'href="/reports/all"' not in content:
        content = content.replace(
            '<a class="btn" href="/features"',
            '<a class="btn gold" href="/reports/all">📕 PDF Report</a>\n    <a class="btn" href="/features"'
        )

    # Tambah tombol di kartu sesi (Replay, Heatmap, PDF)
    if 'class="btn-action show-replay"' not in content:
        content = content.replace(
            '<a href="#" class="btn-action show-detail" data-ts="{{ s.ts }}">Detail</a>',
            '<a href="#" class="btn-action show-detail" data-ts="{{ s.ts }}">Detail</a>\n        <a href="#" class="btn-action show-replay" data-ts="{{ s.ts }}">🎥 Replay</a>\n        <a href="#" class="btn-action show-heatmap" data-ts="{{ s.ts }}">🔥 Heatmap</a>\n        <a href="/reports/session/{{ s.ts }}" class="btn-action">📕 PDF</a>'
        )

    dash_file.write_text(content, encoding="utf-8")
    print(f"      OK  {dash_file} (backup: {backup.name})")
else:
    print(f"      SKIP")


# ============================================================
# STEP 5: Tambah CSS
# ============================================================
print("\n[5/7] Patch style.css...")
css_file = PROJECT / "app" / "static" / "css" / "style.css"
if css_file.exists():
    content = css_file.read_text(encoding="utf-8")

    if ".replay-modal" not in content:
        css_extra = """

/* ============ REPORTS SUITE ============ */
.btn.gold { background: #d29922; color: #0f1117; font-weight: 600; }
.btn.gold:hover { background: #e3b341; }

.replay-modal { text-align: center; }
.replay-img { width: 100%; max-height: 60vh; object-fit: contain; background: #000; border-radius: 6px; border: 1px solid #30363d; }
.replay-slider { width: 100%; margin: 12px 0; accent-color: #58a6ff; }
.replay-controls { display: flex; justify-content: center; gap: 8px; margin: 10px 0; }
.replay-btn { background: #1e6feb; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.replay-btn:hover { background: #388bfd; }
.replay-label { font-size: 12px; color: #8b949e; margin: 4px 0; }
.replay-timeline {
  max-height: 150px; overflow-y: auto; background: #0d1117;
  border: 1px solid #21262d; border-radius: 6px; padding: 8px;
  text-align: left; font-size: 11px; margin-top: 12px;
}
.replay-event { padding: 4px 8px; border-bottom: 1px solid #21262d; color: #8b949e; }
.replay-event:last-child { border-bottom: none; }
.replay-event b { color: #58a6ff; }
.replay-event .time { color: #6e7681; }

.heatmap-container {
  position: relative;
  background: #000;
  border-radius: 6px;
  overflow: hidden;
  min-height: 300px;
}
.heatmap-bg {
  width: 100%;
  display: block;
  opacity: 0.6;
}
.heatmap-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.heatmap-dot {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(255, 100, 100, 0.85) 0%, rgba(255, 100, 100, 0.4) 40%, rgba(255, 100, 100, 0) 70%);
  pointer-events: none;
}
.heatmap-no-bg {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #6e7681;
  font-size: 13px;
}
.heatmap-stats {
  text-align: center;
  margin-top: 10px;
  font-size: 13px;
  color: #8b949e;
}
.heatmap-stats b { color: #58a6ff; }
"""
        content += css_extra
        css_file.write_text(content, encoding="utf-8")
        print(f"      OK  {css_file}")
    else:
        print(f"      SKIP — CSS sudah ada")


# ============================================================
# STEP 6: Patch dashboard.js - tambah JS handlers
# ============================================================
print("\n[6/7] Patch dashboard.js...")
js_file = PROJECT / "app" / "static" / "js" / "dashboard.js"
if js_file.exists():
    content = js_file.read_text(encoding="utf-8")

    if "showReplay" not in content:
        js_extra = r"""

// ============================================================
// REPORTS SUITE — Replay + Heatmap
// ============================================================

// === SESSION REPLAY ===
document.querySelectorAll('.show-replay').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;

    Swal.fire({ title: 'Loading replay...', didOpen: () => Swal.showLoading(), allowOutsideClick: false });

    try {
      const res = await fetch('/api/session/' + ts + '/replay');
      const data = await res.json();
      Swal.close();

      if (!data.ok || !data.frames || !data.frames.length) {
        Swal.fire('Replay', 'Belum ada frame untuk sesi ini', 'info');
        return;
      }

      const frames = data.frames;
      const timeline = data.timeline || [];

      let timelineHtml = '';
      if (timeline.length) {
        timelineHtml = '<div class="replay-timeline">' +
          timeline.slice(-50).map(t =>
            '<div class="replay-event"><b>' + escHtml(t.type) + '</b> <span class="time">' + escHtml(t.time || '') + '</span><br>' +
            '<span style="color:#6e7681;font-size:10px">' + escHtml((t.data || '').substring(0, 120)) + '</span></div>'
          ).join('') + '</div>';
      }

      Swal.fire({
        title: '🎥 Session Replay — ' + ts,
        html:
          '<div class="replay-modal">' +
          '<img id="replayImg" class="replay-img" src="/api/file/' + frames[0].filename + '">' +
          '<div class="replay-label" id="replayLabel">' + escHtml(frames[0].label) + ' (' + frames.length + ' frames)</div>' +
          '<input type="range" id="replaySlider" class="replay-slider" min="0" max="' + (frames.length - 1) + '" value="0">' +
          '<div class="replay-controls">' +
            '<button class="replay-btn" id="replayPrev">⏮ Prev</button>' +
            '<button class="replay-btn" id="replayPlay">▶ Play</button>' +
            '<button class="replay-btn" id="replayNext">⏭ Next</button>' +
          '</div>' +
          timelineHtml +
          '</div>',
        width: 800,
        showConfirmButton: false,
        showCloseButton: true,
        didOpen: () => {
          const img = document.getElementById('replayImg');
          const slider = document.getElementById('replaySlider');
          const label = document.getElementById('replayLabel');
          let playing = false;
          let timer = null;

          function showFrame(i) {
            i = Math.max(0, Math.min(frames.length - 1, i));
            slider.value = i;
            img.src = '/api/file/' + frames[i].filename;
            label.textContent = frames[i].label + ' (' + (i + 1) + '/' + frames.length + ')';
          }

          slider.addEventListener('input', () => showFrame(parseInt(slider.value)));
          document.getElementById('replayPrev').addEventListener('click', () => showFrame(parseInt(slider.value) - 1));
          document.getElementById('replayNext').addEventListener('click', () => showFrame(parseInt(slider.value) + 1));
          document.getElementById('replayPlay').addEventListener('click', function() {
            if (playing) {
              clearInterval(timer);
              playing = false;
              this.textContent = '▶ Play';
            } else {
              playing = true;
              this.textContent = '⏸ Pause';
              timer = setInterval(() => {
                let v = parseInt(slider.value) + 1;
                if (v >= frames.length) v = 0;
                showFrame(v);
              }, 800);
            }
          });
        }
      });
    } catch (err) {
      Swal.close();
      Swal.fire('Error', err.message, 'error');
    }
  });
});

// === CLICK HEATMAP ===
document.querySelectorAll('.show-heatmap').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;

    Swal.fire({ title: 'Loading heatmap...', didOpen: () => Swal.showLoading(), allowOutsideClick: false });

    try {
      const res = await fetch('/api/heatmap/' + ts);
      const data = await res.json();
      Swal.close();

      if (!data.ok || !data.clicks || !data.clicks.length) {
        Swal.fire('Heatmap', 'Belum ada klik untuk sesi ini', 'info');
        return;
      }

      // Bikin visual heatmap
      let bgHtml = '';
      if (data.screenshot_url) {
        bgHtml = '<img class="heatmap-bg" src="' + data.screenshot_url + '">';
      } else {
        bgHtml = '<div class="heatmap-no-bg">Screenshot tidak tersedia</div>';
      }

      const dots = data.clicks.map(c =>
        '<div class="heatmap-dot" style="left:' + c.x + '%;top:' + c.y + '%"></div>'
      ).join('');

      Swal.fire({
        title: '🔥 Click Heatmap — ' + ts,
        html:
          '<div class="heatmap-container">' +
          bgHtml +
          '<div class="heatmap-overlay">' + dots + '</div>' +
          '</div>' +
          '<div class="heatmap-stats">Total klik: <b>' + data.total + '</b> · Area merah = sering diklik</div>',
        width: 750,
        showConfirmButton: true,
        confirmButtonText: 'Tutup'
      });
    } catch (err) {
      Swal.close();
      Swal.fire('Error', err.message, 'error');
    }
  });
});

function escHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
"""
        content += js_extra
        js_file.write_text(content, encoding="utf-8")
        print(f"      OK  {js_file}")
    else:
        print(f"      SKIP — JS sudah ada")


# ============================================================
# STEP 7: Pastikan folder report & config
# ============================================================
print("\n[7/7] Setup folder...")
report_dir = PROJECT / "data" / "reports"
report_dir.mkdir(parents=True, exist_ok=True)
print(f"      OK  {report_dir}")

# Patch Config kalau REPORT_DIR belum ada
config_file = PROJECT / "app" / "config.py"
if config_file.exists():
    content = config_file.read_text(encoding="utf-8")
    if "REPORT_DIR" not in content:
        content = content.replace(
            '    REPLAY_DIR = os.environ.get("REPLAY_DIR", str(BASE_DIR / "data" / "replays"))',
            '    REPLAY_DIR = os.environ.get("REPLAY_DIR", str(BASE_DIR / "data" / "replays"))\n    REPORT_DIR = os.environ.get("REPORT_DIR", str(BASE_DIR / "data" / "reports"))'
        )
        config_file.write_text(content, encoding="utf-8")
        print(f"      OK  Patch config.py (tambah REPORT_DIR)")
    else:
        print(f"      OK  REPORT_DIR sudah ada")


# ============================================================
# SELESAI
# ============================================================
print()
print("=" * 60)
print("  ✅ PAKET 1: REPORTS SUITE — SELESAI")
print("=" * 60)
print()
print("  Fitur yang ditambahkan:")
print("    📕 PDF Report (per sesi, campaign, all)")
print("    🎥 Session Replay (slider playback)")
print("    🔥 Click Heatmap (visual)")
print("    📉 Funnel Analytics (API)")
print("    💧 Screenshot Watermark (auto)")
print()
print("  Cara pakai:")
print("    1. Restart server:")
print("         cd ~/capture-pro")
print("         pkill -f 'python run.py'")
print("         python run.py")
print()
print("    2. Buka dashboard:")
print("         http://localhost:8000/dashboard")
print()
print("    3. Tombol baru:")
print("         - 📕 PDF Report (header) — laporan semua")
print("         - 🎥 Replay (per sesi)")
print("         - 🔥 Heatmap (per sesi)")
print("         - 📕 PDF (per sesi)")
print()
print("  Backup files:")
print("    - app/__init__.py.bak_report")
print("    - app/templates/dashboard.html.bak_report")
print()
if not HAS_PDF:
    print("  ⚠️  WeasyPrint gagal install.")
    print("     PDF akan fallback ke HTML (bisa di-print dari browser).")
    print("     Untuk install manual:")
    print("       pkg install -y pango cairo libffi")
    print("       pip install weasyprint")
    print()
