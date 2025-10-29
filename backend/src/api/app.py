from fastapi import FastAPI

from src.api.middleware.cors import setup_cors
from src.api.routes import health, market, signals
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Crypto Signal Scanner API",
    version="1.0.0",
    description="API para el sistema de señales de trading",
)

setup_cors(app)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("Crypto Signal Scanner API startup complete")
