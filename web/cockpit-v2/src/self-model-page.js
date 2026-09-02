// DOM layer of the self-model viewer. Thin on purpose: every rule lives in
// ./self-model-format.js (pure, node-tested); this file only maps fetch
// states to honest screens. A missing artifact, a broken artifact, and a
// stale one each get their own explicit panel — nothing is invented.

import { append, clear, element, heading, statePanel, truthBadge } from "./components/dom.js";
import {
  ARTIFACT_PATH,
  PRODUCER_COMMAND,
  fetchArtifact,
  formatCellValue,
  identityLines,
  isGreenModelStatus,
  modelStatusMeta,
  readingStatusMeta,
  rowsForModel,
  summarizeModel,
} from "./self-model-format.js";

const REFRESH_INTERVAL_MS = 60_000;

function sectionTitle(kind) {
  return {
    sensors: "حسگرها",
    processes: "پروسه‌های عضو",
    capabilities: "قابلیت‌ها",
    brain_probe: "پروب مغز",
  }[kind] ?? kind;
}

function readingCard(row) {
  const meta = readingStatusMeta(row.status);
  const card = element("article", { className: "card" });
  const header = element("div", { className: "card-header" });
  append(header, element("h3", { className: "inert-text", text: row.id }), truthBadge(meta.label, meta.tone));
  const rows = [
    { label: "وضعیت", value: meta.label },
    { label: "مقدار", value: formatCellValue(row.value) },
    { label: "منبع", value: row.source ?? "—" },
  ];
  if (row.detail) rows.push({ label: "جزئیات", value: row.detail });
  const list = element("dl", { className: "definition-list" });
  for (const item of rows) {
    append(list,
      element("dt", { text: item.label }),
      element("dd", { text: item.value, className: item.label === "منبع" ? "code-value" : undefined }));
  }
  append(card, header, list);
  return card;
}

function renderReady(root, envelope) {
  const model = envelope.data;
  const statusMeta = modelStatusMeta(envelope.status);
  const summary = summarizeModel(model);
  const identity = identityLines(model);

  const page = element("section", { attrs: { "aria-labelledby": "self-model-title" } });
  const headerRow = element("div", { className: "card-header" });
  append(headerRow, truthBadge(statusMeta.label, statusMeta.tone));
  append(page, heading(
    "خودمدل ماشین‌نوشته",
    "این صفحه فقط آرتیفکت تولیدشده توسط producer را نشان می‌دهد؛ هیچ مقداری اینجا ساخته نمی‌شود.",
    { titleId: "self-model-title" },
  ), headerRow);

  const meta = element("dl", { className: "definition-list" });
  const metaRows = [
    { label: "تولید", value: envelope.generated_at ?? "—" },
    { label: "کهنه پس از", value: envelope.stale_after ?? "—" },
    { label: "کامیت", value: identity.commit ?? "نامعلوم" },
    { label: "شاخه", value: identity.branch ?? "نامعلوم" },
    { label: "شمارش",
      value: `${summary.healthy} سالم · ${summary.absent} غایب · ${summary.stale} کهنه · ${summary.failed} خراب · ${summary.unknown} نامعلوم` },
  ];
  for (const item of metaRows) {
    append(meta, element("dt", { text: item.label }), element("dd", { text: item.value }));
  }
  append(page, meta);

  if (!isGreenModelStatus(envelope.status)) {
    append(page, statePanel({
      kind: "warning",
      title: "وضعیت کلی سبز نیست",
      message: "مدل خودش گفت هنوز همهٔ اجزای آن قابل‌راستی‌آزمایی نیست؛ این صفحه وضعیت را ارتقا نمی‌دهد.",
    }));
  }

  const rows = rowsForModel(model);
  const byKind = new Map();
  for (const row of rows) {
    if (!byKind.has(row.kind)) byKind.set(row.kind, []);
    byKind.get(row.kind).push(row);
  }
  for (const [kind, kindRows] of byKind) {
    append(page, element("h2", { text: sectionTitle(kind) }));
    const grid = element("div", { className: "card-grid" });
    for (const row of kindRows) append(grid, readingCard(row));
    append(page, grid);
  }

  const unknowns = Array.isArray(model.unknowns) ? model.unknowns : [];
  if (unknowns.length) {
    append(page, element("h2", { text: "نامعلوم‌های تصریح‌شده" }));
    const list = element("ul");
    for (const item of unknowns) append(list, element("li", { text: String(item) }));
    append(page, list);
  }

  const refresh = element("button", { text: "تازه‌سازی", attrs: { type: "button" } });
  refresh.addEventListener("click", () => void load());
  append(page, refresh);
  append(root, page);
}

function renderFailure(root, state) {
  if (state === "absent") {
    append(root, statePanel({
      kind: "empty",
      title: "آرتیفکت خودمدل وجود ندارد",
      message: `تا producer اجرا نشود چیزی برای نمایش نیست. فرمان تولید: ${PRODUCER_COMMAND}`,
    }));
    return;
  }
  if (state === "malformed") {
    append(root, statePanel({
      kind: "error",
      title: "آرتیفکت ناقص یا خراب است",
      message: "خروجی producer قابل تفسیر نبود؛ این صفحه حدس نمی‌زند و چیزی سبز نشان نمی‌دهد.",
    }));
    return;
  }
  append(root, statePanel({
    kind: "error",
    title: "دریافت آرتیفکت ناموفق بود",
    message: `خواندن ${ARTIFACT_PATH} با خطا مواجه شد؛ وضعیت واقعی نامعلوم است.`,
  }));
}

export function mountSelfModelPage({
  root = document.getElementById("main-content"),
  fetchImpl,
  intervalMs = REFRESH_INTERVAL_MS,
} = {}) {
  let stopped = false;
  let timer = null;

  async function load() {
    const state = await fetchArtifact(fetchImpl);
    if (stopped) return;
    clear(root);
    if (state.state === "ready") renderReady(root, state.envelope);
    else renderFailure(root, state.state);
  }

  function schedule() {
    if (stopped || intervalMs <= 0) return;
    timer = globalThis.setTimeout(() => {
      void load().then(schedule);
    }, intervalMs);
  }

  void load().then(schedule);
  return {
    stop() {
      stopped = true;
      if (timer !== null) globalThis.clearTimeout(timer);
    },
  };
}
