from pydantic_settings import BaseSettings, SettingsConfigDict


class SiteConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_path: str = "data/app.db"
    resend_api_key: str | None = None
    contact_to_email: str | None = None
    session_secret: str | None = None
    admin_password: str | None = None
