from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
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
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )
    
    conversations=relationship(
        "Conversation",
        back_populates="user"
    )
    
    documents = relationship(
    "Document",
    back_populates="user"
    )