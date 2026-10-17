from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.document import Document


def create_document(
    db: Session,
    filename: str,
    user_id: Optional[int] = None,
    status: str = "processing"
) -> Document:
    """Create a new document record with an initial processing status."""
    document = Document(
        filename=filename,
        upload_status=status,
        user_id=user_id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document_status(
    db: Session,
    document_id: int,
    status: str
) -> Optional[Document]:
    """Update processing status of a document (e.g. 'processed', 'failed')."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        document.upload_status = status
        db.commit()
        db.refresh(document)
    return document


def get_document(
    db: Session,
    document_id: int
) -> Optional[Document]:
    """Retrieve document by ID."""
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents_by_user(
    db: Session,
    user_id: int
) -> List[Document]:
    """Retrieve all documents owned by user."""
    return db.query(Document).filter(Document.user_id == user_id).all()


def delete_document(
    db: Session,
    document_id: int
) -> Optional[Document]:
    """Delete document and its associations."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        db.delete(document)
        db.commit()
    return document
