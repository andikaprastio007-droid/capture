"""OSINT Toolkit — semua lookup legal dari sumber publik."""
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
