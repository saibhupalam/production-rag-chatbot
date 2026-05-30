from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends

from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.document_service import create_document

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    document = create_document(
        db=db,
        filename=file.filename
    )

    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.upload_status
    }