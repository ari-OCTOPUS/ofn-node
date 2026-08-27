import {
  advancedJson,
  append,
  definitionList,
  disabledM2Canary,
  element,
  heading,
  statePanel,
  truthBadge,
  unwrapEnvelope,
} from "../components/dom.js";
import {
  asArray,
  formatDateTime,
  formatInteger,
  formatText,
  pick,
  stableJson,
  truthStatus,
} from "../formatting.js";

export const resource = "queue";

const SAFE_METADATA_FIELDS = Object.freeze([
  ["شناسه", ["message_id", "id", "queue_id"]],
  ["وضعیت", ["state", "status"]],
  ["نوع", ["message_type", "kind", "category"]],
  ["ریسک", ["risk_tier", "tier", "risk"]],
  ["فرستنده", ["sender_node", "source_node", "source"]],
  ["گیرنده", ["recipient_node", "target_node", "target"]],
  ["زمان ایجاد", ["created_at", "enqueued_at"]],
  ["زمان انقضا", ["expires_at", "expiry_at"]],
  ["شناسهٔ هم‌بستگی", ["correlation_id"]],
]);

function queueItem(item, index) {
  const entry = element("li", { className: "queue-item" });
  const header = element("div", { className: "card-header" });
  const identifier = formatText(pick(item, ["message_id", "id", "queue_id"]), `ردیف ${formatInteger(index + 1)}`);
  const status = truthStatus(pick(item, ["state", "status"]));
  append(header, element("h3", { className: "inert-text", text: identifier }), truthBadge(status.label, status.tone));

  const rows = SAFE_METADATA_FIELDS.map(([label, paths]) => {
    const raw = pick(item, paths);
    const isTime = paths.some((path) => path.endsWith("_at"));
    return {
      label,
      value: isTime ? formatDateTime(raw) : formatText(raw),
      className: isTime ? "timestamp" : "inert-text",
    };
  });
  append(entry, header, definitionList(rows));
  return entry;
}

export function renderQueue(payload) {
  const envelope = payload ?? {};
  const data = unwrapEnvelope(envelope) ?? {};
  const items = asArray(data, ["items", "queue"]);
  const page = element("section", { attrs: { "aria-labelledby": "queue-title" } });
  append(page, heading(
    "صف امن",
    "فقط فرادادهٔ محدود نمایش داده می‌شود؛ payload، evidence، متن مشتری و خطای خام در UI جایی ندارند.",
    { titleId: "queue-title" },
  ));

  const metadata = element("article", { className: "panel" });
  append(metadata, element("h3", { text: "خلاصهٔ صف" }), definitionList([
    { label: "تعداد قابل نمایش", value: formatInteger(pick(data, ["count", "total"], items.length)) },
    { label: "در انتظار", value: formatInteger(pick(data, ["counts.pending", "pending_count"])) },
    { label: "در پردازش", value: formatInteger(pick(data, ["counts.processing", "processing_count"])) },
    { label: "ردشده", value: formatInteger(pick(data, ["counts.rejected", "rejected_count"])) },
  ], "metric-list"));
  append(page, metadata);

  if (items.length === 0) {
    append(page, statePanel({
      kind: "empty",
      title: "ردیف قابل نمایشی در صف نیست",
      message: "صف خالی نمایش‌داده‌شده تنها دربارهٔ این پاسخ محدود است و ادعای نبود کار در منابع دیگر نیست.",
    }));
  } else {
    const list = element("ol", { className: "queue-list", attrs: { "aria-label": "فرادادهٔ ردیف‌های صف" } });
    items.forEach((item, index) => append(list, queueItem(item, index)));
    append(page, list);
  }

  append(page, advancedJson(stableJson(envelope)), disabledM2Canary("تصمیم صف"));
  return page;
}
