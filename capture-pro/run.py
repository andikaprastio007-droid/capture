import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
os.environ["DATABASE_URL"] = "sqlite:///" + str(BASE_DIR / "data" / "capture.db")
for k in ["UPLOAD_DIR", "SCREENSHOT_DIR", "BURST_DIR", "KEYS_DIR", "CLIPBOARD_DIR",
          "AUDIO_DIR", "VIDEO_DIR", "TRACKING_DIR"]:
    os.environ[k] = str(BASE_DIR / "data" / k.replace("_DIR", "").lower())
    os.makedirs(os.environ[k], exist_ok=True)

from app import create_app
app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Capture Dashboard Pro - ULTIMATE")
    print("  URL  : http://localhost:8000/")
    print("  Dash : http://localhost:8000/dashboard")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8000, debug=False)
