from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter

from src.api.schemas.signal import (
    ConfluenceData,
    SessionLevels,
    SignalIndicators,
    SignalKeyLevels,
    SignalListResponse,
    SignalResponse,
)
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
    key_levels_data = signal.key_levels or {}
    sessions_data = key_levels_data.get("sessions") if isinstance(key_levels_data, dict) else {}
    sessions = {
        name: SessionLevels(high=_sanitize_float(values.get("high")), low=_sanitize_float(values.get("low")))
        for name, values in (sessions_data or {}).items()
        if isinstance(values, dict)
    }
    key_levels_model = SignalKeyLevels(
        poc_weekly=_sanitize_float(key_levels_data.get("poc_weekly")) if isinstance(key_levels_data, dict) else None,
        poc_daily=_sanitize_float(key_levels_data.get("poc_daily")) if isinstance(key_levels_data, dict) else None,
        vah=_sanitize_float(key_levels_data.get("vah")) if isinstance(key_levels_data, dict) else None,
        val=_sanitize_float(key_levels_data.get("val")) if isinstance(key_levels_data, dict) else None,
        pwh=_sanitize_float(key_levels_data.get("pwh")) if isinstance(key_levels_data, dict) else None,
        pwl=_sanitize_float(key_levels_data.get("pwl")) if isinstance(key_levels_data, dict) else None,
        pdh=_sanitize_float(key_levels_data.get("pdh")) if isinstance(key_levels_data, dict) else None,
        pdl=_sanitize_float(key_levels_data.get("pdl")) if isinstance(key_levels_data, dict) else None,
        sessions=sessions or None,
    )

    confluence_data = signal.confluence or {}
    raw_levels = confluence_data.get("levels", []) or []
    confluence_model = ConfluenceData(
        count=int(confluence_data.get("count", 0)),
        levels=[str(level) for level in raw_levels],
        multiplier=float(confluence_data.get("multiplier", 1.0)),
        bonus=int(confluence_data.get("bonus", 0)),
    )

    base_components = {
        str(name): float(value)
        for name, value in (signal.base_components or {}).items()
        if value is not None
    }

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
        base_score=float(signal.base_score),
        btc_multiplier=float(signal.btc_multiplier),
        bonus=int(signal.total_bonus),
        base_components=base_components,
        key_levels=key_levels_model,
        confluence=confluence_model,
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
