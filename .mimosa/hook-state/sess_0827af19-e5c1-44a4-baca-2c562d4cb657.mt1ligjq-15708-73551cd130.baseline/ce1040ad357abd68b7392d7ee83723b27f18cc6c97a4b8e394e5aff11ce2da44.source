import crypto from 'node:crypto';

export function clamp(value, min = 0, max = 1) {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, value));
}

export function round(value, decimals = 4) {
  const factor = 10 ** decimals;
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

export function safeDivide(numerator, denominator, fallback = 0) {
  if (!Number.isFinite(numerator) || !Number.isFinite(denominator) || denominator === 0) return fallback;
  return numerator / denominator;
}

export function logScale(value, cap) {
  if (!Number.isFinite(value) || value <= 0) return 0;
  return clamp(Math.log1p(value) / Math.log1p(cap), 0, 1);
}

export function mean(values) {
  const clean = values.filter((v) => Number.isFinite(v));
  if (!clean.length) return 0;
  return clean.reduce((a, b) => a + b, 0) / clean.length;
}

export function median(values) {
  const clean = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (!clean.length) return 0;
  const mid = Math.floor(clean.length / 2);
  return clean.length % 2 ? clean[mid] : (clean[mid - 1] + clean[mid]) / 2;
}

export function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

export function countBy(values) {
  const out = new Map();
  for (const v of values.filter(Boolean)) out.set(v, (out.get(v) || 0) + 1);
  return out;
}

export function topCounts(values, limit = 5) {
  return [...countBy(values).entries()]
    .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])))
    .slice(0, limit)
    .map(([value, count]) => ({ value, count }));
}

export function stableId(prefix, ...parts) {
  const hash = crypto.createHash('sha1').update(parts.filter(Boolean).join('|')).digest('hex').slice(0, 12);
  return `${prefix}_${hash}`;
}

export function jaccard(a, b) {
  const setA = new Set(tokenize(a));
  const setB = new Set(tokenize(b));
  if (!setA.size && !setB.size) return 0;
  let intersection = 0;
  for (const token of setA) if (setB.has(token)) intersection += 1;
  const union = new Set([...setA, ...setB]).size;
  return safeDivide(intersection, union);
}

export function tokenize(text) {
  return String(text || '')
    .toLowerCase()
    .replace(/[\p{P}\p{S}]+/gu, ' ')
    .split(/\s+/)
    .map((t) => t.trim())
    .filter((t) => t.length >= 2);
}

export function keywordScore(text, keywords) {
  const tokens = new Set(tokenize(text));
  if (!tokens.size) return 0;
  let hits = 0;
  for (const keyword of keywords) {
    const parts = tokenize(keyword);
    if (!parts.length) continue;
    if (parts.every((p) => tokens.has(p))) hits += 1;
  }
  return clamp(hits / Math.max(1, keywords.length));
}

export function isoNow() {
  return new Date().toISOString();
}

export function toCsv(rows) {
  if (!rows.length) return '';
  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    if (value == null) return '';
    const str = typeof value === 'object' ? JSON.stringify(value) : String(value);
    if (/[",\n\r]/.test(str)) return `"${str.replace(/"/g, '""')}"`;
    return str;
  };
  return [headers.join(','), ...rows.map((row) => headers.map((h) => escape(row[h])).join(','))].join('\n');
}

export function mdEscape(value) {
  return String(value ?? '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
}
