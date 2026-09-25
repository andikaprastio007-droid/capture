"""OSINT API Integrations — Shodan, VirusTotal, URLScan, dll."""
import os
import json
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def _get_api_key(service):
    """Ambil API key dari environment variable."""
    keys = {
        "shodan": os.environ.get("SHODAN_API_KEY", ""),
        "virustotal": os.environ.get("VIRUSTOTAL_API_KEY", ""),
        "urlscan": os.environ.get("URLSCAN_API_KEY", ""),
        "hunter": os.environ.get("HUNTER_API_KEY", ""),
        "securitytrails": os.environ.get("SECURITYTRAILS_API_KEY", ""),
        "hibp": os.environ.get("HIBP_API_KEY", ""),
        "ipinfo": os.environ.get("IPINFO_API_KEY", ""),
        "abuseipdb": os.environ.get("ABUSEIPDB_API_KEY", ""),
    }
    return keys.get(service, "")


# ============================================================
# SHODAN
# ============================================================
def shodan_lookup(ip):
    """Cari info device dari Shodan."""
    result = {"ip": ip, "service": "shodan", "lookup_at": datetime.now().isoformat()}
    key = _get_api_key("shodan")
    if not key:
        result["error"] = "SHODAN_API_KEY belum diset di .env"
        result["info"] = "Daftar gratis di https://account.shodan.io/register"
        return result
    try:
        r = requests.get(f"https://api.shodan.io/shodan/host/{ip}?key={key}", timeout=20)
        data = r.json()
        if "error" in data:
            result["error"] = data["error"]
        else:
            result["data"] = {
                "ip": data.get("ip_str"),
                "org": data.get("org"),
                "isp": data.get("isp"),
                "asn": data.get("asn"),
                "country": data.get("country_name"),
                "city": data.get("city"),
                "os": data.get("os"),
                "ports": data.get("ports", []),
                "hostnames": data.get("hostnames", []),
                "domains": data.get("domains", []),
                "vulns": list(data.get("vulns", {}).keys()) if data.get("vulns") else [],
                "last_update": data.get("last_update"),
                "services": [
                    {
                        "port": s.get("port"),
                        "transport": s.get("transport"),
                        "product": s.get("product"),
                        "version": s.get("version"),
                        "banner": (s.get("data", "")[:200] if s.get("data") else ""),
                    }
                    for s in data.get("data", [])
                ]
            }
    except Exception as e:
        result["error"] = str(e)
    return result


def shodan_search(query, limit=20):
    """Search Shodan."""
    result = {"query": query, "service": "shodan", "lookup_at": datetime.now().isoformat()}
    key = _get_api_key("shodan")
    if not key:
        result["error"] = "SHODAN_API_KEY belum diset"
        return result
    try:
        r = requests.get(f"https://api.shodan.io/shodan/host/search?key={key}&query={query}&limit={limit}", timeout=30)
        data = r.json()
        if "error" in data:
            result["error"] = data["error"]
        else:
            result["total"] = data.get("total", 0)
            result["matches"] = [
                {
                    "ip": m.get("ip_str"),
                    "port": m.get("port"),
                    "org": m.get("org"),
                    "product": m.get("product"),
                    "country": m.get("location", {}).get("country_name"),
                }
                for m in data.get("matches", [])[:limit]
            ]
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
# VIRUSTOTAL
# ============================================================
def virustotal_lookup(target, type_="ip"):
    """Cek reputasi IP/domain/hash di VirusTotal."""
    result = {"target": target, "type": type_, "service": "virustotal",
              "lookup_at": datetime.now().isoformat()}
    key = _get_api_key("virustotal")
    if not key:
        result["error"] = "VIRUSTOTAL_API_KEY belum diset di .env"
        result["info"] = "Daftar gratis di https://www.virustotal.com/gui/join-us"
        return result

    try:
        if type_ == "ip":
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{target}"
        elif type_ == "domain":
            url = f"https://www.virustotal.com/api/v3/domains/{target}"
        elif type_ == "url":
            import base64
            url_id = base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
            url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        elif type_ == "hash":
            url = f"https://www.virustotal.com/api/v3/files/{target}"
        else:
            result["error"] = f"Tipe {type_} tidak didukung"
            return result

        headers = {"x-apikey": key}
        r = requests.get(url, headers=headers, timeout=20)
        data = r.json()

        if "error" in data:
            result["error"] = data["error"].get("message", str(data["error"]))
        else:
            attrs = data.get("data", {}).get("attributes", {})
            last_analysis = attrs.get("last_analysis_stats", {})
            result["data"] = {
                "reputation": attrs.get("reputation", 0),
                "malicious": last_analysis.get("malicious", 0),
                "suspicious": last_analysis.get("suspicious", 0),
                "harmless": last_analysis.get("harmless", 0),
                "undetected": last_analysis.get("undetected", 0),
                "total_engines": sum(last_analysis.values()) if last_analysis else 0,
                "country": attrs.get("country"),
                "as_owner": attrs.get("as_owner"),
                "whois": (attrs.get("whois", "")[:500] if attrs.get("whois") else ""),
            }
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
# URLSCAN.IO
# ============================================================
def urlscan_submit(url, visibility="unlisted"):
    """Submit URL ke URLScan.io untuk di-scan."""
    result = {"url": url, "service": "urlscan", "lookup_at": datetime.now().isoformat()}
    key = _get_api_key("urlscan")
    if not key:
        result["error"] = "URLSCAN_API_KEY belum diset di .env"
        result["info"] = "Daftar gratis di https://urlscan.io/user/signup"
        return result
    try:
        r = requests.post(
            "https://urlscan.io/api/v1/scan/",
            headers={"API-Key": key, "Content-Type": "application/json"},
            json={"url": url, "visibility": visibility},
            timeout=30,
        )
        data = r.json()
        if "message" in data and "error" not in data:
            result["message"] = data["message"]
            result["uuid"] = data.get("uuid")
            result["result_url"] = data.get("api")
            result["web_url"] = data.get("result")
            result["note"] = "Scan berjalan. Cek hasil dalam 10-30 detik di web_url"
        else:
            result["error"] = data.get("message", str(data))
    except Exception as e:
        result["error"] = str(e)
    return result


def urlscan_result(uuid):
    """Ambil hasil scan URLScan."""
    result = {"uuid": uuid, "service": "urlscan", "lookup_at": datetime.now().isoformat()}
    try:
        r = requests.get(f"https://urlscan.io/api/v1/result/{uuid}/", timeout=20)
        data = r.json()
        result["data"] = {
            "url": data.get("page", {}).get("url"),
            "domain": data.get("page", {}).get("domain"),
            "ip": data.get("page", {}).get("ip"),
            "country": data.get("page", {}).get("country"),
            "server": data.get("page", {}).get("server"),
            "status": data.get("page", {}).get("status"),
            "screenshot": data.get("task", {}).get("screenshotURL"),
            "requests": len(data.get("data", {}).get("requests", [])),
            "domains": list(set([d.get("domain") for d in data.get("data", {}).get("requests", []) if d.get("domain")]))[:30],
            "technologies": [t.get("name") for t in data.get("meta", {}).get("processors", {}).get("wappa", {}).get("data", [])],
        }
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
# HUNTER.IO (Email Finder)
# ============================================================
def hunter_domain_search(domain):
    """Cari email terkait domain via Hunter.io."""
    result = {"domain": domain, "service": "hunter", "lookup_at": datetime.now().isoformat()}
    key = _get_api_key("hunter")
    if not key:
        result["error"] = "HUNTER_API_KEY belum diset"
        result["info"] = "Daftar gratis di https://hunter.io/users/sign_up"
        return result
    try:
        r = requests.get(
            f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={key}",
            timeout=20,
        )
        data = r.json()
        d = data.get("data", {})
        result["data"] = {
            "organization": d.get("organization"),
            "pattern": d.get("pattern"),
            "emails_count": d.get("emails") and len(d.get("emails", [])) or 0,
            "emails": [
                {"email": e.get("value"), "type": e.get("type"), "confidence": e.get("confidence"),
                 "first_name": e.get("first_name"), "last_name": e.get("last_name")}
                for e in d.get("emails", [])[:30]
            ],
        }
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
# ABUSEIPDB
# ============================================================
def abuseipdb_check(ip):
    """Cek abuse reports untuk IP."""
    result = {"ip": ip, "service": "abuseipdb", "lookup_at": datetime.now().isoformat()}
    key = _get_api_key("abuseipdb")
    if not key:
        result["error"] = "ABUSEIPDB_API_KEY belum diset"
        return result
    try:
        r = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={"Key": key, "Accept": "application/json"},
            timeout=15,
        )
        data = r.json().get("data", {})
        result["data"] = {
            "abuse_confidence_score": data.get("abuseConfidenceScore"),
            "total_reports": data.get("totalReports"),
            "num_distinct_users": data.get("numDistinctUsers"),
            "last_reported": data.get("lastReportedAt"),
            "country": data.get("countryCode"),
            "isp": data.get("isp"),
            "domain": data.get("domain"),
            "usage_type": data.get("usageType"),
        }
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
# TARGET PROFILE AGGREGATOR
# ============================================================
def target_profile(target):
    """Aggregate semua lookup untuk 1 target."""
    import re
    from app.services.osint_pro import ip_intel, email_breach, domain_whois, dns_lookup, ssl_info, http_headers, username_check, phone_lookup

    result = {"target": target, "lookup_at": datetime.now().isoformat()}

    # Auto-detect
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target):
        result["type"] = "ip"
        result["ip"] = ip_intel(target)
        result["shodan"] = shodan_lookup(target)
        result["virustotal"] = virustotal_lookup(target, "ip")
        result["abuseipdb"] = abuseipdb_check(target)
    elif "@" in target:
        result["type"] = "email"
        result["breach"] = email_breach(target)
        if "@" in target:
            domain = target.split("@")[1]
            result["domain_whois"] = domain_whois(domain)
            result["domain_dns"] = dns_lookup(domain)
    elif re.match(r"^[+\d\s\-()]+$", target) and len(target) >= 8:
        result["type"] = "phone"
        result["phone"] = phone_lookup(target)
    elif "." in target and " " not in target:
        result["type"] = "domain"
        result["whois"] = domain_whois(target)
        result["dns"] = dns_lookup(target)
        result["ssl"] = ssl_info(target)
        result["http"] = http_headers(target)
        result["virustotal"] = virustotal_lookup(target, "domain")
        result["hunter"] = hunter_domain_search(target)
    else:
        result["type"] = "username"
        result["username"] = username_check(target)

    # Hitung risk score
    result["risk_score"] = _calc_risk(result)

    return result


def _calc_risk(profile):
    """Hitung risk score 0-100."""
    score = 0
    # Email breach
    if profile.get("breach", {}).get("status") == "BREACHED":
        score += min(50, profile["breach"].get("count", 0) * 10)
    # IP VPN
    if profile.get("ip", {}).get("proxycheck", {}).get("proxy") == "yes":
        score += 20
    # VT malicious
    if profile.get("virustotal", {}).get("data", {}).get("malicious", 0) > 0:
        score += 30
    # Abuse score
    abuse = profile.get("abuseipdb", {}).get("data", {}).get("abuse_confidence_score", 0)
    score += min(30, abuse)
    return min(100, score)
