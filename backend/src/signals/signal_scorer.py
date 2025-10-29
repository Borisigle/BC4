from __future__ import annotations

from typing import Dict


class SignalScorer:
    """Sistema de scoring para señales."""

    def calculate_final_score(self, setup: Dict[str, object], btc_context: Dict[str, object], symbol: str) -> Dict[str, object]:
        base_score = float(setup.get("base_score", 0.0))
        direction = str(setup.get("direction", "LONG")).upper()

        if direction == "LONG":
            multiplier = float(btc_context.get("multiplier_long", 0.7))
        else:
            multiplier = float(btc_context.get("multiplier_short", 0.7))

        bonus = 0
        session_quality = str(btc_context.get("session_quality", "BAJA"))
        bonus += self._calculate_session_bonus(session_quality)
        bonus += self._calculate_correlation_bonus(symbol, btc_context, direction)
        if setup.get("divergence"):
            bonus += 15

        penalties = 0

        final_score = (base_score * multiplier) + bonus - penalties
        final_score = max(0.0, min(100.0, final_score))

        confidence = self._determine_confidence(final_score)
        should_alert = final_score >= 70 or (50 <= final_score < 70 and confidence != "BAJA")

        return {
            "final_score": round(final_score, 2),
            "base_score": int(base_score),
            "btc_multiplier": round(multiplier, 2),
            "bonus": int(bonus),
            "penalties": int(penalties),
            "confidence": confidence,
            "should_alert": should_alert,
        }

    def _calculate_session_bonus(self, session: str) -> int:
        """ALTA: +10, MEDIA: +5, BAJA: 0"""
        session = session.upper()
        if session == "ALTA":
            return 10
        if session == "MEDIA":
            return 5
        return 0

    def _calculate_correlation_bonus(self, symbol: str, btc_context: Dict[str, object], direction: str) -> int:
        """
        Si ETH/SOL se mueve en misma dirección que BTC: +10
        Si se mueve contrario: -15
        """
        if symbol.upper().startswith("BTC"):
            return 0

        btc_trend = str(btc_context.get("trend", "LATERAL")).upper()
        if "ALCISTA" in btc_trend:
            return 10 if direction == "LONG" else -15
        if "BAJISTA" in btc_trend:
            return 10 if direction == "SHORT" else -15
        return 0

    def _determine_confidence(self, score: float) -> str:
        if score >= 80:
            return "ALTA"
        if score >= 65:
            return "MEDIA"
        return "BAJA"
