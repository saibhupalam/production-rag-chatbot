from sqlalchemy import Column,Integer, String
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"
    
    id=Column(Integer,primary_key=True,index=True)
    filename=Column(String, nullable=False)
    upload_status= Column(String, default='processing')
     
    