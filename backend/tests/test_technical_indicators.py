from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.testing import assert_series_equal

from indicators.technical_indicators import TechnicalIndicators


def _sample_ohlcv(rows: int = 10) -> pd.DataFrame:
    base = pd.date_range("2024-01-01", periods=rows, freq="H", tz="UTC")
    data = {
        "open": np.linspace(100, 110, rows),
        "high": np.linspace(101, 112, rows),
        "low": np.linspace(99, 108, rows),
        "close": np.linspace(100, 111, rows),
        "volume": np.linspace(10, 20, rows),
    }
    df = pd.DataFrame(data, index=base)
    df["datetime"] = base
    return df


def test_calculate_ema_matches_pandas() -> None:
    df = _sample_ohlcv(6)
    period = 3

    ema = TechnicalIndicators.calculate_ema(df, period)
    expected = df["close"].ewm(span=period, adjust=False).mean()

    assert_series_equal(ema, expected)


def test_calculate_atr_expected_values() -> None:
    df = pd.DataFrame(
        {
            "high": [10, 12, 13, 14, 15],
            "low": [8, 9, 10, 11, 13],
            "close": [9, 11, 12, 13, 14],
        }
    )
    period = 3

    atr = TechnicalIndicators.calculate_atr(df, period)

    prev_close = df["close"].shift(1)
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - prev_close).abs()
    low_close = (df["low"] - prev_close).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    expected = true_range.ewm(alpha=1 / period, adjust=False).mean()

    assert_series_equal(atr, expected)


def test_calculate_adx_returns_valid_dataframe() -> None:
    df = _sample_ohlcv(20)
    adx_df = TechnicalIndicators.calculate_adx(df, period=5)

    assert set(adx_df.columns) == {"adx", "plus_di", "minus_di"}
    assert len(adx_df) == len(df)
    assert (adx_df[["adx", "plus_di", "minus_di"]].values >= 0).all()
    assert (adx_df[["adx", "plus_di", "minus_di"]].values <= 100).all()
    assert adx_df["adx"].iloc[-1] >= 0


def test_calculate_rsi_within_bounds() -> None:
    df = pd.DataFrame({"close": [100, 102, 104, 103, 105, 104, 106, 108]})
    rsi = TechnicalIndicators.calculate_rsi(df, period=3)

    assert ((rsi >= 0) & (rsi <= 100)).all()

    delta = df["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 3, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / 3, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    expected = 100 - (100 / (1 + rs))
    expected = expected.where(~avg_loss.eq(0), 100)
    both_zero = avg_gain.eq(0) & avg_loss.eq(0)
    expected = expected.where(~both_zero, 50).clip(lower=0, upper=100)

    assert_series_equal(rsi, expected)


def test_calculate_vwap_matches_manual() -> None:
    df = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "high": [101, 102, 103],
            "low": [99, 100, 101],
            "close": [100, 101, 102],
            "volume": [10, 20, 30],
        }
    )

    vwap = TechnicalIndicators.calculate_vwap(df)

    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    expected = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()

    assert_series_equal(vwap, expected)


def test_calculate_session_vwap_resets_each_day() -> None:
    idx = pd.to_datetime(
        [
            "2024-01-01 00:00",
            "2024-01-01 04:00",
            "2024-01-01 08:00",
            "2024-01-02 00:00",
            "2024-01-02 04:00",
            "2024-01-02 08:00",
        ],
        utc=True,
    )
    df = pd.DataFrame(
        {
            "open": np.linspace(100, 105, 6),
            "high": np.linspace(101, 106, 6),
            "low": np.linspace(99, 104, 6),
            "close": np.linspace(100, 105, 6),
            "volume": np.ones(6) * 10,
        },
        index=idx,
    )
    df["datetime"] = idx

    session_vwap = TechnicalIndicators.calculate_session_vwap(df, session_start_hour=0)
    typical_price = (df["high"] + df["low"] + df["close"]) / 3

    assert session_vwap.iloc[0] == typical_price.iloc[0]
    # First candle of the next session should reset to its typical price
    assert session_vwap.iloc[3] == typical_price.iloc[3]
    # Ensure cumulative behaviour within a session
    assert session_vwap.iloc[1] > session_vwap.iloc[0]


def test_add_all_indicators_appends_columns() -> None:
    df = _sample_ohlcv(30)
    ti = TechnicalIndicators()
    enriched = ti.add_all_indicators(df)

    expected_columns = {"ema_20", "ema_50", "atr", "adx", "plus_di", "minus_di", "rsi", "vwap"}
    assert expected_columns.issubset(set(enriched.columns))
    assert len(enriched) == len(df)
