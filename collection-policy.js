(function exposeCollectionPolicy(root, factory) {
  const policy = factory();

  if (typeof module === "object" && module.exports) {
    module.exports = policy;
  }

  root.CollectionPolicy = policy;
})(typeof globalThis !== "undefined" ? globalThis : this, function createCollectionPolicy() {
  "use strict";

  const MIN_PAGE_DELAY_SECONDS = 30;
  const BLOCK_DELAY_SECONDS = 60;
  const PAGES_PER_BLOCK = 4;
  const MAX_ATTEMPTS = 4;

  function normalizePageDelaySeconds(value) {
    const seconds = Number(value);
    if (!Number.isFinite(seconds)) {
      return MIN_PAGE_DELAY_SECONDS;
    }
    return Math.max(MIN_PAGE_DELAY_SECONDS, Math.ceil(seconds));
  }

  function getWaitAfterPageSeconds(page, configuredDelaySeconds) {
    const pageNumber = Number(page);
    if (!Number.isInteger(pageNumber) || pageNumber < 1) {
      throw new RangeError("A página deve ser um número inteiro positivo.");
    }

    const pageDelay = normalizePageDelaySeconds(configuredDelaySeconds);
    if (pageNumber % PAGES_PER_BLOCK === 0) {
      return Math.max(BLOCK_DELAY_SECONDS, pageDelay);
    }
    return pageDelay;
  }

  function getRetryDelaySeconds(retryAfterSeconds) {
    const seconds = Number(retryAfterSeconds);
    if (!Number.isFinite(seconds) || seconds < 0) {
      return BLOCK_DELAY_SECONDS;
    }
    return Math.max(BLOCK_DELAY_SECONDS, Math.ceil(seconds));
  }

  return Object.freeze({
    MIN_PAGE_DELAY_SECONDS,
    BLOCK_DELAY_SECONDS,
    PAGES_PER_BLOCK,
    MAX_ATTEMPTS,
    normalizePageDelaySeconds,
    getWaitAfterPageSeconds,
    getRetryDelaySeconds,
  });
});
