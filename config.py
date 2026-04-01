from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MINIO_PUBLIC_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_PORT: int
    MINIO_BUCKET: str
    MINIO_USE_SSL: bool

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()