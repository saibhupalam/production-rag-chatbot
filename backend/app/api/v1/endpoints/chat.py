from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from app.services.rag_service import (
    answer_question
)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    answer = answer_question(
        db=db,
        question=request.question,
        conversation_id=request.conversation_id
    )

    return ChatResponse(
        answer=answer
    )