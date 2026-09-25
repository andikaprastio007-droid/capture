"""Reports - PDF generator endpoints."""
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
