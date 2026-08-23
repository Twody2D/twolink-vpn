from pydantic import BaseModel


class HysteriaAuthRequest(BaseModel):
    addr: str
    auth: str
    tx: int = 0


class HysteriaAuthResponse(BaseModel):
    ok: bool
    id: str | None = None
    msg: str | None = None
