from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.market_structure import MarketStructure


def _swing_dataframe() -> pd.DataFrame:
    prices = [100, 102, 101, 104, 103, 105, 104, 106, 105]
    highs = [p + 1 for p in prices]
    lows = [p - 1 for p in prices]
    volumes = np.linspace(10, 18, len(prices))
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="H", tz="UTC")

    df = pd.DataFrame(
        {
            "open": prices,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes,
        },
        index=idx,
    )
    df["datetime"] = idx
    return df


def test_detect_swing_points_marks_local_extremes() -> None:
    df = _swing_dataframe()
    result = MarketStructure.detect_swing_points(df, window=2)

    expected_high_idx = result.index[3]
    expected_low_idx = result.index[2]

    assert not result.loc[result.index[1:5], "swing_high"].dropna().empty
    assert result.loc[expected_high_idx, "swing_high"] == result.loc[expected_high_idx, "high"]

    assert not result.loc[result.index[1:5], "swing_low"].dropna().empty
    assert result.loc[expected_low_idx, "swing_low"] == result.loc[expected_low_idx, "low"]


def test_identify_support_resistance_groups_levels() -> None:
    df = _swing_dataframe()
    df = MarketStructure.detect_swing_points(df, window=2)

    zones = MarketStructure.identify_support_resistance(df, tolerance=0.01, min_touches=1)

    assert "supports" in zones and "resistances" in zones
    assert zones["supports"]
    assert zones["resistances"]

    strongest_support = zones["supports"][0]
    strongest_resistance = zones["resistances"][0]

    assert strongest_support["touches"] >= 1
    assert strongest_resistance["touches"] >= 1
    assert strongest_support["strength"] in {"weak", "medium", "strong"}
    assert strongest_resistance["strength"] in {"weak", "medium", "strong"}


def test_determine_trend_identifies_bullish_structure() -> None:
    df = pd.DataFrame(
        {
            "close": [100, 103, 105, 108, 110],
            "ema_20": [99, 101, 103, 106, 108],
            "ema_50": [95, 96, 97, 98, 100],
            "adx": [22, 26, 28, 30, 32],
            "swing_high": [np.nan, 103, np.nan, 108, np.nan],
            "swing_low": [np.nan, np.nan, 101, np.nan, 105],
        }
    )

    result = MarketStructure.determine_trend(df, lookback=len(df))

    assert result["trend"] == "ALCISTA_FUERTE"
    assert result["structure"] == "HH/HL"
    assert result["ema_alignment"] is True
    assert result["trend_strength"] == float(np.clip(df["adx"].iloc[-1], 0, 100))
    assert result["adx_value"] == df["adx"].iloc[-1]


def test_determine_trend_returns_lateral_when_adx_low() -> None:
    df = _swing_dataframe()
    df = MarketStructure.detect_swing_points(df, window=2)

    df["ema_20"] = df["close"] + 1
    df["ema_50"] = df["close"]
    df["adx"] = np.ones(len(df)) * 15

    result = MarketStructure.determine_trend(df, lookback=6)

    assert result["trend"] == "LATERAL"
    assert not result["ema_alignment"]
    assert result["trend_strength"] == 15
