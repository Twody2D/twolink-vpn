from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.node import Node
    from app.models.user import User


class Subscription(Base, TimestampMixin):
    """Binds a user to a specific node. node_id is a real FK from the start
    so a user can be (and later, multiple users can be) placed on any node,
    even though only one node exists today."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Opaque, cryptographically random token used in subscription URLs.
    # Never a sequential/guessable ID (see secrets.token_urlsafe usage).
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # UUID identifying this subscriber as an Xray VLESS client on the node.
    vless_uuid: Mapped[str] = mapped_column(String(36), nullable=False)

    traffic_limit_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    traffic_used_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    node: Mapped["Node"] = relationship()
