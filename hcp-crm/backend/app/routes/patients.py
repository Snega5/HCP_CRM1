from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.activity import ActivityLog
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientListOut, PatientOut, PatientUpdate
from app.services.security import get_current_user

router = APIRouter(prefix="/api/patients", tags=["patients"])


def _get_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def _log(db: Session, action: str, description: str, user: User, patient_id: Optional[int]) -> None:
    db.add(ActivityLog(action=action, description=description, user_id=user.id, patient_id=patient_id))


@router.get("", response_model=PatientListOut)
def list_patients(
    q: Optional[str] = Query(None, description="Search name, ID, diagnosis, doctor or phone"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Patient)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Patient.full_name.ilike(like),
                Patient.patient_code.ilike(like),
                Patient.diagnosis.ilike(like),
                Patient.doctor_assigned.ilike(like),
                Patient.phone.ilike(like),
            )
        )
    total = query.count()
    items = query.order_by(Patient.created_at.desc(), Patient.id.desc()).offset(skip).limit(limit).all()
    return PatientListOut(items=items, total=total)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_or_404(db, patient_id)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = Patient(**payload.model_dump(), created_by=user.id)
    db.add(patient)
    db.flush()  # assigns patient.id
    patient.patient_code = f"HCP-{patient.id:04d}"

    if payload.source == "ai_extractor":
        _log(db, "ai_extraction", f"Saved AI-extracted patient {patient.full_name}", user, patient.id)
    else:
        _log(db, "patient_created", f"Added patient {patient.full_name}", user, patient.id)

    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient = _get_or_404(db, patient_id)
    data = payload.model_dump(exclude_unset=True)

    if "full_name" in data and not data["full_name"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Full name cannot be empty")

    for field, value in data.items():
        setattr(patient, field, value)

    _log(db, "patient_updated", f"Updated patient {patient.full_name}", user, patient.id)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = _get_or_404(db, patient_id)
    name, code = patient.full_name, patient.patient_code
    db.delete(patient)  # related activity rows keep existing; their patient_id becomes NULL
    _log(db, "patient_deleted", f"Deleted patient {name} ({code})", user, None)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
