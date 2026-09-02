import test from "node:test";
import assert from "node:assert/strict";
import {
  ARTIFACT_PATH,
  PRODUCER_COMMAND,
  fetchArtifact,
  formatCellValue,
  identityLines,
  isGreenModelStatus,
  modelStatusMeta,
  normalizeArtifact,
  readingStatusMeta,
  rowsForModel,
  summarizeModel,
} from "../src/self-model-format.js";

function envelope(overrides = {}) {
  return {
    schema: "octopus.self-model.v2",
    generated_at: "2026-09-02T08:25:52Z",
    status: "unverifiable",
    data: {
      code_identity: { commit_sha: "ab12", branch: "lane/self-awareness" },
      sensors: [{
        sensor_id: "code_identity",
        implementation: "git rev-parse HEAD",
        status: "healthy",
        value: "ab12",
        source: "git:HEAD",
        observed_epoch: 1770000000,
        detail: null,
      }],
      processes: [{
        sensor_id: "process_organism",
        implementation: "tcp connect 127.0.0.1:8771",
        status: "healthy",
        value: true,
        source: "tcp:127.0.0.1:8771",
        observed_epoch: 1770000000,
        detail: "connected",
      }, {
        sensor_id: "process_center",
        implementation: "tcp connect 127.0.0.1:8776",
        status: "unknown",
        value: null,
        source: "tcp:127.0.0.1:8776",
        observed_epoch: 1770000000,
        detail: "probe timeout",
      }],
      capabilities: [{
        sensor_id: "capability_self_model",
        implementation: "ofn/kernel/self_model.py::build_model",
        status: "healthy",
        value: true,
        source: "ast:ofn/kernel/self_model.py",
        observed_epoch: null,
        detail: null,
      }],
      events: [{ sha: "x", subject: "s", source: "git:log" }],
      brain_probe: {
        status: "unknown",
        verdict: "unverifiable",
        source: null,
        observed_epoch: null,
        detail: "no dated run evidence",
      },
      unknowns: ["board processes invisible from this host"],
      counts: {
        sensors: 1, processes: 2, capabilities: 1, events: 1,
        healthy: 3, absent: 0, stale: 0, failed: 0, unknown: 1,
      },
    },
    sources: ["git:HEAD"],
    warnings: ["brain_probe_unknown"],
    stale_after: "2026-09-02T08:29:00Z",
    ...overrides,
  };
}

function fakeFetch(handlers) {
  const calls = [];
  const impl = async (path, options) => {
    calls.push({ path, options });
    for (const [match, handler] of handlers) {
      if (path === match) return handler();
    }
    return { ok: false, status: 500 };
  };
  impl.calls = calls;
  return impl;
}

test("normalizeArtifact accepts a real-shaped envelope and rejects everything else", () => {
  assert.equal(normalizeArtifact(envelope()).valid, true);
  for (const bad of [null, [], "text", 3, {}, { ...envelope(), schema: "other.v1" },
    { ...envelope(), status: null }, { ...envelope(), data: null }]) {
    const result = normalizeArtifact(bad);
    assert.equal(result.valid, false, String(JSON.stringify(bad)).slice(0, 40));
    assert.ok(typeof result.reason === "string");
  }
});

test("unknown and unverifiable are never green; only ok is green", () => {
  assert.equal(isGreenModelStatus("ok"), true);
  for (const status of ["unverifiable", "degraded", "unavailable", "unknown", null, undefined, "bogus"]) {
    assert.equal(isGreenModelStatus(status), false, String(status));
    assert.notEqual(modelStatusMeta(status).tone, "ok", String(status));
  }
  assert.equal(modelStatusMeta("unverifiable").tone, "warn");
  assert.equal(modelStatusMeta("unavailable").tone, "bad");
  assert.notEqual(readingStatusMeta("unknown").tone, "ok");
  assert.notEqual(readingStatusMeta("absent").tone, "ok");
});

test("absent or unknown values never render as zero", () => {
  assert.equal(formatCellValue(null), "—");
  assert.equal(formatCellValue(undefined), "—");
  assert.notEqual(formatCellValue(null), "0");
  assert.equal(formatCellValue(0), "0");
  assert.equal(formatCellValue(false), "خیر (اندازه‌گیری‌شده)");
  assert.notEqual(formatCellValue(false), "0");
});

test("rowsForModel flattens groups deterministically and adds the probe row", () => {
  const rowsA = rowsForModel(envelope().data);
  const rowsB = rowsForModel(envelope().data);
  assert.deepEqual(rowsA, rowsB);
  assert.equal(rowsA.length, 5); // 1 sensor + 2 processes + 1 capability + probe
  assert.equal(rowsA[0].id, "code_identity");
  assert.equal(rowsA.at(-1).kind, "brain_probe");
  assert.equal(rowsA.at(-1).value, "unverifiable");
  for (const row of rowsA) {
    assert.ok(["sensors", "processes", "capabilities", "brain_probe"].includes(row.kind));
    assert.ok(["healthy", "stale", "absent", "failed", "unknown"].includes(row.status));
  }
});

test("summarizeModel and identityLines pass through only what exists", () => {
  const summary = summarizeModel(envelope().data);
  assert.equal(summary.unknown, 1);
  assert.equal(summary.healthy, 3);
  assert.deepEqual(identityLines(envelope().data), {
    commit: "ab12", branch: "lane/self-awareness",
  });
  assert.equal(identityLines({}).commit, null);
});

test("fetchArtifact: 404 => absent, broken json => malformed, throw => error, valid => ready", async () => {
  const json = (body, status = 200) => () => ({
    ok: status >= 200 && status < 300, status,
    json: async () => body,
  });
  const fetch404 = fakeFetch([[ARTIFACT_PATH, json({}, 404)]]);
  assert.equal((await fetchArtifact(fetch404)).state, "absent");

  const fetchBroken = fakeFetch([[ARTIFACT_PATH, () => ({
    ok: true, status: 200, json: async () => { throw new Error("bad"); },
  })]]);
  assert.equal((await fetchArtifact(fetchBroken)).state, "malformed");

  const fetchWrongShape = fakeFetch([[ARTIFACT_PATH, json({ nope: true })]]);
  assert.equal((await fetchArtifact(fetchWrongShape)).state, "malformed");

  const fetchThrowing = fakeFetch([[ARTIFACT_PATH, () => { throw new Error("offline"); }]]);
  assert.equal((await fetchArtifact(fetchThrowing)).state, "error");

  const fetchOk = fakeFetch([[ARTIFACT_PATH, json(envelope())]]);
  const ready = await fetchArtifact(fetchOk);
  assert.equal(ready.state, "ready");
  assert.equal(ready.envelope.schema, "octopus.self-model.v2");
  // cache-busting is part of the honesty contract: never a stale cache copy
  assert.equal(fetchOk.calls[0].options.cache, "no-store");
});

test("producer command is pinned for the absent-artifact panel", () => {
  assert.ok(PRODUCER_COMMAND.includes("self_model_producer"));
  assert.ok(PRODUCER_COMMAND.includes("web/cockpit-v2/data/self-model.json"));
});
