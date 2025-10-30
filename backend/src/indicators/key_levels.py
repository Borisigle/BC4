from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class KeyLevelsResult:
    poc_weekly: Optional[float] = None
    poc_daily: Optional[float] = None
    vah: Optional[float] = None
    val: Optional[float] = None
    pwh: Optional[float] = None
    pwl: Optional[float] = None
    pdh: Optional[float] = None
    pdl: Optional[float] = None
    sessions: Dict[str, Dict[str, Optional[float]]] = field(default_factory=dict)


def _sanitize_price(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(result):
        return None
    return result


def _ensure_utc_timestamp(value: datetime) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def _resolve_current_time(current_time: Optional[datetime]) -> datetime:
    if current_time is None:
        return datetime.now(timezone.utc)
    if isinstance(current_time, pd.Timestamp):
        current_time = current_time.to_pydatetime()
    if getattr(current_time, "tzinfo", None) is None:
        return current_time.replace(tzinfo=timezone.utc)
    return current_time.astimezone(timezone.utc)


def calculate_poc(
    df: pd.DataFrame,
    window: timedelta,
    bins: int = 20,
) -> Optional[float]:
    """Calculate the point of control (POC) using a simplified volume profile."""
    profile = _build_volume_profile(df, window, bins)
    if profile.empty:
        return None
    idx = profile["volume"].idxmax()
    if idx is None:
        return None
    return float(profile.loc[idx, "center"])


def calculate_value_area(
    df: pd.DataFrame,
    window: timedelta,
    bins: int = 20,
    value_area: float = 0.7,
) -> Tuple[Optional[float], Optional[float]]:
    """Return the Value Area High (VAH) and Value Area Low (VAL)."""
    if not 0 < value_area <= 1:
        raise ValueError("value_area must be between 0 and 1")

    profile = _build_volume_profile(df, window, bins)
    if profile.empty:
        return None, None

    total_volume = float(profile["volume"].sum())
    if total_volume <= 0:
        return None, None

    threshold = total_volume * float(value_area)
    sorted_profile = profile.sort_values("volume", ascending=False)

    accumulated = 0.0
    selected_rows = []
    for _, row in sorted_profile.iterrows():
        accumulated += float(row["volume"])
        selected_rows.append(row)
        if accumulated >= threshold:
            break

    if not selected_rows:
        return None, None

    selected_df = pd.DataFrame(selected_rows)
    vah = float(selected_df["upper"].max())
    val = float(selected_df["lower"].min())
    return vah, val


def get_previous_period_extremes(
    df: pd.DataFrame,
    current_time: Optional[datetime] = None,
) -> Dict[str, Optional[float]]:
    """Compute highs and lows for the previous day and week (UTC)."""
    extremes = {"pwh": None, "pwl": None, "pdh": None, "pdl": None}
    if df is None or df.empty:
        return extremes

    dt_series = _get_datetime_series(df)
    valid_times = dt_series.dropna()
    if valid_times.empty:
        return extremes

    if current_time is None:
        latest_timestamp = pd.Timestamp(valid_times.iloc[-1])
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.tz_localize("UTC")
        else:
            latest_timestamp = latest_timestamp.tz_convert("UTC")
    else:
        latest_timestamp = _ensure_utc_timestamp(_resolve_current_time(current_time))

    latest_day = latest_timestamp.floor("D")

    prev_day_start = latest_day - timedelta(days=1)
    prev_day_end = latest_day
    prev_day_mask = ((dt_series >= prev_day_start) & (dt_series < prev_day_end)).fillna(False)

    if bool(prev_day_mask.any()):
        prev_day_df = df.loc[prev_day_mask]
        if not prev_day_df.empty:
            high = _sanitize_price(prev_day_df["high"].max())
            low = _sanitize_price(prev_day_df["low"].min())
            if high is not None:
                extremes["pdh"] = high
            if low is not None:
                extremes["pdl"] = low

    week_start = latest_day - timedelta(days=int(latest_day.weekday()))
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start
    prev_week_mask = ((dt_series >= prev_week_start) & (dt_series < prev_week_end)).fillna(False)

    if bool(prev_week_mask.any()):
        prev_week_df = df.loc[prev_week_mask]
        if not prev_week_df.empty:
            high = _sanitize_price(prev_week_df["high"].max())
            low = _sanitize_price(prev_week_df["low"].min())
            if high is not None:
                extremes["pwh"] = high
            if low is not None:
                extremes["pwl"] = low

    return extremes


def get_session_extremes(
    df: pd.DataFrame,
    current_time: Optional[datetime] = None,
) -> Dict[str, Dict[str, Optional[float]]]:
    """Return session highs and lows for the most recent trading sessions."""
    sessions = {
        "asia": {"high": None, "low": None},
        "london": {"high": None, "low": None},
        "new_york": {"high": None, "low": None},
    }

    if df is None or df.empty:
        return sessions

    dt_series = _get_datetime_series(df)
    valid_times = dt_series.dropna()
    if valid_times.empty:
        return sessions

    if current_time is None:
        latest_timestamp = pd.Timestamp(valid_times.iloc[-1])
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.tz_localize("UTC")
        else:
            latest_timestamp = latest_timestamp.tz_convert("UTC")
    else:
        latest_timestamp = _ensure_utc_timestamp(_resolve_current_time(current_time))

    latest_day = latest_timestamp.floor("D")
    day_candidates = [latest_day - timedelta(days=i) for i in range(0, 3)]

    session_windows = {
        "asia": (0, 9),
        "london": (7, 16),
        "new_york": (13, 21),
    }

    for name, (start_hour, end_hour) in session_windows.items():
        for day_start in day_candidates:
            start = day_start + timedelta(hours=start_hour)
            end = day_start + timedelta(hours=end_hour)
            mask = ((dt_series >= start) & (dt_series < end)).fillna(False)
            if bool(mask.any()):
                session_df = df.loc[mask]
                if session_df.empty:
                    continue
                high = _sanitize_price(session_df["high"].max())
                low = _sanitize_price(session_df["low"].min())
                sessions[name] = {"high": high, "low": low}
                break

    return sessions


def calculate_key_levels(
    df: pd.DataFrame,
    timeframe: str,
    current_time: Optional[datetime] = None,
) -> Dict[str, Dict[str, float]]:
    levels: Dict[str, Dict[str, float]] = {}
    if df is None or df.empty:
        return levels

    reference_time = _resolve_current_time(current_time)
    timeframe_normalized = str(timeframe or "").lower()

    def _add_level(key: str, value: Optional[float], label: str, level_type: str) -> None:
        price = _sanitize_price(value)
        if price is None:
            return
        levels[key] = {"price": price, "label": label, "type": level_type}

    weekly_window = timedelta(days=7)
    daily_window = timedelta(days=1)

    _add_level("poc_weekly", calculate_poc(df, weekly_window), "POC W", "poc_weekly")
    _add_level("poc_daily", calculate_poc(df, daily_window), "POC D", "poc_daily")

    vah, val = calculate_value_area(df, weekly_window)
    _add_level("vah_weekly", vah, "VAH W", "vah")
    _add_level("val_weekly", val, "VAL W", "val")

    prev_extremes = get_previous_period_extremes(df, current_time=reference_time)
    _add_level("pdh", prev_extremes.get("pdh"), "PDH", "previous_high")
    _add_level("pdl", prev_extremes.get("pdl"), "PDL", "previous_low")
    _add_level("pwh", prev_extremes.get("pwh"), "PWH", "previous_high")
    _add_level("pwl", prev_extremes.get("pwl"), "PWL", "previous_low")

    if timeframe_normalized in {"1h", "15m"}:
        session_extremes = get_session_extremes(df, current_time=reference_time)
        ny_session = session_extremes.get("new_york") if isinstance(session_extremes, dict) else None
        if isinstance(ny_session, dict):
            _add_level("session_high_ny", ny_session.get("high"), "NY H", "session")
            _add_level("session_low_ny", ny_session.get("low"), "NY L", "session")

    return levels


def _build_volume_profile(df: pd.DataFrame, window: timedelta, bins: int) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["lower", "upper", "center", "volume"])

    filtered = _filter_by_window(df, window)
    if filtered.empty:
        return pd.DataFrame(columns=["lower", "upper", "center", "volume"])

    low_series = pd.to_numeric(filtered.get("low"), errors="coerce")
    high_series = pd.to_numeric(filtered.get("high"), errors="coerce")
    volume_series = pd.to_numeric(filtered.get("volume"), errors="coerce").fillna(0.0)

    min_price = float(np.nanmin(low_series))
    max_price = float(np.nanmax(high_series))

    if not np.isfinite(min_price) or not np.isfinite(max_price):
        return pd.DataFrame(columns=["lower", "upper", "center", "volume"])

    if np.isclose(min_price, max_price):
        total_volume = float(volume_series.sum())
        center = (min_price + max_price) / 2
        return pd.DataFrame([
            {"lower": min_price, "upper": max_price, "center": center, "volume": total_volume}
        ])

    bins = max(1, int(bins))
    edges = np.linspace(min_price, max_price, bins + 1)

    typical_price = (filtered.get("high") + filtered.get("low") + filtered.get("close")) / 3
    typical_price = pd.to_numeric(typical_price, errors="coerce").fillna(method="ffill").fillna(method="bfill")

    bin_indices = np.digitize(typical_price, edges, right=False) - 1
    bin_indices = np.clip(bin_indices, 0, bins - 1)

    accumulated: Dict[int, float] = {}
    for idx, vol in zip(bin_indices, volume_series):
        accumulated[idx] = accumulated.get(idx, 0.0) + float(vol)

    data = []
    for idx, vol in accumulated.items():
        lower = float(edges[idx])
        upper = float(edges[idx + 1])
        center = (lower + upper) / 2
        data.append({"lower": lower, "upper": upper, "center": center, "volume": vol})

    profile = pd.DataFrame(data)
    return profile.sort_values("center").reset_index(drop=True)


def _filter_by_window(df: pd.DataFrame, window: timedelta) -> pd.DataFrame:
    if window <= timedelta(0):
        return df.copy()

    dt_series = _get_datetime_series(df)
    valid_times = dt_series.dropna()
    if valid_times.empty:
        return df.copy()

    end_time = valid_times.iloc[-1]
    start_time = end_time - window
    mask = (dt_series >= start_time).fillna(False)
    return df.loc[mask].copy()


def _get_datetime_series(df: pd.DataFrame) -> pd.Series:
    if "datetime" in df.columns:
        dt = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
        return pd.Series(dt.values, index=df.index)
    if "timestamp" in df.columns:
        dt_index = pd.to_datetime(df["timestamp"], unit="s", utc=True, errors="coerce")
        return pd.Series(dt_index.values, index=df.index)
    if isinstance(df.index, pd.DatetimeIndex):
        idx = df.index
        if idx.tz is None:
            idx = idx.tz_localize("UTC")
        else:
            idx = idx.tz_convert("UTC")
        return pd.Series(idx.values, index=df.index)
    return pd.Series(pd.NaT, index=df.index)
