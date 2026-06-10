from sqlalchemy.orm import Session

from app.models.conversation import Conversation


def create_conversation(
    db: Session,
    title: str,
    user_id: int,
    document_id: int
):

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
    conversation_id: int
):

    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id
        )
        .first()
    )