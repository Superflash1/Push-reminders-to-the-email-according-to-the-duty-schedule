from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DutySchedule(Base):
    __tablename__ = "duty_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    duty_date: Mapped[datetime.date] = mapped_column(Date, unique=True, nullable=False)
    weekday_text: Mapped[str] = mapped_column(Text, default="")
    duty_person_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_sheet: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class PersonContact(Base):
    __tablename__ = "person_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    person_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ReminderRule(Base):
    __tablename__ = "reminder_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    offset_day: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_time: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class MailTemplate(Base):
    __tablename__ = "mail_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_type: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    subject_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_emails: Mapped[str] = mapped_column(Text, default="")
    timezone: Mapped[str] = mapped_column(Text, default="Asia/Shanghai")
    mail_host: Mapped[str] = mapped_column(Text, default="")
    mail_port: Mapped[int] = mapped_column(Integer, default=465)
    mail_user: Mapped[str] = mapped_column(Text, default="")
    mail_password: Mapped[str] = mapped_column(Text, default="")
    mail_from: Mapped[str] = mapped_column(Text, default="")

    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_base_url: Mapped[str] = mapped_column(Text, default="")
    ai_api_key: Mapped[str] = mapped_column(Text, default="")
    ai_model: Mapped[str] = mapped_column(Text, default="")
    ai_temperature: Mapped[int] = mapped_column(Integer, default=20)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class SendLog(Base):
    __tablename__ = "send_logs"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_send_logs_dedupe_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    biz_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    rule_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    to_email: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    rendered_body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="")
    dedupe_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ShiftChangeRecord(Base):
    __tablename__ = "shift_change_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    duty_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    old_person_name: Mapped[str] = mapped_column(Text, nullable=False)
    new_person_name: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    requested_by: Mapped[str] = mapped_column(Text, default="AI")
    source: Mapped[str] = mapped_column(Text, default="ai_chat")
    status: Mapped[str] = mapped_column(Text, default="done")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
