import pandas as pd
import pytest

from data.data_fetcher import DataFetcher
from data.exchange_client import BinanceClient


def test_fetch_historical_data_multiple_symbols(binance_client: BinanceClient) -> None:
    fetcher = DataFetcher(binance_client)
    symbols = ["BTC/USDT", "ETH/USDT"]
    timeframes = ["1h"]

    data = fetcher.fetch_historical_data(symbols, timeframes, limit=5)

    assert set(data.keys()) == set(symbols)
    for symbol in symbols:
        for timeframe in timeframes:
            df = data[symbol][timeframe]
            assert not df.empty
            assert df["datetime"].is_monotonic_increasing
            assert df["timestamp"].diff().dropna().eq(3600).all()


def test_fetch_historical_data_validation_failure() -> None:
    class DummyClient:
        def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:  # noqa: D401
            data = [
                [1_700_000_000_000, 100.0, 110.0, 90.0, 105.0, 10.0],
                [1_700_003_600_000, 105.0, None, 95.0, 100.0, 12.0],
            ]
            return pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])

    fetcher = DataFetcher(DummyClient())

    with pytest.raises(ValueError):
        fetcher.fetch_historical_data(["BTC/USDT"], ["1h"], limit=2)
