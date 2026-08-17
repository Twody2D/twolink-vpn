import httpx

from app.core.config import settings
from app.models.node import Node
from app.services.xray_client.base import XrayClientInterface


def _api_key_for(node: Node) -> str:
    """The plaintext key never lives in the database — only its hash does
    (Node.api_key_hash, for reference/audit). The usable credential lives in
    the backend's own .env, same trust boundary as every other secret here."""
    pairs = (pair.split(":", 1) for pair in settings.node_agent_api_keys.split(",") if pair)
    keys = {node_id: key for node_id, key in pairs}
    key = keys.get(node.node_id)
    if key is None:
        raise RuntimeError(f"no node-agent API key configured for node '{node.node_id}'")
    return key


class RemoteXrayClient(XrayClientInterface):
    """Talks to a remote pico-node's node-agent over HTTPS. The node-agent
    uses a self-signed certificate on the current milestone — cert
    verification is intentionally disabled here; see README for the prod
    requirement (real certificate or mTLS)."""

    async def add_client(self, node: Node, client_uuid: str, email: str) -> None:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.post(
                f"https://{node.agent_host}:{node.agent_port}/clients",
                json={"uuid": client_uuid, "email": email},
                headers={"X-Node-Api-Key": _api_key_for(node)},
            )
            response.raise_for_status()

    async def remove_client(self, node: Node, email: str) -> None:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.delete(
                f"https://{node.agent_host}:{node.agent_port}/clients/{email}",
                headers={"X-Node-Api-Key": _api_key_for(node)},
            )
            response.raise_for_status()
