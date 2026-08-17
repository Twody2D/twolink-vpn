from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str
    backend_internal_api_key: str
    public_base_url: str = "http://localhost:8000"

    # Local node bootstrap (used only to seed the "nodes" table on startup).
    node_id: str
    node_host: str
    xray_vless_port: int
    xray_api_port: int
    reality_public_key: str
    reality_short_id: str
    reality_server_names: str


settings = Settings()
