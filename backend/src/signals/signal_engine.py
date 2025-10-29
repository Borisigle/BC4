from __future__ import annotations

import copy
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import settings
from src.data.cvd_storage import CVDStorage
from src.data.data_storage import DataStorage
from src.indicators.key_levels import (
    calculate_poc,
    calculate_value_area,
    get_previous_period_extremes,
    get_session_extremes,
)
from src.indicators.market_structure import MarketStructure
from src.indicators.technical_indicators import TechnicalIndicators
from src.utils.logger import get_logger
from .btc_filter import BTCFilter
from .confluence_detector import ConfluenceDetector
from .signal import Signal
from .signal_detector import SignalDetector
from .signal_scorer import SignalScorer

logger = get_logger(__name__)


class SignalEngine:
    """Motor principal que orquesta todo el análisis."""

    def __init__(self) -> None:
        self.storage = DataStorage(settings.DB_PATH)
        self.cvd_storage = CVDStorage()
        self.technical_indicators = TechnicalIndicators()
        self.market_structure = MarketStructure()
        self.btc_filter = BTCFilter()
        self.signal_detector = SignalDetector()
        self.confluence_detector = ConfluenceDetector()
        self.signal_scorer = SignalScorer(self.confluence_detector)
        self._key_levels_cache: Dict[str, Dict[str, object]] = {}

    def scan_for_signals(self, symbols: Optional[List[str]] = None) -> List[Signal]:
        if symbols is None:
            symbols = settings.SYMBOLS

        signals: List[Signal] = []

        logger.info("Analizando BTC como filtro maestro...")
        btc_df_4h = self._load_and_prepare_data("BTC/USDT", "4h")
        btc_df_1h = self._load_and_prepare_data("BTC/USDT", "1h")

        if btc_df_4h.empty or btc_df_1h.empty:
            logger.warning("Datos insuficientes de BTC para generar contexto")
            return []

        btc_context = self.btc_filter.analyze_btc_context(btc_df_4h, btc_df_1h)

        if not btc_context.get("should_trade", False):
            logger.warning("BTC context no favorable para operar: %s", btc_context.get("trend"))
            return []

        for symbol in symbols:
            logger.info("Escaneando %s...", symbol)
            df_4h = self._load_and_prepare_data(symbol, "4h")
            df_1h = self._load_and_prepare_data(symbol, "1h")

            if df_4h.empty or df_1h.empty:
                logger.warning("Datos insuficientes para %s", symbol)
                continue

            df_4h_struct = self.market_structure.detect_swing_points(df_4h)
            sr = self.market_structure.identify_support_resistance(df_4h_struct)
            trend = self.market_structure.determine_trend(df_4h_struct)

            market_structure = {
                "supports": sr.get("supports", []),
                "resistances": sr.get("resistances", []),
                "trend": trend,
            }

            cvd_4h = (
                self._load_cvd_series(symbol, "4h", df_4h_struct["timestamp"]) if "timestamp" in df_4h_struct else np.array([])
            )
            cvd_1h = (
                self._load_cvd_series(symbol, "1h", df_1h["timestamp"]) if "timestamp" in df_1h else np.array([])
            )

            long_setup = self.signal_detector.detect_long_setup(df_4h_struct, df_1h, cvd_4h, cvd_1h, market_structure)
            short_setup = self.signal_detector.detect_short_setup(df_4h_struct, df_1h, cvd_4h, cvd_1h, market_structure)

            key_levels = self._get_or_compute_key_levels(symbol, df_1h)
            indicator_context = self._build_indicator_context(df_1h)
            current_price = float(df_1h["close"].iloc[-1])

            for setup in [long_setup, short_setup]:
                if not setup:
                    continue

                augmented_setup = dict(setup)
                direction = str(augmented_setup.get("direction", "LONG")).upper()
                augmented_setup["previous_extreme_sweep"] = self._detect_previous_extreme_sweep(
                    df_1h, key_levels, direction
                )

                score_result = self.signal_scorer.calculate_final_score(
                    augmented_setup,
                    btc_context,
                    symbol,
                    current_price,
                    key_levels,
                    indicator_context,
                )

                confluence_data = score_result.get("confluence", {})
                if confluence_data.get("count", 0) > 0:
                    logger.info(
                        "Confluencia detectada %s %s | niveles=%s multiplicador=%.2f bonus=%s",
                        symbol,
                        direction,
                        confluence_data.get("levels", []),
                        float(confluence_data.get("multiplier", 1.0)),
                        confluence_data.get("bonus", 0),
                    )

                if not score_result.get("should_alert", False):
                    continue

                try:
                    signal = self._create_signal(
                        symbol,
                        augmented_setup,
                        score_result,
                        btc_context,
                        df_1h,
                        key_levels,
                        confluence_data,
                    )
                    signals.append(signal)
                except Exception as exc:
                    logger.exception("Error creando señal para %s: %s", symbol, exc)

        signals.sort(key=lambda s: s.score, reverse=True)
        return signals[:2]

    def _load_and_prepare_data(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        df = self.storage.get_ohlcv(symbol, timeframe, limit)
        if df.empty:
            return df
        df_indicators = self.technical_indicators.add_all_indicators(df)
        return df_indicators

    def _load_cvd_series(self, symbol: str, timeframe: str, timestamps: pd.Series) -> np.ndarray:
        if timestamps is None or len(timestamps) == 0:
            return np.array([], dtype=float)

        cvd_df = self.cvd_storage.get_cvd(symbol, timeframe, limit=len(timestamps) + 10)
        if cvd_df.empty:
            return np.array([], dtype=float)

        cvd_map = {int(row.timestamp): float(row.cvd_cumulative) for row in cvd_df.itertuples()}

        aligned: List[float] = []
        for value in timestamps:
            if pd.isna(value):
                aligned.append(np.nan)
            else:
                aligned.append(cvd_map.get(int(value), np.nan))

        return np.array(aligned, dtype=float)

    def _create_signal(
        self,
        symbol: str,
        setup: Dict[str, object],
        score_result: Dict[str, object],
        btc_context: Dict[str, object],
        df_1h: pd.DataFrame,
        key_levels: Dict[str, Optional[float]],
        confluence: Dict[str, object],
    ) -> Signal:
        current_price = float(df_1h["close"].iloc[-1])
        atr = self._get_last_indicator(df_1h, "atr")
        adx = self._get_last_indicator(df_1h, "adx")
        rsi = self._get_last_indicator(df_1h, "rsi")
        direction = str(setup.get("direction", "LONG")).upper()

        if symbol == "BTC/USDT":
            atr_multiplier = 1.5
        elif symbol == "ETH/USDT":
            atr_multiplier = 2.0
        else:
            atr_multiplier = 2.5

        min_risk_distance = current_price * 0.005

        if direction == "LONG":
            support_value = setup.get("support_level")
            if support_value is None or pd.isna(support_value):
                support = current_price * 0.98
            else:
                support = float(support_value)
            stop_loss = support - atr * atr_multiplier if not pd.isna(atr) else support * 0.98
            if stop_loss >= current_price:
                stop_loss = current_price - max(min_risk_distance, abs(current_price - support))
            risk = max(current_price - stop_loss, min_risk_distance)
            tp1 = current_price + (risk * 2)
            tp2 = current_price + (risk * 3)
            tp3 = current_price + (risk * 4)
        else:
            resistance_value = setup.get("resistance_level")
            if resistance_value is None or pd.isna(resistance_value):
                resistance = current_price * 1.02
            else:
                resistance = float(resistance_value)
            stop_loss = resistance + atr * atr_multiplier if not pd.isna(atr) else resistance * 1.02
            if stop_loss <= current_price:
                stop_loss = current_price + max(min_risk_distance, abs(resistance - current_price))
            risk = max(stop_loss - current_price, min_risk_distance)
            tp1 = current_price - (risk * 2)
            tp2 = current_price - (risk * 3)
            tp3 = current_price - (risk * 4)

        risk_percent = abs((stop_loss - current_price) / current_price) * 100

        confidence = score_result.get("confidence", "BAJA")
        if confidence == "ALTA":
            position_size = 1.5
        elif confidence == "MEDIA":
            position_size = 1.0
        else:
            position_size = 0.5

        return Signal(
            symbol=symbol,
            direction=direction,
            score=float(score_result.get("final_score", 0.0)),
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_percent=risk_percent,
            suggested_position_size=position_size,
            btc_trend=str(btc_context.get("trend", "")),
            session_quality=str(btc_context.get("session_quality", "BAJA")),
            timestamp=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(hours=1),
            reasons=list(setup.get("reasons", [])),
            atr_value=atr,
            adx_value=adx,
            rsi_value=rsi,
            base_score=float(score_result.get("base_score", 0.0)),
            base_components=dict(score_result.get("base_components", {})),
            key_levels=copy.deepcopy(key_levels),
            confluence=copy.deepcopy(confluence),
            btc_multiplier=float(score_result.get("btc_multiplier", 1.0)),
            total_bonus=int(score_result.get("bonus", 0)),
        )

    def _get_or_compute_key_levels(self, symbol: str, df: pd.DataFrame) -> Dict[str, object]:
        cache_entry = self._key_levels_cache.get(symbol)
        now = datetime.utcnow()
        if cache_entry and (now - cache_entry["timestamp"]).total_seconds() < 3600:
            return copy.deepcopy(cache_entry["data"])

        weekly_window = timedelta(days=7)
        daily_window = timedelta(days=1)

        poc_weekly = calculate_poc(df, weekly_window)
        poc_daily = calculate_poc(df, daily_window)
        vah, val = calculate_value_area(df, weekly_window)
        extremes = get_previous_period_extremes(df)
        sessions = get_session_extremes(df)

        key_levels = {
            "poc_weekly": self._sanitize_level(poc_weekly),
            "poc_daily": self._sanitize_level(poc_daily),
            "vah": self._sanitize_level(vah),
            "val": self._sanitize_level(val),
            "pwh": self._sanitize_level(extremes.get("pwh")),
            "pwl": self._sanitize_level(extremes.get("pwl")),
            "pdh": self._sanitize_level(extremes.get("pdh")),
            "pdl": self._sanitize_level(extremes.get("pdl")),
            "sessions": {
                name: {
                    "high": self._sanitize_level(values.get("high")) if isinstance(values, dict) else None,
                    "low": self._sanitize_level(values.get("low")) if isinstance(values, dict) else None,
                }
                for name, values in sessions.items()
            }
            if isinstance(sessions, dict)
            else {},
        }

        self._key_levels_cache[symbol] = {"timestamp": now, "data": copy.deepcopy(key_levels)}
        return copy.deepcopy(key_levels)

    def _build_indicator_context(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        vwap = self._sanitize_level(self._get_last_indicator(df, "vwap"))
        ema_50 = self._sanitize_level(self._get_last_indicator(df, "ema_50"))
        vwap_session = self._sanitize_level(self._get_session_vwap_value(df))
        return {
            "vwap": vwap,
            "ema_50": ema_50,
            "vwap_session": vwap_session,
        }

    def _detect_previous_extreme_sweep(
        self,
        df: pd.DataFrame,
        key_levels: Dict[str, object],
        direction: str,
        lookback: int = 4,
    ) -> bool:
        if df is None or df.empty:
            return False

        direction = direction.upper()
        if direction == "LONG":
            levels = [self._sanitize_level(key_levels.get("pdl")), self._sanitize_level(key_levels.get("pwl"))]
            return any(self._did_price_sweep(df, level, "LONG", lookback) for level in levels if level)
        if direction == "SHORT":
            levels = [self._sanitize_level(key_levels.get("pdh")), self._sanitize_level(key_levels.get("pwh"))]
            return any(self._did_price_sweep(df, level, "SHORT", lookback) for level in levels if level)
        return False

    def _did_price_sweep(self, df: pd.DataFrame, level: Optional[float], direction: str, lookback: int) -> bool:
        if level is None or level <= 0:
            return False
        if df is None or df.empty:
            return False

        recent = df.tail(max(lookback, 2))
        if len(recent) < 2:
            return False

        direction = direction.upper()
        if direction == "LONG":
            swept = float(recent["low"].min()) < level * 0.999
            closed_above = float(recent["close"].iloc[-1]) > level
            return bool(swept and closed_above)
        if direction == "SHORT":
            swept = float(recent["high"].max()) > level * 1.001
            closed_below = float(recent["close"].iloc[-1]) < level
            return bool(swept and closed_below)
        return False

    def _get_session_vwap_value(self, df: pd.DataFrame, session_start_hour: int = 13) -> float:
        try:
            session_vwap = self.technical_indicators.calculate_session_vwap(df, session_start_hour=session_start_hour)
        except Exception:
            return float("nan")
        if session_vwap is None or len(session_vwap) == 0:
            return float("nan")
        return float(session_vwap.iloc[-1])

    @staticmethod
    def _sanitize_level(value: object) -> Optional[float]:
        if value is None:
            return None
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(result) or math.isinf(result):
            return None
        return result

    @staticmethod
    def _get_last_indicator(df: pd.DataFrame, column: str) -> float:
        if column not in df:
            return float("nan")
        series = df[column].dropna()
        if series.empty:
            return float("nan")
        return float(series.iloc[-1])
