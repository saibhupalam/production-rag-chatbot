from fastapi import APIRouter

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
    request: ChatRequest
):

    answer = answer_question(
        request.question
    )

    return ChatResponse(
        answer=answer
    )