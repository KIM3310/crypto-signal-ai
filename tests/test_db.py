from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.db.queries import get_connection, init_schema, insert_signals, insert_backtest
from src.data.models import (
    BacktestResult, BacktestTrade, Signal, TechnicalResult, TradeSignal, SentimentResult,
)


def _tmp_db(tmp_path: Path) -> sqlite3.Connection:
    conn = get_connection(tmp_path / "test.db")
    init_schema(conn)
    return conn


def _signal(price: float = 100.0) -> TradeSignal:
    return TradeSignal(
        timestamp=datetime(2024, 3, 15, tzinfo=timezone.utc),
        coin="BTC",
        signal=Signal.BUY,
        confidence=0.8,
        price=price,
        technical=TechnicalResult(
            rsi=35.0, macd=0.5, macd_signal=0.3, macd_histogram=0.2,
            bb_upper=110.0, bb_middle=100.0, bb_lower=90.0, bb_percent=0.3,
        ),
        sentiment=SentimentResult(score=0.6, summary="bullish"),
        reasoning="RSI oversold",
    )


class TestSchema:
    def test_init_schema_creates_tables(self, tmp_path):
        conn = _tmp_db(tmp_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r[0] for r in tables}
        assert "signals" in names
        assert "backtest_runs" in names
        assert "trades" in names
        conn.close()

    def test_init_schema_idempotent(self, tmp_path):
        conn = _tmp_db(tmp_path)
        init_schema(conn)  # second call should not raise
        conn.close()


class TestInsertSignals:
    def test_insert_and_count(self, tmp_path):
        conn = _tmp_db(tmp_path)
        signals = [_signal(100.0), _signal(105.0)]
        n = insert_signals(conn, signals)
        assert n == 2
        count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        assert count == 2
        conn.close()

    def test_all_technical_fields_stored(self, tmp_path):
        conn = _tmp_db(tmp_path)
        insert_signals(conn, [_signal()])
        row = conn.execute("SELECT * FROM signals WHERE id=1").fetchone()
        # Column indices: rsi=6, macd=7, macd_signal=8, macd_histogram=9,
        # bb_upper=10, bb_middle=11, bb_lower=12, bb_percent=13
        assert row[6] == 35.0   # rsi
        assert row[7] == 0.5    # macd
        assert row[8] == 0.3    # macd_signal
        assert row[9] == 0.2    # macd_histogram
        assert row[10] == 110.0  # bb_upper
        assert row[11] == 100.0  # bb_middle
        assert row[12] == 90.0   # bb_lower
        assert row[13] == 0.3    # bb_percent
        conn.close()

    def test_sentiment_score_stored(self, tmp_path):
        conn = _tmp_db(tmp_path)
        insert_signals(conn, [_signal()])
        row = conn.execute("SELECT sentiment_score FROM signals WHERE id=1").fetchone()
        assert row[0] == 0.6
        conn.close()


class TestInsertBacktest:
    def test_insert_backtest_run(self, tmp_path):
        conn = _tmp_db(tmp_path)
        result = BacktestResult(
            total_return_pct=5.2,
            sharpe_ratio=1.5,
            max_drawdown_pct=3.1,
            win_rate=0.65,
            total_trades=10,
            trades=[
                BacktestTrade(
                    entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    exit_time=datetime(2024, 1, 5, tzinfo=timezone.utc),
                    entry_price=100.0, exit_price=105.0,
                    side="long", pnl_pct=4.8, signal=Signal.BUY,
                )
            ],
            equity_curve=[10000, 10500],
        )
        run_id = insert_backtest(conn, "BTC", result)
        assert run_id >= 1

        row = conn.execute("SELECT * FROM backtest_runs WHERE id=?", (run_id,)).fetchone()
        assert row is not None

        trades = conn.execute("SELECT * FROM trades WHERE backtest_run_id=?", (run_id,)).fetchall()
        assert len(trades) == 1
        conn.close()
