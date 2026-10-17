from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.api.v1.endpoints import document
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import conversation
from app.api.v1.endpoints import auth

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"]
)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)
api_router.include_router(
    document.router,
    tags=["Documents"]
)
api_router.include_router(
    conversation.router,
    tags=["Conversations"]
)
api_router.include_router(
    chat.router,
    tags=["Chat"]
)