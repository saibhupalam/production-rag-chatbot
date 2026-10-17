from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.embedding_service import generate_embeddings
from app.services.qdrant_service import search_chunks
from app.services.llm_service import llm
from app.services.conversation_service import get_conversation
from app.services.message_service import get_conversation_messages, create_message
from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank_candidates
from app.rag.query_rewriter import rewrite_query


def answer_question(
    db: Session,
    question: str,
    conversation_id: int,
    user_id: Optional[int] = None,
    use_advanced_rag: bool = True
) -> str:
    """
    RAG answer generation pipeline:
    1. Resolve conversation and ensure ownership and attached document.
    2. Load conversation history.
    3. Persist incoming user question.
    4. Conversational query rewriting for ambiguous follow-ups (Phase 14D).
    5. Hybrid search combining dense semantic and BM25 lexical retrieval (Phase 14B).
    6. Candidate reranking (Phase 14C).
    7. Generate grounded answer using Groq LLM with strict context constraints.
    8. Persist assistant response and return answer.
    """
    conversation = get_conversation(db, conversation_id, user_id=user_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    document_id = conversation.document_id
    if not document_id:
        raise ValueError(f"Conversation {conversation_id} has no document attached")

    # Load previous history BEFORE adding the current message to history string
    existing_messages = get_conversation_messages(db, conversation_id)

    # Format history string for LLM prompt (limit to last 6 messages to prevent unbounded growth)
    recent_history = existing_messages[-6:]
    history = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_history])

    # Persist the current user message
    create_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=question
    )

    retrieval_query = question

    if use_advanced_rag:
        # Phase 14D: Conversational Query Rewriting
        if existing_messages:
            retrieval_query = rewrite_query(question, existing_messages)

        # Phase 14B: Hybrid Search
        candidates = hybrid_search(
            query=retrieval_query,
            document_id=document_id,
            user_id=user_id,
            limit=8,
            candidate_depth=15
        )

        # Fallback to pure dense search if hybrid search returns empty
        if not candidates:
            query_embedding = generate_embeddings([retrieval_query], is_query=True)[0]
            dense_results = search_chunks(
                query_embedding=query_embedding,
                document_id=document_id,
                user_id=user_id,
                limit=settings.RAG_RETRIEVAL_LIMIT
            )
            candidates = [
                {"text": p.payload.get("text", ""), "chunk_id": p.payload.get("chunk_id", 0)}
                for p in dense_results.points
            ]

        # Phase 14C: Reranking
        final_chunks = rerank_candidates(
            query=retrieval_query,
            candidates=candidates,
            top_k=settings.RAG_RETRIEVAL_LIMIT
        )
    else:
        # Baseline RAG Path: Pure dense search without hybrid, reranking, or query rewrite
        query_embedding = generate_embeddings([question], is_query=True)[0]
        results = search_chunks(
            query_embedding=query_embedding,
            document_id=document_id,
            user_id=user_id,
            limit=settings.RAG_RETRIEVAL_LIMIT
        )
        final_chunks = [
            {"text": p.payload.get("text", "")}
            for p in results.points
        ]

    # Assemble retrieved context
    context = "\n\n".join([c["text"] for c in final_chunks if c.get("text")])
    if not context.strip():
        context = "No relevant context found in document."

    prompt = f"""You are a helpful and precise assistant.

Conversation History:
{history if history else "No previous history."}

Context:
{context}

Current Question:
{question}

Use ONLY the provided context to answer the question.
If the answer is not present in the context, say that the information is not available in the document.
"""

    response = llm.invoke(prompt)
    answer = getattr(response, "content", str(response))

    # Persist assistant response
    create_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer
    )

    return answer