export interface MarketOverview {
  timestamp: string;
  btc_context: {
    trend: 'ALCISTA_FUERTE' | 'BAJISTA_FUERTE' | 'LATERAL' | 'INESTABLE' | string;
    trend_strength: number;
    volatility: 'ALTA' | 'NORMAL' | 'BAJA' | string;
    session_quality: 'ALTA' | 'MEDIA' | 'BAJA' | string;
    should_trade: boolean;
  };
  assets: Asset[];
}

export interface Asset {
  symbol: string;
  price: number;
  change_24h: number;
  trend_4h: string;
  trend_1h: string;
  adx: number;
  rsi: number;
  atr: number;
  ema_20: number;
  ema_50: number;
}

export interface ChartData {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  indicators: {
    ema_20: (number | null)[];
    ema_50: (number | null)[];
    atr: (number | null)[];
    adx: (number | null)[];
    rsi: (number | null)[];
    vwap: (number | null)[];
    cvd: (number | null)[];
  };
  market_structure: MarketStructure;
  trend: TrendInfo;
}

export interface Candle {
  timestamp: number;
  datetime: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketStructure {
  resistances: SupportResistance[];
  supports: SupportResistance[];
  swing_highs: SwingPoint[];
  swing_lows: SwingPoint[];
}

export interface SupportResistance {
  price: number;
  strength: 'strong' | 'medium';
  touches: number;
}

export interface SwingPoint {
  price: number;
  timestamp: number;
  level_type?: 'high' | 'low';
}

export interface TrendInfo {
  current: string;
  bias?: string;
  strength: number | string;
  confidence?: number | string;
  signal?: string;
  comment?: string;
}

export interface Signal {
  symbol: string;
  direction: 'LONG' | 'SHORT';
  score: number;
  confidence: 'ALTA' | 'MEDIA' | 'BAJA' | string;
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3: number;
  risk_percent: number;
  suggested_position_size: number;
  btc_trend: string;
  session_quality: string;
  timestamp: string;
  valid_until: string;
  reasons: string[];
  indicators: {
    atr: number;
    adx: number;
    rsi: number;
  };
}

export interface SignalsResponse {
  signals: Signal[];
}
