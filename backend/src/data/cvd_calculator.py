from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import ccxt
import numpy as np
import pandas as pd

from src.utils.logger import get_logger


class CVDCalculator:
    """Compute Cumulative Volume Delta (CVD) from Binance trades."""

    def __init__(
        self,
        exchange: Optional[ccxt.Exchange] = None,
    ) -> None:
        self.logger = get_logger(__name__)
        self.exchange = exchange or ccxt.binance(
            {
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )

    def fetch_trades_for_timerange(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, object]]:
        """Download Binance trades for the given symbol within a time range."""

        if start_time >= end_time:
            return []

        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        all_trades: List[Dict[str, object]] = []
        current_since = start_ms

        self.logger.info(
            "Fetching trades for %s between %s and %s",
            symbol,
            start_time.isoformat(),
            end_time.isoformat(),
        )

        while current_since < end_ms:
            try:
                trades = self.exchange.fetch_trades(
                    symbol=symbol,
                    since=current_since,
                    limit=1000,
                )
            except Exception as exc:  # pragma: no cover - network errors
                self.logger.error("Error fetching trades for %s: %s", symbol, exc)
                break

            if not trades:
                break

            for trade in trades:
                timestamp = int(trade.get("timestamp", 0))
                if timestamp > end_ms:
                    continue

                side = trade.get("side")
                if side is None:
                    side = self._derive_side_from_info(trade.get("info"))

                formatted = {
                    "timestamp": timestamp,
                    "price": float(trade.get("price", 0.0)),
                    "amount": float(trade.get("amount", 0.0)),
                    "side": side or "buy",
                    "id": str(trade.get("id", "")),
                }
                all_trades.append(formatted)

            current_since = int(trades[-1]["timestamp"]) + 1

            if len(trades) < 1000:
                break

        self.logger.info("Fetched %s trades for %s", len(all_trades), symbol)
        return all_trades

    @staticmethod
    def _derive_side_from_info(info: Optional[Dict[str, object]]) -> Optional[str]:
        if not isinstance(info, dict):
            return None
        is_buyer_maker = info.get("isBuyerMaker")
        if is_buyer_maker is None:
            return None
        # When buyer is maker, seller is the aggressive side → taker sell
        return "sell" if bool(is_buyer_maker) else "buy"

    @staticmethod
    def calculate_cvd_from_trades(trades: List[Dict[str, object]]) -> float:
        cvd_value = 0.0
        for trade in sorted(trades, key=lambda item: item.get("timestamp", 0)):
            amount = float(trade.get("amount", 0.0))
            side = str(trade.get("side", "buy")).lower()
            if side == "buy":
                cvd_value += amount
            else:
                cvd_value -= amount
        return cvd_value

    def calculate_cvd_for_candles(
        self,
        symbol: str,
        timeframe: str,
        candles_df: pd.DataFrame,
    ) -> np.ndarray:
        if candles_df.empty:
            return np.array([], dtype=float)

        timeframe_seconds = self._timeframe_to_seconds(timeframe)
        if timeframe_seconds <= 0:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        cvd_values: List[float] = []

        for _, row in candles_df.iterrows():
            timestamp = int(row["timestamp"])
            candle_start = datetime.utcfromtimestamp(timestamp)
            candle_end = candle_start + timedelta(seconds=timeframe_seconds)

            trades = self.fetch_trades_for_timerange(symbol, candle_start, candle_end)
            period_cvd = self.calculate_cvd_from_trades(trades)
            cvd_values.append(period_cvd)

            self.logger.debug(
                "Candle @ %s: %s trades, CVD %.4f",
                candle_start.isoformat(),
                len(trades),
                period_cvd,
            )

        return np.array(cvd_values, dtype=float)

    @staticmethod
    def calculate_cumulative_cvd(cvd_per_candle: np.ndarray) -> np.ndarray:
        if cvd_per_candle.size == 0:
            return np.array([], dtype=float)
        return np.cumsum(cvd_per_candle)

    @staticmethod
    def _timeframe_to_seconds(timeframe: str) -> int:
        mapping = {
            "1m": 60,
            "5m": 5 * 60,
            "15m": 15 * 60,
            "1h": 60 * 60,
            "4h": 4 * 60 * 60,
            "1d": 24 * 60 * 60,
        }
        return mapping.get(timeframe, -1)
