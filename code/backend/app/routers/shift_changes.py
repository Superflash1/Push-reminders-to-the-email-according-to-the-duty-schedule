from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import DutySchedule, ShiftChangeRecord
from app.schemas.schemas import ShiftChangeCreate, ShiftChangeRecordOut

router = APIRouter(prefix="/api/shift-changes", tags=["shift-changes"])


@router.get("", response_model=list[ShiftChangeRecordOut])
def list_shift_changes(db: Session = Depends(get_db)):
    return db.query(ShiftChangeRecord).order_by(ShiftChangeRecord.created_at.desc()).all()


@router.post("", response_model=ShiftChangeRecordOut)
def create_shift_change(payload: ShiftChangeCreate, db: Session = Depends(get_db)):
    row = db.query(DutySchedule).filter(DutySchedule.duty_date == payload.duty_date).first()
    if not row:
        raise HTTPException(status_code=404, detail="未找到该日期的值班记录")

    old_name = row.duty_person_name
    row.duty_person_name = payload.new_person_name

    rec = ShiftChangeRecord(
        duty_date=payload.duty_date,
        old_person_name=old_name,
        new_person_name=payload.new_person_name,
        reason=payload.reason,
        requested_by=payload.requested_by,
        source=payload.source,
        status="done",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
