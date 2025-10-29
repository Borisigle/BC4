from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd


class PatternDetector:
    """Detecta patrones de velas japonesas."""

    @staticmethod
    def detect_bullish_engulfing(df: pd.DataFrame) -> bool:
        """
        Detecta Bullish Engulfing en últimas 2 velas.

        Requisitos:
        - Vela anterior bajista (close < open)
        - Vela actual alcista (close > open)
        - Body actual > body anterior
        - Vela actual engulle completamente a la anterior
        """
        if df is None or len(df) < 2:
            return False

        last_two = df.tail(2)
        prev = last_two.iloc[0]
        curr = last_two.iloc[1]

        prev_bearish = prev["close"] < prev["open"]
        curr_bullish = curr["close"] > curr["open"]
        if not (prev_bearish and curr_bullish):
            return False

        prev_body = abs(prev["close"] - prev["open"])
        curr_body = abs(curr["close"] - curr["open"])
        if curr_body <= prev_body * 1.05:  # asegurar cuerpo más grande
            return False

        engulfing = curr["open"] <= prev["close"] and curr["close"] >= prev["open"]
        return bool(engulfing)

    @staticmethod
    def detect_bearish_engulfing(df: pd.DataFrame) -> bool:
        """Detecta Bearish Engulfing."""
        if df is None or len(df) < 2:
            return False

        last_two = df.tail(2)
        prev = last_two.iloc[0]
        curr = last_two.iloc[1]

        prev_bullish = prev["close"] > prev["open"]
        curr_bearish = curr["close"] < curr["open"]
        if not (prev_bullish and curr_bearish):
            return False

        prev_body = abs(prev["close"] - prev["open"])
        curr_body = abs(curr["close"] - curr["open"])
        if curr_body <= prev_body * 1.05:
            return False

        engulfing = curr["open"] >= prev["close"] and curr["close"] <= prev["open"]
        return bool(engulfing)

    @staticmethod
    def detect_hammer(df: pd.DataFrame, at_support: bool = False, support_zone: Optional[float] = None) -> bool:
        """
        Detecta Hammer (señal alcista).

        Requisitos:
        - Mecha inferior larga (>2x del body)
        - Mecha superior pequeña o inexistente
        - Body en parte superior de la vela
        - Bonus si está en zona de soporte
        """
        if df is None or df.empty:
            return False

        candle = df.iloc[-1]
        open_price = float(candle["open"])
        close_price = float(candle["close"])
        high_price = float(candle["high"])
        low_price = float(candle["low"])

        body = abs(close_price - open_price)
        if body == 0:
            return False

        lower_wick = min(open_price, close_price) - low_price
        upper_wick = high_price - max(open_price, close_price)

        body_top = max(open_price, close_price)
        in_upper_half = body_top >= high_price - body * 0.5

        conditions = [
            lower_wick >= body * 2,
            upper_wick <= body * 0.5,
            in_upper_half,
        ]

        if at_support and support_zone is not None:
            distance = abs(close_price - support_zone) / max(support_zone, 1e-8)
            conditions.append(distance <= 0.01)

        return all(conditions)

    @staticmethod
    def detect_shooting_star(df: pd.DataFrame, at_resistance: bool = False, resistance_zone: Optional[float] = None) -> bool:
        """Detecta Shooting Star (señal bajista)."""
        if df is None or df.empty:
            return False

        candle = df.iloc[-1]
        open_price = float(candle["open"])
        close_price = float(candle["close"])
        high_price = float(candle["high"])
        low_price = float(candle["low"])

        body = abs(close_price - open_price)
        if body == 0:
            return False

        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price

        body_bottom = min(open_price, close_price)
        in_lower_half = body_bottom <= low_price + body * 0.5

        conditions = [
            upper_wick >= body * 2,
            lower_wick <= body * 0.5,
            in_lower_half,
        ]

        if at_resistance and resistance_zone is not None:
            distance = abs(close_price - resistance_zone) / max(resistance_zone, 1e-8)
            conditions.append(distance <= 0.01)

        return all(conditions)

    @staticmethod
    def detect_three_consecutive(df: pd.DataFrame, direction: str) -> bool:
        """
        Detecta 3 velas consecutivas verdes/rojas con volumen creciente.
        """
        if df is None or len(df) < 3:
            return False

        candles = df.tail(3)
        direction = direction.lower()

        is_green = candles["close"] > candles["open"]
        is_red = candles["close"] < candles["open"]

        volumes = candles["volume"].values
        volume_increasing = all(volumes[i] >= volumes[i - 1] * 0.95 for i in range(1, len(volumes)))

        if direction in {"long", "bullish", "buy"}:
            return bool(is_green.all() and volume_increasing)
        if direction in {"short", "bearish", "sell"}:
            return bool(is_red.all() and volume_increasing)
        return False

    def get_all_patterns(
        self,
        df: pd.DataFrame,
        support_zone: Optional[float] = None,
        resistance_zone: Optional[float] = None,
    ) -> Dict[str, object]:
        """
        Detecta todos los patrones disponibles.

        Returns:
            {
                'bullish': ['engulfing', 'hammer'],
                'bearish': [],
                'score': 10  # Puntos por patrones detectados
            }
        """
        bullish: List[str] = []
        bearish: List[str] = []

        if self.detect_bullish_engulfing(df):
            bullish.append("engulfing")
        if self.detect_hammer(df, at_support=support_zone is not None, support_zone=support_zone):
            bullish.append("hammer")
        if self.detect_three_consecutive(df, "bullish"):
            bullish.append("3_consecutive")

        if self.detect_bearish_engulfing(df):
            bearish.append("engulfing")
        if self.detect_shooting_star(df, at_resistance=resistance_zone is not None, resistance_zone=resistance_zone):
            bearish.append("shooting_star")
        if self.detect_three_consecutive(df, "bearish"):
            bearish.append("3_consecutive")

        # Consolidar score: 10 puntos si hay algún patrón, 0 si no.
        has_pattern = bool(bullish or bearish)
        score = 10 if has_pattern else 0

        return {"bullish": bullish, "bearish": bearish, "score": score}
