from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd

from indicators.market_structure import MarketStructure


class BTCFilter:
    """
    Analiza BTC primero para determinar contexto macro del mercado.
    Todas las señales de alts se ajustan según estado de BTC.
    """

    def __init__(self) -> None:
        self._market_structure = MarketStructure()

    def analyze_btc_context(self, btc_df_4h: pd.DataFrame, btc_df_1h: pd.DataFrame) -> Dict[str, object]:
        """
        Analiza BTC y retorna contexto completo.
        """
        if btc_df_4h is None or btc_df_1h is None:
            raise ValueError("Se requieren dataframes 4H y 1H para analizar BTC")
        if btc_df_4h.empty or btc_df_1h.empty:
            return {
                "trend": "INESTABLE",
                "trend_strength": 0.0,
                "volatility": "ALTA",
                "session_quality": self._get_session_quality(),
                "multiplier_long": 0.2,
                "multiplier_short": 0.2,
                "should_trade": False,
                "current_price": float(btc_df_1h["close"].iloc[-1]) if not btc_df_1h.empty else float("nan"),
                "atr": float("nan"),
                "adx": float("nan"),
            }

        trend_info = self._get_trend_from_df(btc_df_4h)
        volatility = self._calculate_volatility(btc_df_4h)
        session = self._get_session_quality()
        multipliers = self._calculate_multipliers(trend_info, volatility)
        should_trade = self._should_trade_decision(trend_info, volatility)

        current_price = float(btc_df_1h["close"].iloc[-1])
        atr_value = float(btc_df_4h.get("atr", pd.Series([np.nan])).iloc[-1])
        adx_value = float(btc_df_4h.get("adx", pd.Series([np.nan])).iloc[-1])

        return {
            "trend": trend_info.get("trend", "INESTABLE"),
            "trend_strength": float(trend_info.get("trend_strength", 0.0)),
            "volatility": volatility,
            "session_quality": session,
            "multiplier_long": multipliers["long"],
            "multiplier_short": multipliers["short"],
            "should_trade": should_trade,
            "current_price": current_price,
            "atr": atr_value,
            "adx": adx_value,
        }

    def _get_session_quality(self) -> str:
        """
        Determina calidad de sesión actual basado en hora UTC.

        ALTA: 13:00-17:00 UTC (NY session)
        MEDIA: 7:00-12:00 UTC (London session)
        BAJA: Resto
        """
        hour_utc = datetime.utcnow().hour
        if 13 <= hour_utc < 17:
            return "ALTA"
        if 7 <= hour_utc < 13:
            return "MEDIA"
        return "BAJA"

    def _calculate_volatility(self, df: pd.DataFrame, lookback: int = 20) -> str:
        """
        Compara ATR actual vs promedio 20 días.
        ALTA: ATR > promedio × 1.5
        """
        if df.empty or "atr" not in df.columns:
            return "NORMAL"

        recent = df["atr"].dropna()
        if recent.empty:
            return "NORMAL"

        atr_current = float(recent.iloc[-1])
        window = recent.iloc[-lookback:] if len(recent) >= lookback else recent
        atr_mean = float(window.mean()) if not window.empty else atr_current

        if atr_mean <= 0:
            return "NORMAL"
        if atr_current > atr_mean * 1.5:
            return "ALTA"
        if atr_current < atr_mean * 0.7:
            return "BAJA"
        return "NORMAL"

    def _calculate_multipliers(self, trend_info: Dict[str, object], volatility: str) -> Dict[str, float]:
        """
        Calcula multiplicadores de confianza para señales LONG/SHORT en alts.
        """
        trend = str(trend_info.get("trend", "INESTABLE")).upper()

        long_multiplier = 0.7
        short_multiplier = 0.7

        if "ALCISTA" in trend:
            long_multiplier = 1.2 if "FUERTE" in trend else 1.0
            short_multiplier = 0.3 if "FUERTE" in trend else 0.4
        elif "BAJISTA" in trend:
            long_multiplier = 0.4 if "FUERTE" in trend else 0.5
            short_multiplier = 1.2 if "FUERTE" in trend else 1.0
        elif trend == "LATERAL":
            long_multiplier = short_multiplier = 0.7
        else:  # INESTABLE u otros
            long_multiplier = short_multiplier = 0.2

        if volatility.upper() == "ALTA":
            long_multiplier = max(0.2, long_multiplier * 0.5)
            short_multiplier = max(0.2, short_multiplier * 0.5)
        elif volatility.upper() == "BAJA":
            long_multiplier = min(1.2, long_multiplier * 1.1)
            short_multiplier = min(1.2, short_multiplier * 1.1)

        return {"long": float(round(long_multiplier, 2)), "short": float(round(short_multiplier, 2))}

    def _should_trade_decision(self, trend_info: Dict[str, object], volatility: str) -> bool:
        trend = str(trend_info.get("trend", "INESTABLE")).upper()
        strength = float(trend_info.get("trend_strength", 0.0))

        if trend == "INESTABLE":
            return False
        if volatility.upper() == "ALTA" and strength < 35:
            return False
        if trend == "LATERAL" and strength < 20:
            return False
        return True

    def _get_trend_from_df(self, df: pd.DataFrame) -> Dict[str, object]:
        if df.empty:
            return {
                "trend": "INESTABLE",
                "trend_strength": 0.0,
                "structure": "MIXED",
                "ema_alignment": False,
                "adx_value": 0.0,
            }

        swings = self._market_structure.detect_swing_points(df)
        return self._market_structure.determine_trend(swings)
