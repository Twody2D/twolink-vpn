from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.health import router as health_router
from app.api.hysteria import router as hysteria_router
from app.api.internal import router as internal_router
from app.api.subscription import router as subscription_router
from app.core.limiter import limiter

app = FastAPI(title="TwoLink Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health_router)
app.include_router(internal_router)
app.include_router(subscription_router)
app.include_router(hysteria_router)
