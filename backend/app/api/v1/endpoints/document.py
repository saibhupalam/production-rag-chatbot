from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.dependencies import get_db
from app.api.deps import get_current_user_optional
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.utils.text_extractor import extract_text
from app.utils.chunker import chunk_text
from app.rag.semantic_chunker import semantic_chunk_text
from app.services.embedding_service import generate_embeddings
from app.services.qdrant_service import store_chunks
from app.services.document_service import (
    create_document,
    update_document_status,
    get_document,
    get_documents_by_user
)

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # 1. Validate filename and extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid filename."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read content and validate size
    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )

    # 3. Extract text
    try:
        text = extract_text(file.filename, content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract text from file: {str(e)}"
        )

    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text could be extracted from the uploaded document."
        )

    user_id = current_user.id if current_user else 1

    # 4. Chunk text (Semantic chunking with fallback to recursive character splitter)
    try:
        if settings.SEMANTIC_CHUNKING_ENABLED:
            chunks = semantic_chunk_text(text)
        else:
            chunks = chunk_text(text)

        if not chunks:
            chunks = chunk_text(text)

        if not chunks:
            raise ValueError("Document yielded 0 text chunks.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk document: {str(e)}"
        )

    # 5. Create database record in 'processing' status
    document = create_document(
        db=db,
        filename=file.filename,
        user_id=user_id,
        status="processing"
    )

    # 6. Generate embeddings and store in Qdrant with rollback handling
    try:
        embeddings = generate_embeddings(chunks, is_query=False)
        store_chunks(
            document_id=document.id,
            chunks=chunks,
            embeddings=embeddings,
            user_id=user_id
        )
        update_document_status(db, document.id, status="processed")
    except Exception as e:
        update_document_status(db, document.id, status="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed during vector processing: {str(e)}"
        )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": "processed",
        "chunks": len(chunks)
    }


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    docs = get_documents_by_user(db, user_id=user_id)
    return docs


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_single_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} was not found."
        )
    if current_user and doc.user_id and doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this document."
        )
    return doc