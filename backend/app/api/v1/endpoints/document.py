from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends

from sqlalchemy.orm import Session

from app.utils.text_extractor import extract_text
from app.utils.chunker import chunk_text
from app.db.dependencies import get_db
from app.services.document_service import create_document

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    content = await file.read()

    text = extract_text(
    file.filename,
    content
    )
    
    chunks=chunk_text(text)
    
    document = create_document(
        db=db,
        filename=file.filename
    )
    
    

    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.upload_status,
        "characters": len(text) ,
        "preview" : text[:300],
         "chunks": len(chunks),
         "first_chunk": chunks[0]
                
    }