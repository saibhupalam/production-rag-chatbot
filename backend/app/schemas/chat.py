from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    document_id: int


class ChatResponse(BaseModel):
    answer: str