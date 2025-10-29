from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class Signal:
    """Representa una señal de trading completa."""

    symbol: str
    direction: str
    score: float
    confidence: str

    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float

    risk_percent: float
    suggested_position_size: float

    btc_trend: str
    session_quality: str
    timestamp: datetime
    valid_until: datetime

    reasons: List[str]

    atr_value: float
    adx_value: float
    rsi_value: float

    base_score: float
    base_components: Dict[str, float]
    key_levels: Dict[str, object]
    confluence: Dict[str, object]
    btc_multiplier: float
    total_bonus: int

    def to_alert_string(self) -> str:
        """Formatea la señal para mostrar al usuario."""
        direction_icon = "🟢" if self.direction.upper() == "LONG" else "🔴"
        stop_percent_display = -self.risk_percent if self.direction.upper() == "LONG" else self.risk_percent
        reasons_section = "\n".join(f"✓ {reason}" for reason in self.reasons) or "✓ Contexto técnico favorable"

        alert = (
            f"\n🚨 SEÑAL DETECTADA - {self.symbol}\n"
            f"{direction_icon} {self.direction.upper()} - Score: {self.score:.0f}/100\n"
            f"Confianza: {self.confidence}\n\n"
            f"📊 Contexto BTC: {self.btc_trend}\n"
            f"⏰ Sesión: {self.session_quality}\n\n"
            f"💰 NIVELES:\n"
            f"Entry:  ${self.entry_price:,.2f}\n"
            f"Stop:   ${self.stop_loss:,.2f} ({stop_percent_display:.2f}%)\n"
            f"TP1:    ${self.take_profit_1:,.2f} [1:2] - Cerrar 50%\n"
            f"TP2:    ${self.take_profit_2:,.2f} [1:3] - Cerrar 30%\n"
            f"TP3:    ${self.take_profit_3:,.2f} [1:4] - Trailing 20%\n\n"
            f"📈 RAZONES:\n{reasons_section}\n\n"
            f"📊 Indicadores:\n"
            f"   ATR: ${self.atr_value:,.2f} | ADX: {self.adx_value:.1f} | RSI: {self.rsi_value:.1f}\n\n"
            f"⚠️ RIESGO: {self.suggested_position_size:.2f}% de capital sugerido\n"
            f"⏰ Válida hasta: {self.valid_until.strftime('%H:%M UTC')}\n"
        )

        if isinstance(self.confluence, dict) and self.confluence.get("count", 0):
            levels = self.confluence.get("levels", []) or []
            levels_display = ", ".join(str(level) for level in levels) or "N/A"
            alert += f"🔗 Confluencia: {self.confluence['count']} niveles ({levels_display})\n"

        if isinstance(self.key_levels, dict):
            highlights = []
            poc_weekly = self.key_levels.get("poc_weekly")
            if isinstance(poc_weekly, (int, float)):
                highlights.append(f"POC W: ${poc_weekly:,.2f}")
            val = self.key_levels.get("val")
            if isinstance(val, (int, float)):
                highlights.append(f"VAL: ${val:,.2f}")
            vah = self.key_levels.get("vah")
            if isinstance(vah, (int, float)):
                highlights.append(f"VAH: ${vah:,.2f}")
            if highlights:
                alert += "🔑 Key Levels: " + " | ".join(highlights) + "\n"

        return alert
