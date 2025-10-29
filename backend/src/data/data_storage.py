from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint, create_engine, func
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import declarative_base, sessionmaker

from ..utils.logger import get_logger

Base = declarative_base()


class Ohlcv(Base):
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uix_symbol_timeframe_timestamp"),
    )


class DataStorage:
    """Handle persistence of OHLCV data in SQLite using SQLAlchemy."""

    def __init__(self, db_path: str) -> None:
        self.logger = get_logger(__name__)
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def save_ohlcv(self, df: pd.DataFrame, symbol: str, timeframe: str) -> int:
        if df.empty:
            return 0

        session = self.SessionLocal()
        now = datetime.utcnow()
        records = [
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": int(row["timestamp"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "created_at": now,
            }
            for _, row in df.iterrows()
        ]

        stmt = insert(Ohlcv).values(records)
        update_columns = {col: stmt.excluded[col] for col in ["open", "high", "low", "close", "volume"]}
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_=update_columns,
        )

        try:
            session.execute(stmt)
            session.commit()
            self.logger.info("Persisted %s candles for %s @ %s", len(records), symbol, timeframe)
            return len(records)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        session = self.SessionLocal()
        try:
            query = (
                session.query(Ohlcv)
                .filter(Ohlcv.symbol == symbol, Ohlcv.timeframe == timeframe)
                .order_by(Ohlcv.timestamp.desc())
                .limit(limit)
            )
            rows = query.all()
            if not rows:
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "datetime"])

            data = [
                {
                    "timestamp": row.timestamp,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume,
                }
                for row in rows
            ]
            df = pd.DataFrame(data)
            df = df.sort_values("timestamp").reset_index(drop=True)
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            return df
        finally:
            session.close()

    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[int]:
        session = self.SessionLocal()
        try:
            latest = (
                session.query(func.max(Ohlcv.timestamp))
                .filter(Ohlcv.symbol == symbol, Ohlcv.timeframe == timeframe)
                .scalar()
            )
            return int(latest) if latest is not None else None
        finally:
            session.close()
