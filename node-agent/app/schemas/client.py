from pydantic import BaseModel


class ClientCreateRequest(BaseModel):
    uuid: str
    email: str
