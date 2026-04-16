from datetime import datetime, timezone

from src.backtest.engine import run_backtest, compute_sharpe, compute_max_drawdown
from src.data.models import (
    OHLCV,
    Signal,
    TechnicalResult,
    TradeSignal,
)


def _ts(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=timezone.utc)


def _candle(day: int, price: float) -> OHLCV:
    return OHLCV(
        timestamp=_ts(day),
        open=price,
        high=price * 1.01,
        low=price * 0.99,
        close=price,
        volume=1000.0,
    )


def _signal(day: int, price: float, sig: Signal, conf: float = 0.8) -> TradeSignal:
    return TradeSignal(
        timestamp=_ts(day),
        coin="BTC",
        signal=sig,
        confidence=conf,
        price=price,
        technical=TechnicalResult(rsi=50),
        reasoning="test",
    )


class TestBacktest:
    def test_no_signals_no_trades(self):
        candles = [_candle(i, 100.0) for i in range(1, 20)]
        result = run_backtest([], candles)
        assert result.total_trades == 0
        assert result.total_return_pct == 0.0

    def test_buy_and_hold(self):
        candles = [_candle(i, 100.0 + i * 2) for i in range(1, 20)]
        signals = [_signal(1, 102.0, Signal.BUY)]
        result = run_backtest(signals, candles, hold_periods=5)
        assert result.total_trades >= 1
        assert result.trades[0].pnl_pct > 0  # price went up

    def test_buy_sell_exit(self):
        prices = [100, 102, 104, 106, 103, 100, 98, 96, 94, 92]
        candles = [_candle(i + 1, float(p)) for i, p in enumerate(prices)]
        signals = [
            _signal(1, 100.0, Signal.BUY),
            _signal(5, 100.0, Signal.SELL),
        ]
        result = run_backtest(signals, candles, hold_periods=30)
        assert result.total_trades == 1
        # Exited on sell signal at index 4 (price=103), not hold_periods

    def test_low_confidence_skipped(self):
        candles = [_candle(i, 100.0) for i in range(1, 20)]
        signals = [_signal(1, 100.0, Signal.BUY, conf=0.1)]
        result = run_backtest(signals, candles)
        assert result.total_trades == 0

    def test_win_rate_calculation(self):
        prices = [100, 110, 120, 105, 90, 80, 95, 110, 125, 130]
        candles = [_candle(i + 1, float(p)) for i, p in enumerate(prices)]
        signals = [
            _signal(1, 100.0, Signal.BUY),
            _signal(5, 90.0, Signal.BUY),
        ]
        result = run_backtest(signals, candles, hold_periods=3)
        assert result.total_trades >= 1
        assert 0.0 <= result.win_rate <= 1.0


class TestSharpe:
    def test_flat_equity_zero_sharpe(self):
        equity = [10000.0] * 30
        assert compute_sharpe(equity) == 0.0

    def test_positive_return_positive_sharpe(self):
        equity = [10000.0 + i * 50 for i in range(30)]
        assert compute_sharpe(equity) > 0

    def test_single_point_zero(self):
        assert compute_sharpe([10000.0]) == 0.0


class TestMaxDrawdown:
    def test_no_drawdown(self):
        equity = [10000.0 + i * 100 for i in range(20)]
        assert compute_max_drawdown(equity) == 0.0

    def test_known_drawdown(self):
        equity = [100, 110, 120, 100, 90, 95, 130]
        dd = compute_max_drawdown(equity)
        # Peak was 120, trough was 90 -> 25%
        assert abs(dd - 25.0) < 0.1

    def test_single_point(self):
        assert compute_max_drawdown([100.0]) == 0.0
