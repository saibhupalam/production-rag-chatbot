from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.api.deps import get_current_user_optional
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.message import MessageResponse
from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    get_all_conversations,
    delete_conversation
)
from app.services.message_service import get_conversation_messages
from app.services.document_service import get_document

router = APIRouter()


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation"
)
def create_new_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Validate document exists
    doc = get_document(db, request.document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {request.document_id} not found."
        )

    # Determine user_id: do not trust arbitrary user_id from client if user is authenticated
    if current_user:
        user_id = current_user.id
        if doc.user_id and doc.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot create a conversation on another user's document."
            )
    else:
        user_id = request.user_id or 1

    conversation = create_conversation(
        db=db,
        title=request.title.strip() if request.title.strip() else f"Chat: {doc.filename}",
        user_id=user_id,
        document_id=request.document_id
    )
    return conversation


@router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    summary="List all conversations for the active user"
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    return get_all_conversations(db, user_id=user_id)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get single conversation by ID"
)
def get_single_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    conv = get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )

    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation."
        )

    return conv


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse],
    summary="Get all messages in a conversation"
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    conv = get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )

    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to messages in this conversation."
        )

    return get_conversation_messages(db, conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete a conversation"
)
def remove_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    conv = get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )

    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this conversation."
        )

    delete_conversation(db, conversation_id)
    return {
        "message": "Conversation deleted successfully",
        "id": conversation_id
    }