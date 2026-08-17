from abc import ABC, abstractmethod

from app.models.node import Node


class XrayClientInterface(ABC):
    """Business logic (subscription provisioning) talks only to this
    interface and never knows whether a node is local or remote."""

    @abstractmethod
    async def add_client(self, node: Node, client_uuid: str, email: str) -> None: ...

    @abstractmethod
    async def remove_client(self, node: Node, email: str) -> None: ...
