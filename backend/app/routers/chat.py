from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
import json

from app.db.database import get_db
from app.models.interaction import Interaction
from app.schemas import ChatRequest, ChatResponse
from app.agent.graph import build_agent_graph
from app.config import settings

router = APIRouter(prefix="/chat", tags=["Chat Agent"])


def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.1,
    )


def detect_edit_intent(message: str, interaction_id: int):
    llm = get_llm()
    prompt = f"""
You are a CRM assistant. Extract fields the user wants to edit for interaction ID {interaction_id}.
Return ONLY valid JSON. Only include fields mentioned by the user.
Valid fields: hcp_name, interaction_type, attendees, topics_discussed, materials_shared, sentiment, outcomes, followup_actions
For sentiment use only: positive, neutral, negative
User message: "{message}"
Example: {{"hcp_name": "Dr. John", "sentiment": "negative"}}
If no edit intent found, return: {{}}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception:
        return {}


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        edit_keywords = ["correct", "change", "update", "edit", "fix", "wrong", "actually", "sorry"]
        is_edit = any(kw in payload.message.lower() for kw in edit_keywords)

        if is_edit and payload.last_interaction_id:
            fields_to_update = detect_edit_intent(
                payload.message, payload.last_interaction_id
            )

            if fields_to_update:
                interaction = db.query(Interaction).filter(
                    Interaction.id == payload.last_interaction_id
                ).first()

                if interaction:
                    for field, value in fields_to_update.items():
                        setattr(interaction, field, value)
                    db.commit()
                    db.refresh(interaction)

                    form_data = {
                        "hcp_name": str(interaction.hcp_name or ""),
                        "interaction_type": str(interaction.interaction_type or "Meeting"),
                        "date": str(interaction.date) if interaction.date else "",
                        "attendees": str(interaction.attendees or ""),
                        "topics_discussed": str(interaction.topics_discussed or ""),
                        "materials_shared": str(interaction.materials_shared or ""),
                        "sentiment": str(interaction.sentiment or "neutral"),
                        "outcomes": str(interaction.outcomes or ""),
                        "followup_actions": str(interaction.followup_actions or ""),
                        "ai_summary": str(interaction.ai_summary or ""),
                    }

                    updated_fields = ", ".join(
                        [f"{k} to {v}" for k, v in fields_to_update.items()]
                    )
                    reply = f"Done! I have updated: {updated_fields}. All other fields remain unchanged."

                    return ChatResponse(
                        reply=reply,
                        interaction_logged=True,
                        interaction_id=interaction.id,
                        suggested_followups=[],
                        form_data=form_data,
                    )

        from app.db.database import SessionLocal
        fresh_db2 = SessionLocal()
        graph = build_agent_graph(fresh_db2)

        messages = []
        for msg in payload.history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        user_content = payload.message
        if payload.hcp_context:
            user_content = f"[HCP context: {payload.hcp_context}] {user_content}"
        if payload.last_interaction_id:
            user_content = f"[Last logged interaction ID: {payload.last_interaction_id}] {user_content}"

        messages.append(HumanMessage(content=user_content))

        result = graph.invoke({
            "messages": messages,
            "db_session": db,
            "final_response": None,
            "logged_interaction_id": None,
        })

        final_messages = result.get("messages", [])
        reply = ""
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and msg.content:
                reply = msg.content
                break

        interaction_logged = False
        interaction_id = None
        suggested_followups = []
        form_data = None

        for msg in final_messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                try:
                    data = json.loads(msg.content)
                    if isinstance(data, dict):
                        if data.get("status") == "logged":
                            interaction_logged = True
                            interaction_id = data.get("interaction_id")
                            saved = db.query(Interaction).filter(
                                Interaction.id == interaction_id
                            ).first()
                            if saved:
                                form_data = {
                                    "hcp_name": saved.hcp_name,
                                    "interaction_type": saved.interaction_type,
                                    "date": str(saved.date),
                                    "attendees": saved.attendees or "",
                                    "topics_discussed": saved.topics_discussed or "",
                                    "materials_shared": saved.materials_shared or "",
                                    "sentiment": saved.sentiment or "neutral",
                                    "outcomes": saved.outcomes or "",
                                    "followup_actions": saved.followup_actions or "",
                                    "ai_summary": saved.ai_summary or "",
                                }
                        if "suggestions" in data:
                            suggested_followups = data["suggestions"]
                except Exception:
                    pass

        return ChatResponse(
            reply=reply or "I could not process that. Please try again.",
            interaction_logged=interaction_logged,
            interaction_id=interaction_id,
            suggested_followups=suggested_followups,
            form_data=form_data,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    finally:
        try:
            fresh_db2.close()
        except Exception:
            pass