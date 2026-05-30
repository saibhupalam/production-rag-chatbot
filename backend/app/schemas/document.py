from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_status: str