from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "moneywise-service"
    service_port: int = 8400
    environment: str = "dev"

    postgres_dsn: str = "postgresql+psycopg://moneywise:moneywise@postgres:5432/moneywise"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    jwt_secret: str = "moneywise-dev-secret"
    encryption_key: str = "moneywise-encryption-key"

    categorization_accuracy_target: float = 90.0
    report_latency_target_seconds: float = 3.0
    throughput_target_tx_per_day: int = 1_000_000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
