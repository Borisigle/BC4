import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

EXCHANGE = os.getenv("EXCHANGE", "binance")
SYMBOLS = [symbol.strip() for symbol in os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",") if symbol.strip()]
TIMEFRAMES = [tf.strip() for tf in os.getenv("TIMEFRAMES", "1h,4h").split(",") if tf.strip()]
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "100"))
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "crypto_data.db"))
