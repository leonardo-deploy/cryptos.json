"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const policy = require("../collection-policy.js");

test("enforces at least 30 seconds between regular pages", () => {
  assert.equal(policy.normalizePageDelaySeconds(0), 30);
  assert.equal(policy.normalizePageDelaySeconds(29), 30);
  assert.equal(policy.normalizePageDelaySeconds(30), 30);
  assert.equal(policy.normalizePageDelaySeconds(45), 45);
});

test("waits 60 seconds after every block of four pages", () => {
  const waits = Array.from({ length: 8 }, (_, index) =>
    policy.getWaitAfterPageSeconds(index + 1, 30),
  );

  assert.deepEqual(waits, [30, 30, 30, 60, 30, 30, 30, 60]);
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

test("boots the browser application with the shared collection policy", () => {
  const listeners = {};
  const monthOptions = [];
  const elements = new Proxy(
    {
      snapshotMonth: { appendChild: (option) => monthOptions.push(option) },
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
        element.appendChild ||= () => {};
        return element;
      },
    },
  );
  const appSource = fs.readFileSync(require.resolve("../app.js"), "utf8");

  vm.runInNewContext(appSource, {
    CollectionPolicy: policy,
    document: {
      createElement: () => ({}),
      getElementById: (id) => elements[id],
      querySelector: () => ({ value: "current" }),
      querySelectorAll: () => [],
    },
    Intl,
    URL,
    Blob,
    location: { origin: "https://example.com" },
    setTimeout,
  });

  assert.match(appSource, /PAGES=40,PER_PAGE=250/);
  assert.match(appSource, /START_YEAR=2020/);
  assert.ok(monthOptions.some((option) => option.value === "2020-01"));
  assert.match(appSource, /atualcryptos\.json/);
  assert.match(appSource, /cryptos\.json/);
  assert.doesNotMatch(appSource, /\$\('pages'\)/);
  assert.doesNotMatch(appSource, /\$\('perPage'\)/);
  assert.equal(typeof listeners["generate:click"], "function");
});
