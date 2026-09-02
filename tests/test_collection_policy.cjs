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

test("boots the browser application with the shared collection policy", () => {
  const listeners = {};
  const elements = new Proxy(
    {
      limit: { textContent: "40 páginas × 250 criptos — até 10.000 ativos" },
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

  assert.match(elements.limit.textContent, /10\.000 ativos/);
  assert.equal(typeof listeners["generate:click"], "function");
});
