import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../functions/api/history.js", import.meta.url), "utf8");
const moduleUrl = "data:text/javascript;base64," + Buffer.from(source).toString("base64");
const { onRequestGet } = await import(moduleUrl);

function isoDaysAgo(days) {
  const date = new Date(Date.now() - days * 86400000);
  return date.toISOString().slice(0, 10);
}

function context(search) {
  return {
    request: new Request("https://example.com/api/history" + search),
    env: { COINGECKO_API_KEY: "demo-test-key" },
  };
}

test("rejects historical dates older than 365 days", async () => {
  let calls = 0;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response("{}");
  };
  try {
    const response = await onRequestGet(
      context("?id=bitcoin&currency=brl&date=" + isoDaysAgo(366)),
    );
    assert.equal(response.status, 400);
    assert.equal(calls, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("returns the price for the selected completed day", async () => {
  const originalFetch = globalThis.fetch;
  let upstreamUrl;
  globalThis.fetch = async (url) => {
    upstreamUrl = new URL(url);
    return new Response(JSON.stringify({
      id: "bitcoin",
      symbol: "btc",
      name: "Bitcoin",
      image: { small: "https://example.com/btc.png" },
      market_data: {
        current_price: { brl: 350000 },
        market_cap: { brl: 7000000000000 },
        total_volume: { brl: 100000000000 },
      },
    }));
  };
  try {
    const date = isoDaysAgo(1);
    const response = await onRequestGet(
      context("?id=bitcoin&currency=brl&date=" + date),
    );
    const payload = await response.json();
    assert.equal(response.status, 200);
    assert.equal(payload.current_price, 350000);
    assert.equal(payload.historical_date, date);
    assert.equal(upstreamUrl.searchParams.get("date"), date.split("-").reverse().join("-"));
  } finally {
    globalThis.fetch = originalFetch;
  }
});
