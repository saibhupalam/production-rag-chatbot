from typing import Union
from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    question: str
    conversation_id: Union[int, str]

    @field_validator("conversation_id")
    @classmethod
    def parse_conversation_id(cls, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("conversation_id must be an integer or integer string")


class ChatResponse(BaseModel):
    answer: str