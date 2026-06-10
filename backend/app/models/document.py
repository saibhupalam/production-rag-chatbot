from sqlalchemy import Column,Integer, String ,ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    
    id=Column(
        Integer,
        primary_key=True,
        index=True)
    
    filename=Column(
        String, 
        nullable=False)
    
    upload_status= Column(
        String, 
        default='processing')
    
    user_id=Column(
        Integer,
        ForeignKey("users.id")    
    ) 
    
    conversations= relationship(
        "Conversation",
        back_populates="document"
    )
    
    user = relationship(
    "User",
    back_populates="documents"
    )
    