from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.db.database import get_db
from app.agent.graph import build_tools
from app.schemas import (
    LogInteractionInput,
    EditInteractionInput,
    GetHCPHistoryInput,
    SuggestFollowupInput,
    AnalyzeSentimentInput,
)

router = APIRouter(prefix="/tools", tags=["Agent Tools"])


def _get_tools(db: Session):
    tools = build_tools(db)
    return {t.name: t for t in tools}


@router.post("/log-interaction")
def tool_log_interaction(payload: LogInteractionInput, db: Session = Depends(get_db)):
    """Tool 1 - Parse free-text and log an HCP interaction."""
    tools = _get_tools(db)
    result = tools["log_interaction"].invoke(
        {"raw_text": payload.raw_text, "hcp_name": payload.hcp_name}
    )
    return json.loads(result)


@router.post("/edit-interaction")
def tool_edit_interaction(payload: EditInteractionInput, db: Session = Depends(get_db)):
    """Tool 2 - Edit a field in an existing interaction."""
    tools = _get_tools(db)
    updates = payload.updates.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update provided.")
    results = []
    for field, value in updates.items():
        result = tools["edit_interaction"].invoke(
            {"interaction_id": payload.interaction_id, "field": field, "new_value": str(value)}
        )
        results.append(json.loads(result))
    return results


@router.post("/hcp-history")
def tool_get_hcp_history(payload: GetHCPHistoryInput, db: Session = Depends(get_db)):
    """Tool 3 - Get interaction history for an HCP."""
    tools = _get_tools(db)
    result = tools["get_hcp_history"].invoke(
        {"hcp_name": payload.hcp_name, "limit": payload.limit}
    )
    return json.loads(result)


@router.post("/suggest-followup")
def tool_suggest_followup(payload: SuggestFollowupInput, db: Session = Depends(get_db)):
    """Tool 4 - Generate AI follow-up suggestions for an interaction."""
    tools = _get_tools(db)
    result = tools["suggest_followup"].invoke(
        {"interaction_id": payload.interaction_id}
    )
    return json.loads(result)


@router.post("/analyze-sentiment")
def tool_analyze_sentiment(payload: AnalyzeSentimentInput, db: Session = Depends(get_db)):
    """Tool 5 - Analyze sentiment of provided text."""
    tools = _get_tools(db)
    result = tools["analyze_sentiment"].invoke({"text": payload.text})
    return json.loads(result)