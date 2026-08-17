import httpx

from app.core.config import settings


class BackendClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.backend_internal_url,
            headers={"X-Internal-Api-Key": settings.backend_internal_api_key},
            timeout=10.0,
        )

    async def create_subscription(self, telegram_id: int, username: str | None, node_id: str) -> dict:
        response = await self._client.post(
            "/internal/subscriptions",
            json={"telegram_id": telegram_id, "username": username, "node_id": node_id},
        )
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()


backend_client = BackendClient()
