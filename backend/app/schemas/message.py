from pydantic import BaseModel

class MessageResponse(BaseModel):
    id : int
    role: str
    content: str
    class config:
        from_attributes = True