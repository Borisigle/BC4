from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from config import settings
from data.data_storage import DataStorage
from indicators.market_structure import MarketStructure
from indicators.technical_indicators import TechnicalIndicators
from utils.logger import get_logger
from .btc_filter import BTCFilter
from .signal import Signal
from .signal_detector import SignalDetector
from .signal_scorer import SignalScorer

logger = get_logger(__name__)


class SignalEngine:
    """Motor principal que orquesta todo el análisis."""

    def __init__(self) -> None:
        self.storage = DataStorage(settings.DB_PATH)
        self.technical_indicators = TechnicalIndicators()
        self.market_structure = MarketStructure()
        self.btc_filter = BTCFilter()
        self.signal_detector = SignalDetector()
        self.signal_scorer = SignalScorer()

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

            long_setup = self.signal_detector.detect_long_setup(df_4h_struct, df_1h, market_structure)
            short_setup = self.signal_detector.detect_short_setup(df_4h_struct, df_1h, market_structure)

            for setup in [long_setup, short_setup]:
                if not setup:
                    continue

                score_result = self.signal_scorer.calculate_final_score(setup, btc_context, symbol)

                if not score_result.get("should_alert", False):
                    continue

                try:
                    signal = self._create_signal(symbol, setup, score_result, btc_context, df_1h)
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

    def _create_signal(
        self,
        symbol: str,
        setup: Dict[str, object],
        score_result: Dict[str, object],
        btc_context: Dict[str, object],
        df_1h: pd.DataFrame,
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
        )

    @staticmethod
    def _get_last_indicator(df: pd.DataFrame, column: str) -> float:
        if column not in df:
            return float("nan")
        series = df[column].dropna()
        if series.empty:
            return float("nan")
        return float(series.iloc[-1])
