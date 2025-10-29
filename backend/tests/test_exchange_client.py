import pytest

from data.exchange_client import BinanceClient


def test_binance_client_connection(binance_client: BinanceClient) -> None:
    assert "BTC/USDT" in binance_client.client.symbols


def test_get_ohlcv_returns_dataframe(binance_client: BinanceClient) -> None:
    df = binance_client.get_ohlcv("BTC/USDT", "1h", 5)
    assert not df.empty
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert df.isnull().any().sum() == 0


def test_get_ohlcv_invalid_symbol(binance_client: BinanceClient) -> None:
    with pytest.raises(ValueError):
        binance_client.get_ohlcv("INVALID/PAIR", "1h", 5)
