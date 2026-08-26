# Deploy no Cloudflare Pages

Esta versão substitui a interface Streamlit por HTML/CSS/JavaScript e usa uma Pages Function em `/api/markets` como proxy para a CoinGecko.

## Configuração recomendada

1. No Cloudflare, crie um projeto em **Workers & Pages > Pages > Connect to Git**.
2. Selecione este repositório e a branch desejada.
3. Framework preset: **None**.
4. Build command: `exit 0`.
5. Build output directory: `.`.
6. Faça o deploy.

A pasta `functions/` deve permanecer na raiz do projeto. O arquivo `_routes.json` restringe as invocações de Functions a `/api/*`, mantendo os arquivos estáticos fora da Function.

## Chave CoinGecko opcional

O usuário pode informar uma chave Demo apenas durante a sessão no navegador. Para configurar uma chave padrão no servidor, crie no Cloudflare Pages uma variável secreta chamada `COINGECKO_API_KEY` e faça novo deploy. Nunca salve a chave no repositório.

## Desenvolvimento local

Use Wrangler para servir os arquivos estáticos e Pages Functions juntos:

```bash
npx wrangler pages dev .
```

## Arquitetura

- `index.html`: interface.
- `styles.css`: tema Crypto Midnight.
- `app.js`: coleta paginada, pesquisa, prévia e download.
- `functions/api/markets.js`: proxy edge para CoinGecko.
- `_routes.json`: executa Functions apenas em `/api/*`.

A coleta é paginada pelo navegador. Isso evita manter uma única execução server-side aberta durante os intervalos configurados entre páginas.