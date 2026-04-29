from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum


class SentimentEnum(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class InteractionBase(BaseModel):
    hcp_name: str
    interaction_type: str
    date: date
    time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[SentimentEnum] = SentimentEnum.neutral
    outcomes: Optional[str] = None
    followup_actions: Optional[str] = None
    source: Optional[str] = "form"


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[date] = None
    time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[SentimentEnum] = None
    outcomes: Optional[str] = None
    followup_actions: Optional[str] = None


class InteractionResponse(InteractionBase):
    id: int
    ai_summary: Optional[str] = None
    ai_suggested_followups: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    hcp_context: Optional[str] = None
    last_interaction_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    interaction_logged: Optional[bool] = False
    interaction_id: Optional[int] = None
    suggested_followups: Optional[List[str]] = []
    form_data: Optional[dict] = None


class LogInteractionInput(BaseModel):
    raw_text: str
    hcp_name: Optional[str] = None


class EditInteractionInput(BaseModel):
    interaction_id: int
    updates: InteractionUpdate


class GetHCPHistoryInput(BaseModel):
    hcp_name: str
    limit: Optional[int] = 5


class SuggestFollowupInput(BaseModel):
    interaction_id: int


class AnalyzeSentimentInput(BaseModel):
    text: str