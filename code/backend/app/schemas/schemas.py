from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class DutyScheduleOut(BaseModel):
    id: int
    duty_date: date
    weekday_text: str
    duty_person_name: str
    source_sheet: str

    class Config:
        from_attributes = True


class DutyScheduleCreate(BaseModel):
    duty_date: date
    weekday_text: str = ""
    duty_person_name: str
    source_sheet: str = "manual"


class DutyScheduleUpdate(BaseModel):
    duty_date: date | None = None
    weekday_text: str | None = None
    duty_person_name: str | None = None
    source_sheet: str | None = None


class DutyScheduleBatchDeleteRequest(BaseModel):
    ids: list[int]


class DutyScheduleBatchDeleteResponse(BaseModel):
    deleted: int


class PersonContactBase(BaseModel):
    person_name: str
    email: str = ""
    enabled: bool = True
    remark: str = ""


class PersonContactCreate(PersonContactBase):
    pass


class PersonContactUpdate(BaseModel):
    person_name: str | None = None
    email: str | None = None
    enabled: bool | None = None
    remark: str | None = None


class PersonContactOut(PersonContactBase):
    id: int

    class Config:
        from_attributes = True


class ReminderRuleBase(BaseModel):
    offset_day: int
    trigger_time: str
    enabled: bool = True
    sort_order: int = 0


class ReminderRuleCreate(ReminderRuleBase):
    pass


class ReminderRuleUpdate(BaseModel):
    offset_day: int | None = None
    trigger_time: str | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class ReminderRuleOut(ReminderRuleBase):
    id: int

    class Config:
        from_attributes = True


class MailTemplateUpdate(BaseModel):
    subject_template: str
    body_template: str
    enabled: bool = True


class MailTemplateOut(BaseModel):
    id: int
    template_type: str
    subject_template: str
    body_template: str
    enabled: bool

    class Config:
        from_attributes = True


class SystemSettingUpdate(BaseModel):
    admin_emails: str
    timezone: str = "Asia/Shanghai"
    mail_host: str = ""
    mail_port: int = 465
    mail_user: str = ""
    mail_password: str = ""
    mail_from: str = ""

    ai_enabled: bool = False
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_temperature: float = 0.2


class SystemSettingOut(SystemSettingUpdate):
    id: int

    class Config:
        from_attributes = True


class SendLogOut(BaseModel):
    id: int
    biz_date: date
    rule_id: int
    target_type: str
    to_email: str
    subject: str
    rendered_body: str
    status: str
    error_message: str
    dedupe_key: str
    created_at: datetime

    class Config:
        from_attributes = True


class ShiftChangeRecordOut(BaseModel):
    id: int
    duty_date: date
    old_person_name: str
    new_person_name: str
    reason: str
    requested_by: str
    source: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ShiftChangeCreate(BaseModel):
    duty_date: date
    new_person_name: str
    reason: str = ""
    requested_by: str = "manual"
    source: str = "manual"


class TemplatePreviewRequest(BaseModel):
    subject_template: str
    body_template: str
    variables: dict


class TemplatePreviewResponse(BaseModel):
    subject: str
    body: str


class TestMailRequest(BaseModel):
    to_email: EmailStr


class RunOnceResponse(BaseModel):
    processed_rules: int
    message: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
