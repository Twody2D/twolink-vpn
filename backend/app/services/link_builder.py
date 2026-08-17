from urllib.parse import quote

from app.models.node import Node
from app.models.subscription import Subscription


def build_vless_link(subscription: Subscription, node: Node) -> str:
    """Builds a vless:// share link for one subscription on one node.
    Reality parameters come entirely from the node row, which mirrors the
    node's own .env — nothing here is hardcoded to a single server."""

    params = {
        "encryption": "none",
        "security": "reality",
        "sni": node.reality_server_name,
        "fp": "chrome",
        "pbk": node.reality_public_key,
        "sid": node.reality_short_id,
        "type": "tcp",
        "flow": "xtls-rprx-vision",
    }
    query = "&".join(f"{key}={quote(str(value), safe='')}" for key, value in params.items())
    label = quote(f"TwoLink-{node.name}", safe="")

    return f"vless://{subscription.vless_uuid}@{node.host}:{node.vless_port}?{query}#{label}"
