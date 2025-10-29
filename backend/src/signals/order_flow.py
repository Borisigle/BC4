from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


class OrderFlowAnalyzer:
    """
    Analiza presión compradora/vendedora.
    Inicialmente simulado con volumen y price action.
    Futuro: CVD real desde exchange.
    """

    def analyze_volume_pressure(self, df: pd.DataFrame, lookback: int = 4) -> Dict[str, object]:
        """
        Analiza presión de volumen en últimas velas.
        """
        if df is None or df.empty:
            return {
                "pressure": "NEUTRAL",
                "strength": 0.0,
                "volume_ratio": 0.0,
                "score": 0,
            }

        window = df.tail(max(lookback, 1))
        previous = df.iloc[-(lookback * 2): -lookback] if len(df) >= lookback * 2 else df.iloc[:-lookback]

        bullish_volume = window.loc[window["close"] > window["open"], "volume"].sum()
        bearish_volume = window.loc[window["close"] < window["open"], "volume"].sum()
        total_volume = bullish_volume + bearish_volume

        if total_volume == 0:
            pressure = "NEUTRAL"
            strength = 0.0
        else:
            ratio = (bullish_volume - bearish_volume) / total_volume
            strength = float(abs(ratio) * 100)
            if ratio > 0.15:
                pressure = "BUYING"
            elif ratio < -0.15:
                pressure = "SELLING"
            else:
                pressure = "NEUTRAL"

        last_volume = float(window["volume"].iloc[-1])
        mean_volume = previous["volume"].mean() if not previous.empty else df["volume"].iloc[:-1].mean()
        if mean_volume is None or np.isnan(mean_volume) or mean_volume <= 0:
            volume_ratio = 0.0
        else:
            volume_ratio = float(last_volume / mean_volume)

        score = int(min(20, round(strength / 5)))
        return {
            "pressure": pressure,
            "strength": round(strength, 2),
            "volume_ratio": round(volume_ratio, 2),
            "score": score,
        }

    def detect_divergence(self, df: pd.DataFrame) -> Optional[Dict[str, object]]:
        """
        Detecta divergencias precio vs volumen (simulado).
        """
        if df is None or len(df) < 8:
            return None

        window = 4
        recent = df.tail(window)
        previous = df.iloc[-(window * 2):-window]
        if previous.empty:
            return None

        recent_low = recent["low"].min()
        previous_low = previous["low"].min()
        recent_high = recent["high"].max()
        previous_high = previous["high"].max()

        recent_buy_volume = recent.loc[recent["close"] > recent["open"], "volume"].sum()
        previous_buy_volume = previous.loc[previous["close"] > previous["open"], "volume"].sum()
        recent_sell_volume = recent.loc[recent["close"] < recent["open"], "volume"].sum()
        previous_sell_volume = previous.loc[previous["close"] < previous["open"], "volume"].sum()

        # Divergencia alcista: precio hace lower low pero compra aumenta
        bullish = recent_low < previous_low and recent_buy_volume > previous_buy_volume * 1.1
        # Divergencia bajista: precio hace higher high pero venta aumenta
        bearish = recent_high > previous_high and recent_sell_volume > previous_sell_volume * 1.1

        if bullish and not bearish:
            ratio = recent_buy_volume / max(previous_buy_volume, 1e-8)
            strength = "STRONG" if ratio > 1.5 else "WEAK"
            return {
                "type": "BULLISH",
                "strength": strength,
                "bonus_score": 15,
            }

        if bearish and not bullish:
            ratio = recent_sell_volume / max(previous_sell_volume, 1e-8)
            strength = "STRONG" if ratio > 1.5 else "WEAK"
            return {
                "type": "BEARISH",
                "strength": strength,
                "bonus_score": 15,
            }

        return None
