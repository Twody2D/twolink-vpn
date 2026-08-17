from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node
from app.models.subscription import Subscription


async def select_least_loaded_node(session: AsyncSession) -> Node | None:
    """Picks the active node with the fewest active subscriptions. Trivial
    with one node today, but already works over an arbitrary fleet."""

    user_count = func.count(Subscription.id).label("user_count")

    result = await session.execute(
        select(Node, user_count)
        .outerjoin(
            Subscription,
            and_(Subscription.node_id == Node.id, Subscription.is_active.is_(True)),
        )
        .where(Node.is_active.is_(True))
        .group_by(Node.id)
        .order_by(user_count.asc())
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None
