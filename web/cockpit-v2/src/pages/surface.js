import {
  advancedJson,
  append,
  definitionList,
  element,
  heading,
  truthBadge,
  unwrapEnvelope,
} from "../components/dom.js";
import {
  formatDateTime,
  formatInteger,
  formatText,
  stableJson,
  truthStatus,
} from "../formatting.js";

export const resource = "surface";

export const CARD_ORDER = Object.freeze([
  "command_center",
  "self_model",
  "doctor",
  "economic_learning",
  "owner_queue",
  "telegram_bridge",
  "receipts_sync",
]);

const CARD_TITLES = Object.freeze({
  command_center: "مرکز فرمان",
  self_model: "خودمدل",
  doctor: "دکتر",
  economic_learning: "یادگیری اقتصادی",
  owner_queue: "صف مالک",
  telegram_bridge: "پل تلگرام",
  receipts_sync: "رسیدها / همگام‌سازی Obsidian",
});

const CARD_LINKS = Object.freeze({
  command_center: "#/command-center",
  self_model: "/cockpit-v2/self-model.html",
  owner_queue: "#/queue",
});

const SOURCE_NOTES = Object.freeze({
  command_center: "version_metadata · state/self-model/SYSTEM-SELF-MODEL.json · 09-LANES/LB/runs · 09-LANES/ECONOMIC-LEARNING/runs · owner_queue_metadata",
  self_model: "state/self-model/SYSTEM-SELF-MODEL.json",
  doctor: "09-LANES/LB/runs/*/receipt.jsonl",
  economic_learning: "09-LANES/ECONOMIC-LEARNING/runs/*/run-summary.json",
  owner_queue: "owner_queue_metadata (read-model callback)",
  telegram_bridge: "config/telegram_policy.json",
  receipts_sync: "receipts/ · obsidian: wired nowhere",
});

const NUMBER_LABELS = Object.freeze({
  main_sha: "SHA اصلی",
  self_model_sha: "SHA خودمدل",
  doctor_run_id: "شناسهٔ اجرای دکتر",
  verified_payments: "پرداخت‌های تأییدشده",
  owner_queue_count: "تعداد صف مالک",
});

const COUNT_IDS = new Set(["verified_payments", "owner_queue_count"]);

// Verdict badge meta. Unknown/incomplete stay neutral — only an explicit
// consistent verdict is green, and a disagreement is loud, not subtle.
export function verdictMeta(verdict) {
  const status = truthStatus(verdict);
  if (verdict === "inconsistent") {
    return { key: status.key, label: "ناسازگار · INCONSISTENT", tone: "bad" };
  }
  return { key: status.key, label: status.label, tone: status.tone };
}

function numberValue(number) {
  const raw = number?.value;
  if (COUNT_IDS.has(number?.id)) return formatInteger(raw);
  return formatText(raw);
}

function rowsForCommandCenter(card) {
  const numbers = Array.isArray(card?.numbers) ? card.numbers : [];
  const rows = numbers.map((number) => ({
    label: NUMBER_LABELS[number?.id] ?? formatText(number?.id),
    value: numberValue(number),
    className: COUNT_IDS.has(number?.id) ? "" : "inert-text",
  }));
  if (numbers.length === 0) {
    // A missing coherence block is unknown as a whole — never rendered empty.
    rows.push({ label: "هم‌خوانی اعداد", value: formatText(null) });
  }
  const disagreements = Array.isArray(card?.disagreements) ? card.disagreements : [];
  for (const item of disagreements) {
    rows.push({
      label: "ناسازگاری",
      value: `${formatText(item?.left)} ≠ ${formatText(item?.right)}`,
      className: "inert-text",
    });
  }
  return rows;
}

function rowsForSelfModel(card) {
  return [
    { label: "وضعیت مدل", value: formatText(card?.status) },
    { label: "SHA ثبت‌شده", value: formatText(card?.commit_sha), className: "inert-text" },
    { label: "آرتافکت حاضر", value: formatText(card?.artifact_present) },
  ];
}

function rowsForDoctor(card) {
  return [
    { label: "شناسهٔ اجرا", value: formatText(card?.run_id), className: "inert-text" },
    { label: "زمان شروع", value: formatDateTime(card?.started_at), className: "timestamp" },
    { label: "حالت", value: formatText(card?.mode) },
  ];
}

function rowsForEconomicLearning(card) {
  const chains = card?.chains_total === null || card?.chains_total === undefined
    || card?.chains_complete === null || card?.chains_complete === undefined
    ? null
    : `${formatInteger(card.chains_complete)} / ${formatInteger(card.chains_total)}`;
  return [
    { label: "پرداخت‌های تأییدشده", value: formatInteger(card?.verified_payments) },
    { label: "ادعاهای تأییدنشده", value: formatInteger(card?.unverified_payment_claims) },
    { label: "زنجیره‌ها (کامل/کل)", value: chains ?? formatText(null) },
    { label: "کمپین", value: formatText(card?.campaign_id), className: "inert-text" },
    { label: "زمان اجرا", value: formatDateTime(card?.generated_at), className: "timestamp" },
  ];
}

function rowsForOwnerQueue(card) {
  return [
    { label: "ردیف‌های مالک", value: formatInteger(card?.count) },
  ];
}

function rowsForTelegramBridge(card) {
  return [
    { label: "حالت", value: formatText(card?.mode) },
  ];
}

function rowsForReceiptsSync(card) {
  return [
    { label: "تعداد رسیدها", value: formatInteger(card?.receipt_count) },
    { label: "همگام‌سازی Obsidian", value: formatText(card?.obsidian_sync) },
  ];
}

const ROW_BUILDERS = Object.freeze({
  command_center: rowsForCommandCenter,
  self_model: rowsForSelfModel,
  doctor: rowsForDoctor,
  economic_learning: rowsForEconomicLearning,
  owner_queue: rowsForOwnerQueue,
  telegram_bridge: rowsForTelegramBridge,
  receipts_sync: rowsForReceiptsSync,
});

// Plain data rows for one card — unknown stays "نامعلوم", never a green
// claim. Exported for tests; the DOM assembly below only formats these.
export function cardRows(cardId, card) {
  const builder = ROW_BUILDERS[cardId];
  return builder ? builder(card ?? {}) : [];
}

function surfaceCard(cardId, card, status) {
  const article = element("article", { className: "card surface-card" });
  article.dataset.card = cardId;
  const header = element("div", { className: "card-header" });
  const badge = truthStatus(status);
  append(header, element("h3", { text: CARD_TITLES[cardId] ?? cardId }), truthBadge(badge.label, badge.tone));
  append(article, header);
  append(article, definitionList(cardRows(cardId, card), "metric-list"));
  const source = SOURCE_NOTES[cardId];
  if (source) append(article, element("p", { className: "helper", text: `منبع: ${source}` }));
  const link = CARD_LINKS[cardId];
  if (link) {
    append(article, element("a", { text: "جزئیات", attrs: { href: link } }));
  }
  return article;
}

export function renderSurface(payload) {
  const envelope = payload ?? {};
  const data = unwrapEnvelope(envelope) ?? {};
  const cards = data.cards ?? {};
  const statuses = data.card_status ?? {};
  const coherence = data.coherence ?? {};
  const page = element("section", { attrs: { "aria-labelledby": "surface-title" } });
  append(page, heading(
    "نمای هفت‌کارتهٔ مالک",
    "هفت کارت فقط‌خواندنی؛ منبع غایب «نامعلوم» می‌ماند و ناسازگاری اعداد بلند نمایش داده می‌شود.",
    { titleId: "surface-title" },
  ));

  const overview = element("article", { className: "panel" });
  const badge = verdictMeta(coherence.verdict);
  const overviewHeader = element("div", { className: "card-header" });
  append(overviewHeader, element("h3", { text: "هم‌خوانی اعداد" }), truthBadge(badge.label, badge.tone));
  append(overview, overviewHeader);
  append(page, overview);

  const grid = element("div", { className: "card-grid surface-grid" });
  for (const cardId of CARD_ORDER) {
    append(grid, surfaceCard(cardId, cards[cardId], statuses[cardId]));
  }
  append(page, grid, advancedJson(stableJson(envelope)));
  return page;
}
