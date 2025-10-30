from __future__ import annotations

import math
from typing import Dict, Optional

from .confluence_detector import ConfluenceDetector


class SignalScorer:
    """Sistema de scoring avanzado para señales."""

    def __init__(self, confluence_detector: Optional[ConfluenceDetector] = None) -> None:
        self.confluence_detector = confluence_detector or ConfluenceDetector()

    def calculate_final_score(
        self,
        setup: Dict[str, object],
        btc_context: Dict[str, object],
        symbol: str,
        current_price: float,
        key_levels: Dict[str, Optional[float]],
        indicator_context: Dict[str, Optional[float]],
    ) -> Dict[str, object]:
        direction = str(setup.get("direction", "LONG")).upper()

        base_components = self._calculate_base_components(direction, setup, current_price, key_levels, indicator_context)
        base_score = sum(base_components.values())
        base_score = min(base_score, 80.0)

        confluence_levels = self._build_confluence_levels(direction, setup, key_levels, indicator_context)
        confluence_data = self.confluence_detector.detect_confluences(current_price, confluence_levels)
        confluence_bonus = self._calculate_confluence_bonus(confluence_data)
        base_with_multiplier = base_score * float(confluence_data.get("multiplier", 1.0))

        btc_multiplier = self._select_multiplier(direction, btc_context)

        session_quality = str(btc_context.get("session_quality", "BAJA"))
        session_bonus = self._calculate_session_bonus(session_quality)
        correlation_bonus = self._calculate_correlation_bonus(symbol, btc_context, direction)
        divergence_bonus = int(setup.get("divergence", {}).get("bonus_score", 0)) if setup.get("divergence") else 0

        other_bonuses = session_bonus + correlation_bonus + divergence_bonus
        penalties = 0

        final_score = (base_with_multiplier + confluence_bonus) * btc_multiplier + other_bonuses
        confidence = self._determine_confidence(final_score)
        should_alert = final_score >= 60

        return {
            "final_score": round(final_score, 2),
            "base_score": round(base_score, 2),
            "btc_multiplier": round(btc_multiplier, 2),
            "bonus": int(other_bonuses + confluence_bonus),
            "penalties": int(penalties),
            "confidence": confidence,
            "should_alert": should_alert,
            "confluence": {
                "count": int(confluence_data.get("count", 0)),
                "levels": list(confluence_data.get("levels", [])),
                "multiplier": float(confluence_data.get("multiplier", 1.0)),
                "bonus": int(confluence_bonus),
            },
            "base_components": base_components,
            "session_bonus": session_bonus,
            "correlation_bonus": correlation_bonus,
            "divergence_bonus": divergence_bonus,
        }

    def _calculate_base_components(
        self,
        direction: str,
        setup: Dict[str, object],
        current_price: float,
        key_levels: Dict[str, Optional[float]],
        indicator_context: Dict[str, Optional[float]],
    ) -> Dict[str, float]:
        structure = self._structure_score(direction, setup, current_price, key_levels)
        order_flow = self._order_flow_score(setup)
        patterns = self._pattern_score(setup)
        liquidity = self._liquidity_score(setup)
        key_level_score = self._key_level_score(direction, current_price, key_levels, indicator_context)

        return {
            "structure": structure,
            "order_flow": order_flow,
            "patterns": patterns,
            "liquidity": liquidity,
            "key_levels": key_level_score,
        }

    def _structure_score(
        self,
        direction: str,
        setup: Dict[str, object],
        current_price: float,
        key_levels: Dict[str, Optional[float]],
    ) -> float:
        score = 0.0
        support_tolerance = 0.01
        poc_tolerance = 0.005

        if direction == "LONG":
            support = self._to_float(setup.get("support_level"))
            if support and support > 0:
                distance = abs(current_price - support) / max(support, 1e-8)
                if distance <= support_tolerance:
                    score += 15
            poc_weekly = self._to_float(key_levels.get("poc_weekly"))
            if poc_weekly and poc_weekly > 0:
                distance_poc = abs(current_price - poc_weekly) / max(poc_weekly, 1e-8)
                if distance_poc <= poc_tolerance:
                    score += 5
        else:
            resistance = self._to_float(setup.get("resistance_level"))
            if resistance and resistance > 0:
                distance = abs(current_price - resistance) / max(resistance, 1e-8)
                if distance <= support_tolerance:
                    score += 15
            poc_weekly = self._to_float(key_levels.get("poc_weekly"))
            if poc_weekly and poc_weekly > 0:
                distance_poc = abs(current_price - poc_weekly) / max(poc_weekly, 1e-8)
                if distance_poc <= poc_tolerance:
                    score += 5

        return min(score, 20.0)

    def _order_flow_score(self, setup: Dict[str, object]) -> float:
        score = self._to_float(setup.get("orderflow_score")) or 0.0
        return float(max(0.0, min(score, 20.0)))

    def _pattern_score(self, setup: Dict[str, object]) -> float:
        score = self._to_float(setup.get("pattern_score")) or 0.0
        return float(max(0.0, min(score, 10.0)))

    def _liquidity_score(self, setup: Dict[str, object]) -> float:
        base = 10.0 if setup.get("liquidity_sweep") else 0.0
        extra = 5.0 if setup.get("previous_extreme_sweep") else 0.0
        return float(min(15.0, base + extra))

    def _key_level_score(
        self,
        direction: str,
        current_price: float,
        key_levels: Dict[str, Optional[float]],
        indicator_context: Dict[str, Optional[float]],
    ) -> float:
        score = 0.0
        tolerance_value_area = 0.005
        tolerance_vwap = 0.002

        vwap = self._to_float(indicator_context.get("vwap"))

        if direction == "LONG":
            val = self._to_float(key_levels.get("val"))
            if val and val > 0:
                distance = abs(current_price - val) / max(val, 1e-8)
                if distance <= tolerance_value_area:
                    score += 10
            if vwap and vwap > 0:
                distance_vwap = abs(current_price - vwap) / max(vwap, 1e-8)
                if distance_vwap <= tolerance_vwap:
                    score += 5
        else:
            vah = self._to_float(key_levels.get("vah"))
            if vah and vah > 0:
                distance = abs(current_price - vah) / max(vah, 1e-8)
                if distance <= tolerance_value_area:
                    score += 10
            if vwap and vwap > 0 and current_price <= vwap:
                distance_vwap = abs(current_price - vwap) / max(vwap, 1e-8)
                if distance_vwap <= tolerance_vwap:
                    score += 5

        return float(min(score, 15.0))

    def _build_confluence_levels(
        self,
        direction: str,
        setup: Dict[str, object],
        key_levels: Dict[str, Optional[float]],
        indicator_context: Dict[str, Optional[float]],
    ) -> Dict[str, Optional[float]]:
        levels: Dict[str, Optional[float]] = {
            "poc_weekly": key_levels.get("poc_weekly"),
            "poc_daily": key_levels.get("poc_daily"),
            "vwap": indicator_context.get("vwap"),
            "vwap_session": indicator_context.get("vwap_session"),
            "ema_50": indicator_context.get("ema_50"),
            "val": key_levels.get("val"),
            "vah": key_levels.get("vah"),
        }

        if direction == "LONG":
            levels["swing_support"] = setup.get("support_level")
            levels["pdl"] = key_levels.get("pdl")
            levels["pwl"] = key_levels.get("pwl")
        else:
            levels["swing_resistance"] = setup.get("resistance_level")
            levels["pdh"] = key_levels.get("pdh")
            levels["pwh"] = key_levels.get("pwh")

        return levels

    @staticmethod
    def _calculate_confluence_bonus(confluence_data: Dict[str, object]) -> float:
        count = int(confluence_data.get("count", 0))
        if count <= 1:
            return 0.0
        bonus = float((count - 1) * 10)
        if count >= 4:
            bonus += 20.0
        return bonus

    @staticmethod
    def _select_multiplier(direction: str, btc_context: Dict[str, object]) -> float:
        if direction == "LONG":
            return float(btc_context.get("multiplier_long", 0.7))
        return float(btc_context.get("multiplier_short", 0.7))

    def _calculate_session_bonus(self, session: str) -> int:
        session = session.upper()
        if session == "ALTA":
            return 10
        if session == "MEDIA":
            return 5
        return 0

    def _calculate_correlation_bonus(self, symbol: str, btc_context: Dict[str, object], direction: str) -> int:
        if symbol.upper().startswith("BTC"):
            return 0

        btc_trend = str(btc_context.get("trend", "LATERAL")).upper()
        if "ALCISTA" in btc_trend:
            return 10 if direction == "LONG" else -15
        if "BAJISTA" in btc_trend:
            return 10 if direction == "SHORT" else -15
        return 0

    @staticmethod
    def _determine_confidence(score: float) -> str:
        if score >= 110:
            return "ALTA"
        if score >= 85:
            return "MEDIA"
        return "BAJA"

    @staticmethod
    def _to_float(value: object) -> Optional[float]:
        if value is None:
            return None
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(result):
            return None
        return result
