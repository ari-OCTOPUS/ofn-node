// OFN buy.nsw Harvester — shared record contract + client-side preview filter.
//
// CONTRACT (v1): the canonical record shape below is the SAME shape the
// Python ingest gate (ofn/agents/h1_buysw_dom.py, BATCH_SCHEMA
// "buynsw-harvest-batch/1") validates. If you change a key here, change it
// there in the same commit — the test tests/test_h1_buynsw_dom.py pins the
// bridge with a fixture in exactly this shape.
//
// AUTHORITATIVE FILTERING LIVES IN PYTHON (h1_buysw.py). The keyword and
// region lists below are a mirror for UI preview counts only. The server
// re-filters everything and may reject records this UI keeps. Do not treat
// a green count here as an accepted count.

"use strict";

const BATCH_SCHEMA = "buynsw-harvest-batch/1";
const MAX_TEXT = 1200;

// Mirrors ACCEPT_KEYWORDS in ofn/agents/h1_buysw.py (preview only).
const ACCEPT_KEYWORDS = [
  "painting", "repaint", "repainting", "external painting",
  "internal painting", "coating", "facade repaint",
  "paint work", "paintwork",
];

// Mirrors REJECT_KEYWORDS in ofn/agents/h1_buysw.py (preview only).
const REJECT_KEYWORDS = [
  "paint supply", "paint product", "art gallery", "exhibition",
  "artwork", "art collection", "painting exhibition",
  "paints and primers", "bulk paint",
];

// Mirrors ACCEPT_REGIONS in ofn/agents/h1_buysw.py (preview only).
const ACCEPT_REGIONS = [
  "sydney", "cumberland/prospect", "nepean", "northern sydney",
  "inner west", "south east sydney", "south west sydney",
  "central coast", "illawarra", "hunter",
];

function clip(value, limit) {
  const s = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
  return s.slice(0, limit || MAX_TEXT);
}

// "$1,234,567" | "1.2m" | "50 000" -> 1234567.0 | 1200000.0 | 50000.0
function parseAmountAud(text) {
  if (typeof text !== "string" || !text.trim()) return null;
  const m = text.match(/\$?\s*([\d][\d,\s]*(?:\.\d+)?)\s*(m\b|million)?/i);
  if (!m) return null;
  const num = parseFloat(m[1].replace(/[,\s]/g, ""));
  if (!isFinite(num)) return null;
  return m[2] ? num * 1e6 : num;
}

// Normalize one raw DOM extraction into the canonical record shape.
function normalizeRecord(raw, capturedAt) {
  if (!raw || typeof raw !== "object") return null;
  const detailUrl = clip(raw.detail_url, 300);
  const title = clip(raw.title, 220);
  if (!title) return null;
  const uuidM = detailUrl.match(/\/notices\/([^/?#]+)/i);
  return {
    notice_uuid: clip(raw.notice_uuid || (uuidM ? uuidM[1] : ""), 80),
    title: title,
    buyer_name: clip(raw.buyer_name, 160),
    location_text: clip(raw.location_text, 160),
    closing_at: clip(raw.closing_at, 80),
    amount_aud: (typeof raw.amount_aud === "number" && isFinite(raw.amount_aud))
      ? raw.amount_aud
      : parseAmountAud(raw.amount_text || ""),
    detail_url: detailUrl,
    raw_text: clip(raw.raw_text, MAX_TEXT),
    captured_at: clip(capturedAt || new Date().toISOString(), 40),
  };
}

// Preview-only painting filter (server re-filters authoritatively).
function previewKeep(record) {
  if (!record) return false;
  const text = (record.title + " " + (record.raw_text || "")).toLowerCase();
  for (const rk of REJECT_KEYWORDS) {
    if (text.includes(rk)) return false;
  }
  return ACCEPT_KEYWORDS.some((ak) => text.includes(ak));
}

function buildBatch(records, captureUrl, capturedAt) {
  return {
    schema: BATCH_SCHEMA,
    captured_at: clip(capturedAt || new Date().toISOString(), 40),
    capture_url: clip(captureUrl || "", 300),
    records: (records || []).filter(Boolean),
  };
}

function toCSV(records) {
  const cols = [
    "notice_uuid", "title", "buyer_name", "location_text",
    "closing_at", "amount_aud", "detail_url", "captured_at",
  ];
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const lines = [cols.join(",")];
  for (const r of records || []) {
    lines.push(cols.map((c) => esc(r[c])).join(","));
  }
  return lines.join("\r\n") + "\r\n";
}

// Export once for every context: content script (globalThis), popup page
// (classic <script> tag), and service worker (importScripts).
const OFNMapping = {
  BATCH_SCHEMA, ACCEPT_KEYWORDS, REJECT_KEYWORDS, ACCEPT_REGIONS,
  parseAmountAud, normalizeRecord, previewKeep, buildBatch, toCSV, clip,
};
if (typeof module !== "undefined" && module.exports) {
  module.exports = OFNMapping;
}
if (typeof globalThis !== "undefined") {
  globalThis.OFNMapping = OFNMapping;
}
