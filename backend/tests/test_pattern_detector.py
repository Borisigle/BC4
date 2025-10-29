from __future__ import annotations

import pandas as pd

from signals.pattern_detector import PatternDetector


def _df_from_rows(rows: list[dict[str, float]]) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=len(rows), freq="H", tz="UTC")
    df = pd.DataFrame(rows, index=index)
    df["datetime"] = index
    return df


def test_detect_bullish_engulfing() -> None:
    rows = [
        {"open": 101.0, "close": 100.0, "high": 101.5, "low": 99.8, "volume": 100},
        {"open": 99.9, "close": 102.0, "high": 102.5, "low": 99.5, "volume": 120},
    ]
    df = _df_from_rows(rows)
    detector = PatternDetector()
    assert detector.detect_bullish_engulfing(df) is True


def test_detect_bearish_engulfing() -> None:
    rows = [
        {"open": 100.0, "close": 101.2, "high": 101.4, "low": 99.8, "volume": 90},
        {"open": 101.4, "close": 99.6, "high": 101.6, "low": 99.4, "volume": 110},
    ]
    df = _df_from_rows(rows)
    detector = PatternDetector()
    assert detector.detect_bearish_engulfing(df) is True


def test_detect_three_consecutive_bullish() -> None:
    rows = [
        {"open": 100.0, "close": 100.5, "high": 100.6, "low": 99.7, "volume": 100},
        {"open": 100.5, "close": 101.0, "high": 101.1, "low": 100.3, "volume": 120},
        {"open": 101.0, "close": 101.6, "high": 101.8, "low": 100.9, "volume": 140},
    ]
    df = _df_from_rows(rows)
    detector = PatternDetector()
    assert detector.detect_three_consecutive(df, "bullish") is True


def test_get_all_patterns_returns_score_and_labels() -> None:
    rows = [
        {"open": 100.0, "close": 99.4, "high": 100.2, "low": 99.0, "volume": 90},
        {"open": 99.2, "close": 101.1, "high": 101.4, "low": 98.9, "volume": 150},
        {"open": 101.0, "close": 101.5, "high": 101.7, "low": 100.8, "volume": 160},
    ]
    df = _df_from_rows(rows)
    detector = PatternDetector()
    result = detector.get_all_patterns(df, support_zone=99.5)

    assert "engulfing" in result["bullish"]
    assert result["score"] == 10
