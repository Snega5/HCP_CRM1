"""Groq-backed extraction of structured patient details from free text.

Safety rules enforced here (not just in the prompt):
  * the model output must be valid JSON and is re-validated field by field
  * unknown / invalid values become None, never guessed
  * name, email and phone are dropped unless they actually appear in the source text
  * nothing is saved here; the frontend shows the result for human review first
"""
import json
import re
from datetime import date
from typing import Any, Dict, Optional

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    Groq,
    RateLimitError,
)

from app.config import settings
from app.schemas.extraction import ExtractedPatient

SYSTEM_PROMPT = """You extract structured patient information from unstructured medical text.

Return ONLY one JSON object with exactly these keys:
  patient_name, age, gender, phone, email, symptoms, diagnosis,
  medical_history, doctor_assigned, appointment_date

Rules:
- Use ONLY information explicitly stated in the text. Never invent, infer or guess.
- If a value is not stated, use null.
- age: integer number of years, or null.
- gender: "Male", "Female" or "Other", or null if not stated.
- symptoms, diagnosis, medical_history: short phrases in sentence case, taken from the text.
- doctor_assigned: keep the title as written, e.g. "Dr. Kumar".
- appointment_date: "YYYY-MM-DD" only if a full calendar date is stated, otherwise null
  (relative words like "tomorrow" or "next week" are null).
- No explanations, no markdown, no extra keys."""

_NULL_WORDS = {"", "null", "none", "n/a", "na", "unknown", "not mentioned", "not specified", "not stated", "-"}


class ExtractionError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _clean_str(value: Any) -> Optional[str]:
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    s = " ".join(str(value).split())
    return None if s.lower() in _NULL_WORDS else s


def _clean_age(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        age = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None
    return age if 0 <= age <= 130 else None


def _clean_gender(value: Any) -> Optional[str]:
    s = (_clean_str(value) or "").lower()
    return {"male": "Male", "m": "Male", "female": "Female", "f": "Female", "other": "Other"}.get(s)


def _clean_date(value: Any) -> Optional[date]:
    s = _clean_str(value)
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def validate_and_clean(raw: Dict[str, Any], source_text: str) -> ExtractedPatient:
    """Turn whatever the model returned into a safe ExtractedPatient."""
    lowered = source_text.lower()
    text_digits = re.sub(r"\D", "", source_text)

    name = _clean_str(raw.get("patient_name"))
    if name and not any(tok in lowered for tok in re.findall(r"[a-z]{2,}", name.lower())):
        name = None  # name not present in the text -> hallucination

    email = _clean_str(raw.get("email"))
    if email and (not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or email.lower() not in lowered):
        email = None

    phone = _clean_str(raw.get("phone"))
    if phone:
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 7 or digits not in text_digits:
            phone = None

    return ExtractedPatient(
        patient_name=name,
        age=_clean_age(raw.get("age")),
        gender=_clean_gender(raw.get("gender")),
        phone=phone,
        email=email,
        symptoms=_clean_str(raw.get("symptoms")),
        diagnosis=_clean_str(raw.get("diagnosis")),
        medical_history=_clean_str(raw.get("medical_history")),
        doctor_assigned=_clean_str(raw.get("doctor_assigned")),
        appointment_date=_clean_date(raw.get("appointment_date")),
    )


def extract_patient_info(text: str) -> ExtractedPatient:
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("your_"):
        raise ExtractionError(
            "Groq API key is not configured. Add GROQ_API_KEY to backend/.env and restart the server.", 503
        )

    client = Groq(api_key=settings.GROQ_API_KEY, timeout=30.0, max_retries=1)
    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0,
            max_tokens=700,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Medical text:\n\"\"\"\n{text}\n\"\"\""},
            ],
        )
    except AuthenticationError:
        raise ExtractionError("Groq rejected the API key. Check GROQ_API_KEY in backend/.env.", 502)
    except RateLimitError:
        raise ExtractionError("Groq rate limit reached. Wait a moment and try again.", 429)
    except APITimeoutError:
        raise ExtractionError("The AI service timed out. Please try again.", 504)
    except APIConnectionError:
        raise ExtractionError("Could not reach the Groq API. Check your internet connection.", 502)
    except APIStatusError as e:
        raise ExtractionError(f"Groq API error ({e.status_code}). Check GROQ_MODEL and your key.", 502)

    content = (completion.choices[0].message.content or "").strip()
    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        # tolerate a model that wraps the JSON in extra text
        match = re.search(r"\{.*\}", content, re.DOTALL)
        try:
            raw = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError:
            raw = None
    if not isinstance(raw, dict):
        raise ExtractionError("The AI returned an invalid response. Please try again.", 502)

    return validate_and_clean(raw, text)
