from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=False, index=True)
    interaction_type = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)
    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)
    sentiment = Column(String(20), default="neutral")
    outcomes = Column(Text, nullable=True)
    followup_actions = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_suggested_followups = Column(Text, nullable=True)
    source = Column(String(20), default="form")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())