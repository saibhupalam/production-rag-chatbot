from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String,
        nullable=True
    )

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all,delete-orphan"
    )

    documents = relationship(
        "Document",
        back_populates="user",
        cascade="all,delete-orphan"
    )