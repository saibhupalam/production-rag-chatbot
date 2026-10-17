from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.dependencies import get_db
from app.services.qdrant_service import check_qdrant_health

router = APIRouter()


@router.get("/health", summary="Application Health Check")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1;"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    qdrant_healthy = check_qdrant_health()
    qdrant_status = "healthy" if qdrant_healthy else "unreachable"

    overall_status = "healthy" if (db_status == "healthy" and qdrant_healthy) else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "vector_store": qdrant_status
    }