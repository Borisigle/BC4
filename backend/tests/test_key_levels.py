from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from indicators.key_levels import (
    calculate_poc,
    calculate_value_area,
    get_previous_period_extremes,
    get_session_extremes,
)


def _prepare_dataframe(prices: np.ndarray, volumes: np.ndarray, start: str = "2024-01-01") -> pd.DataFrame:
    index = pd.date_range(start, periods=len(prices), freq="H", tz="UTC")
    df = pd.DataFrame(
        {
            "open": prices,
            "high": prices + 0.5,
            "low": prices - 0.5,
            "close": prices,
            "volume": volumes,
        },
        index=index,
    )
    df["datetime"] = index
    df["timestamp"] = (index.view("int64") // 10**9).astype(int)
    return df


def test_calculate_poc_prefers_high_volume_zone() -> None:
    prices = np.concatenate([np.ones(20) * 100, np.ones(20) * 120])
    volumes = np.concatenate([np.ones(20) * 200, np.ones(20) * 50])
    df = _prepare_dataframe(prices, volumes)

    poc = calculate_poc(df, timedelta(days=7))

    assert poc is not None
    assert abs(poc - 100) < 2  # debe estar cerca del cluster principal


def test_value_area_contains_majority_volume() -> None:
    prices = np.concatenate([
        np.linspace(98, 102, 30),
        np.linspace(118, 122, 10),
    ])
    volumes = np.concatenate([
        np.ones(30) * 150,
        np.ones(10) * 40,
    ])
    df = _prepare_dataframe(prices, volumes)

    vah, val = calculate_value_area(df, timedelta(days=7))
    poc = calculate_poc(df, timedelta(days=7))

    assert vah is not None and val is not None and poc is not None
    assert val <= poc <= vah
    assert vah - val < 10  # rango acotado alrededor del cluster principal


def test_previous_period_extremes_detects_week_and_day() -> None:
    hours = 24 * 14
    index = pd.date_range("2024-01-01", periods=hours, freq="H", tz="UTC")
    base_prices = np.linspace(95, 105, hours)
    df = pd.DataFrame(
        {
            "open": base_prices,
            "high": base_prices + 1,
            "low": base_prices - 1,
            "close": base_prices,
            "volume": np.ones(hours) * 100,
        },
        index=index,
    )
    df["datetime"] = index
    df["timestamp"] = (index.view("int64") // 10**9).astype(int)

    prev_week_mask = (df["datetime"] >= "2024-01-01") & (df["datetime"] < "2024-01-08")
    df.loc[prev_week_mask, "high"] = 150
    df.loc[prev_week_mask, "low"] = 60

    prev_day_mask = (df["datetime"] >= "2024-01-13") & (df["datetime"] < "2024-01-14")
    df.loc[prev_day_mask, "high"] = 140
    df.loc[prev_day_mask, "low"] = 70

    extremes = get_previous_period_extremes(df)

    assert extremes["pwh"] == 150
    assert extremes["pwl"] == 60
    assert extremes["pdh"] == 140
    assert extremes["pdl"] == 70


def test_session_extremes_returns_recent_sessions() -> None:
    index = pd.date_range("2024-01-11", periods=24, freq="H", tz="UTC")
    base_prices = np.linspace(100, 104, len(index))
    df = pd.DataFrame(
        {
            "open": base_prices,
            "high": base_prices + 1,
            "low": base_prices - 1,
            "close": base_prices,
            "volume": np.ones(len(index)) * 80,
        },
        index=index,
    )
    df["datetime"] = index
    df["timestamp"] = (index.view("int64") // 10**9).astype(int)

    asia_mask = (df.index.hour >= 0) & (df.index.hour < 9)
    df.loc[asia_mask, "high"] = 112
    df.loc[asia_mask, "low"] = 94

    london_mask = (df.index.hour >= 7) & (df.index.hour < 16)
    df.loc[london_mask, "high"] = 123
    df.loc[london_mask, "low"] = 97

    ny_mask = (df.index.hour >= 13) & (df.index.hour < 21)
    df.loc[ny_mask, "high"] = 131
    df.loc[ny_mask, "low"] = 102

    sessions = get_session_extremes(df)

    assert sessions["asia"]["high"] == 112
    assert sessions["asia"]["low"] == 94
    assert sessions["london"]["high"] == 123
    assert sessions["london"]["low"] == 97
    assert sessions["new_york"]["high"] == 131
    assert sessions["new_york"]["low"] == 102
