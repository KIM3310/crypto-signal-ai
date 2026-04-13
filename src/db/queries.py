"""SQL queries for crypto signal data storage and retrieval.

Uses SQLite for local development. Schema is designed to be portable
to Snowflake / BigQuery / PostgreSQL for production use.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from src.config import DB_PATH
from src.data.models import BacktestResult, TradeSignal


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            coin TEXT NOT NULL,
            signal TEXT NOT NULL,
            confidence REAL NOT NULL,
            price REAL NOT NULL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            macd_histogram REAL,
            bb_upper REAL,
            bb_middle REAL,
            bb_lower REAL,
            bb_percent REAL,
            sentiment_score REAL,
            reasoning TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS backtest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            coin TEXT NOT NULL,
            total_return_pct REAL,
            sharpe_ratio REAL,
            max_drawdown_pct REAL,
            win_rate REAL,
            total_trades INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backtest_run_id INTEGER REFERENCES backtest_runs(id),
            entry_time TEXT,
            exit_time TEXT,
            entry_price REAL,
            exit_price REAL,
            side TEXT,
            pnl_pct REAL,
            signal TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_signals_coin_ts ON signals(coin, timestamp);
        CREATE INDEX IF NOT EXISTS idx_trades_run ON trades(backtest_run_id);
    """)


def insert_signals(conn: sqlite3.Connection, signals: list[TradeSignal]) -> int:
    rows = [
        (
            s.timestamp.isoformat(),
            s.coin,
            s.signal.value,
            s.confidence,
            s.price,
            s.technical.rsi,
            s.technical.macd,
            s.technical.macd_signal,
            s.technical.macd_histogram,
            s.technical.bb_upper,
            s.technical.bb_middle,
            s.technical.bb_lower,
            s.technical.bb_percent,
            s.sentiment.score if s.sentiment else None,
            s.reasoning,
        )
        for s in signals
    ]
    conn.executemany(
        """INSERT INTO signals
           (timestamp, coin, signal, confidence, price, rsi, macd, macd_signal,
            macd_histogram, bb_upper, bb_middle, bb_lower, bb_percent, sentiment_score, reasoning)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return len(rows)


def insert_backtest(conn: sqlite3.Connection, coin: str, result: BacktestResult) -> int:
    cur = conn.execute(
        """INSERT INTO backtest_runs
           (run_date, coin, total_return_pct, sharpe_ratio, max_drawdown_pct, win_rate, total_trades)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            coin,
            result.total_return_pct,
            result.sharpe_ratio,
            result.max_drawdown_pct,
            result.win_rate,
            result.total_trades,
        ),
    )
    run_id = cur.lastrowid

    trade_rows = [
        (
            run_id,
            t.entry_time.isoformat(),
            t.exit_time.isoformat(),
            t.entry_price,
            t.exit_price,
            t.side,
            t.pnl_pct,
            t.signal.value,
        )
        for t in result.trades
    ]
    conn.executemany(
        """INSERT INTO trades
           (backtest_run_id, entry_time, exit_time, entry_price, exit_price, side, pnl_pct, signal)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        trade_rows,
    )
    conn.commit()
    return run_id


# --- Analytics queries ---

QUERY_SIGNAL_DISTRIBUTION = """
    SELECT coin, signal, COUNT(*) as count,
           ROUND(AVG(confidence), 3) as avg_confidence
    FROM signals
    WHERE coin = ?
    GROUP BY coin, signal
    ORDER BY count DESC
"""

QUERY_RECENT_SIGNALS = """
    SELECT timestamp, coin, signal, confidence, price, rsi, reasoning
    FROM signals
    WHERE coin = ?
    ORDER BY timestamp DESC
    LIMIT ?
"""

QUERY_BACKTEST_HISTORY = """
    SELECT id, run_date, coin, total_return_pct, sharpe_ratio,
           max_drawdown_pct, win_rate, total_trades
    FROM backtest_runs
    WHERE coin = ?
    ORDER BY run_date DESC
    LIMIT ?
"""

QUERY_BEST_TRADES = """
    SELECT t.entry_time, t.exit_time, t.entry_price, t.exit_price,
           t.pnl_pct, t.signal, b.coin
    FROM trades t
    JOIN backtest_runs b ON t.backtest_run_id = b.id
    WHERE b.coin = ?
    ORDER BY t.pnl_pct DESC
    LIMIT ?
"""
