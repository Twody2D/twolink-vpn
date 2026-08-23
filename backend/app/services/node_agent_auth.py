from app.core.config import settings
from app.models.node import Node


def api_key_for(node: Node) -> str:
    """The plaintext key never lives in the database — only its hash does
    (Node.api_key_hash, for reference/audit). The usable credential lives in
    the backend's own .env, same trust boundary as every other secret here.
    Shared by every client that talks to a remote pico-node's node-agent
    (Xray, Hysteria2, ...)."""
    pairs = (pair.split(":", 1) for pair in settings.node_agent_api_keys.split(",") if pair)
    keys = {node_id: key for node_id, key in pairs}
    key = keys.get(node.node_id)
    if key is None:
        raise RuntimeError(f"no node-agent API key configured for node '{node.node_id}'")
    return key
