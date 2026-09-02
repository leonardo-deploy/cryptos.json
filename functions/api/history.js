const MIN_RETRY_AFTER_SECONDS = 60;
const MAX_HISTORY_AGE_DAYS = 365;
const RESPONSE_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
};

const json = (data, status = 200, extraHeaders = {}) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { ...RESPONSE_HEADERS, ...extraHeaders },
  });

function retryAfterSeconds(response) {
  const value = Number(response.headers.get("Retry-After"));
  return Number.isFinite(value) && value >= 0
    ? Math.max(MIN_RETRY_AFTER_SECONDS, Math.ceil(value))
    : MIN_RETRY_AFTER_SECONDS;
}

function parseAllowedDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return null;
  const selected = new Date(value + "T00:00:00Z");
  if (Number.isNaN(selected.getTime())) return null;
  const today = new Date();
  const todayUtc = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const ageDays = Math.floor((todayUtc - selected.getTime()) / 86400000);
  if (ageDays < 1 || ageDays > MAX_HISTORY_AGE_DAYS) return null;
  return {
    iso: value,
    coingecko: value.split("-").reverse().join("-"),
  };
}

function upstreamErrorMessage(status) {
  if (status === 401) return "A chave Demo da CoinGecko não foi aceita.";
  if (status === 429) return "Limite de requisições da CoinGecko atingido.";
  if (status === 404) return "Não há dados históricos para este ativo na data selecionada.";
  if (status >= 500) return "A CoinGecko está temporariamente indisponível.";
  return "A CoinGecko recusou a consulta histórica.";
}

export async function onRequestGet(context) {
  try {
    const url = new URL(context.request.url);
    const id = (url.searchParams.get("id") || "").trim();
    const currency = (url.searchParams.get("currency") || "brl").toLowerCase();
    const date = parseAllowedDate(url.searchParams.get("date"));

    if (!/^[a-z0-9._-]{1,200}$/i.test(id)) return json({ error: "Criptomoeda inválida." }, 400);
    if (!["brl", "usd", "eur"].includes(currency)) return json({ error: "Moeda inválida." }, 400);
    if (!date) return json({ error: "A data deve ser um dia concluído dentro dos últimos 365 dias." }, 400);

    const secretKey = typeof context.env?.COINGECKO_API_KEY === "string"
      ? context.env.COINGECKO_API_KEY.trim()
      : "";
    if (!secretKey) return json({ error: "A chave Demo da CoinGecko não está configurada." }, 503);

    const endpoint = new URL(`https://api.coingecko.com/api/v3/coins/${encodeURIComponent(id)}/history`);
    endpoint.searchParams.set("date", date.coingecko);
    endpoint.searchParams.set("localization", "false");

    const response = await fetch(endpoint, {
      headers: {
        accept: "application/json",
        "user-agent": "CryptoJSON-Studio/1.0",
        "x-cg-demo-api-key": secretKey,
      },
    });

    if (!response.ok) {
      const payload = { error: upstreamErrorMessage(response.status), upstream_status: response.status };
      const headers = {};
      if (response.status === 429) {
        payload.retry_after_seconds = retryAfterSeconds(response);
        headers["Retry-After"] = String(payload.retry_after_seconds);
      }
      return json(payload, response.status, headers);
    }

    const payload = await response.json();
    const marketData = payload?.market_data;
    const price = marketData?.current_price?.[currency];
    if (typeof price !== "number") {
      return json({ error: "Sem preço histórico nesta moeda para a data selecionada." }, 404);
    }

    return json({
      id,
      symbol: String(payload.symbol || "").toUpperCase(),
      name: payload.name || id,
      image: payload.image?.small || payload.image?.thumb || null,
      current_price: price,
      market_cap: marketData?.market_cap?.[currency] ?? null,
      total_volume: marketData?.total_volume?.[currency] ?? null,
      historical_date: date.iso,
    });
  } catch (error) {
    console.error(JSON.stringify({
      event: "coingecko_history_proxy_error",
      message: error instanceof Error ? error.message : String(error),
    }));
    return json({ error: "Falha temporária ao consultar o histórico." }, 502);
  }
}

export function onRequestOptions() {
  return new Response(null, { status: 204, headers: { allow: "GET, OPTIONS" } });
}
