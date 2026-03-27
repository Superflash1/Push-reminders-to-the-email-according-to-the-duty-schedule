from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import MailTemplate
from app.schemas.schemas import (
    MailTemplateOut,
    MailTemplateUpdate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from app.services.template_service import render_template

router = APIRouter(prefix="/api/mail-templates", tags=["mail-templates"])


@router.get("", response_model=list[MailTemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(MailTemplate).order_by(MailTemplate.template_type.asc()).all()


@router.put("/{template_type}", response_model=MailTemplateOut)
def update_template(template_type: str, payload: MailTemplateUpdate, db: Session = Depends(get_db)):
    item = db.query(MailTemplate).filter(MailTemplate.template_type == template_type).first()
    if not item:
        raise HTTPException(status_code=404, detail="Template not found")

    item.subject_template = payload.subject_template
    item.body_template = payload.body_template
    item.enabled = payload.enabled

    db.commit()
    db.refresh(item)
    return item


@router.post("/preview", response_model=TemplatePreviewResponse)
def preview_template(payload: TemplatePreviewRequest):
    return TemplatePreviewResponse(
        subject=render_template(payload.subject_template, payload.variables),
        body=render_template(payload.body_template, payload.variables),
    )
