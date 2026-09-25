"""OSINT endpoints — semua lookup dari sumber publik."""
from flask import Blueprint, jsonify, request, render_template, Response
from app.auth import login_required

# Basic OSINT
from app.services.osint_pro import (
    ip_intel, email_breach, domain_whois, dns_lookup,
    subdomain_finder, ssl_info, http_headers, phone_lookup, username_check,
)
# Extended OSINT
from app.services.osint_extended import (
    generate_dorks, username_tracker, wayback_lookup, hibp_check, extract_metadata,
)
# API OSINT
from app.services.osint_api import (
    shodan_lookup, shodan_search, virustotal_lookup, urlscan_submit,
    urlscan_result, hunter_domain_search, abuseipdb_check, target_profile,
)

bp = Blueprint("osint_pro", __name__)


@bp.route("/osint")
@login_required
def osint_page():
    return render_template("osint.html")


# ============================================================
# BASIC OSINT
# ============================================================
@bp.route("/api/osint/ip/<ip>")
@login_required
def api_ip(ip):
    return jsonify(ip_intel(ip))


@bp.route("/api/osint/email/<email>")
@login_required
def api_email(email):
    return jsonify(email_breach(email))


@bp.route("/api/osint/domain/<domain>")
@login_required
def api_domain(domain):
    return jsonify(domain_whois(domain))


@bp.route("/api/osint/dns/<domain>")
@login_required
def api_dns(domain):
    return jsonify(dns_lookup(domain))


@bp.route("/api/osint/subdomain/<domain>")
@login_required
def api_subdomain(domain):
    return jsonify(subdomain_finder(domain))


@bp.route("/api/osint/ssl/<domain>")
@login_required
def api_ssl(domain):
    return jsonify(ssl_info(domain))


@bp.route("/api/osint/http/<path:url>")
@login_required
def api_http(url):
    return jsonify(http_headers(url))


@bp.route("/api/osint/phone/<phone>")
@login_required
def api_phone(phone):
    country = request.args.get("country", "ID")
    return jsonify(phone_lookup(phone, country))


# ============================================================
# EXTENDED OSINT
# ============================================================
@bp.route("/api/osint/dork/<domain>")
@login_required
def api_dork(domain):
    return jsonify(generate_dorks(domain))


@bp.route("/api/osint/username-tracker/<username>")
@login_required
def api_username_tracker(username):
    return jsonify(username_tracker(username))


@bp.route("/api/osint/wayback/<domain>")
@login_required
def api_wayback(domain):
    return jsonify(wayback_lookup(domain))


@bp.route("/api/osint/hibp/<email>")
@login_required
def api_hibp(email):
    return jsonify(hibp_check(email))


@bp.route("/api/osint/metadata", methods=["POST"])
@login_required
def api_metadata():
    """Upload file & extract metadata."""
    if "file" not in request.files:
        return jsonify({"ok": False, "msg": "File tidak ada"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"ok": False, "msg": "Filename kosong"}), 400
    try:
        result = extract_metadata(f.read(), f.filename)
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


# ============================================================
# API OSINT
# ============================================================
@bp.route("/api/osint/shodan/ip/<ip>")
@login_required
def api_shodan_ip(ip):
    return jsonify(shodan_lookup(ip))


@bp.route("/api/osint/shodan/search", methods=["POST"])
@login_required
def api_shodan_search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    limit = int(data.get("limit", 20))
    if not query:
        return jsonify({"ok": False, "msg": "Query kosong"}), 400
    return jsonify(shodan_search(query, limit))


@bp.route("/api/osint/virustotal/<type_>/<path:target>")
@login_required
def api_virustotal(type_, target):
    return jsonify(virustotal_lookup(target, type_))


@bp.route("/api/osint/urlscan/submit", methods=["POST"])
@login_required
def api_urlscan_submit():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"ok": False, "msg": "URL kosong"}), 400
    return jsonify(urlscan_submit(url))


@bp.route("/api/osint/urlscan/result/<uuid>")
@login_required
def api_urlscan_result(uuid):
    return jsonify(urlscan_result(uuid))


@bp.route("/api/osint/hunter/<domain>")
@login_required
def api_hunter(domain):
    return jsonify(hunter_domain_search(domain))


@bp.route("/api/osint/abuseipdb/<ip>")
@login_required
def api_abuseipdb(ip):
    return jsonify(abuseipdb_check(ip))


# ============================================================
# TARGET PROFILE
# ============================================================
@bp.route("/api/osint/profile", methods=["POST"])
@login_required
def api_profile():
    data = request.get_json(silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"ok": False, "msg": "Target kosong"}), 400
    return jsonify({"ok": True, "data": target_profile(target)})


# ============================================================
# BULK LOOKUP
# ============================================================
@bp.route("/api/osint/bulk", methods=["POST"])
@login_required
def api_bulk():
    """Bulk lookup dari list target."""
    data = request.get_json(silent=True) or {}
    targets = data.get("targets") or []
    if not targets:
        return jsonify({"ok": False, "msg": "Targets kosong"}), 400

    # Limit 50 biar tidak timeout
    targets = targets[:50]
    results = []
    for t in targets:
        t = str(t).strip()
        if not t:
            continue
        try:
            results.append(target_profile(t))
        except Exception as e:
            results.append({"target": t, "error": str(e)})

    return jsonify({"ok": True, "count": len(results), "results": results})


# ============================================================
# AUTO TARGET
# ============================================================
@bp.route("/api/osint/target", methods=["POST"])
@login_required
def api_target():
    """Auto-detect target type."""
    import re
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"ok": False, "msg": "Target kosong"}), 400

    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target):
        return jsonify({"type": "ip", "results": ip_intel(target)})
    elif "@" in target:
        return jsonify({"type": "email", "results": email_breach(target)})
    elif re.match(r"^[+\d\s\-()]+$", target) and len(target) >= 8:
        return jsonify({"type": "phone", "results": phone_lookup(target)})
    elif "." in target and " " not in target:
        return jsonify({"type": "domain", "results": {
            "whois": domain_whois(target),
            "dns": dns_lookup(target),
            "ssl": ssl_info(target),
            "http": http_headers(target),
        }})
    else:
        return jsonify({"type": "username", "results": username_check(target)})


# ============================================================
# EXPORT REPORT
# ============================================================
@bp.route("/api/osint/export", methods=["POST"])
@login_required
def api_export():
    """Export hasil OSINT sebagai JSON atau HTML report."""
    data = request.get_json(silent=True) or {}
    profile = data.get("profile") or {}
    fmt = data.get("format", "json")

    if fmt == "json":
        return Response(json.dumps(profile, indent=2, default=str),
                        mimetype="application/json",
                        headers={"Content-Disposition": "attachment; filename=osint.json"})

    # HTML report
    html = _osint_html_report(profile)
    return Response(html, mimetype="text/html")


def _osint_html_report(profile):
    from datetime import datetime
    target = profile.get("target", "Unknown")
    score = profile.get("risk_score", 0)
    score_color = "#c62828" if score > 60 else ("#f57c00" if score > 30 else "#2e7d32")

    rows = ""
    def render_obj(obj, indent=0):
        out = ""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    out += f'<tr><td style="padding:8px;vertical-align:top;color:#666">{"&nbsp;"*indent*4}<b>{k}</b></td><td style="padding:8px">'
                    out += render_obj(v, indent+1)
                    out += '</td></tr>'
                else:
                    out += f'<tr><td style="padding:8px;vertical-align:top;color:#666">{"&nbsp;"*indent*4}{k}</td><td style="padding:8px;word-break:break-all">{v}</td></tr>'
        elif isinstance(obj, list):
            out += '<ul style="margin:0;padding-left:20px">'
            for i in obj[:20]:
                out += f'<li>{render_obj(i, indent+1) if isinstance(i,(dict,list)) else i}</li>'
            out += '</ul>'
        else:
            out += str(obj)
        return out

    rows = render_obj(profile)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>OSINT Report — {target}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; }}
h1 {{ color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 8px; }}
.score {{ display: inline-block; padding: 8px 20px; background: {score_color}; color: #fff; border-radius: 20px; font-weight: bold; font-size: 18px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
td {{ border-bottom: 1px solid #eee; }}
.btn {{ background: #1e6f72; color: #fff; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; margin: 10px 0; }}
@media print {{ .btn {{ display: none; }} }}
</style></head>
<body>
<h1>OSINT Report</h1>
<p><b>Target:</b> {target}</p>
<p><b>Risk Score:</b> <span class="score">{score}/100</span></p>
<p><b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
<h2>Details</h2>
<table>{rows}</table>
<p style="margin-top:40px;text-align:center;color:#999;font-size:12px">Generated by ReconPro OSINT · CONFIDENTIAL</p>
</body></html>"""


import json
