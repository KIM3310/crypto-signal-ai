from __future__ import annotations

import json
import os

from openai import AsyncOpenAI

from src.data.models import SentimentResult

SYSTEM_PROMPT = """You are a crypto market sentiment analyst.
Given a coin name and recent price action summary, produce a JSON object:
{
  "score": <float between -1.0 (very bearish) and 1.0 (very bullish)>,
  "summary": "<one-sentence market sentiment summary in Korean>"
}
Respond ONLY with the JSON object. No markdown, no explanation."""


async def analyze_sentiment(
    coin: str,
    price_summary: str,
    client: AsyncOpenAI | None = None,
) -> SentimentResult:
    """Use LLM to analyze market sentiment from price action context."""
    if client is None:
        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    user_prompt = f"Coin: {coin}\nRecent price action:\n{price_summary}"

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=200,
    )

    text = resp.choices[0].message.content or "{}"
    text = text.strip().removeprefix("```json").removesuffix("```").strip()

    parsed = json.loads(text)
    score = max(-1.0, min(1.0, float(parsed.get("score", 0.0))))

    return SentimentResult(
        score=score,
        summary=parsed.get("summary", ""),
        sources=["llm-price-action-analysis"],
    )


def build_price_summary(closes: list[float], coin: str = "BTC") -> str:
    """Build a concise price action summary for LLM analysis."""
    if len(closes) < 2:
        return f"{coin}: insufficient data"

    current = closes[-1]
    pct_1d = (closes[-1] / closes[-2] - 1) * 100 if len(closes) >= 2 else 0
    pct_7d = (closes[-1] / closes[-7] - 1) * 100 if len(closes) >= 7 else 0
    pct_30d = (closes[-1] / closes[-30] - 1) * 100 if len(closes) >= 30 else 0

    high_30d = max(closes[-30:]) if len(closes) >= 30 else max(closes)
    low_30d = min(closes[-30:]) if len(closes) >= 30 else min(closes)

    return (
        f"{coin} current price: ${current:,.2f}\n"
        f"1D change: {pct_1d:+.2f}%\n"
        f"7D change: {pct_7d:+.2f}%\n"
        f"30D change: {pct_30d:+.2f}%\n"
        f"30D high: ${high_30d:,.2f}, low: ${low_30d:,.2f}"
    )
