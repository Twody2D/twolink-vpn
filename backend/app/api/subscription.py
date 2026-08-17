import base64

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.limiter import limiter
from app.models.node import Node
from app.models.subscription import Subscription
from app.services.link_builder import build_vless_link

router = APIRouter()


@router.get("/sub/{token}")
@limiter.limit("20/minute")
async def get_subscription(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> PlainTextResponse:
    subscription = (
        await session.execute(
            select(Subscription).where(Subscription.token == token, Subscription.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")

    # A token identifies one user; return links for every node that user is
    # currently provisioned on, not just the node this particular token's
    # subscription row was created for.
    rows = (
        await session.execute(
            select(Subscription, Node)
            .join(Node, Subscription.node_id == Node.id)
            .where(
                Subscription.user_id == subscription.user_id,
                Subscription.is_active.is_(True),
                Node.is_active.is_(True),
            )
        )
    ).all()

    links = [build_vless_link(sub, node) for sub, node in rows]
    content = base64.b64encode("\n".join(links).encode()).decode()

    return PlainTextResponse(content)
