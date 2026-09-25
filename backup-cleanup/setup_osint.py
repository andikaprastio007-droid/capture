"""
Installer: OSINT Toolkit
- IP Intelligence
- Email Breach Check
- Domain WHOIS + DNS + Subdomain
- SSL/TLS + HTTP Headers
- Username Enumeration
- Phone Lookup
- Semua hasil bisa di-export
Jalankan: python setup_osint.py
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT = Path.home() / "capture-pro"

if not PROJECT.exists():
    print(f"❌ Folder {PROJECT} tidak ada.")
    sys.exit(1)


# ============================================================
# STEP 0: Install deps
# ============================================================
print("\n[0/6] Install dependencies...")
pkgs = ["dnspython", "python-whois", "phonenumbers", "requests"]
for pkg in pkgs:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"      OK  {pkg}")
    except Exception as e:
        print(f"      WARN  {pkg}: {e}")


# ============================================================
# STEP 1: Bikin service OSINT
# ============================================================
print("\n[1/6] Bikin service osint_pro...")
services = PROJECT / "app" / "services"
services.mkdir(parents=True, exist_ok=True)

osint_py = services / "osint_pro.py"
osint_py.write_text('''"""OSINT Toolkit — semua lookup legal dari sumber publik."""
import os
import json
import socket
import ssl
import urllib.request
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False

try:
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone as tz
    HAS_PHONE = True
except ImportError:
    HAS_PHONE = False


# ============================================================
# IP INTELLIGENCE
# ============================================================
def ip_intel(ip):
    """Cek IP: negara, ISP, VPN, tipe."""
    result = {"ip": ip, "lookup_at": datetime.now().isoformat()}

    # Basic info dari ip-api.com
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=66846719", timeout=10)
        result["basic"] = r.json()
    except Exception as e:
        result["basic"] = {"error": str(e)}

    # VPN check via proxycheck.io
    try:
        r = requests.get(f"https://proxycheck.io/v2/{ip}?vpn=1&asn=1&risk=1", timeout=10)
        data = r.json()
        result["proxycheck"] = data.get(ip, {})
    except Exception as e:
        result["proxycheck"] = {"error": str(e)}

    # ipapi.co
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
        result["ipapi"] = r.json()
    except Exception as e:
        result["ipapi"] = {"error": str(e)}

    # Reverse DNS
    try:
        result["reverse_dns"] = socket.gethostbyaddr(ip)[0]
    except Exception:
        result["reverse_dns"] = None

    # Geolocation map link
    lat = result.get("basic", {}).get("lat")
    lon = result.get("basic", {}).get("lon")
    if lat and lon:
        result["map_url"] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=13/{lat}/{lon}"

    return result


def email_breach(email):
    """Cek email di data breach (Have I Been Pwned)."""
    result = {"email": email, "lookup_at": datetime.now().isoformat()}
    try:
        r = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false",
            headers={"User-Agent": "ReconPro-OSINT"},
            timeout=15,
        )
        if r.status_code == 200:
            result["breaches"] = r.json()
            result["count"] = len(r.json())
            result["status"] = "BREACHED"
        elif r.status_code == 404:
            result["breaches"] = []
            result["count"] = 0
            result["status"] = "CLEAN"
        elif r.status_code == 429:
            result["status"] = "RATE_LIMIT"
            result["error"] = "Rate limit — coba lagi nanti"
        else:
            result["status"] = "UNKNOWN"
            result["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)

    # Bonus: cek domain email (kalau ada)
    if "@" in email:
        domain = email.split("@")[1]
        try:
            result["email_domain"] = domain_whois(domain)
        except Exception:
            pass

    return result


def domain_whois(domain):
    """WHOIS lookup domain."""
    result = {"domain": domain, "lookup_at": datetime.now().isoformat()}
    if not HAS_WHOIS:
        result["error"] = "python-whois tidak terinstall"
        return result
    try:
        w = whois.whois(domain)
        # Convert datetime ke string
        info = {}
        for k, v in dict(w).items():
            if v is None:
                continue
            if isinstance(v, list):
                info[k] = [str(x) if hasattr(x, "isoformat") else x for x in v]
            elif hasattr(v, "isoformat"):
                info[k] = v.isoformat()
            else:
                info[k] = v
        result["whois"] = info
    except Exception as e:
        result["error"] = str(e)
    return result


def dns_lookup(domain):
    """DNS enumeration: A, AAAA, MX, TXT, NS, CNAME, SOA."""
    result = {"domain": domain, "records": {}, "lookup_at": datetime.now().isoformat()}
    if not HAS_DNS:
        result["error"] = "dnspython tidak terinstall"
        return result
    for rtype in ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA", "CAA"]:
        try:
            answers = dns.resolver.resolve(domain, rtype, lifetime=8)
            result["records"][rtype] = [str(r) for r in answers]
        except Exception:
            result["records"][rtype] = []
    return result


def subdomain_finder(domain):
    """Cari subdomain umum."""
    common = [
        "www", "mail", "ftp", "webmail", "smtp", "pop", "ns1", "ns2", "dev",
        "staging", "test", "api", "app", "admin", "portal", "blog", "shop",
        "store", "secure", "vpn", "remote", "support", "help", "docs",
        "m", "mobile", "beta", "demo", "cdn", "static", "img", "images",
        "db", "mysql", "phpmyadmin", "cpanel", "whm", "autodiscover",
        "vpn", "git", "gitlab", "github", "jenkins", "ci", "docker",
    ]

    result = {"domain": domain, "found": [], "lookup_at": datetime.now().isoformat()}

    def check_sub(sub):
        try:
            full = f"{sub}.{domain}"
            socket.gethostbyname(full)
            return full
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=20) as ex:
        for found in ex.map(check_sub, common):
            if found:
                try:
                    ip = socket.gethostbyname(found)
                    result["found"].append({"subdomain": found, "ip": ip})
                except Exception:
                    result["found"].append({"subdomain": found, "ip": None})

    return result


def ssl_info(domain, port=443):
    """Ambil info sertifikat SSL."""
    result = {"domain": domain, "port": port, "lookup_at": datetime.now().isoformat()}
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((domain, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                result["version"] = ssock.version()
                result["cipher"] = ssock.cipher()
                result["cert"] = {
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "notBefore": cert.get("notBefore"),
                    "notAfter": cert.get("notAfter"),
                    "subjectAltName": [x[1] for x in cert.get("subjectAltName", [])],
                    "serialNumber": cert.get("serialNumber"),
                }
    except Exception as e:
        result["error"] = str(e)
    return result


def http_headers(url):
    """Analisis HTTP response headers."""
    if not url.startswith("http"):
        url = "https://" + url
    result = {"url": url, "lookup_at": datetime.now().isoformat()}
    try:
        r = requests.head(url, timeout=10, allow_redirects=True, verify=False)
        result["status_code"] = r.status_code
        result["headers"] = dict(r.headers)
        result["final_url"] = r.url
        # Deteksi teknologi dari header
        server = r.headers.get("Server", "")
        powered = r.headers.get("X-Powered-By", "")
        result["technology"] = {
            "server": server,
            "powered_by": powered,
        }
    except Exception as e:
        result["error"] = str(e)
    return result


def phone_lookup(phone, country="ID"):
    """Info nomor telepon."""
    result = {"phone": phone, "country": country, "lookup_at": datetime.now().isoformat()}
    if not HAS_PHONE:
        result["error"] = "phonenumbers tidak terinstall"
        return result
    try:
        num = phonenumbers.parse(phone, country)
        result["valid"] = phonenumbers.is_valid_number(num)
        result["possible"] = phonenumbers.is_possible_number(num)
        result["carrier"] = carrier.name_for_number(num, "en")
        result["location"] = geocoder.description_for_number(num, "en")
        result["timezones"] = list(tz.time_zones_for_number(num))
        result["international"] = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        result["e164"] = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        result["error"] = str(e)
    return result


def username_check(username):
    """Cek username di berbagai platform."""
    platforms = {
        "instagram": f"https://www.instagram.com/{username}/",
        "twitter": f"https://twitter.com/{username}",
        "facebook": f"https://www.facebook.com/{username}",
        "tiktok": f"https://www.tiktok.com/@{username}",
        "youtube": f"https://www.youtube.com/@{username}",
        "github": f"https://github.com/{username}",
        "reddit": f"https://www.reddit.com/user/{username}",
        "telegram": f"https://t.me/{username}",
        "pinterest": f"https://www.pinterest.com/{username}/",
        "linkedin": f"https://www.linkedin.com/in/{username}",
    }
    result = {"username": username, "found": [], "lookup_at": datetime.now().isoformat()}

    def check(item):
        platform, url = item
        try:
            r = requests.head(url, timeout=6, allow_redirects=True, verify=False,
                              headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                return {"platform": platform, "url": url, "status": 200}
            elif r.status_code in (403, 429):
                return {"platform": platform, "url": url, "status": "may_exist",
                        "note": "Blocked/rate-limit — mungkin ada"}
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=10) as ex:
        for r in ex.map(check, platforms.items()):
            if r:
                result["found"].append(r)

    return result
''')
print(f"      OK  {osint_py}")


# ============================================================
# STEP 2: Bikin route osint_pro
# ============================================================
print("\n[2/6] Bikin route /api/osint...")
osint_route = PROJECT / "app" / "routes" / "osint_pro.py"
osint_route.write_text('''"""OSINT endpoints — semua lookup dari sumber publik."""
from flask import Blueprint, jsonify, request, render_template
from app.auth import login_required
from app.services.osint_pro import (
    ip_intel, email_breach, domain_whois, dns_lookup,
    subdomain_finder, ssl_info, http_headers, phone_lookup, username_check,
)

bp = Blueprint("osint_pro", __name__)


@bp.route("/osint")
@login_required
def osint_page():
    return render_template("osint.html")


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


@bp.route("/api/osint/username/<username>")
@login_required
def api_username(username):
    return jsonify(username_check(username))


@bp.route("/api/osint/target", methods=["POST"])
@login_required
def api_target():
    """Lookup otomatis berdasarkan jenis target (auto-detect)."""
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"ok": False, "msg": "Target kosong"}), 400

    result = {"target": target, "results": {}}

    # Auto-detect tipe target
    import re
    if re.match(r"^\\d{1,3}(\\.\\d{1,3}){3}$", target):
        # IP
        result["type"] = "ip"
        result["results"] = ip_intel(target)
    elif "@" in target:
        # Email
        result["type"] = "email"
        result["results"] = email_breach(target)
    elif re.match(r"^[+\\d\\s\\-()]+$", target) and len(target) >= 8:
        # Phone
        result["type"] = "phone"
        result["results"] = phone_lookup(target)
    elif "." in target and " " not in target:
        # Domain
        result["type"] = "domain"
        result["results"] = {
            "whois": domain_whois(target),
            "dns": dns_lookup(target),
            "ssl": ssl_info(target),
            "http": http_headers(target),
        }
    else:
        # Username
        result["type"] = "username"
        result["results"] = username_check(target)

    return jsonify(result)
''')
print(f"      OK  {osint_route}")


# ============================================================
# STEP 3: Register blueprint
# ============================================================
print("\n[3/6] Register blueprint...")
init = PROJECT / "app" / "__init__.py"
content = init.read_text(encoding="utf-8")
backup = init.with_suffix(".py.bak_osint")
backup.write_text(content, encoding="utf-8")

if "from app.routes.osint_pro import bp as osint_pro_bp" not in content:
    if "from app.routes.api import bp as api_bp" in content:
        content = content.replace(
            "from app.routes.api import bp as api_bp",
            "from app.routes.api import bp as api_bp\n    from app.routes.osint_pro import bp as osint_pro_bp"
        )

if "app.register_blueprint(osint_pro_bp)" not in content:
    if 'app.register_blueprint(api_bp, url_prefix="/api")' in content:
        content = content.replace(
            'app.register_blueprint(api_bp, url_prefix="/api")',
            'app.register_blueprint(api_bp, url_prefix="/api")\n    app.register_blueprint(osint_pro_bp)'
        )

# CSRF exempt
if "csrf.exempt(osint_mod.bp)" not in content:
    for marker in ["csrf.exempt(qr_mod.bp)", "csrf.exempt(tpl_gallery_mod.bp)",
                   "csrf.exempt(api_mod.bp)", "csrf.exempt(tunnel_mod.bp)"]:
        if marker in content:
            content = content.replace(
                marker,
                marker + "\n\n    from app.routes import osint_pro as osint_mod\n    csrf.exempt(osint_mod.bp)"
            )
            break

init.write_text(content, encoding="utf-8")
print(f"      OK  {init}")


# ============================================================
# STEP 4: Bikin template osint.html
# ============================================================
print("\n[4/6] Bikin template osint.html...")
osint_html = PROJECT / "app" / "templates" / "osint.html"
osint_html.write_text('''{% extends "base.html" %}
{% block title %}OSINT Toolkit - ReconPro{% endblock %}
{% block head %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css">
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<style>
.osint-wrap { max-width: 900px; margin: 0 auto; padding: 24px; }
h1 { color: #58a6ff; font-size: 24px; margin: 0 0 8px; }
h2 { color: #58a6ff; font-size: 16px; margin: 20px 0 10px; }
.desc { color: #8b949e; font-size: 13px; margin-bottom: 20px; }
.card { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.field { margin-bottom: 14px; }
.field label { display: block; font-size: 13px; color: #8b949e; margin-bottom: 6px; }
.field input, .field select { width: 100%; padding: 11px; background: #0d1117; border: 1px solid #21262d; color: #e6edf3; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.btn { padding: 10px 20px; background: #1e6feb; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; margin-right: 8px; margin-bottom: 8px; }
.btn:hover { opacity: 0.9; }
.btn.green { background: #2ea043; }
.btn.gold { background: #d29922; color: #0f1117; }
.result { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 16px; margin-top: 16px; font-family: monospace; font-size: 12px; max-height: 500px; overflow: auto; white-space: pre-wrap; color: #8b949e; display: none; }
.result.active { display: block; }
.result .key { color: #58a6ff; }
.result .str { color: #a5d6ff; }
.result .num { color: #79c0ff; }
.result .bool { color: #d2a8ff; }
.quick-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.quick-btn { padding: 6px 12px; background: #21262d; color: #8b949e; border: none; border-radius: 6px; cursor: pointer; font-size: 11px; }
.quick-btn.active { background: #1e6feb; color: #fff; }
.info-badge { display: inline-block; padding: 2px 8px; background: #1e6feb; color: #fff; border-radius: 10px; font-size: 11px; margin-left: 8px; }
</style>
{% endblock %}
{% block body %}
<div class="osint-wrap">
  <p><a href="/dashboard" style="color:#58a6ff;text-decoration:none">← Dashboard</a></p>
  <h1>🔍 OSINT Toolkit</h1>
  <p class="desc">Lookup dari sumber publik — 100% legal</p>

  <div class="card">
    <div class="quick-actions">
      <button class="quick-btn active" data-type="auto">🎯 Auto Detect</button>
      <button class="quick-btn" data-type="ip">🌐 IP Address</button>
      <button class="quick-btn" data-type="email">📧 Email</button>
      <button class="quick-btn" data-type="domain">🔗 Domain</button>
      <button class="quick-btn" data-type="username">👤 Username</button>
      <button class="quick-btn" data-type="phone">📱 Phone</button>
      <button class="quick-btn" data-type="dns">📡 DNS</button>
      <button class="quick-btn" data-type="subdomain">🌳 Subdomain</button>
      <button class="quick-btn" data-type="ssl">🔒 SSL</button>
      <button class="quick-btn" data-type="http">📋 HTTP Headers</button>
    </div>

    <div class="field">
      <label id="targetLabel">Target (auto-detect: IP / email / domain / username / phone)</label>
      <input type="text" id="targetInput" placeholder="Contoh: 8.8.8.8 atau google.com atau test@example.com">
    </div>

    <button class="btn" onclick="lookup()">🔍 Lookup</button>
    <button class="btn green" onclick="copyResult()">📋 Copy JSON</button>
    <button class="btn gold" onclick="downloadResult()">⬇ Download</button>

    <div class="result" id="result"></div>
  </div>

  <div class="card">
    <h2>💡 Contoh Penggunaan</h2>
    <ul style="font-size:13px;color:#8b949e;line-height:1.8">
      <li><b>IP:</b> <code>8.8.8.8</code> — info ISP, negara, VPN, reverse DNS</li>
      <li><b>Email:</b> <code>test@gmail.com</code> — cek data breach</li>
      <li><b>Domain:</b> <code>google.com</code> — WHOIS, DNS, SSL, HTTP headers</li>
      <li><b>Username:</b> <code>john_doe</code> — cek di berbagai sosmed</li>
      <li><b>Phone:</b> <code>+62812345678</code> — carrier, region</li>
    </ul>
    <p style="font-size:12px;color:#6e7681;margin-top:12px">
      ⚠️ Semua lookup pakai API publik. Rate limit mungkin berlaku.
    </p>
  </div>
</div>

<script>
var currentType = "auto";
var lastResult = null;

document.querySelectorAll(".quick-btn").forEach(function(b) {
  b.addEventListener("click", function() {
    document.querySelectorAll(".quick-btn").forEach(function(x) { x.classList.remove("active"); });
    b.classList.add("active");
    currentType = b.dataset.type;
    updateLabel();
  });
});

function updateLabel() {
  var labels = {
    auto: "Target (auto-detect)",
    ip: "IP Address (misal: 8.8.8.8)",
    email: "Email (misal: test@gmail.com)",
    domain: "Domain (misal: google.com)",
    username: "Username (misal: john_doe)",
    phone: "Phone (+62812345678)",
    dns: "Domain (misal: google.com)",
    subdomain: "Domain (misal: google.com)",
    ssl: "Domain (misal: google.com)",
    http: "URL atau domain",
  };
  document.getElementById("targetLabel").textContent = labels[currentType] || "Target";
}

function lookup() {
  var target = document.getElementById("targetInput").value.trim();
  if (!target) {
    Swal.fire("Perlu target", "Isi target dulu", "warning");
    return;
  }

  Swal.fire({ title: "Lookup...", didOpen: function() { Swal.showLoading(); }, allowOutsideClick: false });

  var endpoint;
  if (currentType === "auto") endpoint = "/api/osint/target";
  else if (currentType === "dns") endpoint = "/api/osint/dns/" + encodeURIComponent(target);
  else if (currentType === "subdomain") endpoint = "/api/osint/subdomain/" + encodeURIComponent(target);
  else if (currentType === "ssl") endpoint = "/api/osint/ssl/" + encodeURIComponent(target);
  else if (currentType === "http") endpoint = "/api/osint/http/" + encodeURIComponent(target);
  else endpoint = "/api/osint/" + currentType + "/" + encodeURIComponent(target);

  var opts = { method: currentType === "auto" ? "POST" : "GET" };
  if (currentType === "auto") {
    opts.headers = { "Content-Type": "application/json" };
    opts.body = JSON.stringify({ target: target });
  }

  fetch(endpoint, opts)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      Swal.close();
      lastResult = data;
      document.getElementById("result").textContent = JSON.stringify(data, null, 2);
      document.getElementById("result").classList.add("active");
    })
    .catch(function(e) {
      Swal.close();
      Swal.fire("Error", e.message, "error");
    });
}

function copyResult() {
  if (!lastResult) return;
  navigator.clipboard.writeText(JSON.stringify(lastResult, null, 2));
  Swal.fire({ toast: true, position: "top-end", icon: "success", title: "Copied", timer: 1200, showConfirmButton: false });
}

function downloadResult() {
  if (!lastResult) return;
  var blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: "application/json" });
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "osint-" + Date.now() + ".json";
  a.click();
}
</script>
{% endblock %}
''')
print(f"      OK  {osint_html}")


# ============================================================
# STEP 5: Tambah tombol OSINT di dashboard
# ============================================================
print("\n[5/6] Tambah tombol OSINT di dashboard...")
dash = PROJECT / "app" / "templates" / "dashboard.html"
if dash.exists():
    content = dash.read_text(encoding="utf-8")
    if 'href="/osint"' not in content:
        # Coba tambah setelah tombol QR
        if 'href="/qr-page"' in content:
            content = content.replace(
                '<a class="btn" href="/qr-page"',
                '<a class="btn" href="/osint" style="background:#a06bff">🔍 OSINT</a>\n    <a class="btn" href="/qr-page"'
            )
        else:
            content = content.replace(
                '<a class="btn" href="/features"',
                '<a class="btn" href="/osint" style="background:#a06bff">🔍 OSINT</a>\n    <a class="btn" href="/features"'
            )
        dash.write_text(content, encoding="utf-8")
        print(f"      OK  Tombol OSINT ditambahkan")


# ============================================================
# STEP 6: Verify
# ============================================================
print("\n[6/6] Verify...")
print(f"      osint_pro.py: {'✅' if osint_py.exists() else '❌'}")
print(f"      osint_pro route: {'✅' if osint_route.exists() else '❌'}")
print(f"      osint.html: {'✅' if osint_html.exists() else '❌'}")

print()
print("=" * 60)
print("  ✅ OSINT TOOLKIT — SELESAI")
print("=" * 60)
print()
print("  Fitur baru:")
print("    🔍 IP Intelligence")
print("    📧 Email Breach Check (Have I Been Pwned)")
print("    🔗 Domain WHOIS + DNS + Subdomain")
print("    🔒 SSL/TLS Certificate Info")
print("    📋 HTTP Headers Analysis")
print("    📱 Phone Number Lookup")
print("    👤 Username Enumeration (10+ platform)")
print("    🎯 Auto-detect target")
print()
print("  Cara pakai:")
print("    1. Restart server:")
print("         pkill -f 'python run.py'")
print("         cd ~/capture-pro && python run.py")
print()
print("    2. Buka: http://localhost:8000/osint")
print()
print("  Atau klik tombol '🔍 OSINT' di dashboard.")
print()
