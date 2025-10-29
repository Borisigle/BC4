from __future__ import annotations

from typing import Dict, Iterable

import numpy as np
import pandas as pd

from ..utils.logger import get_logger
from .exchange_client import BinanceClient


def _timeframe_to_seconds(timeframe: str) -> int:
    unit = timeframe[-1]
    value = int(timeframe[:-1])
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 60 * 60
    if unit == "d":
        return value * 24 * 60 * 60
    if unit == "w":
        return value * 7 * 24 * 60 * 60
    if unit == "M":
        # Approximate month as 30 days for consistency with Binance's convention
        return value * 30 * 24 * 60 * 60
    raise ValueError(f"Unsupported timeframe: {timeframe}")


class DataFetcher:
    """Coordinate downloading of OHLCV data for multiple symbols/timeframes."""

    def __init__(self, client: BinanceClient) -> None:
        self.client = client
        self.logger = get_logger(__name__)

    def fetch_historical_data(
        self,
        symbols: Iterable[str],
        timeframes: Iterable[str],
        limit: int,
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        results: Dict[str, Dict[str, pd.DataFrame]] = {}

        for symbol in symbols:
            results[symbol] = {}
            for timeframe in timeframes:
                df = self.client.get_ohlcv(symbol, timeframe, limit)

                df = df.sort_values("timestamp").reset_index(drop=True)
                df["timestamp"] = (df["timestamp"] // 1000).astype(int)  # convert ms → s
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

                self._validate_dataframe(df, timeframe)

                results[symbol][timeframe] = df
                self.logger.info(
                    "Fetched %s candles for %s @ %s (%s → %s)",
                    len(df),
                    symbol,
                    timeframe,
                    df["datetime"].iloc[0].strftime("%Y-%m-%d %H:%M"),
                    df["datetime"].iloc[-1].strftime("%Y-%m-%d %H:%M"),
                )
        return results

    def _validate_dataframe(self, df: pd.DataFrame, timeframe: str) -> None:
        if df.empty:
            raise ValueError("Received empty OHLCV dataframe")

        required_columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "datetime",
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if df[required_columns].isnull().any().any():
            raise ValueError("OHLCV dataframe contains null values")

        diffs = df["timestamp"].diff().dropna()
        expected = _timeframe_to_seconds(timeframe)
        if not diffs.empty and not np.all(diffs == expected):
            raise ValueError("Detected gaps in OHLCV data")
