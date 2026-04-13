from __future__ import annotations

from src.analysis.sentiment import build_price_summary


class TestBuildPriceSummary:
    def test_basic_summary(self):
        closes = [float(100 + i) for i in range(40)]
        result = build_price_summary(closes, "BTC")
        assert "BTC" in result
        assert "current price" in result
        assert "1D change" in result

    def test_insufficient_data(self):
        result = build_price_summary([100.0], "ETH")
        assert "insufficient data" in result

    def test_two_points(self):
        result = build_price_summary([100.0, 110.0], "SOL")
        assert "SOL" in result
        assert "+10.00%" in result

    def test_negative_change(self):
        closes = [100.0, 90.0]
        result = build_price_summary(closes, "BTC")
        assert "-10.00%" in result

    def test_30d_stats_with_enough_data(self):
        closes = [float(100 + i * 0.5) for i in range(40)]
        result = build_price_summary(closes, "BTC")
        assert "30D high" in result
        assert "30D change" in result
