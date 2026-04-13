from __future__ import annotations

import math

from src.data.models import BacktestResult, BacktestTrade, OHLCV, Signal, TradeSignal


def run_backtest(
    signals: list[TradeSignal],
    candles: list[OHLCV],
    initial_capital: float = 10_000.0,
    fee_pct: float = 0.1,
    hold_periods: int = 5,
) -> BacktestResult:
    """Run a simple backtest on generated signals.

    Strategy: enter on BUY/STRONG_BUY, exit after hold_periods candles or on SELL signal.
    """
    capital = initial_capital
    equity_curve = [capital]
    trades: list[BacktestTrade] = []

    signal_map: dict[int, TradeSignal] = {}
    candle_idx_map: dict[str, int] = {}
    for i, candle in enumerate(candles):
        key = candle.timestamp.isoformat()
        candle_idx_map[key] = i

    for sig in signals:
        key = sig.timestamp.isoformat()
        if key in candle_idx_map:
            signal_map[candle_idx_map[key]] = sig

    position_entry: int | None = None
    entry_price = 0.0

    for i in range(len(candles)):
        sig = signal_map.get(i)

        # Check exit conditions
        if position_entry is not None:
            should_exit = False
            if i - position_entry >= hold_periods:
                should_exit = True
            if sig and sig.signal in (Signal.SELL, Signal.STRONG_SELL):
                should_exit = True

            if should_exit:
                exit_price = candles[i].close
                gross_pnl_pct = (exit_price / entry_price - 1) * 100
                net_pnl_pct = gross_pnl_pct - fee_pct * 2  # entry + exit fee
                capital *= 1 + net_pnl_pct / 100

                trades.append(
                    BacktestTrade(
                        entry_time=candles[position_entry].timestamp,
                        exit_time=candles[i].timestamp,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        side="long",
                        pnl_pct=net_pnl_pct,
                        signal=signal_map[position_entry].signal,
                    )
                )
                position_entry = None

        # Check entry conditions
        if position_entry is None and sig:
            if sig.signal in (Signal.BUY, Signal.STRONG_BUY) and sig.confidence >= 0.3:
                position_entry = i
                entry_price = candles[i].close

        equity_curve.append(capital)

    # Close open position at last candle
    if position_entry is not None and len(candles) > 0:
        exit_price = candles[-1].close
        gross_pnl_pct = (exit_price / entry_price - 1) * 100
        net_pnl_pct = gross_pnl_pct - fee_pct * 2

        trades.append(
            BacktestTrade(
                entry_time=candles[position_entry].timestamp,
                exit_time=candles[-1].timestamp,
                entry_price=entry_price,
                exit_price=exit_price,
                side="long",
                pnl_pct=net_pnl_pct,
                signal=signal_map[position_entry].signal,
            )
        )
        capital *= 1 + net_pnl_pct / 100
        equity_curve.append(capital)

    total_return = (capital / initial_capital - 1) * 100
    win_trades = [t for t in trades if t.pnl_pct > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0.0

    return BacktestResult(
        total_return_pct=total_return,
        sharpe_ratio=compute_sharpe(equity_curve),
        max_drawdown_pct=compute_max_drawdown(equity_curve),
        win_rate=win_rate,
        total_trades=len(trades),
        trades=trades,
        equity_curve=equity_curve,
    )


def compute_sharpe(equity_curve: list[float], risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio from equity curve."""
    if len(equity_curve) < 2:
        return 0.0

    returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            returns.append(equity_curve[i] / equity_curve[i - 1] - 1)

    if not returns:
        return 0.0

    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    if std_dev == 0:
        return 0.0

    # Annualize assuming daily returns
    annualized_return = avg_return * 365
    annualized_std = std_dev * math.sqrt(365)

    return (annualized_return - risk_free_rate) / annualized_std


def compute_max_drawdown(equity_curve: list[float]) -> float:
    """Maximum drawdown percentage."""
    if len(equity_curve) < 2:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100 if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    return max_dd
