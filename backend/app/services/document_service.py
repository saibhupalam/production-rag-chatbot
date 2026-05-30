from app.models.document import Document

def create_document( db, filename: str):
    document = Document(
        filename = filename,
        upload_status="uploaded"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document 
