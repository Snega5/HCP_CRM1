from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="staff")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    patients = relationship("Patient", back_populates="created_by_user")
    activities = relationship("ActivityLog", back_populates="user")
