from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .order_flow import OrderFlowAnalyzer
from .pattern_detector import PatternDetector


class SignalDetector:
    """Detecta setups de trading individuales para un activo."""

    def __init__(self) -> None:
        self.pattern_detector = PatternDetector()
        self.orderflow_analyzer = OrderFlowAnalyzer()

    def detect_long_setup(
        self,
        df_4h: pd.DataFrame,
        df_1h: pd.DataFrame,
        cvd_4h: np.ndarray,
        cvd_1h: np.ndarray,
        market_structure: Dict[str, object],
    ) -> Optional[Dict[str, object]]:
        if df_4h is None or df_4h.empty or df_1h is None or df_1h.empty:
            return None

        current_price = float(df_1h["close"].iloc[-1])
        vwap_value = float(df_1h.get("vwap", pd.Series([np.nan])).iloc[-1]) if "vwap" in df_1h else np.nan

        supports = market_structure.get("supports", []) or []
        trend_info = market_structure.get("trend", {}) or {}

        support_level, support_distance = self._find_closest_level(current_price, supports)

        reasons: List[str] = []
        base_score = 0

        structure_conditions = [
            support_level is not None and support_distance <= 0.01,
            "ALCISTA" in str(trend_info.get("trend", "")).upper(),
            str(trend_info.get("structure", "")).upper() == "HH/HL",
            not np.isnan(vwap_value) and current_price >= vwap_value * 0.995,
        ]
        structure_valid = all(structure_conditions)
        if structure_valid:
            base_score += 20
            reasons.append(f"Estructura 4H alcista (HL cerca de soporte {support_level:.2f})")
            reasons.append("Precio sosteniéndose sobre VWAP 1H")
        else:
            return None

        orderflow_result = self.orderflow_analyzer.analyze_volume_pressure(df_1h, cvd_1h, lookback=4)
        orderflow_valid = orderflow_result["pressure"] == "BUYING" and orderflow_result["score"] >= 15
        if not orderflow_valid:
            return None

        base_score += int(orderflow_result["score"])
        reasons.append(
            "Presión compradora real (ΔCVD %.2f | score %d)"
            % (orderflow_result["cvd_change_normalized"], int(orderflow_result["score"]))
        )

        divergence = self.orderflow_analyzer.detect_cvd_divergence(df_1h["close"], cvd_1h, lookback=20)
        if divergence and divergence.get("type") == "BULLISH":
            base_score += int(divergence.get("bonus_score", 0))
            reasons.append(f"Divergencia CVD alcista ({divergence['strength']})")
        else:
            divergence = None

        patterns = self.pattern_detector.get_all_patterns(df_1h, support_level, None)
        pattern_valid = bool(patterns["bullish"])
        if pattern_valid:
            base_score += min(10, int(patterns["score"]))
            for pattern in patterns["bullish"]:
                reasons.append(f"Patrón alcista: {pattern}")

        liquidity_sweep = self._detect_liquidity_sweep_long(df_1h, support_level)
        if liquidity_sweep:
            base_score += 10
            reasons.append("Liquidity sweep completado en soporte")

        entry_zone = self._build_entry_zone_long(current_price, support_level)

        return {
            "direction": "LONG",
            "base_score": base_score,
            "structure_valid": structure_valid,
            "orderflow_valid": orderflow_valid,
            "pattern_valid": pattern_valid,
            "liquidity_sweep": liquidity_sweep,
            "reasons": reasons,
            "support_level": support_level,
            "entry_zone": entry_zone,
            "divergence": divergence,
        }

    def detect_short_setup(
        self,
        df_4h: pd.DataFrame,
        df_1h: pd.DataFrame,
        cvd_4h: np.ndarray,
        cvd_1h: np.ndarray,
        market_structure: Dict[str, object],
    ) -> Optional[Dict[str, object]]:
        if df_4h is None or df_4h.empty or df_1h is None or df_1h.empty:
            return None

        current_price = float(df_1h["close"].iloc[-1])
        vwap_value = float(df_1h.get("vwap", pd.Series([np.nan])).iloc[-1]) if "vwap" in df_1h else np.nan

        resistances = market_structure.get("resistances", []) or []
        trend_info = market_structure.get("trend", {}) or {}

        resistance_level, resistance_distance = self._find_closest_level(current_price, resistances)

        reasons: List[str] = []
        base_score = 0

        structure_conditions = [
            resistance_level is not None and resistance_distance <= 0.01,
            "BAJISTA" in str(trend_info.get("trend", "")).upper(),
            str(trend_info.get("structure", "")).upper() == "LH/LL",
            not np.isnan(vwap_value) and current_price <= vwap_value * 1.005,
        ]
        structure_valid = all(structure_conditions)
        if structure_valid:
            base_score += 20
            reasons.append(
                f"Estructura 4H bajista (LH cerca de resistencia {resistance_level:.2f})"
            )
            reasons.append("Precio rechazado desde VWAP 1H")
        else:
            return None

        orderflow_result = self.orderflow_analyzer.analyze_volume_pressure(df_1h, cvd_1h, lookback=4)
        orderflow_valid = orderflow_result["pressure"] == "SELLING" and orderflow_result["score"] >= 15
        if not orderflow_valid:
            return None

        base_score += int(orderflow_result["score"])
        reasons.append(
            "Presión vendedora real (ΔCVD %.2f | score %d)"
            % (orderflow_result["cvd_change_normalized"], int(orderflow_result["score"]))
        )

        divergence = self.orderflow_analyzer.detect_cvd_divergence(df_1h["close"], cvd_1h, lookback=20)
        if divergence and divergence.get("type") == "BEARISH":
            base_score += int(divergence.get("bonus_score", 0))
            reasons.append(f"Divergencia CVD bajista ({divergence['strength']})")
        else:
            divergence = None

        patterns = self.pattern_detector.get_all_patterns(df_1h, None, resistance_level)
        pattern_valid = bool(patterns["bearish"])
        if pattern_valid:
            base_score += min(10, int(patterns["score"]))
            for pattern in patterns["bearish"]:
                reasons.append(f"Patrón bajista: {pattern}")

        liquidity_sweep = self._detect_liquidity_sweep_short(df_1h, resistance_level)
        if liquidity_sweep:
            base_score += 10
            reasons.append("Liquidity sweep de máximos completado")

        entry_zone = self._build_entry_zone_short(current_price, resistance_level)

        return {
            "direction": "SHORT",
            "base_score": base_score,
            "structure_valid": structure_valid,
            "orderflow_valid": orderflow_valid,
            "pattern_valid": pattern_valid,
            "liquidity_sweep": liquidity_sweep,
            "reasons": reasons,
            "resistance_level": resistance_level,
            "entry_zone": entry_zone,
            "divergence": divergence,
        }

    def _find_closest_level(
        self,
        current_price: float,
        levels: List[Dict[str, float]],
    ) -> Tuple[Optional[float], float]:
        best_level = None
        best_distance = float("inf")
        for level in levels:
            price = level.get("price")
            if price is None:
                continue
            distance = abs(current_price - price) / max(price, 1e-8)
            if distance < best_distance:
                best_distance = distance
                best_level = float(price)
        if best_level is None:
            return None, float("inf")
        return best_level, best_distance

    def _detect_liquidity_sweep_long(self, df: pd.DataFrame, support_level: Optional[float]) -> bool:
        if support_level is None or len(df) < 2:
            return False
        recent = df.tail(2)
        swept = recent["low"].min() < support_level * 0.998
        closed_above = float(df["close"].iloc[-1]) > support_level
        return bool(swept and closed_above)

    def _detect_liquidity_sweep_short(self, df: pd.DataFrame, resistance_level: Optional[float]) -> bool:
        if resistance_level is None or len(df) < 2:
            return False
        recent = df.tail(2)
        swept = recent["high"].max() > resistance_level * 1.002
        closed_below = float(df["close"].iloc[-1]) < resistance_level
        return bool(swept and closed_below)

    def _build_entry_zone_long(self, current_price: float, support_level: Optional[float]) -> Tuple[float, float]:
        if support_level is None:
            delta = current_price * 0.005
            return current_price - delta, current_price + delta
        lower = support_level * 0.998
        upper = support_level * 1.004
        return lower, upper

    def _build_entry_zone_short(self, current_price: float, resistance_level: Optional[float]) -> Tuple[float, float]:
        if resistance_level is None:
            delta = current_price * 0.005
            return current_price - delta, current_price + delta
        lower = resistance_level * 0.996
        upper = resistance_level * 1.002
        return lower, upper

    def _average_volume(self, df: pd.DataFrame, window: int = 20) -> float:
        if df is None or len(df) < 2:
            return 0.0
        historical = df["volume"].iloc[-window - 1 : -1] if len(df) > window else df["volume"].iloc[:-1]
        avg = historical.mean()
        return float(avg) if not np.isnan(avg) else 0.0
