from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import SendLog
from app.schemas.schemas import SendLogOut

router = APIRouter(prefix="/api/send-logs", tags=["send-logs"])


@router.get("", response_model=list[SendLogOut])
def list_logs(db: Session = Depends(get_db)):
    return db.query(SendLog).order_by(SendLog.created_at.desc()).limit(500).all()
