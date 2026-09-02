// Pure formatting/classification for the self-model viewer page.
//
// No DOM, no fetch — every function here is deterministic and covered by
// node tests. The honesty rules of the backend apply verbatim on this
// surface: absent is never zero, unknown is never green, and a payload
// that cannot be understood is shown as broken, never guessed.

export const ARTIFACT_PATH = "/cockpit-v2/data/self-model.json";

export const PRODUCER_COMMAND =
  "python -X utf8 -m ofn.adapters.self_model_producer --repo . --output web/cockpit-v2/data/self-model.json";

const STATUS_META = Object.freeze({
  healthy: { label: "سالم", tone: "ok" },
  stale: { label: "کهنه", tone: "warn" },
  absent: { label: "غایب (اندازه‌گیری‌شده)", tone: "warn" },
  failed: { label: "خراب", tone: "bad" },
  unknown: { label: "نامعلوم", tone: "bad" },
});

const MODEL_STATUS_META = Object.freeze({
  ok: { label: "سالم", tone: "ok" },
  degraded: { label: "مختل", tone: "warn" },
  unverifiable: { label: "قابل‌راستی‌آزمایی-نیست", tone: "warn" },
  unavailable: { label: "در دسترس نیست", tone: "bad" },
});

// A green model status is exactly "ok" — nothing else may ever render green.
export function modelStatusMeta(status) {
  return MODEL_STATUS_META[String(status)] ?? { label: String(status ?? "نامعلوم"), tone: "bad" };
}

export function readingStatusMeta(status) {
  return STATUS_META[String(status)] ?? { label: String(status ?? "نامعلوم"), tone: "bad" };
}

export function isGreenModelStatus(status) {
  return String(status) === "ok";
}

// Validate the fetched payload as a self-model envelope. Anything that is
// not a well-formed envelope is "malformed" — fail closed, no partial
// rendering of guessed fields.
export function normalizeArtifact(payload) {
  if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
    return { valid: false, reason: "not-an-object" };
  }
  const schema = payload.schema;
  const data = payload.data;
  const status = payload.status;
  if (typeof schema !== "string" || !schema.startsWith("octopus.self-model.")) {
    return { valid: false, reason: "schema-mismatch" };
  }
  if (typeof status !== "string") {
    return { valid: false, reason: "status-missing" };
  }
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    return { valid: false, reason: "data-missing" };
  }
  return { valid: true, envelope: payload };
}

// One flat row per reading — value formatting keeps the backend contract:
// null means "not measured" and renders as an em-dash, never as 0; false is
// a measured negative and renders as a word, never as a number.
export function formatCellValue(value) {
  if (value === null || value === undefined) return "—";
  if (value === true) return "بله";
  if (value === false) return "خیر (اندازه‌گیری‌شده)";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(3)));
  }
  return String(value);
}

function readingRow(kind, reading) {
  return Object.freeze({
    kind,
    id: String(reading?.sensor_id ?? "—"),
    status: String(reading?.status ?? "unknown"),
    value: reading?.value ?? null,
    source: reading?.source ?? null,
    detail: reading?.detail ?? null,
  });
}

export function rowsForModel(model) {
  if (!model || typeof model !== "object") return [];
  const rows = [];
  for (const kind of ["sensors", "processes", "capabilities"]) {
    const group = Array.isArray(model[kind]) ? model[kind] : [];
    for (const reading of group) rows.push(readingRow(kind, reading));
  }
  const probe = model.brain_probe;
  if (probe && typeof probe === "object") {
    rows.push(Object.freeze({
      kind: "brain_probe",
      id: "brain_probe",
      status: String(probe.status ?? "unknown"),
      value: probe.verdict ?? null,
      source: probe.source ?? null,
      detail: "بدون شاهد مؤرخ، هرگز «سالم» نیست",
    }));
  }
  return rows;
}

export function summarizeModel(model) {
  const counts = model?.counts && typeof model.counts === "object" ? model.counts : {};
  return Object.freeze({
    sensors: counts.sensors ?? 0,
    processes: counts.processes ?? 0,
    capabilities: counts.capabilities ?? 0,
    events: counts.events ?? 0,
    healthy: counts.healthy ?? 0,
    absent: counts.absent ?? 0,
    stale: counts.stale ?? 0,
    failed: counts.failed ?? 0,
    unknown: counts.unknown ?? 0,
  });
}

export function identityLines(model) {
  const identity = model?.code_identity && typeof model.code_identity === "object"
    ? model.code_identity
    : {};
  return Object.freeze({
    commit: identity.commit_sha ?? null,
    branch: identity.branch ?? null,
  });
}

// Fetch-state machine for the artifact: absent / malformed / ready / error
// are the only outcomes, and each renders explicitly on the page.
export async function fetchArtifact(fetchImpl = (...args) => globalThis.fetch(...args), path = ARTIFACT_PATH) {
  let response;
  try {
    response = await fetchImpl(path, { cache: "no-store" });
  } catch {
    return { state: "error" };
  }
  if (response.status === 404) return { state: "absent" };
  if (!response.ok) return { state: "error" };
  let payload;
  try {
    payload = await response.json();
  } catch {
    return { state: "malformed" };
  }
  const normalized = normalizeArtifact(payload);
  if (!normalized.valid) return { state: "malformed", reason: normalized.reason };
  return { state: "ready", envelope: normalized.envelope };
}
