"""Market-data fetcher.

Uses the public `CoinGecko <https://www.coingecko.com/en/api>`_ API
to pull daily OHLCV candles and a ranked coin list.  CoinGecko's free
tier is rate-limited (about 10--30 req/min depending on IP); callers
should cache responses or use a paid API key for production use.

All network access goes through a single ``httpx.AsyncClient`` to
respect the async FastAPI request model.  Failures are normalized to
``FetchError`` so downstream handlers can translate them into 502
responses without leaking HTTP-client internals.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from src.data.models import OHLCV

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT_SECONDS = 15.0


class FetchError(RuntimeError):
    """Raised when a market-data fetch fails at the network or parse layer."""


def _build_headers() -> dict[str, str]:
    """Attach the optional CoinGecko demo/paid API key when available."""
    headers = {"Accept": "application/json", "User-Agent": "crypto-signal-ai/0.1"}
    key = os.getenv("COINGECKO_API_KEY")
    if key:
        headers["x-cg-demo-api-key"] = key
    return headers


async def _get_json(client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> Any:
    """Issue a GET, raising :class:`FetchError` on any non-2xx or parse failure."""
    url = f"{COINGECKO_BASE}{path}"
    try:
        response = await client.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise FetchError(f"Network error calling {url}: {exc}") from exc

    if response.status_code >= 400:
        raise FetchError(f"Upstream {response.status_code} from {url}: {response.text[:200]}")

    try:
        return response.json()
    except ValueError as exc:
        raise FetchError(f"Invalid JSON from {url}: {exc}") from exc


async def fetch_ohlcv(coin_id: str, days: int = 90) -> list[OHLCV]:
    """Fetch daily OHLC candles for ``coin_id`` over the last ``days`` days.

    CoinGecko's ``/coins/{id}/ohlc`` endpoint returns 4-column rows
    ``[ts_ms, open, high, low, close]``. Volume is fetched separately
    from ``/coins/{id}/market_chart`` and merged by timestamp.

    Parameters
    ----------
    coin_id:
        CoinGecko coin slug (e.g. ``"bitcoin"``).
    days:
        Lookback window in days. CoinGecko accepts ``1``, ``7``, ``14``,
        ``30``, ``90``, ``180``, ``365``, or ``"max"``.

    Returns
    -------
    list[OHLCV]
        Candles in chronological order.  Volume is ``0.0`` when the
        market-chart call fails so technical indicators still work.
    """
    headers = _build_headers()
    async with httpx.AsyncClient(headers=headers) as client:
        ohlc = await _get_json(
            client,
            f"/coins/{coin_id}/ohlc",
            {"vs_currency": "usd", "days": days},
        )
        try:
            chart = await _get_json(
                client,
                f"/coins/{coin_id}/market_chart",
                {"vs_currency": "usd", "days": days, "interval": "daily"},
            )
            volume_by_ts: dict[int, float] = {
                int(ts): float(vol) for ts, vol in chart.get("total_volumes", [])
            }
        except FetchError as exc:
            logger.warning("volume fetch failed for %s: %s", coin_id, exc)
            volume_by_ts = {}

    if not isinstance(ohlc, list):
        raise FetchError(f"Unexpected OHLC payload for {coin_id}: {type(ohlc).__name__}")

    candles: list[OHLCV] = []
    for row in ohlc:
        if not isinstance(row, list) or len(row) < 5:
            continue
        ts_ms, open_, high, low, close = row[0], row[1], row[2], row[3], row[4]
        try:
            ts = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OverflowError) as exc:
            logger.debug("skipping candle with bad timestamp %r: %s", ts_ms, exc)
            continue
        candles.append(
            OHLCV(
                timestamp=ts,
                open=float(open_),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=volume_by_ts.get(int(ts_ms), 0.0),
            )
        )
    return candles


async def fetch_coin_list(limit: int = 50) -> list[dict[str, Any]]:
    """Return the top ``limit`` coins by market-cap from CoinGecko.

    Each entry has at least ``id``, ``symbol``, ``name``, and
    ``current_price`` keys; callers should treat it as a read-only dict.
    """
    if limit < 1:
        raise FetchError("limit must be >= 1")

    headers = _build_headers()
    async with httpx.AsyncClient(headers=headers) as client:
        data = await _get_json(
            client,
            "/coins/markets",
            {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false",
            },
        )

    if not isinstance(data, list):
        raise FetchError(f"Unexpected coin-list payload: {type(data).__name__}")
    return data
