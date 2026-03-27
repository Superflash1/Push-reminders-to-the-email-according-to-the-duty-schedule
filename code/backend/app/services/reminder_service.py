from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import (
    DutySchedule,
    MailTemplate,
    PersonContact,
    ReminderRule,
    SendLog,
    SystemSetting,
)
from app.services.mail_service import send_mail
from app.services.template_service import render_template


def run_reminder_once(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now()
    now_hm = now.strftime("%H:%M")

    rules = (
        db.query(ReminderRule)
        .filter(ReminderRule.enabled.is_(True), ReminderRule.trigger_time == now_hm)
        .order_by(ReminderRule.sort_order.asc(), ReminderRule.id.asc())
        .all()
    )

    setting = db.query(SystemSetting).first()
    if not setting:
        return 0

    templates = {t.template_type: t for t in db.query(MailTemplate).filter(MailTemplate.enabled.is_(True)).all()}
    duty_tpl = templates.get("DUTY_REMINDER")
    admin_tpl = templates.get("ADMIN_FALLBACK")

    processed = 0

    for rule in rules:
        biz_date = now.date() if rule.offset_day == 0 else (now.date() + timedelta(days=1))
        schedule = db.query(DutySchedule).filter(DutySchedule.duty_date == biz_date).first()
        if not schedule:
            continue

        contact = (
            db.query(PersonContact)
            .filter(
                PersonContact.person_name == schedule.duty_person_name,
                PersonContact.enabled.is_(True),
            )
            .first()
        )

        variables = {
            "duty_date": schedule.duty_date.strftime("%Y-%m-%d"),
            "weekday": schedule.weekday_text,
            "duty_person_name": schedule.duty_person_name,
            "duty_person_email": (contact.email if contact else ""),
            "rule_day_label": "当天" if rule.offset_day == 0 else "前一天",
            "rule_time": rule.trigger_time,
            "now": now.strftime("%Y-%m-%d %H:%M:%S"),
            "admin_emails": setting.admin_emails,
            "missing_reason": "未配置邮箱或邮箱已禁用",
        }

        if contact and contact.email and duty_tpl:
            _try_send_and_log(
                db=db,
                biz_date=biz_date,
                rule_id=rule.id,
                target_type="DUTY",
                to_email=contact.email,
                subject_template=duty_tpl.subject_template,
                body_template=duty_tpl.body_template,
                variables=variables,
                setting=setting,
            )
            processed += 1
        elif admin_tpl:
            for admin_email in [e.strip() for e in setting.admin_emails.split(",") if e.strip()]:
                _try_send_and_log(
                    db=db,
                    biz_date=biz_date,
                    rule_id=rule.id,
                    target_type="ADMIN",
                    to_email=admin_email,
                    subject_template=admin_tpl.subject_template,
                    body_template=admin_tpl.body_template,
                    variables=variables,
                    setting=setting,
                )
                processed += 1

    return processed


def _try_send_and_log(
    *,
    db: Session,
    biz_date,
    rule_id: int,
    target_type: str,
    to_email: str,
    subject_template: str,
    body_template: str,
    variables: dict,
    setting: SystemSetting,
):
    dedupe_key = f"{biz_date}|{rule_id}|{target_type}|{to_email}"

    subject = render_template(subject_template, variables)
    body = render_template(body_template, variables)

    try:
        send_mail(
            host=setting.mail_host,
            port=setting.mail_port,
            username=setting.mail_user,
            password=setting.mail_password,
            mail_from=setting.mail_from,
            to_email=to_email,
            subject=subject,
            body=body,
        )
        log = SendLog(
            biz_date=biz_date,
            rule_id=rule_id,
            target_type=target_type,
            to_email=to_email,
            subject=subject,
            rendered_body=body,
            status="SUCCESS",
            error_message="",
            dedupe_key=dedupe_key,
        )
        db.add(log)
        db.commit()
    except IntegrityError:
        db.rollback()
    except Exception as e:
        db.rollback()
        try:
            fail_log = SendLog(
                biz_date=biz_date,
                rule_id=rule_id,
                target_type=target_type,
                to_email=to_email,
                subject=subject,
                rendered_body=body,
                status="FAILED",
                error_message=str(e),
                dedupe_key=dedupe_key,
            )
            db.add(fail_log)
            db.commit()
        except IntegrityError:
            db.rollback()
