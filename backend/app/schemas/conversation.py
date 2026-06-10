from pydantic import BaseModel


class ConversationCreate(BaseModel):

    title: str

    user_id: int

    document_id: int


class ConversationResponse(BaseModel):

    id: int

    title: str

    class Config:
        from_attributes = True