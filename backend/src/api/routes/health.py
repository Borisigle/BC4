from datetime import datetime, timezone

from fastapi import APIRouter

from src.api.schemas.health import HealthResponse

router = APIRouter()

_API_VERSION = "1.0.0"


def _utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return API health information."""
    return HealthResponse(status="ok", timestamp=_utc_now_iso(), version=_API_VERSION)
