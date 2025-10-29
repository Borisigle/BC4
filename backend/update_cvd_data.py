"""Update script to compute and persist CVD values for all configured assets."""

from __future__ import annotations

from src.config import settings
from src.data.cvd_calculator import CVDCalculator
from src.data.cvd_storage import CVDStorage
from src.data.data_storage import DataStorage
from src.utils.logger import get_logger


logger = get_logger(__name__)


def update_cvd_for_all_assets(limit: int = 200) -> None:
    cvd_calculator = CVDCalculator()
    cvd_storage = CVDStorage()
    ohlcv_storage = DataStorage(settings.DB_PATH)

    for symbol in settings.SYMBOLS:
        for timeframe in settings.TIMEFRAMES:
            logger.info("Updating CVD for %s @ %s", symbol, timeframe)

            try:
                candles = ohlcv_storage.get_ohlcv(symbol, timeframe, limit)
                if candles.empty:
                    logger.warning("No OHLCV data for %s @ %s", symbol, timeframe)
                    continue

                cvd_period = cvd_calculator.calculate_cvd_for_candles(symbol, timeframe, candles)
                cvd_cumulative = cvd_calculator.calculate_cumulative_cvd(cvd_period)

                cvd_storage.save_cvd(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamps=candles["timestamp"].astype(int).tolist(),
                    cvd_period=cvd_period.astype(float).tolist(),
                    cvd_cumulative=cvd_cumulative.astype(float).tolist(),
                )

                logger.info("CVD updated successfully for %s @ %s", symbol, timeframe)
            except Exception as exc:  # pragma: no cover - runtime safety
                logger.error("Failed to update CVD for %s @ %s: %s", symbol, timeframe, exc)


if __name__ == "__main__":
    logger.info("Starting CVD update job")
    update_cvd_for_all_assets()
    logger.info("CVD update job completed")
