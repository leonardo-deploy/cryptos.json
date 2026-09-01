<div align="center">

# 🪙 CryptoJSON Studio

### Um gerador elegante de catálogos de criptomoedas, pronto para rodar no Streamlit.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-ready-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![CoinGecko](https://img.shields.io/badge/data-CoinGecko-8DC63F)](https://www.coingecko.com/)
[![Qualidade](https://github.com/leonardo-deploy/cryptos.json/actions/workflows/ci.yml/badge.svg)](https://github.com/leonardo-deploy/cryptos.json/actions/workflows/ci.yml)

Transforme dados de mercado da CoinGecko em um arquivo `cryptos.json` limpo, pesquisável e disponível para download — diretamente pelo navegador.

</div>

---

## ✨ O que o projeto oferece

- Interface moderna e responsiva construída com Streamlit.
- Catálogo atual com até 10.000 ativos por execução: no máximo 40 páginas, sempre com 250 criptos por página.
- Catálogo mensal dos últimos 365 dias, usando o preço do último dia do mês escolhido para até 250 ativos.
- Escolha entre BRL, USD e EUR como moeda de referência.
- Progresso da coleta em tempo real e mensagens de erro amigáveis.
- Contadores ao vivo de páginas, criptos consultadas e segundos restantes entre páginas e blocos.
- Cinco tentativas por página, pausa especial para HTTP 429 e continuidade após falhas persistentes.
- Coleta em blocos de quatro páginas, com pausa adicional de 60 segundos entre blocos.
- Pesquisa e prévia tabular antes do download.
- JSON UTF-8, versionado e ordenado por capitalização de mercado.
- Ranking sequencial de fallback para ativos sem posição informada pela CoinGecko.
- Compatibilidade com o campo legado `current_price_brl` quando a moeda é BRL.
- Modo CLI para automações e rotinas locais.
- Núcleo modular, testes automatizados e configuração pronta para deploy.
- Integração contínua no GitHub Actions para testes e lint em cada pull request.

## 🖥️ Como funciona

1. Selecione a moeda e escolha entre **Momento atual** e **Fechamento mensal**.
2. No modo mensal, selecione um dos meses disponíveis dentro dos últimos 365 dias.
3. Clique em **Gerar catálogo** e acompanhe o progresso.
4. Pesquise e confira os resultados na prévia.
5. Baixe `cryptos.json` no modo atual ou um arquivo como `janeiro2025.json` no modo mensal.

```mermaid
flowchart LR
    A[Interface Streamlit] --> B[Cliente CoinGecko]
    B --> C[Normalização e deduplicação]
    C --> D[Prévia pesquisável]
    C --> E[Download cryptos.json]
```

## 📦 Estrutura do JSON

```json
{
  "schema_version": 1,
  "last_updated_timestamp": "2026-08-24T09:00:00-03:00",
  "source": "CoinGecko",
  "vs_currency": "brl",
  "total": 1,
  "cryptos": [
    {
      "id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "display_name": "BTC - Bitcoin",
      "image": "https://...",
      "current_price": 350000,
      "current_price_brl": 350000,
      "market_cap_rank": 1,
      "market_cap": 6900000000000,
      "total_volume": 180000000000,
      "price_change_percentage_24h": 1.25
    }
  ]
}
```

> Os valores acima são apenas ilustrativos. O arquivo baixado contém os dados disponíveis no momento da geração.

## 🚀 Executar localmente

Requisitos: Python 3.11 ou superior e Git.

```bash
git clone https://github.com/leonardo-deploy/cryptos.json.git
cd cryptos.json
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Instale e inicie:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá em `http://localhost:8501`.

## ☁️ Deploy no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io/).
2. Entre com a conta que possui acesso ao repositório.
3. Clique em **Create app**.
4. Escolha este repositório e a branch `main`.
5. Em **Main file path**, informe `app.py`.
6. Clique em **Deploy**.

O Streamlit instalará automaticamente as dependências de `requirements.txt`.

### Chave CoinGecko opcional

O app funciona sem chave, mas a chave Demo pode oferecer limites mais previsíveis. No Streamlit Cloud, abra **App settings → Secrets** e adicione:

```toml
COINGECKO_API_KEY = "sua-chave-demo"
```

Também é possível usar a variável de ambiente `COINGECKO_API_KEY` localmente. A chave nunca é gravada no JSON.

## ⌨️ Gerar pelo terminal

```bash
python gerar_cryptos_json.py --currency brl --output cryptos.json
```

Parâmetros disponíveis:

| Parâmetro | Padrão | Descrição |
|---|---:|---|
| `--currency` | `brl` | Moeda: `brl`, `usd` ou `eur` |
| `--delay` | `30.0` | Intervalo em segundos entre páginas (mínimo de 30) |
| `--block-delay` | `60.0` | Pausa adicional entre blocos de quatro páginas (mínimo de 60) |
| `--output` | `cryptos.json` | Caminho do arquivo de saída |

## 🧪 Qualidade do código

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
```

## 🗂️ Organização

```text
.
├── .streamlit/config.toml    # Tema e configuração do servidor
├── app.py                    # Interface web
├── gerar_cryptos_json.py     # Interface de linha de comando
├── src/
│   ├── coingecko.py          # Cliente HTTP resiliente
│   └── exporter.py           # Normalização e serialização
├── tests/                    # Testes automatizados
└── requirements.txt          # Dependências de produção
```

## 🔌 Uso em outra aplicação

Depois do download, hospede o arquivo junto à sua aplicação ou carregue-o diretamente:

```python
import json

with open("cryptos.json", encoding="utf-8") as file:
    catalog = json.load(file)

bitcoin = next(coin for coin in catalog["cryptos"] if coin["id"] == "bitcoin")
print(bitcoin["display_name"])
```

## ℹ️ Fonte e limites

Os dados são fornecidos pela [CoinGecko API](https://docs.coingecko.com/reference/coins-markets). A disponibilidade e a frequência permitida dependem do plano e dos limites vigentes da API. O projeto implementa timeout, retentativas e intervalos automáticos. A coleta atual tem limite rígido de 40 páginas com 250 ativos por página. O histórico da chave Demo cobre somente os últimos 365 dias e é consultado individualmente por ativo; por isso, o modo mensal é limitado a 250 ativos e pode levar mais tempo.

---

<div align="center">
  Feito para transformar dados cripto em integrações simples, confiáveis e reutilizáveis.
</div>
