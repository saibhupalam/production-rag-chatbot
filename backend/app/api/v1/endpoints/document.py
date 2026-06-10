from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends

from sqlalchemy.orm import Session

from app.utils.text_extractor import extract_text
from app.utils.chunker import chunk_text
from app.db.dependencies import get_db
from app.services.document_service import create_document

from app.services.embedding_service import (
    generate_embeddings
)

from app.services.qdrant_service import (
    store_chunks
)

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
    
    embeddings=generate_embeddings(
        chunks
    )
    
    document = create_document(
        db=db,
        filename=file.filename
    )
    
    store_chunks(
        document_id=document.id,
        chunks=chunks,
        embeddings=embeddings
    )
    
    

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": "processed",
        "chunks": len(chunks)
                
    }