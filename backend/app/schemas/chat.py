from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id:str


class ChatResponse(BaseModel):
    answer: str