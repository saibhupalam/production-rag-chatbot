from pydantic import BaseModel, ConfigDict
from typing import Optional


class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_status: str
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)