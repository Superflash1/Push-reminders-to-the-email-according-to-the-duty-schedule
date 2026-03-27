from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.scheduler import start_scheduler, stop_scheduler
from app.models.models import MailTemplate, ReminderRule, SystemSetting
from app.routers import (
    ai_chat,
    contacts,
    logs,
    reminders,
    rules,
    schedule,
    settings as settings_router,
    shift_changes,
    templates,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_schema_if_needed()
    _seed_initial_data()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schedule.router)
app.include_router(contacts.router)
app.include_router(rules.router)
app.include_router(templates.router)
app.include_router(settings_router.router)
app.include_router(logs.router)
app.include_router(reminders.router)
app.include_router(shift_changes.router)
app.include_router(ai_chat.router)

WEB_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")


@app.get("/")
def root_or_health():
    index_file = WEB_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"name": settings.app_name, "status": "ok"}


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if full_path.startswith("api"):
        return {"detail": "Not Found"}

    index_file = WEB_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return {"name": settings.app_name, "status": "ok"}


def _migrate_schema_if_needed():
    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(system_settings)")).fetchall()
        }

        if "ai_enabled" not in cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN ai_enabled INTEGER DEFAULT 0"))
        if "ai_base_url" not in cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN ai_base_url TEXT DEFAULT ''"))
        if "ai_api_key" not in cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN ai_api_key TEXT DEFAULT ''"))
        if "ai_model" not in cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN ai_model TEXT DEFAULT ''"))
        if "ai_temperature" not in cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN ai_temperature INTEGER DEFAULT 20"))


def _seed_initial_data():
    db = SessionLocal()
    try:
        if not db.query(SystemSetting).first():
            db.add(
                SystemSetting(
                    admin_emails="",
                    timezone="Asia/Shanghai",
                    mail_host=settings.mail_host,
                    mail_port=settings.mail_port,
                    mail_user=settings.mail_user,
                    mail_password=settings.mail_password,
                    mail_from=settings.mail_from,
                    ai_enabled=False,
                    ai_base_url="",
                    ai_api_key="",
                    ai_model="",
                    ai_temperature=20,
                )
            )

        existing_types = {x.template_type for x in db.query(MailTemplate).all()}
        if "DUTY_REMINDER" not in existing_types:
            db.add(
                MailTemplate(
                    template_type="DUTY_REMINDER",
                    subject_template="[值班提醒] {{duty_date}} {{duty_person_name}}",
                    body_template=(
                        "您好 {{duty_person_name}}，\n"
                        "您在 {{duty_date}}（{{weekday}}）值班。\n"
                        "提醒规则：{{rule_day_label}} {{rule_time}}。\n"
                        "发送时间：{{now}}"
                    ),
                    enabled=True,
                )
            )

        if "ADMIN_FALLBACK" not in existing_types:
            db.add(
                MailTemplate(
                    template_type="ADMIN_FALLBACK",
                    subject_template="[管理员告警] {{duty_date}} 值班人无可用邮箱",
                    body_template=(
                        "值班人 {{duty_person_name}} 在 {{duty_date}}（{{weekday}}）无可用邮箱。\n"
                        "触发点：{{rule_day_label}} {{rule_time}}。\n"
                        "原因：{{missing_reason}}。\n"
                        "管理员：{{admin_emails}}。\n"
                        "发送时间：{{now}}"
                    ),
                    enabled=True,
                )
            )

        if db.query(ReminderRule).count() == 0:
            db.add(ReminderRule(offset_day=-1, trigger_time="18:00", enabled=True, sort_order=1))
            db.add(ReminderRule(offset_day=0, trigger_time="09:00", enabled=True, sort_order=2))

        db.commit()
    finally:
        db.close()
