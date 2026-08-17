import secrets

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings


async def verify_backend(request: Request, x_node_api_key: str = Header(...)) -> None:
    allowed_ips = {ip.strip() for ip in settings.allowed_backend_ips.split(",") if ip.strip()}
    client_ip = request.client.host if request.client else None

    if allowed_ips and client_ip not in allowed_ips:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="source IP not allowed")

    if not secrets.compare_digest(x_node_api_key, settings.node_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")
