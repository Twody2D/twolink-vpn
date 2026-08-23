from abc import ABC, abstractmethod

from app.models.node import Node


class HysteriaClientInterface(ABC):
    """Unlike Xray, Hysteria2 never gets a client pushed into it — the server
    asks us for an auth decision on every connection (see api/hysteria.py).
    add/remove here just make sure the right answer exists wherever that
    check happens: nowhere for a local node (the backend's own DB is already
    the source of truth), a node-agent's cache for a remote one."""

    @abstractmethod
    async def add_client(self, node: Node, password: str, client_id: str) -> None: ...

    @abstractmethod
    async def remove_client(self, node: Node, client_id: str) -> None: ...
