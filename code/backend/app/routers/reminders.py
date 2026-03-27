from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import RunOnceResponse
from app.services.reminder_service import run_reminder_once

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("/run-once", response_model=RunOnceResponse)
def run_once(db: Session = Depends(get_db)):
    processed = run_reminder_once(db)
    return RunOnceResponse(processed_rules=processed, message="done")
