from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    API_PREFIX: str = Field(default="/api")
    APP_DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./backend/database.db"

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:4173"

    OPENAI_API_KEY: str = ""

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
