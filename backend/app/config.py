from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Job Tracker MVP"

    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field("job_tracker", alias="MONGODB_DB")
    mongodb_collection: str = Field("jobs", alias="MONGODB_COLLECTION")

    google_client_id: str = Field(..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        "http://localhost:8000/api/gmail/oauth/callback",
        alias="GOOGLE_REDIRECT_URI",
    )
    gmail_query: str = Field(
        "(subject:(job OR opportunity OR application) newer_than:30d)",
        alias="GMAIL_SEARCH_QUERY",
    )
    gmail_max_results: int = Field(20, alias="GMAIL_MAX_RESULTS")
    gmail_token_path: str = Field(".gmail_token.json", alias="GMAIL_TOKEN_PATH")
    gmail_scopes: str = Field(
        "https://www.googleapis.com/auth/gmail.readonly",
        alias="GMAIL_SCOPES",
    )

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")

    scheduler_interval_minutes: int = Field(60, alias="SCHEDULER_INTERVAL_MINUTES")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
