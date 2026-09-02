"""Gera cryptos.json pelo terminal usando o mesmo núcleo do app Streamlit."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.coingecko import CoinGeckoClient, FetchProgress
from src.exporter import build_catalog, catalog_to_json

MAX_PAGES = 40
CRYPTOS_PER_PAGE = 250


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera um catálogo JSON de criptomoedas da CoinGecko.")
    parser.add_argument("--currency", choices=("brl", "usd", "eur"), default="brl")
    parser.add_argument("--delay", type=float, default=30.0)
    parser.add_argument("--block-delay", type=float, default=60.0)
    parser.add_argument("--output", type=Path, default=Path("cryptos.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    def report(progress: FetchProgress) -> None:
        print(f"[{progress.page}/{MAX_PAGES}] {progress.message} Total: {progress.collected}")

    client = CoinGeckoClient(api_key=os.getenv("COINGECKO_API_KEY"))
    coins = client.fetch_markets(
        currency=args.currency,
        pages=MAX_PAGES,
        per_page=CRYPTOS_PER_PAGE,
        delay_seconds=args.delay,
        block_delay_seconds=args.block_delay,
        progress_callback=report,
    )
    payload = catalog_to_json(build_catalog(coins, currency=args.currency))
    args.output.write_bytes(payload)
    print(f"Arquivo salvo em {args.output.resolve()} ({len(coins)} registros).")


if __name__ == "__main__":
    main()
