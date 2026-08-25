"""Cliente resiliente para o endpoint de mercados da CoinGecko."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://api.coingecko.com/api/v3/coins/markets"
SUPPORTED_CURRENCIES = {"brl", "usd", "eur"}


class CoinGeckoError(RuntimeError):
    """Erro amigável ocorrido durante a coleta."""


@dataclass(frozen=True)
class FetchProgress:
    page: int
    collected: int
    message: str


ProgressCallback = Callable[[FetchProgress], None]


class CoinGeckoClient:
    """Cliente HTTP com timeout, repetição e suporte à chave Demo."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        retry = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "CryptoJSON-Studio/1.0",
            }
        )
        if api_key:
            self.session.headers["x-cg-demo-api-key"] = api_key.strip()

    def fetch_markets(
        self,
        *,
        currency: str = "brl",
        pages: int = 4,
        per_page: int = 250,
        delay_seconds: float = 30.0,
        progress_callback: ProgressCallback | None = None,
    ) -> list[dict[str, Any]]:
        """Coleta páginas de mercado e encerra ao encontrar uma página vazia."""
        currency = currency.lower()
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Moeda não suportada: {currency}")
        if not 1 <= pages <= 80:
            raise ValueError("O total de páginas deve ficar entre 1 e 80.")
        if not 1 <= per_page <= 250:
            raise ValueError("O total por página deve ficar entre 1 e 250.")
        if pages > 1 and delay_seconds < 30:
            raise ValueError("O intervalo entre páginas deve ser de pelo menos 30 segundos.")

        collected: list[dict[str, Any]] = []
        for page in range(1, pages + 1):
            if progress_callback:
                progress_callback(FetchProgress(page, len(collected), f"Consultando a página {page}…"))
            params = {
                "vs_currency": currency,
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": "false",
                "price_change_percentage": "24h",
                "locale": "pt",
            }
            try:
                response = self.session.get(API_URL, params=params, timeout=self.timeout_seconds)
            except requests.Timeout as exc:
                raise CoinGeckoError("A CoinGecko demorou demais para responder. Tente novamente.") from exc
            except requests.RequestException as exc:
                raise CoinGeckoError("Não foi possível conectar à CoinGecko. Verifique a conexão e tente novamente.") from exc

            if response.status_code == 429:
                raise CoinGeckoError(
                    "O limite temporário da CoinGecko foi atingido. Aguarde alguns minutos, reduza as páginas ou informe uma chave Demo."
                )
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                raise CoinGeckoError(f"A CoinGecko respondeu com o código HTTP {response.status_code}.") from exc

            try:
                page_items = response.json()
            except requests.JSONDecodeError as exc:
                raise CoinGeckoError("A CoinGecko retornou uma resposta que não é um JSON válido.") from exc
            if not isinstance(page_items, list):
                raise CoinGeckoError("A CoinGecko retornou dados em um formato inesperado.")
            if not page_items:
                if progress_callback:
                    progress_callback(FetchProgress(page, len(collected), "Fim da lista encontrado."))
                break

            collected.extend(item for item in page_items if isinstance(item, dict))
            if progress_callback:
                progress_callback(FetchProgress(page, len(collected), f"Página {page} concluída."))
            if page < pages and len(page_items) == per_page and delay_seconds:
                time.sleep(delay_seconds)
            if len(page_items) < per_page:
                break

        if not collected:
            raise CoinGeckoError("Nenhuma criptomoeda foi encontrada para gerar o catálogo.")
        return collected
