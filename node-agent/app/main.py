from fastapi import FastAPI

from app.api.clients import router as clients_router
from app.api.health import router as health_router
from app.api.hysteria import auth_router as hysteria_auth_router
from app.api.hysteria import users_router as hysteria_users_router

app = FastAPI(title="TwoLink Node Agent")

app.include_router(health_router)
app.include_router(clients_router)
app.include_router(hysteria_users_router)
app.include_router(hysteria_auth_router)
