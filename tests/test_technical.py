from datetime import datetime, timezone

from src.analysis.technical import compute_rsi, compute_macd, compute_bollinger, analyze
from src.data.models import OHLCV


def _make_candles(closes: list[float]) -> list[OHLCV]:
    from datetime import timedelta
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        OHLCV(
            timestamp=base + timedelta(days=i),
            open=c, high=c * 1.01, low=c * 0.99, close=c, volume=1000.0,
        )
        for i, c in enumerate(closes)
    ]


class TestRSI:
    def test_rsi_returns_correct_length(self):
        closes = [float(40 + i) for i in range(30)]
        result = compute_rsi(closes)
        assert len(result) == len(closes)

    def test_rsi_first_values_are_none(self):
        closes = [float(40 + i) for i in range(30)]
        result = compute_rsi(closes, period=14)
        assert all(r is None for r in result[:14])

    def test_rsi_values_in_range(self):
        closes = [float(40 + i % 10) for i in range(50)]
        result = compute_rsi(closes)
        for r in result:
            if r is not None:
                assert 0.0 <= r <= 100.0

    def test_rsi_uptrend_is_high(self):
        closes = [float(100 + i * 2) for i in range(30)]
        result = compute_rsi(closes)
        valid = [r for r in result if r is not None]
        assert valid[-1] > 60

    def test_rsi_downtrend_is_low(self):
        closes = [float(200 - i * 2) for i in range(30)]
        result = compute_rsi(closes)
        valid = [r for r in result if r is not None]
        assert valid[-1] < 40

    def test_rsi_insufficient_data(self):
        result = compute_rsi([1.0, 2.0, 3.0])
        assert all(r is None for r in result)


class TestMACD:
    def test_macd_returns_correct_length(self):
        closes = [float(50 + i) for i in range(40)]
        result = compute_macd(closes)
        assert len(result) == len(closes)

    def test_macd_early_values_are_none(self):
        closes = [float(50 + i) for i in range(40)]
        result = compute_macd(closes)
        assert result[0] == (None, None, None)

    def test_macd_later_values_are_tuples(self):
        closes = [float(50 + i) for i in range(40)]
        result = compute_macd(closes)
        macd_v, sig_v, hist_v = result[-1]
        assert macd_v is not None
        assert sig_v is not None
        assert hist_v is not None

    def test_macd_histogram_is_difference(self):
        closes = [float(50 + i * 0.5) for i in range(40)]
        result = compute_macd(closes)
        macd_v, sig_v, hist_v = result[-1]
        if macd_v is not None and sig_v is not None:
            assert abs(hist_v - (macd_v - sig_v)) < 1e-10


class TestBollinger:
    def test_bollinger_returns_correct_length(self):
        closes = [float(100 + i) for i in range(30)]
        result = compute_bollinger(closes)
        assert len(result) == len(closes)

    def test_bollinger_bands_order(self):
        closes = [float(100 + i % 5) for i in range(30)]
        result = compute_bollinger(closes)
        upper, middle, lower, pct = result[-1]
        assert upper > middle > lower

    def test_bollinger_percent_in_range_normally(self):
        closes = [float(100 + i % 3) for i in range(30)]
        result = compute_bollinger(closes)
        _, _, _, pct = result[-1]
        assert pct is not None
        assert -0.5 <= pct <= 1.5  # can go slightly outside 0-1


class TestAnalyze:
    def test_analyze_returns_results_for_each_candle(self):
        candles = _make_candles([float(100 + i) for i in range(40)])
        results = analyze(candles)
        assert len(results) == len(candles)

    def test_analyze_populates_all_indicators(self):
        candles = _make_candles([float(100 + i * 0.5) for i in range(40)])
        results = analyze(candles)
        last = results[-1]
        assert last.rsi is not None
        assert last.macd is not None
        assert last.bb_upper is not None
