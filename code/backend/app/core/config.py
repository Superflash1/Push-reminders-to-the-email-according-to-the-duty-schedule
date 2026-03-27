from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Duty Reminder"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    sqlite_path: str = "./duty_reminder.db"
    timezone: str = "Asia/Shanghai"

    mail_host: str = ""
    mail_port: int = 465
    mail_user: str = ""
    mail_password: str = ""
    mail_from: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()