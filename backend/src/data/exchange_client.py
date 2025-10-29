from __future__ import annotations

import time
from typing import Optional

import ccxt
import pandas as pd
from ccxt.base.errors import BadSymbol, ExchangeError, NetworkError, RequestTimeout

from ..utils.logger import get_logger


class BinanceClient:
    """Thin wrapper around ccxt's Binance client for OHLCV data."""

    def __init__(
        self,
        enable_rate_limit: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        session: Optional[object] = None,
    ) -> None:
        self.logger = get_logger(__name__)
        client_kwargs = {"enableRateLimit": enable_rate_limit}
        if session is not None:
            client_kwargs["session"] = session
        self.client = ccxt.binance(client_kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Retrieve OHLCV data for the given symbol and timeframe."""
        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt < self.max_retries:
            try:
                self.logger.info(
                    "Requesting OHLCV: symbol=%s timeframe=%s limit=%s", symbol, timeframe, limit
                )
                raw_ohlcv = self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                if not raw_ohlcv:
                    raise ValueError(f"No OHLCV data returned for {symbol} {timeframe}")

                df = pd.DataFrame(
                    raw_ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                df["timestamp"] = df["timestamp"].astype("int64")
                numeric_columns = ["open", "high", "low", "close", "volume"]
                df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")

                if df[numeric_columns].isnull().any().any():
                    raise ValueError(f"Received invalid OHLCV data for {symbol} {timeframe}")

                return df
            except BadSymbol as exc:
                self.logger.error("Invalid trading pair requested: %s", symbol)
                raise ValueError(f"Invalid symbol: {symbol}") from exc
            except (NetworkError, RequestTimeout) as exc:
                attempt += 1
                last_exception = exc
                self.logger.warning(
                    "Network error fetching OHLCV (attempt %s/%s): %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                time.sleep(self.retry_delay * attempt)
            except ExchangeError as exc:
                self.logger.error("Exchange error fetching OHLCV: %s", exc)
                raise RuntimeError("Exchange error while fetching OHLCV data") from exc

        raise RuntimeError("Failed to fetch OHLCV data after multiple attempts") from last_exception
