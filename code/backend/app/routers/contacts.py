from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import DutySchedule, PersonContact
from app.schemas.schemas import PersonContactCreate, PersonContactOut, PersonContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[PersonContactOut])
def list_contacts(db: Session = Depends(get_db)):
    # 自动从值班表补齐联系人姓名（邮箱先留空，后续可人工维护）
    schedule_names = {
        (name or "").strip()
        for (name,) in db.query(DutySchedule.duty_person_name)
        .filter(DutySchedule.duty_person_name.isnot(None))
        .all()
    }
    schedule_names.discard("")

    existing_names = {
        (name or "").strip()
        for (name,) in db.query(PersonContact.person_name)
        .filter(PersonContact.person_name.isnot(None))
        .all()
    }

    missing_names = [name for name in schedule_names if name not in existing_names]
    if missing_names:
        for name in sorted(missing_names):
            db.add(PersonContact(person_name=name, email="", enabled=True, remark=""))
        db.commit()

    return db.query(PersonContact).order_by(PersonContact.person_name.asc()).all()


@router.post("", response_model=PersonContactOut)
def create_contact(payload: PersonContactCreate, db: Session = Depends(get_db)):
    item = PersonContact(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{contact_id}", response_model=PersonContactOut)
def update_contact(contact_id: int, payload: PersonContactUpdate, db: Session = Depends(get_db)):
    item = db.query(PersonContact).filter(PersonContact.id == contact_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Contact not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    item = db.query(PersonContact).filter(PersonContact.id == contact_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(item)
    db.commit()
    return {"ok": True}
