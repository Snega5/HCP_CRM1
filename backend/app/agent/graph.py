import json
from typing import Annotated, TypedDict, List, Optional

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from sqlalchemy.orm import Session

from app.config import settings
from app.models.interaction import Interaction


class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]
    db_session: Session
    final_response: Optional[str]
    logged_interaction_id: Optional[int]


def build_tools(db: Session):
    llm_plain = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.1,
    )

    @tool
    def log_interaction(raw_text: str, hcp_name: Optional[str] = None) -> str:
        """Parse a free-text HCP interaction, extract structured data using LLM, and save to DB."""
        extraction_prompt = f"""
You are a life-science CRM assistant. Extract the following fields from the
interaction note below and return ONLY valid JSON (no markdown, no explanation).

Fields to extract:
- hcp_name (string)
- interaction_type (one of: Meeting, Call, Email, Conference, Other)
- date (YYYY-MM-DD, use today if missing)
- attendees (comma-separated names or null)
- topics_discussed (brief summary as single string or null)
- materials_shared (comma-separated or null)
- sentiment (must be exactly one of: positive, neutral, negative)
- outcomes (string or null)
- followup_actions (string or null)
- summary (1-2 sentence summary of the interaction)

Interaction note:
\"\"\"{raw_text}\"\"\"
"""
        response = llm_plain.invoke([HumanMessage(content=extraction_prompt)])
        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
        except Exception:
            data = {}

        from datetime import date as dt_date

        if hcp_name:
            data["hcp_name"] = hcp_name

        sentiment_val = str(data.get("sentiment", "neutral")).lower()
        if sentiment_val not in ["positive", "neutral", "negative"]:
            sentiment_val = "neutral"

        try:
            interaction_date = dt_date.fromisoformat(
                data.get("date", str(dt_date.today()))
            )
        except Exception:
            interaction_date = dt_date.today()

        interaction = Interaction(
            hcp_name=data.get("hcp_name", "Unknown HCP"),
            interaction_type=data.get("interaction_type", "Meeting"),
            date=interaction_date,
            attendees=data.get("attendees"),
            topics_discussed=data.get("topics_discussed"),
            materials_shared=data.get("materials_shared"),
            sentiment=sentiment_val,
            outcomes=data.get("outcomes"),
            followup_actions=data.get("followup_actions"),
            ai_summary=data.get("summary"),
            source="chat",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "status": "logged",
            "interaction_id": interaction.id,
            "hcp_name": interaction.hcp_name,
            "ai_summary": interaction.ai_summary,
        })

    @tool
    def edit_interaction(interaction_id: int, field: str, new_value: str) -> str:
        """Modify a specific field of an already-logged HCP interaction."""
        interaction = db.query(Interaction).filter(
            Interaction.id == interaction_id
        ).first()
        if not interaction:
            return json.dumps({"error": f"Interaction {interaction_id} not found."})

        allowed_fields = {
            "hcp_name", "interaction_type", "attendees", "topics_discussed",
            "materials_shared", "sentiment", "outcomes",
            "followup_actions", "ai_summary",
        }
        if field not in allowed_fields:
            return json.dumps({"error": f"Field '{field}' cannot be edited."})

        setattr(interaction, field, new_value)
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "status": "updated",
            "interaction_id": interaction.id,
            "field": field,
            "new_value": new_value,
        })

    @tool
    def get_hcp_history(hcp_name: str, limit: int = 5) -> str:
        """Retrieve the most recent interactions logged for a given HCP."""
        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
            .order_by(Interaction.date.desc())
            .limit(limit)
            .all()
        )
        if not interactions:
            return json.dumps({
                "message": f"No interactions found for HCP '{hcp_name}'."
            })

        result = []
        for i in interactions:
            result.append({
                "id": i.id,
                "date": str(i.date),
                "interaction_type": i.interaction_type,
                "topics_discussed": i.topics_discussed,
                "sentiment": i.sentiment,
                "outcomes": i.outcomes,
                "ai_summary": i.ai_summary,
            })
        return json.dumps({"hcp_name": hcp_name, "history": result})

    @tool
    def suggest_followup(interaction_id: int) -> str:
        """Generate AI-driven next-best-action follow-up suggestions for a logged interaction."""
        interaction = db.query(Interaction).filter(
            Interaction.id == interaction_id
        ).first()
        if not interaction:
            return json.dumps({"error": f"Interaction {interaction_id} not found."})

        prompt = f"""
You are a life-science field rep assistant. Based on the following HCP interaction,
suggest 3 to 5 concise, actionable follow-up actions.
Return ONLY a JSON array of strings, e.g. ["Action 1", "Action 2"].

HCP: {interaction.hcp_name}
Type: {interaction.interaction_type}
Topics: {interaction.topics_discussed}
Outcomes: {interaction.outcomes}
Sentiment: {interaction.sentiment}
"""
        response = llm_plain.invoke([HumanMessage(content=prompt)])
        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            suggestions = json.loads(raw)
        except Exception:
            suggestions = [
                "Schedule a follow-up meeting",
                "Send product brochure",
                "Check sample inventory",
            ]

        interaction.ai_suggested_followups = json.dumps(suggestions)
        db.commit()

        return json.dumps({
            "interaction_id": interaction_id,
            "hcp_name": interaction.hcp_name,
            "suggestions": suggestions,
        })

    @tool
    def analyze_sentiment(text: str) -> str:
        """Analyze the sentiment of text from an HCP interaction note."""
        prompt = f"""
Analyze the sentiment of the following text from a healthcare professional interaction.
Return ONLY JSON with keys:
- "sentiment": exactly one of positive, neutral, negative
- "reason": one sentence explanation

Text:
\"\"\"{text}\"\"\"
"""
        response = llm_plain.invoke([HumanMessage(content=prompt)])
        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)
        except Exception:
            result = {
                "sentiment": "neutral",
                "reason": "Could not determine sentiment.",
            }

        return json.dumps(result)

    return [
        log_interaction,
        edit_interaction,
        get_hcp_history,
        suggest_followup,
        analyze_sentiment,
    ]


def build_agent_graph(db: Session):
    tools = build_tools(db)

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.2,
    ).bind_tools(tools)

    tool_node = ToolNode(tools)

    SYSTEM_PROMPT = """You are an intelligent CRM assistant for life-science field representatives.
You help log, retrieve, and analyze interactions with Healthcare Professionals (HCPs).

You have access to these tools:
1. log_interaction     - Log a new HCP interaction from a natural-language description.
2. edit_interaction    - Edit a field in an existing interaction by ID. Call this tool MULTIPLE TIMES to edit multiple fields. For example to change name AND sentiment, call edit_interaction twice - once for hcp_name and once for sentiment.
3. get_hcp_history     - Retrieve past interactions for a specific HCP.
4. suggest_followup    - Generate AI follow-up action suggestions for an interaction.
5. analyze_sentiment   - Determine the sentiment of a given text.

IMPORTANT RULES:
- When editing multiple fields, call edit_interaction once per field.
- Valid sentiment values are ONLY: positive, neutral, negative (lowercase).
- Always confirm back to the user what was changed after editing.
- When the user says the interaction ID in context, use that ID for edits."""

    def call_model(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", END: END}
    )
    graph.add_edge("tools", "agent")

    return graph.compile()