from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.api.deps import get_current_user_optional
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation_service import get_conversation
from app.services.rag_service import answer_question

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with document grounded in conversation"
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    # 1. Validate conversation exists
    conversation = get_conversation(db, request.conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {request.conversation_id} not found."
        )

    # 2. Validate conversation ownership
    if current_user and conversation.user_id and conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to chat in this conversation."
        )

    # 3. Answer question via RAG pipeline
    try:
        user_id = current_user.id if current_user else conversation.user_id
        answer = answer_question(
            db=db,
            question=request.question.strip(),
            conversation_id=request.conversation_id,
            user_id=user_id
        )
        return ChatResponse(answer=answer)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG processing failed: {str(e)}"
        )