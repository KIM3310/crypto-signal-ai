"""Centralized configuration. All hardcoded values live here."""

from __future__ import annotations

import os
from pathlib import Path


# --- LLM ---
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

# --- Technical Analysis ---
RSI_PERIOD: int = int(os.environ.get("RSI_PERIOD", "14"))
MACD_FAST: int = int(os.environ.get("MACD_FAST", "12"))
MACD_SLOW: int = int(os.environ.get("MACD_SLOW", "26"))
MACD_SIGNAL: int = int(os.environ.get("MACD_SIGNAL", "9"))
BB_PERIOD: int = int(os.environ.get("BB_PERIOD", "20"))
BB_STD: float = float(os.environ.get("BB_STD", "2.0"))

# --- Signal Classification ---
SIGNAL_MAX_SCORE: float = float(os.environ.get("SIGNAL_MAX_SCORE", "7.5"))
STRONG_BUY_THRESHOLD: float = float(os.environ.get("STRONG_BUY_THRESHOLD", "4.0"))
BUY_THRESHOLD: float = float(os.environ.get("BUY_THRESHOLD", "1.5"))
STRONG_SELL_THRESHOLD: float = float(os.environ.get("STRONG_SELL_THRESHOLD", "-4.0"))
SELL_THRESHOLD: float = float(os.environ.get("SELL_THRESHOLD", "-1.5"))
SENTIMENT_POSITIVE_THRESHOLD: float = 0.3
SENTIMENT_NEGATIVE_THRESHOLD: float = -0.3

# --- Backtest ---
DEFAULT_INITIAL_CAPITAL: float = 10_000.0
DEFAULT_FEE_PCT: float = 0.1
DEFAULT_HOLD_PERIODS: int = 5
MIN_SIGNAL_CONFIDENCE: float = 0.3
ANNUALIZE_FACTOR: int = 365  # crypto = 365, stocks = 252

# --- Scheduler ---
DEFAULT_COINS: list[str] = os.environ.get("DEFAULT_COINS", "bitcoin,ethereum").split(",")
CHECK_INTERVAL_SECONDS: int = int(os.environ.get("CHECK_INTERVAL", str(6 * 60 * 60)))

# --- Database ---
DB_PATH: Path = Path(os.environ.get("DB_PATH", "data/signals.db"))

# --- CoinGecko ---
COINGECKO_BASE: str = "https://api.coingecko.com/api/v3"
COINGECKO_TIMEOUT: int = 30
