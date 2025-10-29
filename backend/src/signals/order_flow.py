from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class OrderFlowAnalyzer:
    """Analyse real order-flow using CVD data."""

    def analyze_volume_pressure(
        self,
        df: pd.DataFrame,
        cvd_data: np.ndarray,
        lookback: int = 4,
    ) -> Dict[str, object]:
        default = {
            "pressure": "NEUTRAL",
            "strength": 0.0,
            "cvd_change": 0.0,
            "cvd_change_normalized": 0.0,
            "volume_ratio": 0.0,
            "score": 0,
        }

        if df is None or df.empty:
            return default
        if cvd_data is None:
            return default

        cvd_series = np.asarray(cvd_data, dtype=float)
        if cvd_series.size == 0:
            return default

        min_len = min(len(df), cvd_series.size)
        if min_len < max(lookback, 2):
            return default

        df_subset = df.tail(min_len).copy()
        cvd_subset = cvd_series[-min_len:]

        recent_df = df_subset.tail(lookback)
        recent_cvd = cvd_subset[-lookback:]

        valid_mask = ~np.isnan(recent_cvd)
        if valid_mask.sum() < 2:
            return default

        recent_df = recent_df.iloc[np.arange(len(recent_df))[valid_mask]]
        recent_cvd = recent_cvd[valid_mask]

        cvd_change = float(recent_cvd[-1] - recent_cvd[0])
        avg_volume = float(recent_df["volume"].mean()) if not recent_df.empty else 0.0
        cvd_change_normalized = (cvd_change / avg_volume) * 100 if avg_volume > 0 else 0.0

        strength = min(100.0, abs(cvd_change_normalized))
        if cvd_change_normalized > 30:
            pressure = "BUYING"
            score = 20
        elif cvd_change_normalized < -30:
            pressure = "SELLING"
            score = 20
        else:
            pressure = "NEUTRAL"
            score = int(strength / 5)

        last_volume = float(recent_df["volume"].iloc[-1]) if not recent_df.empty else 0.0
        volume_ratio = (last_volume / avg_volume) if avg_volume > 0 else 1.0
        if volume_ratio > 1.3:
            score = min(20, score + 5)

        return {
            "pressure": pressure,
            "strength": strength,
            "cvd_change": cvd_change,
            "cvd_change_normalized": cvd_change_normalized,
            "volume_ratio": volume_ratio,
            "score": min(20, score),
        }

    def detect_cvd_divergence(
        self,
        price_data: pd.Series,
        cvd_data: np.ndarray,
        lookback: int = 20,
    ) -> Optional[Dict[str, object]]:
        if price_data is None or cvd_data is None:
            return None
        if price_data.empty:
            return None

        cvd_series = np.asarray(cvd_data, dtype=float)
        min_len = min(len(price_data), cvd_series.size)
        if min_len < 6:
            return None

        window = min(lookback, min_len)
        price_recent = price_data.iloc[-window:]
        cvd_recent = cvd_series[-window:]

        index_recent = price_recent.index
        cvd_series_recent = pd.Series(cvd_recent, index=index_recent)
        valid = cvd_series_recent.dropna()
        if len(valid) < 5:
            return None

        aligned_prices = price_recent.loc[valid.index].to_numpy(dtype=float)
        aligned_cvd = valid.to_numpy(dtype=float)

        price_lows_idx = self._find_local_minima(aligned_prices, window=3)
        price_highs_idx = self._find_local_maxima(aligned_prices, window=3)

        if len(price_lows_idx) >= 2:
            idx1, idx2 = price_lows_idx[-2], price_lows_idx[-1]
            price1, price2 = aligned_prices[idx1], aligned_prices[idx2]
            cvd1, cvd2 = aligned_cvd[idx1], aligned_cvd[idx2]
            if price2 < price1 and cvd2 > cvd1:
                delta = abs(cvd2 - cvd1) / max(abs(cvd1), 1e-8)
                strength = "STRONG" if delta > 0.1 else "WEAK"
                return {
                    "type": "BULLISH",
                    "strength": strength,
                    "bonus_score": 15 if strength == "STRONG" else 10,
                    "description": "Precio marcó un mínimo menor pero CVD hizo un mínimo mayor",
                }

        if len(price_highs_idx) >= 2:
            idx1, idx2 = price_highs_idx[-2], price_highs_idx[-1]
            price1, price2 = aligned_prices[idx1], aligned_prices[idx2]
            cvd1, cvd2 = aligned_cvd[idx1], aligned_cvd[idx2]
            if price2 > price1 and cvd2 < cvd1:
                delta = abs(cvd2 - cvd1) / max(abs(cvd1), 1e-8)
                strength = "STRONG" if delta > 0.1 else "WEAK"
                return {
                    "type": "BEARISH",
                    "strength": strength,
                    "bonus_score": 15 if strength == "STRONG" else 10,
                    "description": "Precio marcó un máximo mayor pero CVD hizo un máximo menor",
                }

        return None

    def _find_local_minima(self, data: np.ndarray, window: int = 3) -> List[int]:
        minima: List[int] = []
        for i in range(window, len(data) - window):
            if all(data[i] <= data[j] for j in range(i - window, i)) and all(
                data[i] <= data[j] for j in range(i + 1, i + window + 1)
            ):
                minima.append(i)
        return minima

    def _find_local_maxima(self, data: np.ndarray, window: int = 3) -> List[int]:
        maxima: List[int] = []
        for i in range(window, len(data) - window):
            if all(data[i] >= data[j] for j in range(i - window, i)) and all(
                data[i] >= data[j] for j in range(i + 1, i + window + 1)
            ):
                maxima.append(i)
        return maxima
