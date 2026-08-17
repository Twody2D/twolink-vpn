from starlette.concurrency import run_in_threadpool
from xtlsapi import XrayClient as XtlsClient
from xtlsapi.exceptions import EmailAlreadyExists, EmailNotFound

from app.models.node import Node
from app.services.xray_client.base import XrayClientInterface

VLESS_INBOUND_TAG = "vless-reality"
VLESS_FLOW = "xtls-rprx-vision"


class LocalXrayClient(XrayClientInterface):
    """Talks to Xray's gRPC HandlerService directly over the internal docker
    network — no config file edit or restart. Used for the node co-located
    with the backend (node.is_local)."""

    async def add_client(self, node: Node, client_uuid: str, email: str) -> None:
        client = XtlsClient(node.xray_api_host, node.xray_api_port)
        try:
            await run_in_threadpool(
                client.add_client, VLESS_INBOUND_TAG, client_uuid, email, protocol="vless", flow=VLESS_FLOW
            )
        except EmailAlreadyExists:
            pass

    async def remove_client(self, node: Node, email: str) -> None:
        client = XtlsClient(node.xray_api_host, node.xray_api_port)
        try:
            await run_in_threadpool(client.remove_client, VLESS_INBOUND_TAG, email)
        except EmailNotFound:
            pass
