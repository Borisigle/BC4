from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np
import pandas as pd

from ..utils.dataframe_helpers import ensure_datetime_index, require_columns


class TechnicalIndicators:
    """Collection of common technical analysis indicators."""

    REQUIRED_OHLC_COLUMNS: List[str] = ["open", "high", "low", "close", "volume"]

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
        """
        Calculate the exponential moving average over a dataframe column.

        Args:
            df: DataFrame containing the target column.
            period: EMA smoothing period.
            column: Column name to operate on.

        Returns:
            Series with EMA values.
        """
        if period <= 0:
            raise ValueError("period must be positive")

        if column not in df.columns:
            raise ValueError(f"DataFrame missing required column: {column}")

        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Compute the Average True Range using Welles Wilder's smoothing.

        Args:
            df: DataFrame containing OHLC data.
            period: ATR period.

        Returns:
            Series with ATR values.
        """
        if period <= 0:
            raise ValueError("period must be positive")

        require_columns(df, ["high", "low", "close"])

        prev_close = df["close"].shift(1)
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - prev_close).abs()
        low_close = (df["low"] - prev_close).abs()

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.ewm(alpha=1 / period, adjust=False).mean()
        return atr

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate the Average Directional Index and the directional indicators.

        Args:
            df: DataFrame with OHLC columns.
            period: Smoothing period.

        Returns:
            DataFrame with columns ["adx", "plus_di", "minus_di"].
        """
        if period <= 0:
            raise ValueError("period must be positive")

        require_columns(df, ["high", "low", "close"])

        high = df["high"]
        low = df["low"]

        up_move = high.diff()
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        plus_dm_series = pd.Series(plus_dm, index=df.index)
        minus_dm_series = pd.Series(minus_dm, index=df.index)

        atr = TechnicalIndicators.calculate_atr(df, period)

        smoothed_plus_dm = plus_dm_series.ewm(alpha=1 / period, adjust=False).mean()
        smoothed_minus_dm = minus_dm_series.ewm(alpha=1 / period, adjust=False).mean()

        with np.errstate(divide="ignore", invalid="ignore"):
            plus_di = 100 * smoothed_plus_dm / atr
            minus_di = 100 * smoothed_minus_dm / atr

        plus_di = plus_di.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        minus_di = minus_di.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        di_sum = plus_di + minus_di
        with np.errstate(divide="ignore", invalid="ignore"):
            dx = (plus_di - minus_di).abs() / di_sum * 100
        dx = dx.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        adx = dx.ewm(alpha=1 / period, adjust=False).mean()

        result = pd.DataFrame({
            "adx": adx.clip(lower=0, upper=100),
            "plus_di": plus_di.clip(lower=0, upper=100),
            "minus_di": minus_di.clip(lower=0, upper=100),
        })
        return result

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        """
        Compute the Relative Strength Index (RSI).

        Args:
            df: DataFrame containing the price column.
            period: RSI period.
            column: Column name containing price data.

        Returns:
            Series with RSI values in range 0-100.
        """
        if period <= 0:
            raise ValueError("period must be positive")
        if column not in df.columns:
            raise ValueError(f"DataFrame missing required column: {column}")

        delta = df[column].diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)

        avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        rsi = rsi.where(~avg_loss.eq(0), 100)
        both_zero = avg_gain.eq(0) & avg_loss.eq(0)
        rsi = rsi.where(~both_zero, 50)

        return rsi.clip(lower=0, upper=100)

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Compute cumulative Volume Weighted Average Price.

        Args:
            df: DataFrame with OHLCV data.

        Returns:
            Series with VWAP values.
        """
        require_columns(df, TechnicalIndicators.REQUIRED_OHLC_COLUMNS)

        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        cumulative_vp = (typical_price * df["volume"]).cumsum()
        cumulative_volume = df["volume"].cumsum().replace(0, np.nan)
        vwap = cumulative_vp / cumulative_volume
        return vwap

    @staticmethod
    def calculate_session_vwap(df: pd.DataFrame, session_start_hour: int = 0) -> pd.Series:
        """
        Compute VWAP that resets at the start of each trading session.

        Args:
            df: DataFrame with a DatetimeIndex or a "datetime" column.
            session_start_hour: Hour (UTC) when the session starts.

        Returns:
            Series containing session VWAP values.
        """
        if not 0 <= session_start_hour <= 23:
            raise ValueError("session_start_hour must be between 0 and 23")

        require_columns(df, TechnicalIndicators.REQUIRED_OHLC_COLUMNS)
        indexed = ensure_datetime_index(df)

        typical_price = (indexed["high"] + indexed["low"] + indexed["close"]) / 3
        volume = indexed["volume"]

        session_start = indexed.index.floor("D") + pd.to_timedelta(session_start_hour, unit="h")
        before_session_start = indexed.index < session_start
        session_start = session_start.where(~before_session_start, session_start - pd.Timedelta(days=1))

        vp = typical_price * volume
        cumulative_vp = vp.groupby(session_start).cumsum()
        cumulative_volume = volume.groupby(session_start).cumsum().replace(0, np.nan)

        session_vwap = cumulative_vp / cumulative_volume
        session_vwap.index = indexed.index
        return session_vwap

    def add_all_indicators(
        self,
        df: pd.DataFrame,
        ema_periods: Optional[Iterable[int]] = None,
        atr_period: int = 14,
        adx_period: int = 14,
        rsi_period: int = 14,
    ) -> pd.DataFrame:
        """
        Calculate and append the default indicator set to the dataframe.

        Returns:
            DataFrame with additional indicator columns.
        """
        ema_periods = list(ema_periods or [20, 50])
        result = df.copy()

        for period in ema_periods:
            result[f"ema_{period}"] = self.calculate_ema(result, period)

        result["atr"] = self.calculate_atr(result, atr_period)

        adx_df = self.calculate_adx(result, adx_period)
        result = result.join(adx_df)

        result["rsi"] = self.calculate_rsi(result, rsi_period)
        result["vwap"] = self.calculate_vwap(result)

        return result
