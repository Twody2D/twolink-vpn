import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import verify_internal_api_key
from app.models.node import Node
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionCreateRequest, SubscriptionResponse
from app.services.hysteria_client import get_hysteria_client
from app.services.node_selection import select_least_loaded_node
from app.services.xray_client import get_xray_client

router = APIRouter(prefix="/internal", dependencies=[Depends(verify_internal_api_key)])


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> Subscription:
    if payload.node_id is not None:
        node = (
            await session.execute(select(Node).where(Node.node_id == payload.node_id, Node.is_active.is_(True)))
        ).scalar_one_or_none()
    else:
        node = await select_least_loaded_node(session)

    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node not found or inactive")

    user = (await session.execute(select(User).where(User.telegram_id == payload.telegram_id))).scalar_one_or_none()
    if user is None:
        user = User(telegram_id=payload.telegram_id, username=payload.username)
        session.add(user)
        await session.flush()

    token = secrets.token_urlsafe(32)
    client_uuid = str(uuid.uuid4())
    hysteria_password = secrets.token_urlsafe(24)

    subscription = Subscription(
        user_id=user.id,
        node_id=node.id,
        token=token,
        vless_uuid=client_uuid,
        hysteria_password=hysteria_password,
    )
    session.add(subscription)
    await session.flush()

    await get_xray_client(node).add_client(node, client_uuid, token)
    await get_hysteria_client(node).add_client(node, hysteria_password, token)

    await session.commit()
    await session.refresh(subscription)
    return subscription


@router.delete("/subscriptions/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(token: str, session: AsyncSession = Depends(get_session)) -> None:
    subscription = (await session.execute(select(Subscription).where(Subscription.token == token))).scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")

    node = (await session.execute(select(Node).where(Node.id == subscription.node_id))).scalar_one()

    await get_xray_client(node).remove_client(node, subscription.token)
    await get_hysteria_client(node).remove_client(node, subscription.token)

    await session.delete(subscription)
    await session.commit()
