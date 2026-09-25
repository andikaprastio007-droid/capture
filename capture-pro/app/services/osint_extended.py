"""OSINT Extended — Dork, Username, Wayback, HIBP, Metadata, dll."""
import os
import io
import json
import socket
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ============================================================
# GOOGLE DORK GENERATOR
# ============================================================
def generate_dorks(domain):
    """Generate 50+ Google Dork queries untuk domain."""
    d = domain.lower().strip()
    dorks = [
        # ==== FILE SENSITIF ====
        {"category": "File Sensitif", "query": f"site:{d} filetype:pdf", "desc": "PDF files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:doc OR filetype:docx", "desc": "Word docs"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:xls OR filetype:xlsx", "desc": "Excel files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:sql", "desc": "SQL dumps"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:env", "desc": "Env files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:log", "desc": "Log files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:bak", "desc": "Backup files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:config", "desc": "Config files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:txt", "desc": "Text files"},
        {"category": "File Sensitif", "query": f"site:{d} filetype:xml", "desc": "XML files"},

        # ==== DIRECTORY ====
        {"category": "Directory", "query": f"site:{d} intitle:index.of", "desc": "Directory listing"},
        {"category": "Directory", "query": f"site:{d} intitle:index.of.parent", "desc": "Parent directory"},
        {"category": "Directory", "query": f"site:{d} intitle:index.of.backup", "desc": "Backup dir"},
        {"category": "Directory", "query": f"site:{d} intitle:\"index of\"", "desc": "Index of"},

        # ==== LOGIN PANEL ====
        {"category": "Login Panel", "query": f"site:{d} inurl:admin", "desc": "Admin panel"},
        {"category": "Login Panel", "query": f"site:{d} inurl:login", "desc": "Login page"},
        {"category": "Login Panel", "query": f"site:{d} inurl:dashboard", "desc": "Dashboard"},
        {"category": "Login Panel", "query": f"site:{d} inurl:portal", "desc": "Portal"},
        {"category": "Login Panel", "query": f"site:{d} inurl:panel", "desc": "Panel"},
        {"category": "Login Panel", "query": f"site:{d} inurl:wp-admin", "desc": "WordPress admin"},
        {"category": "Login Panel", "query": f"site:{d} inurl:cpanel", "desc": "cPanel"},
        {"category": "Login Panel", "query": f"site:{d} inurl:phpmyadmin", "desc": "phpMyAdmin"},

        # ==== KONFIGURASI ====
        {"category": "Konfigurasi", "query": f"site:{d} inurl:config", "desc": "Config pages"},
        {"category": "Konfigurasi", "query": f"site:{d} inurl:setup", "desc": "Setup pages"},
        {"category": "Konfigurasi", "query": f"site:{d} inurl:install", "desc": "Install pages"},
        {"category": "Konfigurasi", "query": f"site:{d} ext:ini", "desc": "INI files"},
        {"category": "Konfigurasi", "query": f"site:{d} ext:conf", "desc": "Conf files"},

        # ==== CREDENTIALS ====
        {"category": "Credentials", "query": f"site:{d} \"password\"", "desc": "Password mentions"},
        {"category": "Credentials", "query": f"site:{d} \"api_key\"", "desc": "API keys"},
        {"category": "Credentials", "query": f"site:{d} \"api_secret\"", "desc": "API secrets"},
        {"category": "Credentials", "query": f"site:{d} \"access_token\"", "desc": "Access tokens"},
        {"category": "Credentials", "query": f"site:{d} \"secret_key\"", "desc": "Secret keys"},
        {"category": "Credentials", "query": f"site:{d} \"private_key\"", "desc": "Private keys"},
        {"category": "Credentials", "query": f"site:{d} \"aws_access_key\"", "desc": "AWS keys"},

        # ==== ERROR PAGES ====
        {"category": "Error Pages", "query": f"site:{d} intext:\"SQL syntax\"", "desc": "SQL errors"},
        {"category": "Error Pages", "query": f"site:{d} intext:\"Warning: mysql\"", "desc": "MySQL warnings"},
        {"category": "Error Pages", "query": f"site:{d} intext:\"Fatal error\"", "desc": "PHP fatal"},
        {"category": "Error Pages", "query": f"site:{d} intext:\"stack trace\"", "desc": "Stack traces"},

        # ==== UPLOAD / BACKUP ====
        {"category": "Upload/Backup", "query": f"site:{d} inurl:upload", "desc": "Upload pages"},
        {"category": "Upload/Backup", "query": f"site:{d} inurl:backup", "desc": "Backup pages"},
        {"category": "Upload/Backup", "query": f"site:{d} inurl:old", "desc": "Old pages"},
        {"category": "Upload/Backup", "query": f"site:{d} inurl:test", "desc": "Test pages"},
        {"category": "Upload/Backup", "query": f"site:{d} inurl:dev", "desc": "Dev pages"},
        {"category": "Upload/Backup", "query": f"site:{d} inurl:staging", "desc": "Staging pages"},

        # ==== EMAIL ====
        {"category": "Email", "query": f"site:{d} \"@\"{d}", "desc": "Email addresses"},

        # ==== SUBDOMAIN VIA GOOGLE ====
        {"category": "Subdomain", "query": f"site:*.{d}", "desc": "Subdomains"},
        {"category": "Subdomain", "query": f"site:*.{d} -www", "desc": "Subdomains (no www)"},

        # ==== GITHUB ====
        {"category": "GitHub", "query": f"site:github.com \"{d}\"", "desc": "GitHub mentions"},
        {"category": "GitHub", "query": f"site:github.com \"{d}\" password", "desc": "GitHub + password"},
        {"category": "GitHub", "query": f"site:github.com \"{d}\" token", "desc": "GitHub + token"},

        # ==== PASTEBIN ====
        {"category": "Pastebin", "query": f"site:pastebin.com \"{d}\"", "desc": "Pastebin leaks"},

        # ==== LINKEDIN ====
        {"category": "LinkedIn", "query": f"site:linkedin.com \"{d}\"", "desc": "LinkedIn employees"},
    ]
    return {"domain": d, "count": len(dorks), "dorks": dorks}


# ============================================================
# USERNAME TRACKER (200+ platform)
# ============================================================
def username_tracker(username):
    """Cek username di 100+ platform."""
    username = username.strip().lstrip("@")

    platforms = {
        # Sosmed
        "Instagram": f"https://www.instagram.com/{username}/",
        "Twitter": f"https://twitter.com/{username}",
        "X": f"https://x.com/{username}",
        "Facebook": f"https://www.facebook.com/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Snapchat": f"https://www.snapchat.com/add/{username}",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Tumblr": f"https://{username}.tumblr.com",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "LinkedIn": f"https://www.linkedin.com/in/{username}",
        "Telegram": f"https://t.me/{username}",
        "Discord": f"https://discord.com/users/{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "VK": f"https://vk.com/{username}",
        "Weibo": f"https://weibo.com/{username}",
        "Clubhouse": f"https://www.clubhouse.com/@{username}",
        "Mastodon": f"https://mastodon.social/@{username}",

        # Dev
        "GitHub": f"https://github.com/{username}",
        "GitLab": f"https://gitlab.com/{username}",
        "Bitbucket": f"https://bitbucket.org/{username}/",
        "StackOverflow": f"https://stackoverflow.com/users/{username}",
        "Dev.to": f"https://dev.to/{username}",
        "Medium": f"https://medium.com/@{username}",
        "Hashnode": f"https://hashnode.com/@{username}",
        "Replit": f"https://replit.com/@{username}",
        "CodePen": f"https://codepen.io/{username}",
        "HackerRank": f"https://www.hackerrank.com/{username}",
        "LeetCode": f"https://leetcode.com/{username}",
        "Kaggle": f"https://www.kaggle.com/{username}",
        "NPM": f"https://www.npmjs.com/~{username}",
        "PyPI": f"https://pypi.org/user/{username}/",
        "DockerHub": f"https://hub.docker.com/u/{username}",

        # Gaming
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Xbox": f"https://xboxgamertag.com/search/{username}",
        "PSN": f"https://psnprofiles.com/{username}",
        "Roblox": f"https://www.roblox.com/user.aspx?username={username}",
        "Minecraft": f"https://namemc.com/profile/{username}",
        "Chess.com": f"https://www.chess.com/member/{username}",

        # Music
        "Spotify": f"https://open.spotify.com/user/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "Bandcamp": f"https://bandcamp.com/{username}",
        "Mixcloud": f"https://www.mixcloud.com/{username}/",
        "Last.fm": f"https://www.last.fm/user/{username}",

        # Design/Foto
        "Behance": f"https://www.behance.net/{username}",
        "Dribbble": f"https://dribbble.com/{username}",
        "Flickr": f"https://www.flickr.com/people/{username}",
        "500px": f"https://500px.com/p/{username}",
        "DeviantArt": f"https://www.deviantart.com/{username}",
        "Unsplash": f"https://unsplash.com/@{username}",

        # Marketplace
        "Etsy": f"https://www.etsy.com/shop/{username}",
        "eBay": f"https://www.ebay.com/usr/{username}",
        "Fiverr": f"https://www.fiverr.com/{username}",
        "Upwork": f"https://www.upwork.com/freelancers/~{username}",
        "Tokopedia": f"https://www.tokopedia.com/{username}",
        "Shopee": f"https://shopee.co.id/{username}",

        # Blog
        "WordPress": f"https://{username}.wordpress.com",
        "Blogger": f"https://{username}.blogspot.com",
        "Substack": f"https://{username}.substack.com",
        "Ghost": f"https://{username}.ghost.io",
        "Notion": f"https://{username}.notion.site",

        # Lain
        "Patreon": f"https://www.patreon.com/{username}",
        "Ko-fi": f"https://ko-fi.com/{username}",
        "BuyMeACoffee": f"https://www.buymeacoffee.com/{username}",
        "Keybase": f"https://keybase.io/{username}",
        "About.me": f"https://about.me/{username}",
        "Gravatar": f"https://en.gravatar.com/{username}",
        "Pastebin": f"https://pastebin.com/u/{username}",
        "Imgur": f"https://imgur.com/user/{username}",
        "Giphy": f"https://giphy.com/{username}",
        "Vimeo": f"https://vimeo.com/{username}",
        "Dailymotion": f"https://www.dailymotion.com/{username}",
        "Rumble": f"https://rumble.com/user/{username}",
        "Odysee": f"https://odysee.com/@{username}",
        "Bitchute": f"https://www.bitchute.com/channel/{username}/",
    }

    result = {
        "username": username,
        "checked": 0,
        "found": [],
        "errors": [],
        "lookup_at": datetime.now().isoformat(),
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def check(item):
        platform, url = item
        try:
            r = requests.head(url, timeout=8, allow_redirects=True, verify=False, headers=headers)
            # 200 = ada, 404 = tidak ada, 403/401 = mungkin ada (private), 3xx = redirect (mungkin ada)
            if r.status_code == 200:
                return {"platform": platform, "url": url, "status": 200, "confidence": "high"}
            elif r.status_code in (403, 401):
                return {"platform": platform, "url": url, "status": r.status_code,
                        "confidence": "medium", "note": "Private atau butuh login"}
        except Exception as e:
            return None
        return None

    with ThreadPoolExecutor(max_workers=25) as ex:
        futures = {ex.submit(check, item): item for item in platforms.items()}
        for f in as_completed(futures):
            result["checked"] += 1
            r = f.result()
            if r:
                result["found"].append(r)

    return result


# ============================================================
# WAYBACK MACHINE
# ============================================================
def wayback_lookup(domain):
    """Ambil snapshot history dari archive.org."""
    result = {"domain": domain, "snapshots": [], "lookup_at": datetime.now().isoformat()}
    try:
        # Query CDX API
        url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit=100&collapse=timestamp:6"
        r = requests.get(url, timeout=30)
        data = r.json()
        if len(data) > 1:
            headers = data[0]
            for row in data[1:]:
                d = dict(zip(headers, row))
                ts = d.get("timestamp", "")
                if len(ts) >= 14:
                    dt = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]}"
                else:
                    dt = ts
                result["snapshots"].append({
                    "timestamp": dt,
                    "url": d.get("original", ""),
                    "status": d.get("statuscode", ""),
                    "mimetype": d.get("mimetype", ""),
                    "archive_url": f"https://web.archive.org/web/{ts}/{d.get('original', '')}",
                })
        result["total"] = len(result["snapshots"])
    except Exception as e:
        result["error"] = str(e)
    return result


# ============================================================
# HIBP (Have I Been Pwned) - Public API
# ============================================================
def hibp_check(email):
    """Cek email di HIBP public API."""
    result = {"email": email, "lookup_at": datetime.now().isoformat()}
    headers = {"User-Agent": "ReconPro-OSINT"}
    try:
        r = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false",
            headers=headers, timeout=15
        )
        if r.status_code == 200:
            breaches = r.json()
            result["status"] = "BREACHED"
            result["count"] = len(breaches)
            result["breaches"] = [
                {"name": b.get("Name"), "title": b.get("Title"),
                 "date": b.get("BreachDate"), "pwn_count": b.get("PwnCount"),
                 "data_classes": b.get("DataClasses")}
                for b in breaches
            ]
        elif r.status_code == 404:
            result["status"] = "CLEAN"
            result["count"] = 0
            result["breaches"] = []
        elif r.status_code == 429:
            result["status"] = "RATE_LIMIT"
            result["error"] = "Rate limit — coba lagi nanti"
        else:
            result["status"] = f"HTTP_{r.status_code}"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
    return result


# ============================================================
# DOCUMENT METADATA
# ============================================================
def extract_metadata(file_bytes, filename):
    """Extract metadata dari PDF/DOCX/XLSX."""
    result = {"filename": filename, "lookup_at": datetime.now().isoformat()}
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    try:
        if ext == "pdf":
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                result["metadata"] = dict(reader.metadata) if reader.metadata else {}
                result["pages"] = len(reader.pages)
            except Exception as e:
                result["error"] = f"PDF: {e}"

        elif ext in ("docx", "doc"):
            try:
                import docx
                d = docx.Document(io.BytesIO(file_bytes))
                props = d.core_properties
                result["metadata"] = {
                    "author": props.author,
                    "category": props.category,
                    "comments": props.comments,
                    "content_status": props.content_status,
                    "created": str(props.created) if props.created else None,
                    "identifier": props.identifier,
                    "keywords": props.keywords,
                    "language": props.language,
                    "last_modified_by": props.last_modified_by,
                    "last_printed": str(props.last_printed) if props.last_printed else None,
                    "modified": str(props.modified) if props.modified else None,
                    "revision": props.revision,
                    "subject": props.subject,
                    "title": props.title,
                    "version": props.version,
                }
            except Exception as e:
                result["error"] = f"DOCX: {e}"

        elif ext in ("xlsx", "xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
                props = wb.properties
                result["metadata"] = {
                    "creator": props.creator,
                    "created": str(props.created) if props.created else None,
                    "modified": str(props.modified) if props.modified else None,
                    "title": props.title,
                    "subject": props.subject,
                    "description": props.description,
                    "keywords": props.keywords,
                    "category": props.category,
                    "last_modified_by": props.lastModifiedBy,
                }
                result["sheets"] = wb.sheetnames
            except Exception as e:
                result["error"] = f"XLSX: {e}"
        else:
            result["error"] = f"Format {ext} tidak didukung (pakai pdf/docx/xlsx)"

    except Exception as e:
        result["error"] = str(e)

    return result
