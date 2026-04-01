from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Dùng Optional để cho phép các biến này có thể bị bỏ trống (None)
    MINIO_PUBLIC_URL: Optional[str] = None
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_PORT: Optional[int] = None
    MINIO_BUCKET: Optional[str] = None
    MINIO_USE_SSL: Optional[bool] = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()