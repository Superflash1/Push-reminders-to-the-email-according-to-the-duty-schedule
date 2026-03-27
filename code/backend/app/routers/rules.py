from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import ReminderRule
from app.schemas.schemas import ReminderRuleCreate, ReminderRuleOut, ReminderRuleUpdate

router = APIRouter(prefix="/api/reminder-rules", tags=["reminder-rules"])


@router.get("", response_model=list[ReminderRuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.query(ReminderRule).order_by(ReminderRule.sort_order.asc(), ReminderRule.id.asc()).all()


@router.post("", response_model=ReminderRuleOut)
def create_rule(payload: ReminderRuleCreate, db: Session = Depends(get_db)):
    item = ReminderRule(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{rule_id}", response_model=ReminderRuleOut)
def update_rule(rule_id: int, payload: ReminderRuleUpdate, db: Session = Depends(get_db)):
    item = db.query(ReminderRule).filter(ReminderRule.id == rule_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Rule not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    item = db.query(ReminderRule).filter(ReminderRule.id == rule_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(item)
    db.commit()
    return {"ok": True}
