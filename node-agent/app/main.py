from fastapi import FastAPI

from app.api.clients import router as clients_router
from app.api.health import router as health_router

app = FastAPI(title="TwoLink Node Agent")

app.include_router(health_router)
app.include_router(clients_router)
