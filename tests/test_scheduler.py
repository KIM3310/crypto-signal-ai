from __future__ import annotations

from src.workflows.scheduler import format_signal_alert


class TestFormatSignalAlert:
    def test_basic_format(self):
        signal_data = {
            "latest": [
                {
                    "signal": "buy",
                    "confidence": 0.75,
                    "price": 65000,
                    "rsi": 35,
                    "reasoning": "RSI 과매도",
                }
            ],
            "sentiment": {"summary": "시장 긍정적"},
        }
        backtest_data = {
            "total_return_pct": 12.5,
            "sharpe_ratio": 1.8,
            "max_drawdown_pct": 5.2,
            "win_rate": 0.68,
        }
        result = format_signal_alert("BTC", signal_data, backtest_data)
        assert "BTC" in result
        assert "buy" in result
        assert "12.5" in result or "+12.50" in result

    def test_no_backtest(self):
        signal_data = {
            "latest": [
                {
                    "signal": "sell",
                    "confidence": 0.6,
                    "price": 60000,
                    "rsi": 72,
                    "reasoning": "RSI 과매수",
                }
            ],
        }
        result = format_signal_alert("ETH", signal_data, None)
        assert "ETH" in result
        assert "백테스트" not in result

    def test_none_latest(self):
        result = format_signal_alert("SOL", {"latest": None}, None)
        assert "SOL" in result

    def test_empty_latest(self):
        result = format_signal_alert("BTC", {"latest": []}, None)
        assert "BTC" in result

    def test_missing_sentiment(self):
        signal_data = {
            "latest": [
                {
                    "signal": "neutral",
                    "confidence": 0.3,
                    "price": 100,
                    "rsi": 50,
                    "reasoning": "중립",
                }
            ],
            "sentiment": None,
        }
        result = format_signal_alert("DOGE", signal_data, None)
        assert "DOGE" in result

    def test_full_backtest_metrics(self):
        signal_data = {
            "latest": [
                {
                    "signal": "strong_buy",
                    "confidence": 0.9,
                    "price": 70000,
                    "rsi": 25,
                    "reasoning": "RSI+MACD",
                }
            ]
        }
        backtest = {
            "total_return_pct": -3.5,
            "sharpe_ratio": -0.2,
            "max_drawdown_pct": 15.0,
            "win_rate": 0.4,
        }
        result = format_signal_alert("BTC", signal_data, backtest)
        assert "Sharpe" in result
        assert "MDD" in result
        assert "승률" in result
