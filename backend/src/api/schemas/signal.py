from typing import List, Optional

from pydantic import BaseModel


class SignalIndicators(BaseModel):
    atr: Optional[float] = None
    adx: Optional[float] = None
    rsi: Optional[float] = None


class SignalResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    score: float
    confidence: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_percent: float
    suggested_position_size: float
    btc_trend: str
    session_quality: str
    timestamp: str
    valid_until: str
    reasons: List[str]
    indicators: SignalIndicators


class SignalListResponse(BaseModel):
    timestamp: str
    count: int
    signals: List[SignalResponse]
