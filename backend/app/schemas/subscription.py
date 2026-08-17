from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionCreateRequest(BaseModel):
    telegram_id: int
    username: str | None = None
    node_id: str


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str
    vless_uuid: str
    node_id: int
    expires_at: datetime | None
    is_active: bool
