"""Auto-annotate screenshot dengan IP + waktu + device."""
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
