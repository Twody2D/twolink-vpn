from fastapi import APIRouter, Depends, status

from app.core.security import verify_backend
from app.schemas.hysteria import (
    HysteriaAuthRequest,
    HysteriaAuthResponse,
    HysteriaUserCreateRequest,
)
from app.services import hysteria

# Credential push from the backend — same trust boundary as /clients.
users_router = APIRouter(prefix="/hysteria", dependencies=[Depends(verify_backend)])


@users_router.post("/users", status_code=status.HTTP_201_CREATED)
async def add_user(payload: HysteriaUserCreateRequest) -> dict:
    hysteria.add_user(payload.password, payload.client_id)
    return {"status": "ok"}


@users_router.delete("/users/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(client_id: str) -> None:
    hysteria.remove_user(client_id)


# Called by this node's own Hysteria server on every connection — no way for
# it to attach the backend's API key header, so this is unauthenticated and
# relies on the same docker-network isolation as the backend's own endpoint.
auth_router = APIRouter(prefix="/hysteria")


@auth_router.post("/authenticate", response_model=HysteriaAuthResponse)
async def authenticate(payload: HysteriaAuthRequest) -> HysteriaAuthResponse:
    client_id = hysteria.authenticate(payload.auth)
    if client_id is None:
        return HysteriaAuthResponse(ok=False, msg="invalid credentials")
    return HysteriaAuthResponse(ok=True, id=client_id)
