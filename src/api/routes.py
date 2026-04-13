from __future__ import annotations

from fastapi import FastAPI, Query
from pydantic import BaseModel

from src.data.fetcher import fetch_ohlcv, fetch_coin_list
from src.analysis.signals import generate_signals
from src.analysis.sentiment import analyze_sentiment, build_price_summary
from src.backtest.engine import run_backtest
from src.db.queries import (
    get_connection,
    init_schema,
    insert_signals,
    insert_backtest,
    QUERY_RECENT_SIGNALS,
    QUERY_SIGNAL_DISTRIBUTION,
    QUERY_BACKTEST_HISTORY,
)

app = FastAPI(
    title="Crypto Signal AI",
    description="AI-powered crypto trading signal generator with backtesting",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    conn = get_connection()
    init_schema(conn)
    conn.close()


@app.get("/api/signals/{coin_id}")
async def get_signals(
    coin_id: str = "bitcoin",
    days: int = Query(default=90, le=365),
    with_sentiment: bool = Query(default=False),
):
    """Generate trading signals for a given coin."""
    candles = await fetch_ohlcv(coin_id, days=days)

    sentiment = None
    if with_sentiment and candles:
        closes = [c.close for c in candles]
        summary = build_price_summary(closes, coin_id.upper())
        sentiment = await analyze_sentiment(coin_id, summary)

    signals = generate_signals(candles, coin_id.upper(), sentiment)

    conn = get_connection()
    insert_signals(conn, signals)
    conn.close()

    latest = signals[-5:] if signals else []
    return {
        "coin": coin_id,
        "total_signals": len(signals),
        "latest": [
            {
                "timestamp": s.timestamp.isoformat(),
                "signal": s.signal.value,
                "confidence": round(s.confidence, 3),
                "price": s.price,
                "rsi": round(s.technical.rsi, 2) if s.technical.rsi else None,
                "reasoning": s.reasoning,
            }
            for s in latest
        ],
        "sentiment": {
            "score": sentiment.score,
            "summary": sentiment.summary,
        }
        if sentiment
        else None,
    }


@app.get("/api/backtest/{coin_id}")
async def run_backtest_endpoint(
    coin_id: str = "bitcoin",
    days: int = Query(default=90, le=365),
    hold_periods: int = Query(default=5, le=30),
    fee_pct: float = Query(default=0.1),
):
    """Run backtest on a coin's historical data."""
    candles = await fetch_ohlcv(coin_id, days=days)
    signals = generate_signals(candles, coin_id.upper())
    result = run_backtest(signals, candles, hold_periods=hold_periods, fee_pct=fee_pct)

    conn = get_connection()
    run_id = insert_backtest(conn, coin_id, result)
    conn.close()

    return {
        "coin": coin_id,
        "run_id": run_id,
        "total_return_pct": round(result.total_return_pct, 2),
        "sharpe_ratio": round(result.sharpe_ratio, 3),
        "max_drawdown_pct": round(result.max_drawdown_pct, 2),
        "win_rate": round(result.win_rate, 3),
        "total_trades": result.total_trades,
        "recent_trades": [
            {
                "entry": t.entry_time.isoformat(),
                "exit": t.exit_time.isoformat(),
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl_pct": round(t.pnl_pct, 2),
            }
            for t in result.trades[-10:]
        ],
    }


@app.get("/api/analytics/{coin_id}")
async def get_analytics(
    coin_id: str = "bitcoin",
    limit: int = Query(default=20, le=100),
):
    """Get stored signal analytics and backtest history."""
    conn = get_connection()

    distribution = conn.execute(QUERY_SIGNAL_DISTRIBUTION, (coin_id.upper(),)).fetchall()
    recent = conn.execute(QUERY_RECENT_SIGNALS, (coin_id.upper(), limit)).fetchall()
    history = conn.execute(QUERY_BACKTEST_HISTORY, (coin_id.upper(), 10)).fetchall()

    conn.close()

    return {
        "coin": coin_id,
        "signal_distribution": [dict(r) for r in distribution],
        "recent_signals": [dict(r) for r in recent],
        "backtest_history": [dict(r) for r in history],
    }


@app.get("/api/coins")
async def list_coins(limit: int = Query(default=20, le=50)):
    """List top coins by market cap."""
    coins = await fetch_coin_list(limit=limit)
    return {
        "count": len(coins),
        "coins": [
            {
                "id": c["id"],
                "symbol": c["symbol"],
                "name": c["name"],
                "current_price": c.get("current_price"),
                "market_cap": c.get("market_cap"),
                "price_change_24h_pct": c.get("price_change_percentage_24h"),
            }
            for c in coins
        ],
    }


# === Webhook endpoints for n8n / workflow automation ===


class WebhookAlertRequest(BaseModel):
    coins: list[str] = ["bitcoin", "ethereum"]
    with_backtest: bool = True


class ProvisionRequest(BaseModel):
    team_name: str
    use_case: str
    coins: list[str] = ["bitcoin"]


@app.post("/api/webhook/alert")
async def webhook_alert(req: WebhookAlertRequest):
    """n8n-compatible webhook: generate signals for multiple coins at once."""
    from src.workflows.scheduler import check_and_alert

    results = await check_and_alert(coins=req.coins, run_backtest_flag=req.with_backtest)
    return {"status": "ok", "results": results}


@app.post("/api/webhook/provision")
async def webhook_provision(req: ProvisionRequest):
    """Provision a new monitoring workspace for a Non-Tech team."""
    import hashlib
    from datetime import datetime, timezone

    api_key = hashlib.sha256(
        f"{req.team_name}:{datetime.now(timezone.utc).isoformat()}".encode()
    ).hexdigest()[:24]

    return {
        "team_name": req.team_name,
        "use_case": req.use_case,
        "coins": req.coins,
        "api_key_masked": f"{api_key[:8]}...{api_key[-4:]}",
        "dashboard_url": f"/dashboard/{req.team_name.lower().replace(' ', '-')}",
        "provisioned_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }
