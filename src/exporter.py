"""Normalização e serialização do catálogo JSON."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

BRASILIA_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def _number(value: Any) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def normalize_coin(coin: dict[str, Any], currency: str) -> dict[str, Any] | None:
    coin_id = str(coin.get("id") or "").strip()
    symbol = str(coin.get("symbol") or "").strip().upper()
    name = str(coin.get("name") or "").strip()
    if not coin_id or not symbol or not name:
        return None

    current_price = _number(coin.get("current_price"))
    normalized: dict[str, Any] = {
        "id": coin_id,
        "symbol": symbol,
        "name": name,
        "display_name": f"{symbol} - {name}",
        "image": str(coin.get("image") or ""),
        "current_price": current_price,
        f"current_price_{currency}": current_price,
        "market_cap_rank": _number(coin.get("market_cap_rank")),
        "market_cap": _number(coin.get("market_cap")),
        "total_volume": _number(coin.get("total_volume")),
        "price_change_percentage_24h": _number(coin.get("price_change_percentage_24h")),
    }
    return normalized


def build_catalog(
    coins: Iterable[dict[str, Any]],
    *,
    currency: str = "brl",
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Cria um catálogo determinístico, removendo IDs duplicados e registros incompletos."""
    currency = currency.lower()
    unique: dict[str, dict[str, Any]] = {}
    for coin in coins:
        normalized = normalize_coin(coin, currency)
        if normalized and normalized["id"] not in unique:
            unique[normalized["id"]] = normalized

    normalized_coins = list(unique.values())
    normalized_coins.sort(
        key=lambda item: (
            item["market_cap_rank"] is None,
            item["market_cap_rank"] if item["market_cap_rank"] is not None else float("inf"),
            item["name"].casefold(),
        )
    )
    next_fallback_rank = max(
        (int(item["market_cap_rank"]) for item in normalized_coins if item["market_cap_rank"] is not None),
        default=0,
    ) + 1
    for item in normalized_coins:
        if item["market_cap_rank"] is None:
            item["market_cap_rank"] = next_fallback_rank
            next_fallback_rank += 1

    timestamp = generated_at or datetime.now(BRASILIA_TIMEZONE)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=BRASILIA_TIMEZONE)
    else:
        timestamp = timestamp.astimezone(BRASILIA_TIMEZONE)
    iso_timestamp = timestamp.isoformat(timespec="seconds")
    return {
        "schema_version": 1,
        "last_updated_timestamp": iso_timestamp,
        "source": "CoinGecko",
        "vs_currency": currency,
        "total": len(normalized_coins),
        "cryptos": normalized_coins,
    }


def catalog_to_json(catalog: dict[str, Any]) -> bytes:
    return json.dumps(catalog, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
