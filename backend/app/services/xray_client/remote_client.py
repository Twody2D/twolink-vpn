from app.models.node import Node
from app.services.xray_client.base import XrayClientInterface


class RemoteXrayClient(XrayClientInterface):
    """Talks to a remote pico-node's node-agent over HTTPS. Not implemented
    yet — the node-agent service and its API contract land in a later step."""

    async def add_client(self, node: Node, client_uuid: str, email: str) -> None:
        raise NotImplementedError("remote node-agent client is not implemented yet")

    async def remove_client(self, node: Node, email: str) -> None:
        raise NotImplementedError("remote node-agent client is not implemented yet")
