from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

GENDER_MAP = {"male": "Male", "female": "Female", "other": "Other"}


class _Cleaner(BaseModel):
    """Shared validators: trim strings, turn blanks into None, normalise gender."""

    @field_validator("*", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @field_validator("gender", check_fields=False)
    @classmethod
    def normalise_gender(cls, v):
        if v is None:
            return v
        key = v.strip().lower()
        if key not in GENDER_MAP:
            raise ValueError("gender must be Male, Female or Other")
        return GENDER_MAP[key]


class PatientBase(_Cleaner):
    full_name: str = Field(min_length=1, max_length=120)
    age: Optional[int] = Field(default=None, ge=0, le=130)
    gender: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[EmailStr] = None
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    medical_history: Optional[str] = None
    doctor_assigned: Optional[str] = Field(default=None, max_length=120)
    appointment_date: Optional[date] = None


class PatientCreate(PatientBase):
    # "ai_extractor" is used by the AI extractor page (Stage 4)
    source: Literal["manual", "ai_extractor"] = "manual"


class PatientUpdate(_Cleaner):
    """All fields optional: only the fields sent are changed."""

    full_name: Optional[str] = Field(default=None, max_length=120)
    age: Optional[int] = Field(default=None, ge=0, le=130)
    gender: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[EmailStr] = None
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    medical_history: Optional[str] = None
    doctor_assigned: Optional[str] = Field(default=None, max_length=120)
    appointment_date: Optional[date] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_code: Optional[str] = None
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    medical_history: Optional[str] = None
    doctor_assigned: Optional[str] = None
    appointment_date: Optional[date] = None
    source: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PatientListOut(BaseModel):
    items: List[PatientOut]
    total: int
