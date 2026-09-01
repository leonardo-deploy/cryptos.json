const HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "public, max-age=86400",
  "x-content-type-options": "nosniff",
};

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: HEADERS });

function validDate(value) {
  if (!/^\d{2}-\d{2}-\d{4}$/.test(value || "")) return false;
  const [day, month, year] = value.split("-").map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  return parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month - 1 && parsed.getUTCDate() === day;
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const id = url.searchParams.get("id") || "";
  const date = url.searchParams.get("date") || "";
  const currency = (url.searchParams.get("currency") || "brl").toLowerCase();
  if (!/^[a-z0-9._-]{1,128}$/i.test(id)) return json({ error: "ID inválido." }, 400);
  if (!validDate(date)) return json({ error: "Data inválida." }, 400);
  if (!["brl", "usd", "eur"].includes(currency)) return json({ error: "Moeda inválida." }, 400);

  const key = typeof context.env?.COINGECKO_API_KEY === "string"
    ? context.env.COINGECKO_API_KEY.trim()
    : "";
  if (!key) return json({ error: "A chave Demo da CoinGecko não está configurada." }, 503);

  const endpoint = new URL(`https://api.coingecko.com/api/v3/coins/${encodeURIComponent(id)}/history`);
  endpoint.searchParams.set("date", date);
  endpoint.searchParams.set("localization", "false");
  const response = await fetch(endpoint, {
    headers: { accept: "application/json", "x-cg-demo-api-key": key },
  });
  if (!response.ok) {
    return json({ error: "Não foi possível obter o preço histórico.", upstream_status: response.status }, response.status);
  }
  const payload = await response.json();
  return json({
    price: payload?.market_data?.current_price?.[currency] ?? null,
    market_cap: payload?.market_data?.market_cap?.[currency] ?? null,
  });
}

export function onRequestOptions() {
  return new Response(null, { status: 204, headers: { allow: "GET, OPTIONS" } });
}
