import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr


def send_mail(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    mail_from: str,
    to_email: str,
    subject: str,
    body: str,
) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr(("Duty Reminder", mail_from))
    msg["To"] = to_email
    msg["Subject"] = subject

    with smtplib.SMTP_SSL(host, port) as server:
        if username and password:
            server.login(username, password)
        server.sendmail(mail_from, [to_email], msg.as_string())
