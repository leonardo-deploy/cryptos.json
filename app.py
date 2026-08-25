"""Interface Streamlit do gerador de catálogo de criptomoedas."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.coingecko import CoinGeckoClient, CoinGeckoError, FetchProgress
from src.exporter import build_catalog, catalog_to_json

st.set_page_config(
    page_title="CryptosJson",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --accent: #8b5cf6; --accent-2: #22d3ee; }
      .stApp {
        background:
          radial-gradient(circle at 12% 8%, rgba(139,92,246,.14), transparent 30rem),
          radial-gradient(circle at 90% 12%, rgba(34,211,238,.10), transparent 28rem),
          #080b14;
      }
      [data-testid="stSidebar"] { background: rgba(13,17,30,.92); }
      .hero {
        padding: 2.2rem 2.4rem;
        border: 1px solid rgba(148,163,184,.16);
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(139,92,246,.16), rgba(34,211,238,.07));
        box-shadow: 0 24px 80px rgba(0,0,0,.24);
        margin-bottom: 1.4rem;
      }
      .eyebrow { color: #67e8f9; font-size: .78rem; font-weight: 750; letter-spacing: .14em; }
      .hero h1 { margin: .35rem 0 .5rem; font-size: clamp(2rem, 5vw, 3.55rem); line-height: 1.05; }
      .hero p { max-width: 750px; color: #b8c2d8; font-size: 1.05rem; margin: 0; }
      [data-testid="stMetric"] {
        background: rgba(15,23,42,.62); border: 1px solid rgba(148,163,184,.13);
        border-radius: 16px; padding: .75rem 1rem;
      }
      .stButton > button, .stDownloadButton > button { border-radius: 12px; min-height: 2.8rem; font-weight: 700; }
      .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        border: 0; background: linear-gradient(90deg, var(--accent), #6d5dfc 55%, var(--accent-2));
      }
      .hint { color: #94a3b8; font-size: .88rem; }
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _secret(name: str) -> str | None:
    """Obtém segredo sem exigir que secrets.toml exista."""
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name)  # type: ignore[no-any-return]
    except FileNotFoundError:
        return None


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "—"
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            ZoneInfo("America/Sao_Paulo")
        )
        return timestamp.strftime("%d/%m/%Y %H:%M (Brasília)")
    except ValueError:
        return value


st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">COINGECKO → JSON</div>
      <h1>CryptoJSON Studio</h1>
      <p>Gere um catálogo limpo, atualizado e pronto para integrar às suas aplicações — sem editar código e com download imediato.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuração")
    currency = st.selectbox(
        "Moeda de referência",
        options=["brl", "usd", "eur"],
        format_func=lambda item: {"brl": "Real (BRL)", "usd": "Dólar (USD)", "eur": "Euro (EUR)"}[item],
    )
    pages = st.slider("Páginas da API", min_value=1, max_value=80, value=4)
    per_page = st.select_slider("Criptos por página", options=[50, 100, 150, 200, 250], value=250)
    request_delay = st.slider(
        "Intervalo entre páginas (s)", min_value=30.0, max_value=120.0, value=30.0, step=5.0
    )
    api_key = st.text_input(
        "Chave Demo da CoinGecko (opcional)",
        value=_secret("COINGECKO_API_KEY") or "",
        type="password",
        help="Pode reduzir erros de limite. A chave não é incluída no arquivo gerado.",
    )
    st.caption(f"Limite configurado: até {pages * per_page:,} ativos".replace(",", "."))
    generate = st.button("Gerar catálogo", type="primary", use_container_width=True, icon="🚀")

    st.divider()
    st.markdown("**Formato de saída**")
    st.caption("JSON UTF-8, identado, com metadados da geração e lista ordenada por capitalização de mercado.")

if "catalog" not in st.session_state:
    st.session_state.catalog = None

if generate:
    progress_bar = st.progress(0, text="Preparando a coleta…")
    status_box = st.empty()

    def update_progress(progress: FetchProgress) -> None:
        ratio = min(progress.page / pages, 1.0)
        progress_bar.progress(
            ratio,
            text=f"Página {progress.page}/{pages} · {progress.collected:,} criptomoedas coletadas".replace(",", "."),
        )
        status_box.caption(progress.message)

    client = CoinGeckoClient(api_key=api_key or None)
    try:
        coins = client.fetch_markets(
            currency=currency,
            pages=pages,
            per_page=per_page,
            delay_seconds=request_delay,
            progress_callback=update_progress,
        )
        catalog = build_catalog(coins, currency=currency)
        st.session_state.catalog = catalog
        st.session_state.catalog_bytes = catalog_to_json(catalog)
        progress_bar.progress(1.0, text="Catálogo concluído")
        status_box.empty()
        st.toast(f"{catalog['total']:,} criptomoedas prontas para download!".replace(",", "."), icon="✅")
    except CoinGeckoError as exc:
        progress_bar.empty()
        status_box.empty()
        st.error(str(exc), icon="⚠️")
    except (TypeError, ValueError):
        progress_bar.empty()
        status_box.empty()
        st.error("Não foi possível concluir a geração. Tente novamente em alguns instantes.", icon="⚠️")

catalog: dict[str, Any] | None = st.session_state.catalog

if catalog:
    total, updated, source, output_currency = st.columns(4)
    total.metric("Criptomoedas", f"{catalog['total']:,}".replace(",", "."))
    updated.metric("Atualizado em", _format_timestamp(catalog.get("last_updated_timestamp")))
    source.metric("Fonte", "CoinGecko")
    output_currency.metric("Moeda", str(catalog.get("vs_currency", "brl")).upper())

    st.subheader("Prévia do catálogo")
    search = st.text_input(
        "Pesquisar na prévia",
        placeholder="Digite Bitcoin, BTC ou o ID do ativo…",
        label_visibility="collapsed",
        icon="🔎",
    )
    rows = catalog["cryptos"]
    if search.strip():
        needle = search.casefold().strip()
        rows = [
            row
            for row in rows
            if needle in row["name"].casefold()
            or needle in row["symbol"].casefold()
            or needle in row["id"].casefold()
        ]

    table_rows = [
        {
            "Posição": row.get("market_cap_rank"),
            "Símbolo": row["symbol"],
            "Nome": row["name"],
            f"Preço ({catalog['vs_currency'].upper()})": row["current_price"],
            "Variação 24h (%)": row.get("price_change_percentage_24h"),
            "ID CoinGecko": row["id"],
        }
        for row in rows
    ]
    dataframe = pd.DataFrame(table_rows)
    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        height=min(560, 38 + max(len(dataframe), 1) * 35),
        column_config={
            f"Preço ({catalog['vs_currency'].upper()})": st.column_config.NumberColumn(format="%.8f"),
            "Variação 24h (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )
    st.caption(f"Exibindo {len(rows):,} de {catalog['total']:,} registros.".replace(",", "."))

    download_col, info_col = st.columns([1, 2])
    with download_col:
        st.download_button(
            "Baixar cryptos.json",
            data=st.session_state.catalog_bytes,
            file_name="cryptos.json",
            mime="application/json",
            type="primary",
            use_container_width=True,
            icon="⬇️",
        )
    with info_col:
        st.markdown(
            '<p class="hint">O download contém todos os registros coletados, mesmo quando a prévia está filtrada.</p>',
            unsafe_allow_html=True,
        )
else:
    st.info("Configure a coleta na barra lateral e clique em **Gerar catálogo**.", icon="💡")
    feature_a, feature_b, feature_c = st.columns(3)
    with feature_a:
        st.markdown("### ⚡ Atualizado\nPreços e dados de mercado obtidos diretamente da CoinGecko.")
    with feature_b:
        st.markdown("### 🧩 Compatível\nEstrutura estável, legível e pronta para Python, JavaScript ou bancos de dados.")
    with feature_c:
        st.markdown("### 📦 Portátil\nUm clique gera o arquivo para usar em qualquer outro projeto.")
