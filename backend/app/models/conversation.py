from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )
    
    user = relationship(
    "User",
    back_populates="conversations"
    )

    messages = relationship(
    "Message",
    back_populates="conversation"
    )
    