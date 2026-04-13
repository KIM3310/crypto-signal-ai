from __future__ import annotations

from datetime import datetime, timezone

from src.data.models import OHLCV, SentimentResult, Signal, TechnicalResult, TradeSignal
from src.analysis.technical import analyze


def classify_signal(tech: TechnicalResult, sentiment: SentimentResult | None) -> tuple[Signal, float, str]:
    """Combine technical indicators and sentiment into a trading signal."""
    score = 0.0
    reasons: list[str] = []

    # RSI
    if tech.rsi is not None:
        if tech.rsi < 30:
            score += 2.0
            reasons.append(f"RSI 과매도({tech.rsi:.1f})")
        elif tech.rsi < 40:
            score += 1.0
            reasons.append(f"RSI 매수 접근({tech.rsi:.1f})")
        elif tech.rsi > 70:
            score -= 2.0
            reasons.append(f"RSI 과매수({tech.rsi:.1f})")
        elif tech.rsi > 60:
            score -= 1.0
            reasons.append(f"RSI 매도 접근({tech.rsi:.1f})")

    # MACD
    if tech.macd_histogram is not None:
        if tech.macd_histogram > 0 and tech.macd is not None and tech.macd_signal is not None:
            if tech.macd > tech.macd_signal:
                score += 1.5
                reasons.append("MACD 골든크로스")
        elif tech.macd_histogram < 0:
            score -= 1.5
            reasons.append("MACD 데드크로스")

    # Bollinger Bands
    if tech.bb_percent is not None:
        if tech.bb_percent < 0.0:
            score += 2.0
            reasons.append("볼린저 밴드 하단 돌파")
        elif tech.bb_percent < 0.2:
            score += 1.0
            reasons.append("볼린저 밴드 하단 접근")
        elif tech.bb_percent > 1.0:
            score -= 2.0
            reasons.append("볼린저 밴드 상단 돌파")
        elif tech.bb_percent > 0.8:
            score -= 1.0
            reasons.append("볼린저 밴드 상단 접근")

    # Sentiment
    if sentiment is not None:
        score += sentiment.score * 2.0
        if sentiment.score > 0.3:
            reasons.append(f"긍정 감성({sentiment.score:.2f})")
        elif sentiment.score < -0.3:
            reasons.append(f"부정 감성({sentiment.score:.2f})")

    # Classify
    max_score = 9.5  # theoretical max
    confidence = min(1.0, abs(score) / (max_score * 0.5))

    if score >= 4.0:
        signal = Signal.STRONG_BUY
    elif score >= 1.5:
        signal = Signal.BUY
    elif score <= -4.0:
        signal = Signal.STRONG_SELL
    elif score <= -1.5:
        signal = Signal.SELL
    else:
        signal = Signal.NEUTRAL

    return signal, confidence, " | ".join(reasons) if reasons else "중립"


def generate_signals(
    candles: list[OHLCV],
    coin: str = "BTC",
    sentiment: SentimentResult | None = None,
) -> list[TradeSignal]:
    """Generate trading signals from OHLCV data."""
    technicals = analyze(candles)
    signals: list[TradeSignal] = []

    for i, (candle, tech) in enumerate(zip(candles, technicals)):
        if tech.rsi is None:
            continue

        signal, confidence, reasoning = classify_signal(tech, sentiment)

        signals.append(
            TradeSignal(
                timestamp=candle.timestamp,
                coin=coin,
                signal=signal,
                confidence=confidence,
                price=candle.close,
                technical=tech,
                sentiment=sentiment,
                reasoning=reasoning,
            )
        )

    return signals
