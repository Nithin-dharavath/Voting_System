from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "voting_system"
    db_user: str = "root"
    db_password: str = ""
    db_pool_size: int = 5

    jwt_secret: str = "your-super-secret-key-change-this-in-env"  # noqa: S105
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    upload_dir: str = "uploads"
    log_level: str = "INFO"
    environment: str = "development"

    sentry_dsn: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
