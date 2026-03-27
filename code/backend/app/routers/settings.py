from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import SystemSetting
from app.schemas.schemas import SystemSettingOut, SystemSettingUpdate, TestMailRequest
from app.services.mail_service import send_mail

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create_setting(db: Session) -> SystemSetting:
    setting = db.query(SystemSetting).first()
    if not setting:
        setting = SystemSetting(
            admin_emails="",
            timezone="Asia/Shanghai",
            mail_host="",
            mail_port=465,
            mail_user="",
            mail_password="",
            mail_from="",
            ai_enabled=False,
            ai_base_url="",
            ai_api_key="",
            ai_model="",
            ai_temperature=20,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def _to_out(setting: SystemSetting) -> SystemSettingOut:
    return SystemSettingOut(
        id=setting.id,
        admin_emails=setting.admin_emails,
        timezone=setting.timezone,
        mail_host=setting.mail_host,
        mail_port=setting.mail_port,
        mail_user=setting.mail_user,
        mail_password=setting.mail_password,
        mail_from=setting.mail_from,
        ai_enabled=setting.ai_enabled,
        ai_base_url=setting.ai_base_url,
        ai_api_key=setting.ai_api_key,
        ai_model=setting.ai_model,
        ai_temperature=(setting.ai_temperature or 20) / 100,
    )


@router.get("", response_model=SystemSettingOut)
def get_settings(db: Session = Depends(get_db)):
    setting = _get_or_create_setting(db)
    return _to_out(setting)


@router.put("", response_model=SystemSettingOut)
def update_settings(payload: SystemSettingUpdate, db: Session = Depends(get_db)):
    setting = _get_or_create_setting(db)

    setting.admin_emails = payload.admin_emails
    setting.timezone = payload.timezone
    setting.mail_host = payload.mail_host
    setting.mail_port = payload.mail_port
    setting.mail_user = payload.mail_user
    setting.mail_password = payload.mail_password
    setting.mail_from = payload.mail_from

    setting.ai_enabled = payload.ai_enabled
    setting.ai_base_url = payload.ai_base_url.strip()
    setting.ai_api_key = payload.ai_api_key.strip()
    setting.ai_model = payload.ai_model.strip()
    setting.ai_temperature = int(max(0, min(100, round(payload.ai_temperature * 100))))

    db.commit()
    db.refresh(setting)
    return _to_out(setting)


@router.post("/test-mail")
def test_mail(payload: TestMailRequest, db: Session = Depends(get_db)):
    setting = _get_or_create_setting(db)
    send_mail(
        host=setting.mail_host,
        port=setting.mail_port,
        username=setting.mail_user,
        password=setting.mail_password,
        mail_from=setting.mail_from,
        to_email=str(payload.to_email),
        subject="[测试] 值班提醒系统",
        body="这是一封测试邮件，表示 SMTP 配置可用。",
    )
    return {"ok": True}
