from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter

from src.api.schemas.signal import SignalIndicators, SignalListResponse, SignalResponse
from src.signals.signal import Signal
from src.signals.signal_engine import SignalEngine

router = APIRouter()
engine = SignalEngine()


def _isoformat(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _sanitize_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def signal_to_response(signal: Signal) -> SignalResponse:
    return SignalResponse(
        id=str(uuid4()),
        symbol=signal.symbol,
        direction=signal.direction,
        score=float(signal.score),
        confidence=signal.confidence,
        entry_price=float(signal.entry_price),
        stop_loss=float(signal.stop_loss),
        take_profit_1=float(signal.take_profit_1),
        take_profit_2=float(signal.take_profit_2),
        take_profit_3=float(signal.take_profit_3),
        risk_percent=float(signal.risk_percent),
        suggested_position_size=float(signal.suggested_position_size),
        btc_trend=signal.btc_trend,
        session_quality=signal.session_quality,
        timestamp=_isoformat(signal.timestamp),
        valid_until=_isoformat(signal.valid_until),
        reasons=list(signal.reasons),
        indicators=SignalIndicators(
            atr=_sanitize_float(signal.atr_value),
            adx=_sanitize_float(signal.adx_value),
            rsi=_sanitize_float(signal.rsi_value),
        ),
    )


@router.get("/current", response_model=SignalListResponse)
async def get_current_signals() -> SignalListResponse:
    """Ejecuta scan y retorna señales actuales."""
    signals = engine.scan_for_signals()
    responses = [signal_to_response(signal) for signal in signals]

    return SignalListResponse(
        timestamp=_isoformat(datetime.now(timezone.utc)),
        count=len(responses),
        signals=responses,
    )
