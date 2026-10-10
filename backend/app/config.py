import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Sentinel"
    APP_SUBTITLE: str = "Privileged Access Monitoring Tool"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "sentinel-super-secret-production-and-demo-key-at-least-32-chars-long"
    
    # Database
    DATABASE_PATH: str = os.getenv("SENTINEL_DB_PATH", "./sentinel.db")
    
    # Session & Security
    SESSION_COOKIE_NAME: str = "sentinel_session"
    CSRF_COOKIE_NAME: str = "sentinel_csrf"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    COOKIE_SECURE: bool = os.getenv("SENTINEL_COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
    COOKIE_SAMESITE: str = "lax"
    SESSION_EXPIRE_HOURS: int = int(os.getenv("SENTINEL_DEMO_EXPIRE_HOURS", "24"))
    
    # Ingestion limits
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    MAX_UPLOAD_ROWS: int = 10000
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Root paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ROOT_DIR: Path = BASE_DIR.parent
    
    @property
    def sqlite_url(self) -> str:
        db_path = Path(self.DATABASE_PATH).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.as_posix()}"

    class Config:
        env_prefix = "SENTINEL_"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
