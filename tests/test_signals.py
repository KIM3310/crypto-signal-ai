from datetime import datetime, timedelta, timezone

from src.analysis.signals import classify_signal, generate_signals
from src.data.models import OHLCV, SentimentResult, Signal, TechnicalResult


class TestClassifySignal:
    def test_oversold_rsi_is_buy(self):
        tech = TechnicalResult(rsi=25.0, macd=0.1, macd_signal=0.05, macd_histogram=0.05, bb_percent=0.1)
        signal, conf, _ = classify_signal(tech, None)
        assert signal in (Signal.BUY, Signal.STRONG_BUY)

    def test_overbought_rsi_is_sell(self):
        tech = TechnicalResult(rsi=80.0, macd=-0.1, macd_signal=0.05, macd_histogram=-0.15, bb_percent=0.9)
        signal, conf, _ = classify_signal(tech, None)
        assert signal in (Signal.SELL, Signal.STRONG_SELL)

    def test_neutral_indicators(self):
        tech = TechnicalResult(rsi=50.0, macd=0.01, macd_signal=0.01, macd_histogram=0.0, bb_percent=0.5)
        signal, _, _ = classify_signal(tech, None)
        assert signal == Signal.NEUTRAL

    def test_sentiment_boosts_buy(self):
        tech = TechnicalResult(rsi=35.0, macd=0.1, macd_signal=0.05, macd_histogram=0.05, bb_percent=0.3)
        sentiment = SentimentResult(score=0.8, summary="bullish")
        signal, _, reasoning = classify_signal(tech, sentiment)
        assert signal in (Signal.BUY, Signal.STRONG_BUY)
        assert "긍정" in reasoning

    def test_sentiment_boosts_sell(self):
        tech = TechnicalResult(rsi=65.0, macd=-0.1, macd_signal=0.05, macd_histogram=-0.15, bb_percent=0.85)
        sentiment = SentimentResult(score=-0.8, summary="bearish")
        signal, _, reasoning = classify_signal(tech, sentiment)
        assert signal in (Signal.SELL, Signal.STRONG_SELL)
        assert "부정" in reasoning

    def test_bollinger_lower_break(self):
        tech = TechnicalResult(rsi=45.0, bb_percent=-0.1)
        signal, _, reasoning = classify_signal(tech, None)
        assert "볼린저" in reasoning

    def test_confidence_bounded(self):
        tech = TechnicalResult(rsi=10.0, macd=5.0, macd_signal=0.0, macd_histogram=5.0, bb_percent=-0.5)
        _, conf, _ = classify_signal(tech, None)
        assert 0.0 <= conf <= 1.0


class TestGenerateSignals:
    def test_generates_signals_from_candles(self):
        candles = [
            OHLCV(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i),
                open=float(100 + i), high=float(102 + i),
                low=float(98 + i), close=float(100 + i),
                volume=1000.0,
            )
            for i in range(40)
        ]
        signals = generate_signals(candles, "BTC")
        assert len(signals) > 0
        assert all(s.coin == "BTC" for s in signals)

    def test_signals_have_valid_fields(self):
        candles = [
            OHLCV(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i),
                open=float(100 + i % 10), high=float(105 + i % 10),
                low=float(95 + i % 10), close=float(100 + i % 10),
                volume=1000.0,
            )
            for i in range(40)
        ]
        signals = generate_signals(candles)
        for s in signals:
            assert isinstance(s.signal, Signal)
            assert 0.0 <= s.confidence <= 1.0
            assert s.price > 0
