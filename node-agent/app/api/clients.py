from fastapi import APIRouter, Depends, status
from starlette.concurrency import run_in_threadpool

from app.core.security import verify_backend
from app.schemas.client import ClientCreateRequest
from app.services import xray

router = APIRouter(dependencies=[Depends(verify_backend)])


@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def add_client(payload: ClientCreateRequest) -> dict:
    await run_in_threadpool(xray.add_client, payload.uuid, payload.email)
    return {"status": "ok"}


@router.delete("/clients/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_client(email: str) -> None:
    await run_in_threadpool(xray.remove_client, email)


@router.get("/metrics")
async def metrics() -> dict:
    return await run_in_threadpool(xray.get_metrics)
