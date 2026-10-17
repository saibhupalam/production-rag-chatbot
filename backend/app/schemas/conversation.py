from typing import Optional
from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str
    user_id: Optional[int] = None
    document_id: int


class ConversationResponse(BaseModel):
    id: int
    title: str
    document_id: Optional[int] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)