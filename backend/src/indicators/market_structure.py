from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from ..utils.dataframe_helpers import require_columns


@dataclass
class _Zone:
    price: float
    touches: int

    def register(self, price: float, weight: float = 1.0) -> None:
        total_weight = self.touches + weight
        self.price = (self.price * self.touches + price * weight) / total_weight
        self.touches = int(total_weight)


class MarketStructure:
    """Market structure utilities to analyse swings and trend context."""

    @staticmethod
    def detect_swing_points(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """
        Identify swing highs and lows using a centered rolling window.

        Args:
            df: DataFrame containing high/low columns.
            window: Number of candles to compare on each side.

        Returns:
            DataFrame copy with swing_high and swing_low columns.
        """
        if window <= 0:
            raise ValueError("window must be positive")

        require_columns(df, ["high", "low"])

        result = df.copy()
        lookback = window * 2 + 1

        rolling_high = result["high"].rolling(window=lookback, center=True, min_periods=lookback).max()
        rolling_low = result["low"].rolling(window=lookback, center=True, min_periods=lookback).min()

        result["swing_high"] = result["high"].where(result["high"] == rolling_high)
        result["swing_low"] = result["low"].where(result["low"] == rolling_low)
        return result

    @staticmethod
    def identify_support_resistance(
        df: pd.DataFrame,
        tolerance: float = 0.005,
        min_touches: int = 2,
        lookback: int = 100,
    ) -> Dict[str, List[Dict[str, float | int | str]]]:
        """
        Group swing points into support and resistance zones.
        """
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        if min_touches < 1:
            raise ValueError("min_touches must be at least 1")
        if lookback <= 0:
            raise ValueError("lookback must be positive")

        require_columns(df, ["close", "swing_high", "swing_low"])

        data = df.iloc[-lookback:] if len(df) > lookback else df
        current_price = float(data["close"].iloc[-1])

        resistances = MarketStructure._cluster_levels(data["swing_high"].dropna(), tolerance)
        supports = MarketStructure._cluster_levels(data["swing_low"].dropna(), tolerance)

        resistances = [zone for zone in resistances if zone.touches >= min_touches]
        supports = [zone for zone in supports if zone.touches >= min_touches]

        def _format_zone(zone: _Zone) -> Dict[str, float | int | str]:
            if zone.touches >= 3:
                strength = "strong"
            elif zone.touches == 2:
                strength = "medium"
            else:
                strength = "weak"
            return {
                "price": float(zone.price),
                "touches": int(zone.touches),
                "strength": strength,
            }

        def _sort_key(zone: _Zone) -> Tuple[int, float]:
            if zone.touches >= 3:
                rank = 0
            elif zone.touches == 2:
                rank = 1
            else:
                rank = 2
            return rank, abs(zone.price - current_price)

        resistances_sorted = sorted(resistances, key=_sort_key)
        supports_sorted = sorted(supports, key=_sort_key)

        return {
            "resistances": [_format_zone(zone) for zone in resistances_sorted],
            "supports": [_format_zone(zone) for zone in supports_sorted],
        }

    @staticmethod
    def _cluster_levels(prices: Iterable[float], tolerance: float) -> List[_Zone]:
        levels: List[_Zone] = []

        for value in sorted(prices):
            if np.isnan(value):
                continue

            matched = False
            for level in levels:
                if abs(value - level.price) / max(level.price, 1e-8) <= tolerance:
                    level.register(value)
                    matched = True
                    break
            if not matched:
                levels.append(_Zone(price=float(value), touches=1))

        return levels

    @staticmethod
    def determine_trend(df: pd.DataFrame, lookback: int = 20) -> Dict[str, float | str | bool]:
        """
        Determine directional bias leveraging swings, EMAs, and ADX.
        """
        if lookback <= 0:
            raise ValueError("lookback must be positive")

        required = ["close", "ema_20", "ema_50", "adx", "swing_high", "swing_low"]
        require_columns(df, required)

        recent = df.iloc[-lookback:] if len(df) > lookback else df
        last_row = recent.iloc[-1]
        last_close = float(last_row["close"])
        ema20 = float(last_row["ema_20"])
        ema50 = float(last_row["ema_50"])
        adx_value = float(last_row["adx"])

        recent_highs = recent.loc[recent["swing_high"].notna(), "swing_high"]
        recent_lows = recent.loc[recent["swing_low"].notna(), "swing_low"]

        structure = "MIXED"
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            last_two_highs = recent_highs.iloc[-2:]
            last_two_lows = recent_lows.iloc[-2:]
            if last_two_highs.iloc[0] < last_two_highs.iloc[1] and last_two_lows.iloc[0] < last_two_lows.iloc[1]:
                structure = "HH/HL"
            elif last_two_highs.iloc[0] > last_two_highs.iloc[1] and last_two_lows.iloc[0] > last_two_lows.iloc[1]:
                structure = "LH/LL"

        bull_alignment = last_close > ema20 > ema50
        bear_alignment = last_close < ema20 < ema50
        ema_alignment = bull_alignment or bear_alignment

        trend_strength = float(np.clip(adx_value, 0, 100))

        trend = "INESTABLE"
        if adx_value < 20:
            trend = "LATERAL"
        elif structure == "HH/HL" and bull_alignment and adx_value >= 25:
            trend = "ALCISTA_FUERTE"
        elif structure == "LH/LL" and bear_alignment and adx_value >= 25:
            trend = "BAJISTA_FUERTE"

        return {
            "trend": trend,
            "trend_strength": trend_strength,
            "structure": structure,
            "ema_alignment": ema_alignment,
            "adx_value": float(adx_value),
        }
