from datetime import datetime, timezone

import pytest

from src.exporter import build_catalog, catalog_to_json


def test_build_catalog_normalizes_deduplicates_and_sorts() -> None:
    coins = [
        {"id": "ether", "symbol": "eth", "name": "Ether", "current_price": 20, "market_cap_rank": 2},
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "current_price": 30, "market_cap_rank": 1},
        {"id": "bitcoin", "symbol": "btc", "name": "Duplicado", "current_price": 99, "market_cap_rank": 3},
        {"id": "incompleto", "symbol": "", "name": "Ignorado"},
    ]
    catalog = build_catalog(
        coins,
        currency="brl",
        generated_at=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
    )

    assert catalog["total"] == 2
    assert catalog["last_updated_timestamp"] == "2026-08-24T09:00:00-03:00"
    assert [coin["id"] for coin in catalog["cryptos"]] == ["bitcoin", "ether"]
    assert catalog["cryptos"][0]["symbol"] == "BTC"
    assert catalog["cryptos"][0]["current_price_brl"] == 30


def test_catalog_to_json_keeps_unicode_and_rejects_nan() -> None:
    payload = catalog_to_json({"nome": "Real brasileiro"})
    assert "brasileiro" in payload.decode("utf-8")

    with pytest.raises(ValueError):
        catalog_to_json({"price": float("nan")})
