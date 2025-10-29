from __future__ import annotations

import pandas as pd
import pytest
from typing import Callable

from signals.signal_engine import SignalEngine


def _make_df(values: dict[str, list[float]], symbol: str, timeframe: str, freq: str) -> pd.DataFrame:
    length = len(next(iter(values.values())))
    index = pd.date_range("2024-01-01", periods=length, freq=freq, tz="UTC")
    df = pd.DataFrame(values, index=index)
    df["datetime"] = index
    df.attrs["symbol"] = symbol
    df.attrs["timeframe"] = timeframe
    return df


def _btc_4h() -> pd.DataFrame:
    values = {
        "open": [26000, 26100, 26200, 26300, 26400, 26500],
        "high": [26080, 26190, 26290, 26390, 26490, 26590],
        "low": [25920, 26010, 26110, 26210, 26310, 26410],
        "close": [26100, 26200, 26300, 26400, 26500, 26600],
        "volume": [1500, 1600, 1700, 1800, 1850, 1900],
        "atr": [350] * 6,
        "adx": [32] * 6,
        "ema_20": [26050, 26140, 26240, 26340, 26440, 26540],
        "ema_50": [25800] * 6,
        "rsi": [58] * 6,
        "vwap": [26040, 26130, 26230, 26330, 26430, 26530],
    }
    return _make_df(values, "BTC/USDT", "4h", "4H")


def _btc_1h() -> pd.DataFrame:
    values = {
        "open": [26500, 26520, 26540, 26560, 26580, 26600],
        "high": [26540, 26560, 26580, 26600, 26620, 26640],
        "low": [26480, 26500, 26520, 26540, 26560, 26580],
        "close": [26520, 26540, 26560, 26580, 26600, 26620],
        "volume": [900, 920, 940, 960, 980, 1000],
        "atr": [120] * 6,
        "adx": [30] * 6,
        "rsi": [55] * 6,
        "vwap": [26500, 26520, 26540, 26560, 26580, 26600],
    }
    return _make_df(values, "BTC/USDT", "1h", "H")


def _eth_4h() -> pd.DataFrame:
    values = {
        "open": [96.0, 97.0, 98.0, 99.0, 100.0, 101.0],
        "high": [96.8, 97.8, 98.8, 99.8, 100.8, 101.8],
        "low": [95.2, 96.2, 97.2, 98.2, 99.2, 100.2],
        "close": [97.0, 98.0, 99.0, 100.0, 101.0, 102.0],
        "volume": [600, 620, 640, 660, 680, 700],
        "atr": [1.2] * 6,
        "adx": [30] * 6,
        "ema_20": [96.5, 97.5, 98.5, 99.5, 100.5, 101.5],
        "ema_50": [95.0] * 6,
        "rsi": [60] * 6,
        "vwap": [96.6, 97.6, 98.6, 99.6, 100.6, 101.6],
    }
    return _make_df(values, "ETH/USDT", "4h", "4H")


def _eth_1h() -> pd.DataFrame:
    values = {
        "open": [98.8, 99.0, 99.1, 99.2, 99.3, 99.5, 99.9, 99.6],
        "high": [99.2, 99.3, 99.5, 99.6, 99.8, 100.2, 100.5, 100.9],
        "low": [98.5, 98.8, 99.0, 99.1, 99.2, 99.1, 99.4, 99.4],
        "close": [99.0, 99.1, 99.2, 99.3, 99.5, 100.0, 100.2, 100.5],
        "volume": [80, 90, 95, 100, 120, 140, 160, 200],
        "atr": [0.8] * 8,
        "adx": [28] * 8,
        "rsi": [55] * 8,
        "vwap": [98.9, 99.0, 99.1, 99.2, 99.4, 99.6, 99.9, 100.2],
    }
    return _make_df(values, "ETH/USDT", "1h", "H")


@pytest.fixture()
def engine(monkeypatch: pytest.MonkeyPatch) -> SignalEngine:
    engine = SignalEngine()

    builders: dict[tuple[str, str], Callable[[], pd.DataFrame]] = {
        ("BTC/USDT", "4h"): _btc_4h,
        ("BTC/USDT", "1h"): _btc_1h,
        ("ETH/USDT", "4h"): _eth_4h,
        ("ETH/USDT", "1h"): _eth_1h,
    }

    def fake_load(symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        builder = builders[(symbol, timeframe)]
        df = builder()
        return df

    monkeypatch.setattr(engine, "_load_and_prepare_data", fake_load)

    sr_map = {
        "BTC/USDT": {
            "supports": [{"price": 25800.0, "touches": 3, "strength": "strong"}],
            "resistances": [{"price": 27000.0, "touches": 2, "strength": "medium"}],
        },
        "ETH/USDT": {
            "supports": [{"price": 100.0, "touches": 3, "strength": "strong"}],
            "resistances": [{"price": 105.0, "touches": 2, "strength": "medium"}],
        },
    }

    trend_map = {
        "BTC/USDT": {
            "trend": "ALCISTA_FUERTE",
            "trend_strength": 70,
            "structure": "HH/HL",
            "ema_alignment": True,
            "adx_value": 32,
        },
        "ETH/USDT": {
            "trend": "ALCISTA_FUERTE",
            "trend_strength": 65,
            "structure": "HH/HL",
            "ema_alignment": True,
            "adx_value": 30,
        },
    }

    class StubMarketStructure:
        @staticmethod
        def detect_swing_points(df: pd.DataFrame) -> pd.DataFrame:
            return df

        @staticmethod
        def identify_support_resistance(df: pd.DataFrame) -> dict[str, object]:
            symbol = df.attrs["symbol"]
            return sr_map[symbol]

        @staticmethod
        def determine_trend(df: pd.DataFrame) -> dict[str, object]:
            symbol = df.attrs["symbol"]
            return trend_map[symbol]

    engine.market_structure = StubMarketStructure()

    btc_context = {
        "trend": "ALCISTA_FUERTE",
        "trend_strength": 70,
        "volatility": "NORMAL",
        "session_quality": "ALTA",
        "multiplier_long": 1.2,
        "multiplier_short": 0.3,
        "should_trade": True,
        "current_price": 26600.0,
        "atr": 120.0,
        "adx": 32.0,
    }

    monkeypatch.setattr(engine.btc_filter, "analyze_btc_context", lambda df4h, df1h: btc_context)

    return engine


def test_scan_for_signals_produces_long_signal(engine: SignalEngine) -> None:
    signals = engine.scan_for_signals(symbols=["ETH/USDT"])

    assert len(signals) == 1
    signal = signals[0]
    assert signal.symbol == "ETH/USDT"
    assert signal.direction == "LONG"
    assert signal.score >= 80
    assert signal.stop_loss < signal.entry_price
    assert signal.take_profit_1 > signal.entry_price
    assert "TP1" in signal.to_alert_string()
