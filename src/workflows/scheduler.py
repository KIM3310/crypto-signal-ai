"""Standalone automation scheduler for crypto signal monitoring.

Runs signal generation on a configurable interval without n8n,
with Slack/webhook notification support for Non-Tech team usage.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import httpx

from src.config import DEFAULT_COINS, CHECK_INTERVAL_SECONDS
from src.data.fetcher import fetch_ohlcv, FetchError
from src.analysis.signals import generate_signals
from src.analysis.sentiment import analyze_sentiment, build_price_summary
from src.backtest.engine import run_backtest
from src.db.queries import get_connection, init_schema, insert_signals, insert_backtest

logger = logging.getLogger(__name__)


async def notify_slack(webhook_url: str, message: str) -> None:
    """Send alert to Slack via incoming webhook."""
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(webhook_url, json={"text": message})


async def notify_webhook(url: str, payload: dict) -> None:
    """Send alert to any webhook endpoint (n8n, Zapier, etc.)."""
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload)


def format_signal_alert(coin: str, signal_data: dict, backtest_data: dict | None) -> str:
    """Format signal data into a Korean alert message for Non-Tech users."""
    latest = (signal_data.get("latest") or [{}])[-1]
    sentiment = signal_data.get("sentiment") or {}

    lines = [
        f"📊 *{coin.upper()} 시그널 리포트*",
        f"시간: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"시그널: {latest.get('signal', 'N/A')}",
        f"신뢰도: {latest.get('confidence', 0):.1%}",
        f"가격: ${latest.get('price', 0):,.2f}",
        f"RSI: {latest.get('rsi', 'N/A')}",
        f"근거: {latest.get('reasoning', '')}",
    ]

    if sentiment:
        lines.append(f"감성분석: {sentiment.get('summary', '')}")

    if backtest_data:
        lines.extend([
            "",
            f"📈 백테스트 (90일)",
            f"총 수익률: {backtest_data.get('total_return_pct', 0):+.2f}%",
            f"Sharpe: {backtest_data.get('sharpe_ratio', 0):.3f}",
            f"MDD: -{backtest_data.get('max_drawdown_pct', 0):.2f}%",
            f"승률: {backtest_data.get('win_rate', 0):.1%}",
        ])

    return "\n".join(lines)


async def check_and_alert(
    coins: list[str] | None = None,
    slack_webhook: str | None = None,
    n8n_webhook: str | None = None,
    run_backtest_flag: bool = True,
) -> list[dict]:
    """Run signal check for given coins and send alerts."""
    coins = coins or DEFAULT_COINS
    slack_url = slack_webhook or os.environ.get("SLACK_WEBHOOK_URL")
    n8n_url = n8n_webhook or os.environ.get("N8N_WEBHOOK_URL")

    conn = get_connection()
    init_schema(conn)

    results = []

    for coin in coins:
        try:
            candles = await fetch_ohlcv(coin, days=90)
            if not candles:
                continue

            closes = [c.close for c in candles]
            summary = build_price_summary(closes, coin.upper())

            sentiment = None
            if os.environ.get("OPENAI_API_KEY"):
                sentiment = await analyze_sentiment(coin, summary)

            signals = generate_signals(candles, coin.upper(), sentiment)
            insert_signals(conn, signals)

            latest = signals[-1] if signals else None
            signal_data = {
                "coin": coin,
                "total_signals": len(signals),
                "latest": [
                    {
                        "signal": s.signal.value,
                        "confidence": round(s.confidence, 3),
                        "price": s.price,
                        "rsi": round(s.technical.rsi, 2) if s.technical.rsi else None,
                        "reasoning": s.reasoning,
                    }
                    for s in signals[-3:]
                ],
                "sentiment": {"score": sentiment.score, "summary": sentiment.summary}
                if sentiment
                else None,
            }

            backtest_data = None
            if run_backtest_flag:
                bt_result = run_backtest(signals, candles)
                insert_backtest(conn, coin, bt_result)
                backtest_data = {
                    "total_return_pct": round(bt_result.total_return_pct, 2),
                    "sharpe_ratio": round(bt_result.sharpe_ratio, 3),
                    "max_drawdown_pct": round(bt_result.max_drawdown_pct, 2),
                    "win_rate": round(bt_result.win_rate, 3),
                }

            # Alert on actionable signals only
            if latest and latest.signal.value in ("strong_buy", "strong_sell"):
                message = format_signal_alert(coin, signal_data, backtest_data)

                if slack_url:
                    await notify_slack(slack_url, message)

                if n8n_url:
                    await notify_webhook(n8n_url, {
                        "type": "crypto_signal",
                        "coin": coin,
                        "signal": latest.signal.value,
                        "confidence": latest.confidence,
                        "price": latest.price,
                        "backtest": backtest_data,
                        "message": message,
                    })

            results.append({"coin": coin, "signal": signal_data, "backtest": backtest_data})

        except Exception as e:
            logger.error(f"Error processing {coin}: {e}")
            results.append({"coin": coin, "error": str(e)})

    conn.close()
    return results


async def run_scheduler(
    interval: int = CHECK_INTERVAL_SECONDS,
    coins: list[str] | None = None,
) -> None:
    """Run continuous monitoring loop."""
    logger.info(f"Starting crypto signal scheduler (interval={interval}s, coins={coins})")

    while True:
        logger.info("Running signal check...")
        results = await check_and_alert(coins=coins)

        for r in results:
            if "error" in r:
                logger.error(f"{r['coin']}: {r['error']}")
            else:
                latest = r["signal"]["latest"][-1] if r["signal"]["latest"] else {}
                logger.info(f"{r['coin']}: {latest.get('signal', 'N/A')} (conf={latest.get('confidence', 0):.2f})")

        await asyncio.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())
