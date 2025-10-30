from __future__ import annotations

import math
from typing import Dict, List, Optional


class ConfluenceDetector:
    """Detecta niveles técnicos que confluyen cerca del precio actual."""

    def detect_confluences(
        self,
        price: float,
        levels: Dict[str, Optional[float]],
        tolerance: float = 0.005,
    ) -> Dict[str, object]:
        if not math.isfinite(price) or price <= 0:
            return {"count": 0, "levels": [], "multiplier": 1.0}

        tolerance = max(0.0, float(tolerance))
        nearby: List[str] = []

        for name, level in levels.items():
            if level is None:
                continue
            if not isinstance(level, (int, float)):
                continue
            if not math.isfinite(level) or level <= 0:
                continue

            distance = abs(price - float(level)) / price
            if distance <= tolerance:
                nearby.append(name)

        multiplier = self.calculate_multiplier(len(nearby))
        return {"count": len(nearby), "levels": nearby, "multiplier": multiplier}

    @staticmethod
    def calculate_multiplier(count: int) -> float:
        if count >= 4:
            return 1.5
        if count == 3:
            return 1.2
        if count >= 1:
            return 1.0
        return 1.0
