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
  formatPercent,
  formatText,
  pick,
  stableJson,
  truthStatus,
} from "../formatting.js";

export const resource = "nodes";

function nodeCard(node, index) {
  const card = element("article", { className: "card" });
  const header = element("div", { className: "card-header" });
  const identity = formatText(pick(node, ["node_id", "id", "name"]), `نود ${formatInteger(index + 1)}`);
  const status = truthStatus(pick(node, ["truth_status", "status", "health.status", "health"]));
  append(header, element("h3", { className: "inert-text", text: identity }), truthBadge(status.label, status.tone));
  append(card, header, definitionList([
    { label: "نقش", value: formatText(pick(node, ["role", "node_role"])) },
    { label: "آخرین مشاهده", value: formatDateTime(pick(node, ["observed_at", "last_seen_at", "updated_at"])), className: "timestamp" },
    { label: "CPU", value: formatPercent(pick(node, ["cpu.utilisation", "cpu.utilization", "cpu_percent"])) },
    { label: "RAM", value: formatPercent(pick(node, ["memory.utilisation", "memory.utilization", "memory_percent"])) },
    { label: "دما", value: pick(node, ["temperature_c"]) === null ? "نامعلوم" : `${formatText(pick(node, ["temperature_c"]))} °C` },
    { label: "شنونده‌ها", value: formatInteger(pick(node, ["listener_count", "listeners.count"])) },
    { label: "منبع شاهد", value: formatText(pick(node, ["source", "evidence_source"])) },
    { label: "نسخه", value: formatText(pick(node, ["version", "release"])), className: "code-value" },
  ]));
  return card;
}

export function renderNodes(payload) {
  const envelope = payload ?? {};
  const data = unwrapEnvelope(envelope) ?? {};
  const nodes = asArray(data, ["items", "nodes"]);
  const page = element("section", { attrs: { "aria-labelledby": "nodes-title" } });
  append(page, heading(
    "نودها",
    "کارت‌های نود تنها شواهد تازه و صریح را نشان می‌دهند؛ متریک غایب سالم فرض نمی‌شود.",
    { titleId: "nodes-title" },
  ));

  if (nodes.length === 0) {
    append(page, statePanel({
      kind: "empty",
      title: "هیچ نودی گزارش نشده است",
      message: "این نتیجه به معنی صفر نود یا سلامت شبکه نیست؛ شاهد قابل نمایش وجود ندارد.",
    }));
  } else {
    const grid = element("div", { className: "card-grid" });
    nodes.forEach((node, index) => append(grid, nodeCard(node, index)));
    append(page, grid);
  }
  append(page, advancedJson(stableJson(envelope)), disabledM2Canary("کنترل نود"));
  return page;
}
