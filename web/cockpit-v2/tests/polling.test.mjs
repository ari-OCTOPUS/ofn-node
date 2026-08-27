import test from "node:test";
import assert from "node:assert/strict";
import {
  HIDDEN_INTERVAL_MS,
  MAX_BACKOFF_MS,
  VISIBLE_INTERVAL_MS,
  computeBackoffDelay,
  createApiClient,
  createPollController,
} from "../src/api.js";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function fakeClock() {
  let sequence = 0;
  const jobs = new Map();
  return {
    setTimeout(fn, delay) {
      const id = ++sequence;
      jobs.set(id, { fn, delay });
      return id;
    },
    clearTimeout(id) {
      jobs.delete(id);
    },
    delays() {
      return [...jobs.values()].map((job) => job.delay);
    },
    runDelay(delay) {
      const match = [...jobs].find(([, job]) => job.delay === delay);
      assert.ok(match, `missing scheduled delay ${delay}`);
      const [id, job] = match;
      jobs.delete(id);
      job.fn();
    },
    count() {
      return jobs.size;
    },
  };
}

async function settle() {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}

test("polling uses 15s visible and 60s hidden intervals", async () => {
  const clock = fakeClock();
  let hidden = false;
  const controller = createPollController({
    request: async () => ({ data: { generated_at: "source-time" }, etag: '"a"' }),
    isHidden: () => hidden,
    setTimeoutImpl: clock.setTimeout,
    clearTimeoutImpl: clock.clearTimeout,
    timeoutMs: 999,
  });

  controller.start({ immediate: true });
  await settle();
  assert.ok(clock.delays().includes(VISIBLE_INTERVAL_MS));

  hidden = true;
  controller.visibilityChanged();
  assert.ok(clock.delays().includes(HIDDEN_INTERVAL_MS));
  controller.teardown();
});

test("one resource never overlaps an inflight request", async () => {
  const pending = deferred();
  let calls = 0;
  const controller = createPollController({
    request: () => { calls += 1; return pending.promise; },
    timeoutMs: 60_000,
  });
  controller.start({ immediate: true });
  await settle();
  const second = await controller.refresh();
  assert.equal(calls, 1);
  assert.deepEqual(second, { skipped: "inflight" });
  pending.resolve({ data: {} });
  await settle();
  controller.teardown();
});

test("teardown aborts inflight work", async () => {
  let signal;
  const pending = deferred();
  const controller = createPollController({
    request: ({ signal: supplied }) => { signal = supplied; return pending.promise; },
    timeoutMs: 60_000,
  });
  controller.start({ immediate: true });
  await settle();
  assert.equal(signal.aborted, false);
  controller.teardown();
  assert.equal(signal.aborted, true);
  pending.resolve({ data: { late: true } });
  await settle();
});

test("backoff is exponential and capped", () => {
  assert.equal(computeBackoffDelay(0, VISIBLE_INTERVAL_MS), VISIBLE_INTERVAL_MS);
  assert.equal(computeBackoffDelay(1, VISIBLE_INTERVAL_MS), 30_000);
  assert.equal(computeBackoffDelay(2, VISIBLE_INTERVAL_MS), 60_000);
  assert.equal(computeBackoffDelay(99, VISIBLE_INTERVAL_MS), MAX_BACKOFF_MS);
});

test("304 is accepted without parsing JSON and preserves body", async () => {
  let jsonCalls = 0;
  let receivedIfNoneMatch = null;
  const fetchImpl = async (_path, options) => {
    receivedIfNoneMatch = options.headers["If-None-Match"];
    return {
      status: 304,
      ok: false,
      headers: { get: (name) => name.toLowerCase() === "etag" ? '"v2"' : null },
      json: async () => { jsonCalls += 1; throw new Error("must not parse 304"); },
    };
  };
  const api = createApiClient({ fetchImpl, getSession: () => "memory-token" });
  const result = await api.get("/api/v2/owner/status", { etag: '"v1"' });
  assert.equal(receivedIfNoneMatch, '"v1"');
  assert.equal(jsonCalls, 0);
  assert.deepEqual(result, { notModified: true, data: null, etag: '"v2"' });
});

test("generation guard prevents a late response from overwriting state", async () => {
  const pending = deferred();
  const updates = [];
  const controller = createPollController({
    request: () => pending.promise,
    onUpdate: (update) => updates.push(update),
    timeoutMs: 60_000,
  });
  controller.start({ immediate: true });
  await settle();
  controller.visibilityChanged();
  pending.resolve({ data: { value: "late" } });
  await settle();
  assert.equal(updates.some((update) => update.data?.value === "late"), false);
  controller.teardown();
});

test("source generated-at and client last-success remain separate", async () => {
  const updates = [];
  const controller = createPollController({
    request: async () => ({ data: { generated_at: "2026-08-27T00:00:00Z" } }),
    onUpdate: (update) => updates.push(update),
    now: () => 123456,
  });
  controller.start({ immediate: true });
  await settle();
  const success = updates.findLast((update) => update.status === "success");
  assert.equal(success.generatedAt, "2026-08-27T00:00:00Z");
  assert.equal(success.lastSuccessAt, 123456);
  controller.teardown();
});

test("401 stops polling permanently and invokes expiry callback", async () => {
  let expired = 0;
  const controller = createPollController({
    request: async () => { const error = new Error("expired"); error.status = 401; throw error; },
    onAuthExpired: () => { expired += 1; },
  });
  controller.start({ immediate: true });
  await settle();
  assert.equal(expired, 1);
  assert.equal(controller.snapshot().stoppedForAuth, true);
  assert.deepEqual(await controller.refresh(), { skipped: "stopped" });
});
