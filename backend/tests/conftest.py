import sys
from pathlib import Path

import pytest

from data.exchange_client import BinanceClient

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="module")
def binance_client() -> BinanceClient:
    client = BinanceClient(max_retries=3, retry_delay=1)
    client.client.load_markets()
    return client
