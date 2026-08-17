from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Node(Base, TimestampMixin):
    """A single Xray server. Subscriptions reference nodes by node_id so the
    backend can manage and serve configs for multiple servers, not just one."""

    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)

    vless_port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    ss_port: Mapped[int] = mapped_column(Integer, nullable=False, default=8388)

    # Where the backend reaches this node's Xray gRPC management API.
    # For a node co-located with the backend (same docker-compose project)
    # this is the "xray" service DNS name; for a remote node it would be a
    # private/VPN address the backend can reach — never the public client host.
    xray_api_host: Mapped[str] = mapped_column(String(255), nullable=False)
    xray_api_port: Mapped[int] = mapped_column(Integer, nullable=False, default=10085)

    reality_public_key: Mapped[str] = mapped_column(String(64), nullable=False)
    reality_short_id: Mapped[str] = mapped_column(String(16), nullable=False)
    reality_server_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
