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
  formatDateTime,
  formatInteger,
  formatMoneyAUD,
  formatText,
  pick,
  stableJson,
  truthStatus,
} from "../formatting.js";

export const resource = "status";

export function renderCommandCenter(payload) {
  const envelope = payload ?? {};
  const data = unwrapEnvelope(envelope) ?? {};
  const page = element("section", { attrs: { "aria-labelledby": "command-center-title" } });
  append(page, heading(
    "مرکز فرمان",
    "نمای حقیقت عملیاتی؛ نبود شاهد به‌صورت نامعلوم نمایش داده می‌شود.",
    { titleId: "command-center-title" },
  ));

  const status = truthStatus(pick(data, ["truth_status", "status", "health.status", "health"]));
  const overview = element("article", { className: "card" });
  const cardHeader = element("div", { className: "card-header" });
  append(cardHeader, element("h3", { text: "وضعیت جاری" }), truthBadge(status.label, status.tone));
  append(
    overview,
    cardHeader,
    definitionList([
      { label: "دسترس‌پذیری", value: formatText(pick(data, ["availability.status", "availability", "readiness.status"])) },
      { label: "حالت اجرا", value: formatText(pick(data, ["runtime.mode", "mode", "boot_mode"])) },
      { label: "کلید توقف", value: formatText(pick(data, ["killed", "kill_switch.engaged", "stopped"])) },
      { label: "صف در انتظار", value: formatInteger(pick(data, ["queue.pending", "queue_pending", "pending_count"])) },
      { label: "نودهای گزارش‌دهنده", value: formatInteger(pick(data, ["nodes.reporting", "node_count", "nodes.count"])) },
      { label: "تولید داده", value: formatDateTime(pick(envelope, ["generated_at", "meta.generated_at"], pick(data, ["generated_at"]))) , className: "timestamp"},
    ], "metric-list"),
  );

  const money = element("article", { className: "card" });
  append(
    money,
    element("div", { className: "card-header" }),
  );
  money.firstChild.append(element("h3", { text: "حقیقت مالی" }), truthBadge("فقط AUD", "neutral"));
  append(money, definitionList([
    {
      label: "وجه نقد تأییدشده",
      value: formatMoneyAUD(pick(data, ["verified_cash_cents"]) === null
        ? null
        : Number(pick(data, ["verified_cash_cents"])) / 100),
      className: "money",
    },
    {
      label: "حاشیه مشارکت اثبات‌شده",
      value: formatMoneyAUD(pick(data, ["contribution_margin_cents"]) === null
        ? null
        : Number(pick(data, ["contribution_margin_cents"])) / 100),
      className: "money",
    },
    { label: "برآورد پیشنهاد", value: "برآورد است؛ وجه نقد نیست" },
    { label: "رزرو", value: "رزرو است؛ وجه نقد نیست" },
    { label: "فاکتور", value: "فاکتور است؛ وجه نقد نیست" },
  ], "metric-list"));

  const grid = element("div", { className: "card-grid" });
  append(grid, overview, money);
  append(page, grid, advancedJson(stableJson(envelope)), disabledM2Canary("فرمان‌های مالک"));
  return page;
}
