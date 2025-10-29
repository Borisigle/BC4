from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import pandas as pd
from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint

from src.config import settings
from src.data.data_storage import Base, DataStorage
from src.utils.logger import get_logger


logger = get_logger(__name__)


class CVDData(Base):
    """SQLAlchemy model to persist calculated CVD values."""

    __tablename__ = "cvd_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)
    cvd_period = Column(Float, nullable=False)
    cvd_cumulative = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uix_cvd_symbol_timeframe_ts"),
    )


class CVDStorage(DataStorage):
    """Handle persistence for CVD data."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        super().__init__(db_path or settings.DB_PATH)

    def save_cvd(
        self,
        symbol: str,
        timeframe: str,
        timestamps: List[int],
        cvd_period: List[float],
        cvd_cumulative: List[float],
    ) -> int:
        if not timestamps:
            return 0
        if not (len(timestamps) == len(cvd_period) == len(cvd_cumulative)):
            raise ValueError("CVD data length mismatch")

        session = self.SessionLocal()
        try:
            records = []
            for ts, period_value, cumulative_value in zip(timestamps, cvd_period, cvd_cumulative):
                record = CVDData(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=int(ts),
                    cvd_period=float(period_value),
                    cvd_cumulative=float(cumulative_value),
                )
                records.append(record)

            for record in records:
                session.merge(record)

            session.commit()
            logger.info(
                "Stored %s CVD rows for %s @ %s",
                len(records),
                symbol,
                timeframe,
            )
            return len(records)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_cvd(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        session = self.SessionLocal()
        try:
            query = (
                session.query(CVDData)
                .filter(CVDData.symbol == symbol, CVDData.timeframe == timeframe)
                .order_by(CVDData.timestamp.desc())
                .limit(limit)
            )
            rows = query.all()
            if not rows:
                return pd.DataFrame(columns=["timestamp", "cvd_period", "cvd_cumulative"])

            data = {
                "timestamp": [row.timestamp for row in reversed(rows)],
                "cvd_period": [row.cvd_period for row in reversed(rows)],
                "cvd_cumulative": [row.cvd_cumulative for row in reversed(rows)],
            }
            return pd.DataFrame(data)
        finally:
            session.close()
