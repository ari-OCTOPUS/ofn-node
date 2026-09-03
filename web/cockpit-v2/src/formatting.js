export const UNKNOWN_TEXT = "نامعلوم";

const FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
const STATUS_LABELS = Object.freeze({
  ok: "سالم",
  healthy: "سالم",
  live: "زنده",
  online: "برخط",
  ready: "آماده",
  verified: "تأییدشده",
  fresh: "تازه",
  true: "بله",
  degraded: "کاهش‌یافته",
  partial: "ناقص",
  stale: "کهنه",
  pending: "در انتظار",
  warning: "هشدار",
  false: "خیر",
  error: "خطا",
  failed: "ناموفق",
  offline: "آفلاین",
  contradicted: "متناقض",
  blocked: "مسدود",
  unknown: UNKNOWN_TEXT,
  unavailable: "در دسترس نیست",
  not_measured: "اندازه‌گیری نشده",
  not_exposed: "ارائه نشده",
  not_modeled: "مدل نشده",
  not_implemented: "پیاده‌سازی نشده",
  consistent: "سازگار",
  inconsistent: "ناسازگار",
});

export function isNil(value) {
  return value === null || value === undefined;
}

export function formatText(value, fallback = UNKNOWN_TEXT) {
  if (isNil(value) || value === "") return fallback;
  if (typeof value === "boolean") return value ? "بله" : "خیر";
  return String(value);
}

export function toFaDigits(value) {
  return String(value).replace(/\d/g, (digit) => FA_DIGITS[Number(digit)]);
}

export function formatNumber(value) {
  if (isNil(value) || value === "" || !Number.isFinite(Number(value))) {
    return UNKNOWN_TEXT;
  }
  return new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 }).format(Number(value));
}

export function formatInteger(value) {
  if (isNil(value) || value === "" || !Number.isFinite(Number(value))) {
    return UNKNOWN_TEXT;
  }
  return new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(Number(value));
}

export function formatPercent(value) {
  if (isNil(value) || value === "" || !Number.isFinite(Number(value))) {
    return UNKNOWN_TEXT;
  }
  const numeric = Number(value);
  const normalized = Math.abs(numeric) <= 1 ? numeric : numeric / 100;
  return new Intl.NumberFormat("fa-IR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(normalized);
}

export function formatMoneyAUD(value) {
  if (isNil(value) || value === "" || !Number.isFinite(Number(value))) {
    return UNKNOWN_TEXT;
  }
  return new Intl.NumberFormat("fa-IR", {
    style: "currency",
    currency: "AUD",
    currencyDisplay: "code",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function formatDateTime(value) {
  if (isNil(value) || value === "") return UNKNOWN_TEXT;
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return UNKNOWN_TEXT;
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "Australia/Sydney",
  }).format(date);
}

export function formatDurationSeconds(value) {
  if (isNil(value) || !Number.isFinite(Number(value))) return UNKNOWN_TEXT;
  const seconds = Math.max(0, Math.round(Number(value)));
  if (seconds < 60) return `${formatInteger(seconds)} ثانیه`;
  if (seconds < 3600) return `${formatInteger(seconds / 60)} دقیقه`;
  if (seconds < 86400) return `${formatInteger(seconds / 3600)} ساعت`;
  return `${formatInteger(seconds / 86400)} روز`;
}

export function truthStatus(value) {
  if (isNil(value) || value === "") {
    return { key: "unknown", label: UNKNOWN_TEXT, tone: "neutral" };
  }
  const raw = typeof value === "object"
    ? value.status ?? value.truth_status ?? value.state ?? value.value
    : value;
  if (isNil(raw) || raw === "") {
    return { key: "unknown", label: UNKNOWN_TEXT, tone: "neutral" };
  }
  const key = String(raw).trim().toLowerCase().replace(/[\s-]+/g, "_");
  const ok = new Set(["ok", "healthy", "live", "online", "ready", "verified", "fresh", "true", "consistent"]);
  const warn = new Set(["degraded", "partial", "stale", "pending", "warning", "incomplete", "unverifiable"]);
  const bad = new Set(["error", "failed", "offline", "contradicted", "blocked", "false", "inconsistent"]);
  return {
    key,
    label: STATUS_LABELS[key] ?? String(raw),
    tone: ok.has(key) ? "ok" : warn.has(key) ? "warn" : bad.has(key) ? "bad" : "neutral",
  };
}

export function stableJson(value) {
  const seen = new WeakSet();
  const visit = (entry) => {
    if (entry === null || typeof entry !== "object") return entry;
    if (seen.has(entry)) return "[Circular]";
    seen.add(entry);
    if (Array.isArray(entry)) return entry.map(visit);
    const result = {};
    for (const key of Object.keys(entry).sort()) result[key] = visit(entry[key]);
    return result;
  };
  try {
    return JSON.stringify(visit(value), null, 2);
  } catch {
    return String(value);
  }
}

export function pick(object, paths, fallback = null) {
  for (const path of paths) {
    const parts = Array.isArray(path) ? path : String(path).split(".");
    let cursor = object;
    let present = true;
    for (const part of parts) {
      if (cursor === null || cursor === undefined || !(part in Object(cursor))) {
        present = false;
        break;
      }
      cursor = cursor[part];
    }
    if (present && cursor !== undefined) return cursor;
  }
  return fallback;
}

export function asArray(value, keys = []) {
  if (Array.isArray(value)) return value;
  for (const key of keys) {
    const nested = pick(value, [key]);
    if (Array.isArray(nested)) return nested;
  }
  return [];
}
