from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str
    backend_internal_api_key: str
    public_base_url: str = "http://localhost:8000"


settings = Settings()
