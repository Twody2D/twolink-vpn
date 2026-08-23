import httpx

from app.models.node import Node
from app.services.hysteria_client.base import HysteriaClientInterface
from app.services.node_agent_auth import api_key_for


class RemoteHysteriaClient(HysteriaClientInterface):
    """Pushes the credential into a remote pico-node's node-agent, which
    caches it locally so the node's own Hysteria server can authenticate
    against it without either side calling out over the internet on every
    connection. Same self-signed-cert tradeoff as RemoteXrayClient — see
    README for the prod requirement (real certificate or mTLS)."""

    async def add_client(self, node: Node, password: str, client_id: str) -> None:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.post(
                f"https://{node.agent_host}:{node.agent_port}/hysteria/users",
                json={"password": password, "client_id": client_id},
                headers={"X-Node-Api-Key": api_key_for(node)},
            )
            response.raise_for_status()

    async def remove_client(self, node: Node, client_id: str) -> None:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.delete(
                f"https://{node.agent_host}:{node.agent_port}/hysteria/users/{client_id}",
                headers={"X-Node-Api-Key": api_key_for(node)},
            )
            response.raise_for_status()
