from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # This node's own secret — generated once when the node is provisioned,
    # never derived from or stored as plaintext in the backend's database.
    node_api_key: str

    # Defense-in-depth alongside the API key: only accept requests that
    # claim to come from the main server's IP(s). Comma-separated; empty
    # disables the IP check (not recommended outside local dev).
    allowed_backend_ips: str = ""

    xray_api_host: str = "xray"
    xray_api_port: int = 10085


settings = Settings()
