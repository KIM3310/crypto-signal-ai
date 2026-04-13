from __future__ import annotations

import numpy as np

from src.config import RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL, BB_PERIOD, BB_STD
from src.data.models import OHLCV, TechnicalResult


def compute_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    """Relative Strength Index."""
    results: list[float | None] = [None] * len(closes)
    if len(closes) < period + 1:
        return results

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    for i in range(period, len(closes)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period

        if avg_loss == 0:
            results[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            results[i] = 100.0 - (100.0 / (1.0 + rs))

    return results


def compute_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> list[tuple[float | None, float | None, float | None]]:
    """MACD, Signal, Histogram."""
    results: list[tuple[float | None, float | None, float | None]] = [
        (None, None, None)
    ] * len(closes)
    if len(closes) < slow:
        return results

    arr = np.array(closes, dtype=float)

    def ema(data: np.ndarray, span: int) -> np.ndarray:
        alpha = 2.0 / (span + 1)
        out = np.empty_like(data)
        out[0] = data[0]
        for i in range(1, len(data)):
            out[i] = alpha * data[i] + (1 - alpha) * out[i - 1]
        return out

    ema_fast = ema(arr, fast)
    ema_slow = ema(arr, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line

    for i in range(slow - 1, len(closes)):
        results[i] = (float(macd_line[i]), float(signal_line[i]), float(histogram[i]))

    return results


def compute_bollinger(
    closes: list[float],
    period: int = 20,
    num_std: float = 2.0,
) -> list[tuple[float | None, float | None, float | None, float | None]]:
    """Bollinger Bands: upper, middle, lower, %B."""
    results: list[tuple[float | None, float | None, float | None, float | None]] = [
        (None, None, None, None)
    ] * len(closes)
    if len(closes) < period:
        return results

    arr = np.array(closes, dtype=float)

    for i in range(period - 1, len(closes)):
        window = arr[i - period + 1 : i + 1]
        middle = float(np.mean(window))
        std = float(np.std(window, ddof=1))
        upper = middle + num_std * std
        lower = middle - num_std * std

        band_width = upper - lower
        pct_b = (closes[i] - lower) / band_width if band_width > 0 else 0.5

        results[i] = (upper, middle, lower, pct_b)

    return results


def analyze(candles: list[OHLCV]) -> list[TechnicalResult]:
    """Run all technical indicators on OHLCV data."""
    closes = [c.close for c in candles]

    rsi_values = compute_rsi(closes)
    macd_values = compute_macd(closes)
    bb_values = compute_bollinger(closes)

    results: list[TechnicalResult] = []
    for i in range(len(candles)):
        macd_v, macd_s, macd_h = macd_values[i]
        bb_u, bb_m, bb_l, bb_p = bb_values[i]

        results.append(
            TechnicalResult(
                rsi=rsi_values[i],
                macd=macd_v,
                macd_signal=macd_s,
                macd_histogram=macd_h,
                bb_upper=bb_u,
                bb_middle=bb_m,
                bb_lower=bb_l,
                bb_percent=bb_p,
            )
        )

    return results
