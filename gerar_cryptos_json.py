"""Gera cryptos.json pelo terminal usando o mesmo núcleo do app Streamlit."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.coingecko import CoinGeckoClient, FetchProgress
from src.exporter import build_catalog, catalog_to_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera um catálogo JSON de criptomoedas da CoinGecko.")
    parser.add_argument("--currency", choices=("brl", "usd", "eur"), default="brl")
    parser.add_argument("--pages", type=int, default=4)
    parser.add_argument("--per-page", type=int, default=250)
    parser.add_argument("--delay", type=float, default=30.0)
    parser.add_argument("--output", type=Path, default=Path("cryptos.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    def report(progress: FetchProgress) -> None:
        print(f"[{progress.page}/{args.pages}] {progress.message} Total: {progress.collected}")

    client = CoinGeckoClient(api_key=os.getenv("COINGECKO_API_KEY"))
    coins = client.fetch_markets(
        currency=args.currency,
        pages=args.pages,
        per_page=args.per_page,
        delay_seconds=args.delay,
        progress_callback=report,
    )
    payload = catalog_to_json(build_catalog(coins, currency=args.currency))
    args.output.write_bytes(payload)
    print(f"Arquivo salvo em {args.output.resolve()} ({len(coins)} registros).")


if __name__ == "__main__":
    main()
