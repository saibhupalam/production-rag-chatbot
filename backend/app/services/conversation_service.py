from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.conversation import Conversation


def create_conversation(
    db: Session,
    title: str,
    user_id: Optional[int],
    document_id: int
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        title=title,
        user_id=user_id,
        document_id=document_id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(
    db: Session,
    conversation_id: int,
    user_id: Optional[int] = None
) -> Optional[Conversation]:
    """Retrieve conversation by ID, optionally enforcing user ownership."""
    query = db.query(Conversation).filter(Conversation.id == conversation_id)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    return query.first()


def get_all_conversations(
    db: Session,
    user_id: Optional[int] = None
) -> List[Conversation]:
    """Retrieve all conversations, optionally filtered by user."""
    query = db.query(Conversation)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    return query.order_by(Conversation.id.desc()).all()


def delete_conversation(
    db: Session,
    conversation_id: int,
    user_id: Optional[int] = None
) -> Optional[Conversation]:
    """Delete a conversation, optionally validating user ownership."""
    conversation = get_conversation(db, conversation_id, user_id=user_id)
    if conversation:
        db.delete(conversation)
        db.commit()
    return conversation