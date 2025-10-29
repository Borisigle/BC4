from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from src.config import settings
from src.data.data_fetcher import DataFetcher
from src.data.data_storage import DataStorage
from src.data.exchange_client import BinanceClient
from src.utils.logger import get_logger


def main() -> None:
    project_root = Path(__file__).resolve().parent
    load_dotenv(project_root / ".env")

    logger = get_logger(__name__)

    client = BinanceClient()
    fetcher = DataFetcher(client)
    storage = DataStorage(settings.DB_PATH)

    results = fetcher.fetch_historical_data(settings.SYMBOLS, settings.TIMEFRAMES, settings.DEFAULT_LIMIT)

    total_records = 0
    summary_lines = []

    for symbol, timeframe_map in results.items():
        for timeframe, df in timeframe_map.items():
            stored = storage.save_ohlcv(df, symbol, timeframe)
            total_records += stored

            start_ts = df["datetime"].iloc[0].strftime("%Y-%m-%d %H:%M")
            end_ts = df["datetime"].iloc[-1].strftime("%Y-%m-%d %H:%M")
            summary_lines.append(
                f"✓ {symbol} {timeframe}: {stored} velas descargadas ({start_ts} → {end_ts})"
            )

    for line in summary_lines:
        print(line)

    print(f"Total: {total_records} registros almacenados")

    btc_df = storage.get_ohlcv("BTC/USDT", "1h", 5)
    if not btc_df.empty:
        display_df = btc_df.tail(5).copy()
        display_df["datetime"] = display_df["datetime"].dt.strftime("%Y-%m-%d %H:%M")
        display_df = display_df[["datetime", "open", "high", "low", "close", "volume"]]

        print("\nÚltimas 5 velas BTC/USDT 1h:")
        print(display_df.to_string(index=False))
    else:
        logger.warning("No data found in storage for BTC/USDT 1h")


if __name__ == "__main__":
    main()
