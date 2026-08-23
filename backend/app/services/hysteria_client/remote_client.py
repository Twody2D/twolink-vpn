from app.models.node import Node
from app.services.hysteria_client.base import HysteriaClientInterface


class RemoteHysteriaClient(HysteriaClientInterface):
    """Pushes the credential into a remote pico-node's node-agent, which
    caches it locally so the node's own Hysteria server can authenticate
    against it without either side calling out over the internet on every
    connection. Not implemented yet — lands with node-agent's /hysteria/users
    endpoint in a later step."""

    async def add_client(self, node: Node, password: str, client_id: str) -> None:
        raise NotImplementedError("remote node-agent Hysteria client is not implemented yet")

    async def remove_client(self, node: Node, client_id: str) -> None:
        raise NotImplementedError("remote node-agent Hysteria client is not implemented yet")
