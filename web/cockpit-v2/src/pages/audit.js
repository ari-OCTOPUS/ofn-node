import {
  advancedJson,
  append,
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

export const resource = "audit";
const PAGE_SIZE = 20;

function normalized(value) {
  return formatText(value, "").toLocaleLowerCase("fa-IR");
}

function filterRows(rows, query, category) {
  const needle = query.trim().toLocaleLowerCase("fa-IR");
  return rows.filter((row) => {
    const rowCategory = formatText(pick(row, ["category", "event", "kind", "type"]), "");
    if (category !== "all" && rowCategory !== category) return false;
    if (!needle) return true;
    const searchable = [
      pick(row, ["event_id", "id", "seq"]),
      rowCategory,
      pick(row, ["source", "node_id"]),
      pick(row, ["status", "outcome"]),
      pick(row, ["correlation_id"]),
    ].map(normalized).join(" ");
    return searchable.includes(needle);
  });
}

function auditItem(row, index) {
  const item = element("li", { className: "audit-item" });
  const header = element("div", { className: "card-header" });
  const category = formatText(pick(row, ["category", "event", "kind", "type"]), `رویداد ${formatInteger(index + 1)}`);
  const status = truthStatus(pick(row, ["status", "outcome", "verification.status"]));
  append(header, element("h3", { className: "inert-text", text: category }), truthBadge(status.label, status.tone));
  append(
    item,
    header,
    element("p", { className: "timestamp", text: formatDateTime(pick(row, ["occurred_at", "created_at", "ts", "timestamp"])) }),
    element("p", { className: "inert-text", text: `منبع: ${formatText(pick(row, ["source", "node_id"]))}` }),
    element("p", { className: "inert-text", text: `شناسه: ${formatText(pick(row, ["event_id", "id", "seq"]))}` }),
    element("p", { className: "inert-text", text: `هم‌بستگی: ${formatText(pick(row, ["correlation_id"]))}` }),
  );
  return item;
}

export function renderAudit(payload) {
  const envelope = payload ?? {};
  const data = unwrapEnvelope(envelope) ?? {};
  const rows = asArray(data, ["items", "events", "audit"]);
  const page = element("section", { attrs: { "aria-labelledby": "audit-title" } });
  append(page, heading(
    "ممیزی",
    "جست‌وجو و فیلتر فقط روی فرادادهٔ امنٔ همین پاسخ انجام می‌شود؛ details و payload نمایش داده نمی‌شوند.",
    { titleId: "audit-title" },
  ));

  const controls = element("form", { className: "control-row", attrs: { role: "search" } });
  const searchLabel = element("label", { text: "جست‌وجوی فراداده" });
  const search = element("input", {
    attrs: {
      type: "search",
      name: "audit-search",
      autocomplete: "off",
      placeholder: "شناسه، دسته، منبع یا وضعیت",
      "aria-controls": "audit-results",
    },
  });
  append(searchLabel, search);

  const categories = [...new Set(rows.map((row) => formatText(pick(row, ["category", "event", "kind", "type"]), "")).filter(Boolean))].sort();
  const filterLabel = element("label", { text: "دسته" });
  const select = element("select", { attrs: { name: "audit-category", "aria-controls": "audit-results" } });
  append(select, element("option", { text: "همه", attrs: { value: "all" } }));
  categories.forEach((category) => append(select, element("option", { className: "inert-text", text: category, attrs: { value: category } })));
  append(filterLabel, select);
  append(controls, searchLabel, filterLabel);
  append(page, controls);

  const resultRegion = element("div", { attrs: { id: "audit-results", "aria-live": "polite" } });
  const pager = element("nav", { className: "pagination", attrs: { "aria-label": "صفحه‌بندی ممیزی" } });
  const previous = element("button", { text: "صفحهٔ قبل", attrs: { type: "button" } });
  const summary = element("span", { className: "muted" });
  const next = element("button", { text: "صفحهٔ بعد", attrs: { type: "button" } });
  append(pager, previous, summary, next);
  let currentPage = 1;

  const draw = () => {
    while (resultRegion.firstChild) resultRegion.removeChild(resultRegion.firstChild);
    const filtered = filterRows(rows, search.value, select.value);
    const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    currentPage = Math.min(Math.max(1, currentPage), pages);
    const first = (currentPage - 1) * PAGE_SIZE;
    const visible = filtered.slice(first, first + PAGE_SIZE);

    if (visible.length === 0) {
      append(resultRegion, statePanel({
        kind: "empty",
        title: "رویدادی مطابق فیلتر نیست",
        message: "عبارت جست‌وجو یا دسته را تغییر دهید.",
      }));
    } else {
      const list = element("ol", { className: "audit-list" });
      visible.forEach((row, index) => append(list, auditItem(row, first + index)));
      append(resultRegion, list);
    }
    summary.textContent = `صفحه ${formatInteger(currentPage)} از ${formatInteger(pages)} · ${formatInteger(filtered.length)} نتیجه`;
    previous.disabled = currentPage <= 1;
    next.disabled = currentPage >= pages;
  };

  search.addEventListener("input", () => { currentPage = 1; draw(); });
  select.addEventListener("change", () => { currentPage = 1; draw(); });
  controls.addEventListener("submit", (event) => event.preventDefault());
  previous.addEventListener("click", () => { currentPage -= 1; draw(); search.focus(); });
  next.addEventListener("click", () => { currentPage += 1; draw(); search.focus(); });
  draw();

  append(page, resultRegion, pager, advancedJson(stableJson(envelope)));
  return page;
}
