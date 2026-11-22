from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class RecentPatient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_code: Optional[str] = None
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_assigned: Optional[str] = None
    created_at: Optional[datetime] = None


class RecentActivity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    description: str
    created_at: Optional[datetime] = None


class AgeBucket(BaseModel):
    label: str
    count: int


class DashboardStats(BaseModel):
    total_patients: int
    new_this_week: int
    appointments_today: int
    ai_extractions: int
    gender_distribution: Dict[str, int]
    age_distribution: List[AgeBucket]
    recent_patients: List[RecentPatient]
    recent_activities: List[RecentActivity]
