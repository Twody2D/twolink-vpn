from app.models.node import Node
from app.services.xray_client.base import XrayClientInterface
from app.services.xray_client.local_client import LocalXrayClient
from app.services.xray_client.remote_client import RemoteXrayClient

_local_client = LocalXrayClient()
_remote_client = RemoteXrayClient()


def get_xray_client(node: Node) -> XrayClientInterface:
    return _local_client if node.is_local else _remote_client
