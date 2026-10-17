from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str

    model_config = ConfigDict(from_attributes=True)