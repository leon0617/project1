from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Project1 API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_type: Literal["sqlite", "postgres"] = "sqlite"
    database_url: Optional[str] = None
    
    # SQLite settings (dev)
    sqlite_db_path: str = "./app.db"
    
    # PostgreSQL settings (production)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    
    # Scheduler
    scheduler_enabled: bool = False
    scheduler_timezone: str = "UTC"
    
    # Playwright
    playwright_browser: str = "chromium"
    playwright_headless: bool = True
    playwright_executable_path: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def database_connection_url(self) -> str:
        if self.database_url:
            return self.database_url
        
        if self.database_type == "sqlite":
            return f"sqlite:///{self.sqlite_db_path}"
        else:
            if not all([self.postgres_host, self.postgres_user, self.postgres_password, self.postgres_db]):
                raise ValueError("PostgreSQL credentials not fully configured")
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )


settings = Settings()
