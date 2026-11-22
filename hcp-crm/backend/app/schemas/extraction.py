from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    text: str = Field(min_length=10, max_length=5000, description="Unstructured medical text")


class ExtractedPatient(BaseModel):
    """Every field is optional: anything not stated in the text must be null."""

    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    medical_history: Optional[str] = None
    doctor_assigned: Optional[str] = None
    appointment_date: Optional[date] = None


class ExtractResponse(BaseModel):
    extracted: ExtractedPatient
    model: str
