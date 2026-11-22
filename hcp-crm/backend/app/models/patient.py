from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String(20), unique=True, index=True)  # e.g. HCP-0001, set on create
    full_name = Column(String(120), nullable=False, index=True)
    age = Column(Integer)
    gender = Column(String(20))
    phone = Column(String(30))
    email = Column(String(120))
    diagnosis = Column(Text)
    symptoms = Column(Text)
    medical_history = Column(Text)
    doctor_assigned = Column(String(120))
    appointment_date = Column(Date)
    source = Column(String(20), nullable=False, default="manual")  # "manual" | "ai_extractor"
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    created_by_user = relationship("User", back_populates="patients")
    activities = relationship("ActivityLog", back_populates="patient")
