from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_db_host: str
    app_db_port: int
    app_db_name: str
    app_db_user: str
    app_db_password: str

    session_secret_key: str = "dev-only-change-me"
    admin_username: str = "admin"
    admin_password: str = "admin1234"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.app_db_user}:{self.app_db_password}"
            f"@{self.app_db_host}:{self.app_db_port}/{self.app_db_name}"
        )


settings = Settings()
