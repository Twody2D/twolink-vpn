from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Node(Base, TimestampMixin):
    """A single Xray server — either co-located with the backend (is_local)
    or a remote pico-node managed over HTTPS via its node-agent. Subscriptions
    reference nodes by node_id so the backend can manage and serve configs
    for a whole fleet, not just one hardcoded server."""

    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)

    vless_port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    ss_port: Mapped[int] = mapped_column(Integer, nullable=False, default=8388)

    # Where the backend reaches this node's Xray gRPC management API.
    # For a local node this is the "xray" service DNS name on the shared
    # docker network; for a remote node it's meaningless (remote nodes are
    # only reachable through their node-agent, never directly).
    xray_api_host: Mapped[str] = mapped_column(String(255), nullable=False)
    xray_api_port: Mapped[int] = mapped_column(Integer, nullable=False, default=10085)

    reality_public_key: Mapped[str] = mapped_column(String(64), nullable=False)
    reality_short_id: Mapped[str] = mapped_column(String(16), nullable=False)
    reality_server_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # True for the single node co-located with the backend (in-process/docker
    # network access to Xray). False for remote pico-nodes, which are only
    # reachable through their node-agent over HTTPS with their own API key.
    is_local: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # SHA-256 hex digest of the node-agent's API key — never the plaintext key.
    # The plaintext key itself lives only in the backend's own .env
    # (NODE_AGENT_API_KEYS), the same trust boundary as every other secret in
    # this project — this hash is a reference/audit value, not the credential
    # used to authenticate requests. Null for local nodes.
    api_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Where the backend reaches this node's node-agent over HTTPS. Null for
    # local nodes, which are never contacted through node-agent.
    agent_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Operational health, distinct from is_active (admin-controlled "accept
    # new users on this node or not"): "online" | "offline" | "unknown".
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")

    max_users: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
