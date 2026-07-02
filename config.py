from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "voting_system"
    db_user: str = "root"
    db_password: str = ""
    db_pool_size: int = 25
    db_pool_connection_timeout: int = 30

    jwt_secret: str = "your-super-secret-key-change-this-in-env"  # noqa: S105
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    upload_dir: str = "uploads"
    log_level: str = "INFO"
    environment: str = "development"

    sentry_dsn: str | None = None
    breach_check_enabled: bool = True

    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "voting_system"

    s3_bucket: str | None = None
    s3_region: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @model_validator(mode="after")
    def enforce_jwt_secret_in_production(self):
        if (
            self.environment == "production"
            and self.jwt_secret == "your-super-secret-key-change-this-in-env"  # noqa: S105
        ):
            raise ValueError("JWT_SECRET must be changed from the default value in production")
        return self


settings = Settings()
