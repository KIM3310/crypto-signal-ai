from __future__ import annotations

import json
import logging
import os

from openai import AsyncOpenAI

from src.config import LLM_MODEL, LLM_TEMPERATURE
from src.data.models import SentimentResult

logger = logging.getLogger(__name__)

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
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, returning neutral sentiment")
            return SentimentResult(score=0.0, summary="API key not configured", sources=[])
        client = AsyncOpenAI(api_key=api_key)

    user_prompt = f"Coin: {coin}\nRecent price action:\n{price_summary}"

    try:
        resp = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=200,
        )

        if not resp.choices:
            logger.warning("LLM returned empty choices")
            return SentimentResult(score=0.0, summary="LLM returned no response", sources=[])

        text = resp.choices[0].message.content or "{}"
        text = text.strip().removeprefix("```json").removesuffix("```").strip()

        parsed = json.loads(text)
        score = max(-1.0, min(1.0, float(parsed.get("score", 0.0))))

        return SentimentResult(
            score=score,
            summary=parsed.get("summary", ""),
            sources=["llm-price-action-analysis"],
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return SentimentResult(score=0.0, summary="LLM response parse error", sources=[])
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid score value from LLM: {e}")
        return SentimentResult(score=0.0, summary="Invalid LLM output", sources=[])
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return SentimentResult(score=0.0, summary=f"Analysis error: {type(e).__name__}", sources=[])


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
