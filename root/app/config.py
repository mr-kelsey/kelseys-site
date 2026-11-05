from pydantic_settings import BaseSettings, SettingsConfigDict


class SiteConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_path: str = "data/app.db"
    session_secret: str | None = None
    admin_password: str | None = None
