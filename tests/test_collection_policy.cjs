"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const policy = require("../collection-policy.js");

test("enforces at least 5 seconds between regular pages", () => {
  assert.equal(policy.normalizePageDelaySeconds(0), 5);
  assert.equal(policy.normalizePageDelaySeconds(4), 5);
  assert.equal(policy.normalizePageDelaySeconds(5), 5);
  assert.equal(policy.normalizePageDelaySeconds(45), 45);
});

test("waits 15 seconds after every block of four pages", () => {
  const waits = Array.from({ length: 8 }, (_, index) =>
    policy.getWaitAfterPageSeconds(index + 1, 5),
  );

  assert.deepEqual(waits, [5, 5, 5, 15, 5, 5, 5, 15]);
});

test("preserves a configured page delay longer than the block delay", () => {
  assert.equal(policy.getWaitAfterPageSeconds(1, 90), 90);
  assert.equal(policy.getWaitAfterPageSeconds(4, 90), 90);
});

test("honors Retry-After without retrying sooner than 60 seconds", () => {
  assert.equal(policy.getRetryDelaySeconds(undefined), 60);
  assert.equal(policy.getRetryDelaySeconds(15), 60);
  assert.equal(policy.getRetryDelaySeconds(75), 75);
});

test("keeps only assets with at least R$ 1 million in market cap", () => {
  const rows = [
    { id: "above", market_cap: 1_500_000 },
    { id: "exact", market_cap: 1_000_000 },
    { id: "below", market_cap: 999_999 },
    { id: "missing", market_cap: null },
  ];

  assert.equal(policy.MIN_MARKET_CAP_BRL, 1_000_000);
  assert.deepEqual(
    policy.filterByMinimumMarketCap(rows).map((row) => row.id),
    ["above", "exact"],
  );
});

test("detects when a market-cap ordered page crosses the floor", () => {
  assert.equal(
    policy.hasReachedMarketCapFloor([
      { market_cap: 1_500_000 },
      { market_cap: 999_999 },
    ]),
    true,
  );
  assert.equal(
    policy.hasReachedMarketCapFloor([
      { market_cap: 1_500_000 },
      { market_cap: 1_000_000 },
      { market_cap: null },
    ]),
    false,
  );
});

test("boots the browser application with the shared collection policy", () => {
  const listeners = {};
  const elements = new Proxy(
    {
      limit: { textContent: "Market cap mínimo — R$ 1.000.000" },
      delay: { value: "0" },
    },
    {
      get(target, id) {
        if (!target[id]) {
          target[id] = {};
        }
        const element = target[id];
        element.classList ||= { toggle() {}, add() {} };
        element.addEventListener ||= (event, callback) => {
          listeners[id + ":" + event] = callback;
        };
        return element;
      },
    },
  );
  const appSource = fs.readFileSync(require.resolve("../app.js"), "utf8");

  vm.runInNewContext(appSource, {
    CollectionPolicy: policy,
    document: { getElementById: (id) => elements[id] },
    Intl,
    URL,
    Blob,
    location: { origin: "https://example.com" },
    setTimeout,
  });

  assert.match(elements.limit.textContent, /R\$ 1\.000\.000/);
  assert.equal(typeof listeners["generate:click"], "function");
});

test("browser collection filters the crossing page and stops immediately", async () => {
  const listeners = {};
  const elements = new Proxy(
    {
      currency: { value: "brl" },
      limit: { textContent: "Market cap mínimo — R$ 1.000.000" },
    },
    {
      get(target, id) {
        if (!target[id]) target[id] = {};
        const element = target[id];
        element.classList ||= { toggle() {}, add() {} };
        element.style ||= {};
        element.addEventListener ||= (event, callback) => {
          listeners[id + ":" + event] = callback;
        };
        return element;
      },
    },
  );
  const appSource = fs.readFileSync(require.resolve("../app.js"), "utf8");
  let fetchCalls = 0;

  vm.runInNewContext(appSource, {
    CollectionPolicy: policy,
    document: { getElementById: (id) => elements[id] },
    fetch: async () => {
      fetchCalls += 1;
      return new Response(JSON.stringify([
        { id: "above", symbol: "up", name: "Above", current_price: 10, market_cap: 1_500_000 },
        { id: "exact", symbol: "eq", name: "Exact", current_price: 5, market_cap: 1_000_000 },
        { id: "below", symbol: "down", name: "Below", current_price: 1, market_cap: 999_999 },
      ]));
    },
    Response,
    AbortController,
    Intl,
    URL,
    Blob,
    location: { origin: "https://example.com" },
    requestAnimationFrame: (callback) => callback(),
    setTimeout,
    clearTimeout,
  });

  await listeners["generate:click"]();

  assert.equal(fetchCalls, 1);
  assert.equal(elements.totalMetric.textContent, "2");
  assert.equal(elements.progressPct.textContent, "100%");
  assert.match(elements.progressMessage.textContent, /R\$ 1\.000\.000/);
  assert.match(elements.tbody.innerHTML, /Above/);
  assert.match(elements.tbody.innerHTML, /Exact/);
  assert.doesNotMatch(elements.tbody.innerHTML, /Below/);
});
