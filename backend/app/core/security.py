import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_internal_api_key(x_internal_api_key: str = Header(...)) -> None:
    if not secrets.compare_digest(x_internal_api_key, settings.backend_internal_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")
