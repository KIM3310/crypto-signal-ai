"""Domain models for market data, analysis results, signals, and backtests.

All models are plain dataclasses so they serialize cleanly to JSON via
``dataclasses.asdict`` and interop with the ``sqlite3`` row factory.
Enums are serialized by their ``.value`` when persisted.

This module is intentionally free of I/O and framework imports so it
can be imported from any layer (analysis, backtest, db, api, tests)
without pulling in heavy dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------
# Signal enum (classification output of the analysis layer)
# ---------------------------------------------------------------------


class Signal(str, Enum):
    """Trading-signal classification.

    Inherits from ``str`` so comparisons, JSON serialization, and SQL
    parameter binding all treat the enum as its string value.
    """

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

    @property
    def is_buy(self) -> bool:
        """True for BUY and STRONG_BUY."""
        return self in (Signal.BUY, Signal.STRONG_BUY)

    @property
    def is_sell(self) -> bool:
        """True for SELL and STRONG_SELL."""
        return self in (Signal.SELL, Signal.STRONG_SELL)


# ---------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class OHLCV:
    """One candle: open, high, low, close, volume at a timestamp.

    All numeric fields are ``float`` so numpy operations stay
    zero-copy.  ``timestamp`` is timezone-aware (UTC in tests and
    production paths).
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# ---------------------------------------------------------------------
# Analysis results
# ---------------------------------------------------------------------


@dataclass
class TechnicalResult:
    """Technical-indicator snapshot for a single candle.

    Every field is optional because indicators have a warm-up period:
    RSI needs ``period+1`` candles, MACD needs the slow-EMA window, and
    Bollinger Bands need ``period`` candles.  Callers must guard
    against ``None`` before comparing.
    """

    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_percent: Optional[float] = None


@dataclass
class SentimentResult:
    """LLM-backed sentiment read for a single coin.

    ``score`` is in ``[-1.0, 1.0]`` where positive values mean bullish.
    ``sources`` defaults to an empty list so callers can always
    iterate.
    """

    score: float
    summary: str
    sources: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------
# Trade signal (combined technical + sentiment output)
# ---------------------------------------------------------------------


@dataclass
class TradeSignal:
    """Decision-ready trade signal surfaced by the signal layer."""

    timestamp: datetime
    coin: str
    signal: Signal
    confidence: float
    price: float
    technical: TechnicalResult
    reasoning: str = ""
    sentiment: Optional[SentimentResult] = None


# ---------------------------------------------------------------------
# Backtest results
# ---------------------------------------------------------------------


@dataclass
class BacktestTrade:
    """One round-tripped trade in a backtest run."""

    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    side: str  # "long" or "short"
    pnl_pct: float
    signal: Signal


@dataclass
class BacktestResult:
    """Aggregate outcome of a backtest run over a candle series."""

    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
