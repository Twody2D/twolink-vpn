from app.models.node import Node
from app.services.hysteria_client.base import HysteriaClientInterface


class LocalHysteriaClient(HysteriaClientInterface):
    """No-op: the local node's Hysteria server authenticates straight against
    the backend's own database (see /internal/hysteria/authenticate), so
    there is nothing separate to push when a subscription is created or
    removed — the database row already is the answer."""

    async def add_client(self, node: Node, password: str, client_id: str) -> None:
        pass

    async def remove_client(self, node: Node, client_id: str) -> None:
        pass
