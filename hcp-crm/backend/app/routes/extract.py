from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.models.user import User
from app.schemas.extraction import ExtractRequest, ExtractResponse
from app.services.groq_service import ExtractionError, extract_patient_info
from app.services.security import get_current_user

router = APIRouter(prefix="/api/extract", tags=["ai-extractor"])


@router.post("", response_model=ExtractResponse)
def extract(payload: ExtractRequest, _: User = Depends(get_current_user)):
    """Extract patient fields from free text. Returns data for REVIEW; nothing is saved."""
    try:
        extracted = extract_patient_info(payload.text)
    except ExtractionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ExtractResponse(extracted=extracted, model=settings.GROQ_MODEL)
