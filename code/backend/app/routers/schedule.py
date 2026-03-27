import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import DutySchedule
from app.schemas.schemas import (
    DutyScheduleBatchDeleteRequest,
    DutyScheduleBatchDeleteResponse,
    DutyScheduleCreate,
    DutyScheduleOut,
    DutyScheduleUpdate,
)
from app.services.excel_import_service import import_schedule_from_excel

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("/import")
def import_schedule(file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        return import_schedule_from_excel(tmp_path, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="导入失败：存在重复日期，请检查 Excel 中同一天是否出现多次")
    finally:
        try:
            file.file.close()
        except Exception:
            pass

        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except PermissionError:
                pass


@router.get("", response_model=list[DutyScheduleOut])
def list_schedule(db: Session = Depends(get_db)):
    return db.query(DutySchedule).order_by(DutySchedule.duty_date.asc()).all()


@router.post("", response_model=DutyScheduleOut)
def create_schedule(payload: DutyScheduleCreate, db: Session = Depends(get_db)):
    conflict = db.query(DutySchedule).filter(DutySchedule.duty_date == payload.duty_date).first()
    if conflict:
        raise HTTPException(status_code=400, detail="该日期已存在值班记录")

    item = DutySchedule(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{schedule_id}", response_model=DutyScheduleOut)
def update_schedule(schedule_id: int, payload: DutyScheduleUpdate, db: Session = Depends(get_db)):
    item = db.query(DutySchedule).filter(DutySchedule.id == schedule_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule not found")

    data = payload.model_dump(exclude_unset=True)
    if "duty_date" in data:
        new_date = data["duty_date"]
        conflict = (
            db.query(DutySchedule)
            .filter(DutySchedule.duty_date == new_date, DutySchedule.id != schedule_id)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=400, detail="该日期已存在值班记录")

    for k, v in data.items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)
    return item


@router.post("/batch-delete", response_model=DutyScheduleBatchDeleteResponse)
def batch_delete_schedule(payload: DutyScheduleBatchDeleteRequest, db: Session = Depends(get_db)):
    ids = [i for i in payload.ids if isinstance(i, int)]
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要删除的记录")

    deleted = db.query(DutySchedule).filter(DutySchedule.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    item = db.query(DutySchedule).filter(DutySchedule.id == schedule_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(item)
    db.commit()
    return {"ok": True}
