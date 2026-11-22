from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.activity import ActivityLog
from app.models.patient import Patient
from app.models.user import User
from app.schemas.dashboard import AgeBucket, DashboardStats
from app.services.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

AGE_BUCKETS = [("0-17", 0, 17), ("18-35", 18, 35), ("36-50", 36, 50), ("51-65", 51, 65), ("66+", 66, 200)]


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total = db.query(func.count(Patient.id)).scalar() or 0
    new_this_week = db.query(func.count(Patient.id)).filter(Patient.created_at >= week_ago).scalar() or 0
    appointments_today = (
        db.query(func.count(Patient.id)).filter(Patient.appointment_date == date.today()).scalar() or 0
    )
    ai_extractions = db.query(func.count(Patient.id)).filter(Patient.source == "ai_extractor").scalar() or 0

    # Gender: anything that isn't Male/Female (including missing) is grouped as "Other"
    gender = {"Male": 0, "Female": 0, "Other": 0}
    for g, count in db.query(Patient.gender, func.count(Patient.id)).group_by(Patient.gender).all():
        key = (g or "").strip().capitalize()
        gender[key if key in ("Male", "Female") else "Other"] += count

    # Age groups (patients without an age are left out of this chart)
    age_counts = db.query(
        *[func.count(Patient.id).filter(Patient.age >= lo, Patient.age <= hi) for _, lo, hi in AGE_BUCKETS]
    ).one()
    age_distribution = [AgeBucket(label=label, count=c or 0) for (label, _, _), c in zip(AGE_BUCKETS, age_counts)]

    recent_patients = db.query(Patient).order_by(Patient.created_at.desc()).limit(5).all()
    recent_activities = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(8).all()

    return DashboardStats(
        total_patients=total,
        new_this_week=new_this_week,
        appointments_today=appointments_today,
        ai_extractions=ai_extractions,
        gender_distribution=gender,
        age_distribution=age_distribution,
        recent_patients=recent_patients,
        recent_activities=recent_activities,
    )
