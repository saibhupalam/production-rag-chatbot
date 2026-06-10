from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse
)

from app.services.conversation_service import (
    create_conversation
)

router = APIRouter()


@router.post(
    "/conversations",
    response_model=ConversationResponse
)
def create_new_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db)
):

    conversation = create_conversation(
        db=db,
        title=request.title,
        user_id=request.user_id,
        document_id=request.document_id
    )

    return conversation