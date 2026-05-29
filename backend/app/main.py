from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User 
from app.models import *

Base.metadata.create_all(bind=engine)

app=FastAPI(
    title=settings.PROJECT_NAME
)

app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

@app.get('/')
async def root():
    return {"message": "Production RAG Chatbot API Running"}