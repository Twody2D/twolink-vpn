from app.models.node import Node
from app.services.hysteria_client.base import HysteriaClientInterface
from app.services.hysteria_client.local_client import LocalHysteriaClient
from app.services.hysteria_client.remote_client import RemoteHysteriaClient

_local_client = LocalHysteriaClient()
_remote_client = RemoteHysteriaClient()


def get_hysteria_client(node: Node) -> HysteriaClientInterface:
    return _local_client if node.is_local else _remote_client
