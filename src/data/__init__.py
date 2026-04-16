"""Data layer: domain models and market-data fetchers."""

from src.data.models import (
    OHLCV,
    BacktestResult,
    BacktestTrade,
    SentimentResult,
    Signal,
    TechnicalResult,
    TradeSignal,
)
from src.data.fetcher import (
    FetchError,
    fetch_coin_list,
    fetch_ohlcv,
)

__all__ = [
    "OHLCV",
    "BacktestResult",
    "BacktestTrade",
    "SentimentResult",
    "Signal",
    "TechnicalResult",
    "TradeSignal",
    "FetchError",
    "fetch_coin_list",
    "fetch_ohlcv",
]
