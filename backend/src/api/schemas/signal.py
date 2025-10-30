from typing import Dict, List, Optional

from pydantic import BaseModel


class SignalIndicators(BaseModel):
    atr: Optional[float] = None
    adx: Optional[float] = None
    rsi: Optional[float] = None


class SessionLevels(BaseModel):
    high: Optional[float] = None
    low: Optional[float] = None


class ConfluenceData(BaseModel):
    count: int
    levels: List[str]
    multiplier: float
    bonus: int


class SignalKeyLevels(BaseModel):
    poc_weekly: Optional[float] = None
    poc_daily: Optional[float] = None
    vah: Optional[float] = None
    val: Optional[float] = None
    pwh: Optional[float] = None
    pwl: Optional[float] = None
    pdh: Optional[float] = None
    pdl: Optional[float] = None
    sessions: Optional[Dict[str, SessionLevels]] = None


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
    base_score: float
    btc_multiplier: float
    bonus: int
    base_components: Dict[str, float]
    key_levels: SignalKeyLevels
    confluence: ConfluenceData


class SignalListResponse(BaseModel):
    timestamp: str
    count: int
    signals: List[SignalResponse]
