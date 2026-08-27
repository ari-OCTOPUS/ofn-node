import {
  advancedJson,
  append,
  definitionList,
  disabledM2Canary,
  element,
  heading,
  truthBadge,
  unwrapEnvelope,
} from "../components/dom.js";
import {
  asArray,
  formatInteger,
  formatMoneyAUD,
  formatText,
  pick,
  stableJson,
  truthStatus,
} from "../formatting.js";

export const resource = "legs";

export const LIFECYCLE_LEGS = Object.freeze([
  { id: "DEMAND", label: "تقاضا" },
  { id: "QUALIFICATION", label: "ارزیابی" },
  { id: "OFFER", label: "پیشنهاد" },
  { id: "CONVERSION", label: "تبدیل" },
  { id: "DELIVERY", label: "تحویل" },
  { id: "CASH", label: "وجه نقد" },
  { id: "RETENTION", label: "نگهداشت" },
  { id: "FINANCE", label: "مالی" },
]);

function centsToAUD(value) {
  if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return formatMoneyAUD(null);
  return formatMoneyAUD(Number(value) / 100);
}

function rowFor(rows, id) {
  return rows.find((row) => String(row?.leg_id ?? row?.id ?? "").toUpperCase() === id) ?? null;
}

function legCard(definition, row) {
  const leg = row ?? { leg_id: definition.id, truth_status: "UNKNOWN" };
  const status = truthStatus(pick(leg, ["truth_status", "status", "state"]));
  const card = element("article", {
    className: "card leg-card",
    attrs: { "data-leg-id": definition.id },
  });
  const header = element("div", { className: "card-header" });
  const title = element("div");
  append(
    title,
    element("p", { className: "eyebrow ltr-isolate", text: definition.id }),
    element("h3", { text: definition.label }),
  );
  append(header, title, truthBadge(status.label, status.tone));

  const metrics = [
    { label: "ورودی", value: formatInteger(pick(leg, ["input_count", "inputs"])) },
    { label: "خروجی", value: formatInteger(pick(leg, ["output_count", "outputs"])) },
    { label: "رویداد امروز", value: formatInteger(pick(leg, ["events_today", "today_count"])) },
    { label: "منبع", value: formatText(pick(leg, ["source", "evidence_source"])) },
  ];

  if (definition.id === "OFFER") {
    metrics.push({ label: "ارزش پیشنهادی (برآورد، نه وجه نقد)", value: centsToAUD(pick(leg, ["estimated_value_cents", "quote_value_cents"])), className: "money" });
  }
  if (definition.id === "CONVERSION") {
    metrics.push({ label: "ارزش رزرو (نه وجه نقد)", value: centsToAUD(pick(leg, ["booking_value_cents", "booked_value_cents"])), className: "money" });
  }
  if (definition.id === "CASH") {
    metrics.push(
      { label: "فاکتور (نه وجه نقد)", value: centsToAUD(pick(leg, ["invoice_value_cents"])), className: "money" },
      { label: "وجه نقد تأییدشده", value: centsToAUD(pick(leg, ["verified_cash_cents"])), className: "money" },
    );
  }
  if (definition.id === "FINANCE") {
    metrics.push(
      { label: "وجه نقد تأییدشده", value: centsToAUD(pick(leg, ["verified_cash_cents"])), className: "money" },
      { label: "حاشیه مشارکت", value: centsToAUD(pick(leg, ["contribution_margin_cents"])), className: "money" },
    );
  }

  append(card, header, definitionList(metrics));
  return card;
}

export function renderLegs(payload) {
  const envelope = payload ?? {};
  const data = unwrapEnvelope(envelope) ?? {};
  const rows = asArray(data, ["items", "legs"]);
  const page = element("section", { attrs: { "aria-labelledby": "legs-title" } });
  append(page, heading(
    "هشت پایهٔ چرخهٔ کسب‌وکار",
    "پیشنهاد، رزرو و فاکتور هرگز به‌عنوان وجه نقد تأییدشده محاسبه نمی‌شوند.",
    { titleId: "legs-title" },
  ));

  const grid = element("div", { className: "card-grid", attrs: { "aria-label": "هشت کارت چرخه" } });
  for (const definition of LIFECYCLE_LEGS) {
    append(grid, legCard(definition, rowFor(rows, definition.id)));
  }
  append(page, grid, advancedJson(stableJson(envelope)), disabledM2Canary("فرمان چرخه"));
  return page;
}
