from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.subscription import Subscription
from app.schemas.hysteria import HysteriaAuthRequest, HysteriaAuthResponse

# No verify_internal_api_key here — Hysteria's built-in HTTP auth caller has
# no way to attach that header. Same trust boundary as Xray's gRPC endpoint:
# reachable only from inside the docker network, never published to the host.
router = APIRouter(prefix="/internal")


@router.post("/hysteria/authenticate", response_model=HysteriaAuthResponse)
async def authenticate(
    payload: HysteriaAuthRequest,
    session: AsyncSession = Depends(get_session),
) -> HysteriaAuthResponse:
    subscription = (
        await session.execute(
            select(Subscription).where(
                Subscription.hysteria_password == payload.auth,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()

    if subscription is None:
        return HysteriaAuthResponse(ok=False, msg="invalid credentials")

    return HysteriaAuthResponse(ok=True, id=subscription.token)
