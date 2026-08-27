export function element(tagName, { className = "", text = null, attrs = {}, dataset = {} } = {}) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== null && text !== undefined) node.textContent = String(text);
  for (const [name, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (value === true) node.setAttribute(name, "");
    else node.setAttribute(name, String(value));
  }
  for (const [name, value] of Object.entries(dataset)) {
    if (value !== null && value !== undefined) node.dataset[name] = String(value);
  }
  return node;
}

export function append(parent, ...children) {
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined && child !== false) parent.append(child);
  }
  return parent;
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

export function heading(title, description, { titleId = null } = {}) {
  const wrapper = element("header", { className: "page-heading" });
  const copy = element("div");
  const h2 = element("h2", { text: title, attrs: titleId ? { id: titleId } : {} });
  const paragraph = element("p", { className: "muted", text: description });
  append(copy, h2, paragraph);
  append(wrapper, copy);
  return wrapper;
}

export function truthBadge(label, tone = "neutral") {
  return element("span", {
    className: "truth-label",
    text: label,
    dataset: { tone },
  });
}

export function definitionList(rows, className = "detail-list") {
  const list = element("dl", { className });
  for (const row of rows) {
    const box = element("div");
    const term = element("dt", { text: row.label });
    const value = element("dd", {
      className: row.className ?? "",
      text: row.value,
      attrs: row.title ? { title: row.title } : {},
    });
    append(box, term, value);
    append(list, box);
  }
  return list;
}

export function statePanel({ kind = "empty", title, message, busy = false, action = null }) {
  const panel = element("section", {
    className: "page-state",
    attrs: {
      "data-kind": kind,
      "aria-busy": busy ? "true" : "false",
      role: kind === "error" ? "alert" : undefined,
    },
  });
  if (busy) append(panel, element("p", { className: "loading-indicator", attrs: { "aria-hidden": "true" } }));
  append(panel, element("h2", { text: title }), element("p", { text: message }));
  if (action) append(panel, action);
  return panel;
}

export function advancedJson(value, label = "JSON پیشرفته (فقط خواندن)") {
  const details = element("details", { className: "advanced-json" });
  const summary = element("summary", { text: label });
  const pre = element("pre", {
    className: "inert-text",
    attrs: { tabindex: "0", "aria-label": "دادهٔ JSON فقط خواندنی" },
  });
  pre.textContent = value;
  append(details, summary, pre);
  return details;
}

export function disabledM2Canary(label = "فرمان مالک") {
  const wrapper = element("section", {
    className: "command-canary",
    attrs: { "aria-label": "فرمان‌های آینده" },
  });
  const copy = element("div");
  append(
    copy,
    element("strong", { text: label }),
    element("p", { className: "helper", text: "در M1 هیچ فرمان یا اثر اجرایی ارسال نمی‌شود." }),
  );
  const button = element("button", {
    text: "Available after M2 owner-command canary",
    attrs: { type: "button", disabled: true, "aria-disabled": "true" },
  });
  append(wrapper, copy, button);
  return wrapper;
}

export function unwrapEnvelope(value) {
  if (value && typeof value === "object" && "data" in value) return value.data;
  return value;
}
