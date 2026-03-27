from datetime import datetime

from jinja2 import StrictUndefined, Template


def render_template(content: str, variables: dict) -> str:
    template = Template(content, undefined=StrictUndefined)
    return template.render(**variables)


def build_default_variables() -> dict:
    return {
        "duty_date": "",
        "weekday": "",
        "duty_person_name": "",
        "duty_person_email": "",
        "rule_day_label": "",
        "rule_time": "",
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "admin_emails": "",
        "missing_reason": "",
    }
