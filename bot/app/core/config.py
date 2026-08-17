from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    backend_internal_api_key: str
    backend_internal_url: str = "http://backend:8000"
    public_base_url: str = "http://localhost:8000"
    node_id: str


settings = Settings()
