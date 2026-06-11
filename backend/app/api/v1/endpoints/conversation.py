from fastapi import APIRouter
from fastapi import Depends
from typing import List

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse
)

from app.schemas.message import(
    MessageResponse
)


from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    get_all_conversations,
    delete_conversation
)

from app.services.message_service import(
    get_conversation_messages
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


@router.get(
    "/conversations",
    response_model=List[ConversationResponse]
)

def list_conversations(
    db:Session = Depends(get_db)
):
    return get_all_conversations(db)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse
)
def get_single_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    return get_conversation(
        db,
        conversation_id
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse]
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    return get_conversation_messages(
        db,
        conversation_id
    )


@router.delete(
    "/conversations/{conversation_id}"
)
def remove_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    delete_conversation(
        db,
        conversation_id
    )

    return {
        "message":
        "Conversation deleted"
    }