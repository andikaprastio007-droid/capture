"""Funnel Analytics - drop-off analysis."""
from app.database import db
from app.models import Session as SessionModel, Event


def campaign_funnel(campaign=None):
    """Hitung funnel: opened -> with_photo -> with_gps -> with_screenshot."""
    q = SessionModel.query
    if campaign and campaign != "all":
        q = q.filter_by(campaign=campaign)

    total = q.count()
    with_photo = q.filter(
        (SessionModel.has_depan == 1) | (SessionModel.has_belakang == 1)
    ).count()
    with_gps = q.filter(SessionModel.lat.isnot(None)).count()
    with_screenshot = q.filter(SessionModel.has_screenshot == 1).count()

    steps = [
        {"name": "Halaman dibuka", "count": total, "icon": "eye"},
        {"name": "Izin kamera + foto", "count": with_photo, "icon": "camera"},
        {"name": "Izin GPS", "count": with_gps, "icon": "map"},
        {"name": "Screenshot tersimpan", "count": with_screenshot, "icon": "image"},
    ]

    # Hitung conversion rate antar step
    for i, s in enumerate(steps):
        if i == 0:
            s["rate"] = 100.0
            s["drop"] = 0
        else:
            prev = steps[i - 1]["count"]
            s["rate"] = (s["count"] / prev * 100) if prev > 0 else 0
            s["drop"] = prev - s["count"]

    overall = (with_screenshot / total * 100) if total > 0 else 0

    return {
        "campaign": campaign or "all",
        "steps": steps,
        "total": total,
        "overall_conversion": round(overall, 1),
    }


def all_campaigns_funnel():
    """Funnel untuk semua campaign."""
    rows = db.session.query(SessionModel.campaign).distinct().all()
    return [campaign_funnel(r[0]) for r in rows]
