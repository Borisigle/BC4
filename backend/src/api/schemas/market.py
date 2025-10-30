from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BTCContext(BaseModel):
    trend: str
    trend_strength: float
    volatility: str
    session_quality: str
    should_trade: bool


class MarketAsset(BaseModel):
    symbol: str
    price: float
    change_24h: Optional[float] = None
    trend_4h: str
    trend_1h: str
    adx: Optional[float] = None
    rsi: Optional[float] = None
    atr: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None


class MarketOverviewResponse(BaseModel):
    timestamp: str
    btc_context: BTCContext
    assets: List[MarketAsset]


class Candle(BaseModel):
    timestamp: int
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketChartIndicators(BaseModel):
    ema_20: List[Optional[float]]
    ema_50: List[Optional[float]]
    atr: List[Optional[float]]
    adx: List[Optional[float]]
    rsi: List[Optional[float]]
    vwap: List[Optional[float]]
    cvd: List[Optional[float]]


class MarketStructureLevel(BaseModel):
    price: float
    strength: str
    touches: int
    first_touch: Optional[str] = None
    last_touch: Optional[str] = None


class SwingPoint(BaseModel):
    timestamp: int
    price: float


class MarketStructureResponse(BaseModel):
    resistances: List[MarketStructureLevel]
    supports: List[MarketStructureLevel]
    swing_highs: List[SwingPoint]
    swing_lows: List[SwingPoint]


class KeyLevel(BaseModel):
    price: float
    label: str
    type: str


class TrendResponse(BaseModel):
    current: str
    strength: float
    structure: str
    ema_alignment: bool
    adx_value: float


class MarketChartResponse(BaseModel):
    symbol: str
    timeframe: str
    candles: List[Candle]
    indicators: MarketChartIndicators
    market_structure: MarketStructureResponse
    key_levels: Dict[str, KeyLevel] = Field(default_factory=dict)
    trend: TrendResponse
