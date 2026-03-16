"""Environment-based application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configurable knobs, overridable via .env or environment variables."""

    model_path: str = "./models/minehelper-v1"
    device: str = "cpu"
    # Keep generation bounded for API responsiveness.
    max_tokens: int = 20000
    generation_timeout_seconds: float = 30.0
    max_retries: int = 2
    host: str = "0.0.0.0"
    port: int = 1298

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
