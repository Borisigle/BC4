from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas.market import (
    BTCContext,
    Candle,
    MarketAsset,
    MarketChartIndicators,
    MarketChartResponse,
    MarketOverviewResponse,
    MarketStructureLevel,
    MarketStructureResponse,
    SwingPoint,
    TrendResponse,
)
from src.config import settings
from src.data.cvd_storage import CVDStorage
from src.data.data_storage import DataStorage
from src.indicators.key_levels import calculate_key_levels
from src.indicators.market_structure import MarketStructure
from src.indicators.technical_indicators import TechnicalIndicators
from src.signals.btc_filter import BTCFilter
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

storage = DataStorage(settings.DB_PATH)
cvd_storage = CVDStorage()
technical_indicators = TechnicalIndicators()
market_structure = MarketStructure()
btc_filter = BTCFilter()

SYMBOL_MAP: Dict[str, str] = {symbol.upper(): symbol for symbol in settings.SYMBOLS}
SYMBOL_ORDER: List[str] = list(settings.SYMBOLS)
ALLOWED_TIMEFRAMES: Tuple[str, ...] = tuple(tf.lower() for tf in settings.TIMEFRAMES)
INDICATOR_PADDING = 50
LEVEL_TOLERANCE = 0.005


def _isoformat(value: Union[datetime, pd.Timestamp]) -> str:
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            value = value.tz_localize("UTC")
        else:
            value = value.tz_convert("UTC")
        value = value.to_pydatetime()

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat().replace("+00:00", "Z")


def _sanitize_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def _load_dataset(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    fetch_limit = max(limit + INDICATOR_PADDING, settings.DEFAULT_LIMIT)
    df = storage.get_ohlcv(symbol, timeframe, fetch_limit)
    if df.empty:
        return df
    df_indicators = technical_indicators.add_all_indicators(df)
    return df_indicators


def _get_last_value(df: pd.DataFrame, column: str) -> Optional[float]:
    if column not in df.columns:
        return None
    series = df[column].dropna()
    if series.empty:
        return None
    return float(series.iloc[-1])


def _compute_change_24h(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "close" not in df.columns:
        return None
    if len(df) < 25:
        return None
    last_close = float(df["close"].iloc[-1])
    previous_close = float(df["close"].iloc[-25])
    if previous_close == 0:
        return None
    change = ((last_close - previous_close) / previous_close) * 100
    return change


def _build_asset_overview(symbol: str) -> Optional[MarketAsset]:
    df_4h = _load_dataset(symbol, "4h", settings.DEFAULT_LIMIT)
    df_1h = _load_dataset(symbol, "1h", settings.DEFAULT_LIMIT)

    if df_4h.empty or df_1h.empty:
        logger.warning("Datos insuficientes para generar overview de %s", symbol)
        return None

    trend_4h_info = market_structure.determine_trend(market_structure.detect_swing_points(df_4h))
    trend_1h_info = market_structure.determine_trend(market_structure.detect_swing_points(df_1h))

    price = _get_last_value(df_1h, "close")
    if price is None:
        logger.warning("No se pudo determinar precio actual para %s", symbol)
        return None

    change_24h = _compute_change_24h(df_1h)

    adx = _get_last_value(df_4h, "adx")
    rsi = _get_last_value(df_1h, "rsi")
    atr = _get_last_value(df_4h, "atr")
    ema_20 = _get_last_value(df_4h, "ema_20")
    ema_50 = _get_last_value(df_4h, "ema_50")

    trend_adx = _sanitize_float(trend_4h_info.get("adx_value"))
    fallback_adx = _sanitize_float(adx)
    adx_value = trend_adx if trend_adx is not None else fallback_adx

    return MarketAsset(
        symbol=symbol,
        price=float(price),
        change_24h=_sanitize_float(change_24h),
        trend_4h=str(trend_4h_info.get("trend", "INESTABLE")),
        trend_1h=str(trend_1h_info.get("trend", "INESTABLE")),
        adx=adx_value,
        rsi=_sanitize_float(rsi),
        atr=_sanitize_float(atr),
        ema_20=_sanitize_float(ema_20),
        ema_50=_sanitize_float(ema_50),
    )


def _prepare_btc_context() -> BTCContext:
    btc_symbol = "BTC/USDT"
    df_4h = _load_dataset(btc_symbol, "4h", settings.DEFAULT_LIMIT)
    df_1h = _load_dataset(btc_symbol, "1h", settings.DEFAULT_LIMIT)

    context = btc_filter.analyze_btc_context(df_4h, df_1h)

    return BTCContext(
        trend=str(context.get("trend", "INESTABLE")),
        trend_strength=float(context.get("trend_strength", 0.0)),
        volatility=str(context.get("volatility", "NORMAL")),
        session_quality=str(context.get("session_quality", "MEDIA")),
        should_trade=bool(context.get("should_trade", False)),
    )


def _format_levels(levels: Iterable[Dict[str, object]], df: pd.DataFrame, swing_column: str) -> List[MarketStructureLevel]:
    formatted: List[MarketStructureLevel] = []
    if swing_column not in df.columns:
        return formatted

    for level in levels:
        price = float(level.get("price", float("nan")))
        if math.isnan(price):
            continue
        touches = int(level.get("touches", 0))
        strength = str(level.get("strength", "weak"))

        mask = df[swing_column].notna() & (df[swing_column].sub(price).abs() / max(price, 1e-8) <= LEVEL_TOLERANCE)
        matches = df.loc[mask]

        first_touch = _isoformat(matches["datetime"].iloc[0]) if not matches.empty else None
        last_touch = _isoformat(matches["datetime"].iloc[-1]) if not matches.empty else None

        formatted.append(
            MarketStructureLevel(
                price=price,
                strength=strength,
                touches=touches,
                first_touch=first_touch,
                last_touch=last_touch,
            )
        )

    return formatted


def _collect_swing_points(df: pd.DataFrame, column: str) -> List[SwingPoint]:
    if column not in df.columns:
        return []

    subset = df.loc[df[column].notna(), ["timestamp", column]]
    points: List[SwingPoint] = []
    for _, row in subset.iterrows():
        timestamp_raw = int(row["timestamp"])
        price = float(row[column])
        points.append(SwingPoint(timestamp=timestamp_raw * 1000, price=price))
    return points


def _indicator_list(df: pd.DataFrame, column: str) -> List[Optional[float]]:
    if column not in df.columns:
        return [None] * len(df)
    return [_sanitize_float(value) for value in df[column]]


def _load_cvd_values(symbol: str, timeframe: str, timestamps: List[int]) -> List[Optional[float]]:
    if not timestamps:
        return []

    cvd_df = cvd_storage.get_cvd(symbol, timeframe, limit=len(timestamps) + INDICATOR_PADDING)
    if cvd_df.empty:
        return [None] * len(timestamps)

    cvd_map = {int(row.timestamp): float(row.cvd_cumulative) for row in cvd_df.itertuples()}
    values: List[Optional[float]] = []
    for ts in timestamps:
        ts_int = int(ts)
        values.append(_sanitize_float(cvd_map.get(ts_int)))
    return values


def _build_trend_response(df: pd.DataFrame) -> TrendResponse:
    info = market_structure.determine_trend(df)

    strength = _sanitize_float(info.get("trend_strength"))
    adx_value = _sanitize_float(info.get("adx_value"))

    return TrendResponse(
        current=str(info.get("trend", "INESTABLE")),
        strength=strength if strength is not None else 0.0,
        structure=str(info.get("structure", "MIXED")),
        ema_alignment=bool(info.get("ema_alignment", False)),
        adx_value=adx_value if adx_value is not None else 0.0,
    )


def _prepare_chart_response(df: pd.DataFrame, symbol: str, timeframe: str, limit: int) -> MarketChartResponse:
    if df.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datos insuficientes para el símbolo y timeframe solicitados")

    df_with_swings = market_structure.detect_swing_points(df)
    df_tail = df_with_swings.tail(limit).reset_index(drop=True)

    cvd_values = _load_cvd_values(symbol, timeframe, df_tail["timestamp"].astype(int).tolist())
    df_tail = df_tail.copy()
    df_tail["cvd"] = cvd_values

    candles = [
        Candle(
            timestamp=int(row.timestamp) * 1000,
            datetime=_isoformat(row.datetime),
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
            volume=float(row.volume),
        )
        for row in df_tail.itertuples()
    ]

    indicators = MarketChartIndicators(
        ema_20=_indicator_list(df_tail, "ema_20"),
        ema_50=_indicator_list(df_tail, "ema_50"),
        atr=_indicator_list(df_tail, "atr"),
        adx=_indicator_list(df_tail, "adx"),
        rsi=_indicator_list(df_tail, "rsi"),
        vwap=_indicator_list(df_tail, "vwap"),
        cvd=_indicator_list(df_tail, "cvd"),
    )

    levels = market_structure.identify_support_resistance(df_with_swings, tolerance=LEVEL_TOLERANCE)
    structure = MarketStructureResponse(
        resistances=_format_levels(levels.get("resistances", []), df_with_swings, "swing_high"),
        supports=_format_levels(levels.get("supports", []), df_with_swings, "swing_low"),
        swing_highs=_collect_swing_points(df_tail, "swing_high"),
        swing_lows=_collect_swing_points(df_tail, "swing_low"),
    )

    key_levels = calculate_key_levels(
        df=df_with_swings,
        timeframe=timeframe,
        current_time=datetime.now(timezone.utc),
    )

    trend = _build_trend_response(df_with_swings)

    return MarketChartResponse(
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
        indicators=indicators,
        market_structure=structure,
        key_levels=key_levels,
        trend=trend,
    )


@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview() -> MarketOverviewResponse:
    """Retorna overview de todos los activos."""
    now_iso = _isoformat(datetime.now(timezone.utc))
    btc_context = _prepare_btc_context()

    assets: List[MarketAsset] = []
    for symbol in SYMBOL_ORDER:
        try:
            asset = _build_asset_overview(symbol)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Error construyendo overview para %s: %s", symbol, exc)
            asset = None
        if asset:
            assets.append(asset)

    if not assets:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No hay datos de mercado disponibles")

    return MarketOverviewResponse(timestamp=now_iso, btc_context=btc_context, assets=assets)


@router.get("/chart/{symbol:path}/{timeframe}", response_model=MarketChartResponse)
async def get_chart_data(
    symbol: str,
    timeframe: str,
    limit: int = Query(100, ge=10, le=500),
) -> MarketChartResponse:
    """Retorna datos completos de un activo para renderizar gráfico."""
    normalized_symbol = symbol.upper()
    normalized_timeframe = timeframe.lower()

    if normalized_symbol not in SYMBOL_MAP:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Símbolo no soportado")

    if normalized_timeframe not in ALLOWED_TIMEFRAMES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timeframe no soportado")

    canonical_symbol = SYMBOL_MAP[normalized_symbol]
    df = _load_dataset(canonical_symbol, normalized_timeframe, limit)

    return _prepare_chart_response(df, canonical_symbol, normalized_timeframe, limit)
