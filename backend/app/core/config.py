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

    # Set only after the hysteria container has printed its fingerprint once
    # (see hysteria/entrypoint.sh) and it's been copied into .env — same
    # bootstrap pattern as the Reality keys above.
    hysteria_port: int | None = None
    hysteria_cert_fingerprint: str | None = None

    # Plaintext API keys for remote pico-nodes' node-agents, format
    # "node_id:key,node_id2:key2". Never stored in the database — see
    # app/services/xray_client/remote_client.py.
    node_agent_api_keys: str = ""


settings = Settings()
