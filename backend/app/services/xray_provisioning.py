from xtlsapi import XrayClient
from xtlsapi.exceptions import EmailAlreadyExists, EmailNotFound

from app.models.node import Node

VLESS_INBOUND_TAG = "vless-reality"
VLESS_FLOW = "xtls-rprx-vision"


def _client_for(node: Node) -> XrayClient:
    return XrayClient(node.xray_api_host, node.xray_api_port)


def add_vless_client(node: Node, client_uuid: str, email: str) -> None:
    """Adds a client to the running Xray instance via its gRPC HandlerService —
    no config file edit or restart, so existing connections are unaffected."""
    client = _client_for(node)
    try:
        client.add_client(VLESS_INBOUND_TAG, client_uuid, email, protocol="vless", flow=VLESS_FLOW)
    except EmailAlreadyExists:
        pass


def remove_vless_client(node: Node, email: str) -> None:
    client = _client_for(node)
    try:
        client.remove_client(VLESS_INBOUND_TAG, email)
    except EmailNotFound:
        pass
