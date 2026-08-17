from xtlsapi import XrayClient
from xtlsapi.exceptions import EmailAlreadyExists, EmailNotFound

from app.core.config import settings

VLESS_INBOUND_TAG = "vless-reality"
VLESS_FLOW = "xtls-rprx-vision"


def _client() -> XrayClient:
    return XrayClient(settings.xray_api_host, settings.xray_api_port)


def add_client(client_uuid: str, email: str) -> None:
    try:
        _client().add_client(VLESS_INBOUND_TAG, client_uuid, email, protocol="vless", flow=VLESS_FLOW)
    except EmailAlreadyExists:
        pass


def remove_client(email: str) -> None:
    try:
        _client().remove_client(VLESS_INBOUND_TAG, email)
    except EmailNotFound:
        pass


def get_metrics() -> dict:
    client = _client()
    return {
        "uplink_bytes": client.get_inbound_upload_traffic(VLESS_INBOUND_TAG),
        "downlink_bytes": client.get_inbound_download_traffic(VLESS_INBOUND_TAG),
    }
