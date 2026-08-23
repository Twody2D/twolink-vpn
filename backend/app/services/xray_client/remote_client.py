import httpx

from app.models.node import Node
from app.services.node_agent_auth import api_key_for
from app.services.xray_client.base import XrayClientInterface


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
                headers={"X-Node-Api-Key": api_key_for(node)},
            )
            response.raise_for_status()

    async def remove_client(self, node: Node, email: str) -> None:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.delete(
                f"https://{node.agent_host}:{node.agent_port}/clients/{email}",
                headers={"X-Node-Api-Key": api_key_for(node)},
            )
            response.raise_for_status()
