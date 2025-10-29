"""Trading signal detection package."""

from .signal_engine import SignalEngine
from .signal import Signal
from .confluence_detector import ConfluenceDetector

__all__ = ["SignalEngine", "Signal", "ConfluenceDetector"]
