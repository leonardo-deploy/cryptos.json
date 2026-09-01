import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../functions/api/history.js", import.meta.url), "utf8");
const { onRequestGet } = await import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));

function context(search, key = "demo-key") {
  return {
    request: new Request("https://example.com/api/history" + search),
    env: { COINGECKO_API_KEY: key },
  };
}

test("validates historical snapshot parameters", async () => {
  assert.equal((await onRequestGet(context("?id=bitcoin&date=31-02-2025"))).status, 400);
  assert.equal((await onRequestGet(context("?id=bitcoin&date=31-01-2025&currency=x"))).status, 400);
});

test("returns the selected currency price and market cap", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.match(String(url), /coins\/bitcoin\/history/);
    assert.match(String(url), /date=31-01-2025/);
    return new Response(JSON.stringify({
      market_data: {
        current_price: { brl: 600000 },
        market_cap: { brl: 12000000000000 },
      },
    }));
  };
  try {
    const response = await onRequestGet(context("?id=bitcoin&date=31-01-2025&currency=brl"));
    assert.deepEqual(await response.json(), { price: 600000, market_cap: 12000000000000 });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
