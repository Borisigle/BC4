from __future__ import annotations

from typing import Iterable

import pandas as pd


def require_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    """Ensure the dataframe contains the required columns."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")


def ensure_datetime_index(df: pd.DataFrame, datetime_column: str = "datetime") -> pd.DataFrame:
    """Return a dataframe with a DatetimeIndex, using the provided column when necessary."""
    if isinstance(df.index, pd.DatetimeIndex):
        return df

    if datetime_column not in df.columns:
        raise ValueError("DataFrame must have a DatetimeIndex or a datetime column")

    indexed = df.copy()
    indexed.index = pd.to_datetime(indexed[datetime_column], utc=True)
    return indexed
