from typing import List, Any
from app.core.config import settings
from app.services.llm_service import llm


def rewrite_query(
    query: str,
    history_messages: List[Any],
    max_history_turns: int = 4
) -> str:
    """
    Transform ambiguous follow-up questions into standalone retrieval queries
    using recent conversation history.
    Preserves original question if history is empty, rewriting is disabled,
    or if rewriting encounters any error.
    """
    if not query or not query.strip():
        return query

    if not settings.QUERY_REWRITE_ENABLED or not history_messages:
        return query.strip()

    # Limit to recent history turns (each turn has user + assistant)
    recent_msgs = history_messages[-(max_history_turns * 2):]
    formatted_history = []
    for m in recent_msgs:
        role = getattr(m, "role", None) or m.get("role", "user")
        content = getattr(m, "content", None) or m.get("content", "")
        formatted_history.append(f"{role}: {content}")

    if not formatted_history:
        return query.strip()

    history_text = "\n".join(formatted_history)

    prompt = f"""You are a search query reformulation assistant.
Given the following conversation history and a follow-up question, rewrite the question into a specific, standalone retrieval search query that captures all necessary entities and context from the discussion.

If the question is already completely standalone and unambiguous, output it unchanged.
Do NOT answer the question.
Do NOT include quotes, preambles, or markdown formatting. Output ONLY the reformulated query.

Conversation History:
{history_text}

Follow-up Question:
{query.strip()}

Standalone Search Query:"""

    try:
        response = llm.invoke(prompt)
        rewritten = response.content.strip().strip('"').strip("'").strip()
        if rewritten and len(rewritten) > 3:
            return rewritten
        return query.strip()
    except Exception as e:
        print(f"Warning: Query rewrite failed ({e}). Falling back to original query.")
        return query.strip()
