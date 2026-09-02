// OFN buy.nsw Harvester — content script.
//
// The live buy.nsw DOM is behind a WAF the agent cannot see, so extraction
// is heuristic by design and every selector degrades to "anchor with
// /notices/ in href" — the one URL pattern verified from research. The
// DEBUG_DUMP mode exists to lock selectors against the real DOM later:
// it reports what the heuristics see, never guesses silently.
//
// No network calls of any kind. Reads only the page the human is on.

"use strict";

const NOTICE_HREF = /\/notices\//i;
const NEXT_PAGE_TEXT = /^(next|>|»|older)\s*$/i;
const MAX_CARD_CLIMB = 7;
const AUTO_MAX_PAGES = 10;
const AUTO_STORAGE_KEY = "ofn_buynsw_auto_pages";

function absolute(href) {
  try {
    return new URL(href, location.href).href.split("#")[0];
  } catch (e) {
    return "";
  }
}

function anchorToCard(anchor) {
  // Climb from the tender link to the nearest container that plausibly holds
  // the card's other fields: more text than the link alone, bounded depth.
  let node = anchor;
  const linkText = (anchor.innerText || "").trim();
  for (let i = 0; i < MAX_CARD_CLIMB && node && node !== document.body; i++) {
    node = node.parentElement;
    if (!node) break;
    const t = (node.innerText || "").trim();
    if (t.length > Math.max(linkText.length + 40, 90)) return node;
  }
  return anchor.parentElement || anchor;
}

// label:value extraction from free card text. Bounded and conservative:
// unknown labels are simply not extracted (the record still carries raw_text).
const FIELD_PATTERNS = [
  ["closing_at", /(?:closing|closes|close[sd]?)\s*(?:date|time)?\s*[:\-]?\s*([^\n|]{4,60})/i],
  ["amount_text", /(?:estimated\s+)?(?:value|worth|amount|estimate)\s*[:\-]?\s*([^\n|]{2,40})/i],
  ["buyer_name", /(?:buyer|agency|organisation|organization|issuer)\s*[:\-]?\s*([^\n|]{2,120})/i],
  ["location_text", /(?:location|region|site|place|suburb)\s*[:\-]?\s*([^\n|]{2,120})/i],
];

function extractFromCard(card, anchor) {
  const text = (card.innerText || "").replace(/\r/g, "");
  const out = {
    title: (anchor.getAttribute("aria-label") || anchor.innerText || "").trim(),
    detail_url: absolute(anchor.getAttribute("href") || ""),
    raw_text: text,
  };
  for (const [key, re] of FIELD_PATTERNS) {
    const m = text.match(re);
    if (m) out[key] = m[1].trim();
  }
  return out;
}

function extractRecords() {
  const seen = new Map();
  const anchors = Array.from(document.querySelectorAll("a[href]"));
  for (const anchor of anchors) {
    const href = anchor.getAttribute("href") || "";
    if (!NOTICE_HREF.test(href)) continue;
    const url = absolute(href);
    if (!url || seen.has(url)) continue;
    const card = anchorToCard(anchor);
    seen.set(url, extractFromCard(card, anchor));
  }
  const capturedAt = new Date().toISOString();
  const records = [];
  for (const raw of seen.values()) {
    const rec = window.OFNMapping.normalizeRecord(raw, capturedAt);
    if (rec) records.push(rec);
  }
  return records;
}

function findNextPage() {
  const rel = document.querySelector('a[rel="next"]');
  if (rel && rel.getAttribute("href")) return absolute(rel.getAttribute("href"));
  const here = new URL(location.href);
  const herePage = parseInt(here.searchParams.get("page") || "1", 10) || 1;
  for (const a of Array.from(document.querySelectorAll("a[href]"))) {
    const label = (a.getAttribute("aria-label") || a.innerText || "").trim();
    if (!NEXT_PAGE_TEXT.test(label)) continue;
    let next;
    try {
      next = new URL(a.getAttribute("href"), location.href);
    } catch (e) {
      continue;
    }
    const nextStart = parseInt(next.searchParams.get("startRow") || "0", 10);
    const nextPage = parseInt(next.searchParams.get("page") || "1", 10) || 1;
    if (nextStart > 0 || nextPage > herePage) return next.href.split("#")[0];
  }
  return null;
}

// --- message surface (popup / background are the only callers) ---

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || typeof msg.type !== "string") return;

  if (msg.type === "HARVEST_PAGE") {
    const records = extractRecords();
    const keep = records.filter(window.OFNMapping.previewKeep);
    sendResponse({
      ok: true,
      url: location.href,
      found: records.length,
      previewKept: keep.length,
      records: records,
    });
    return;
  }

  if (msg.type === "DEBUG_DUMP") {
    const records = extractRecords();
    sendResponse({
      ok: true,
      url: location.href,
      documentTitle: document.title,
      linkCount: records.length,
      nextPage: findNextPage(),
      sampleCards: records.slice(0, 5).map((r) => ({
        title: r.title,
        detail_url: r.detail_url,
        buyer_name: r.buyer_name,
        location_text: r.location_text,
        closing_at: r.closing_at,
        amount_aud: r.amount_aud,
        raw_text_head: (r.raw_text || "").slice(0, 400),
      })),
    });
    return;
  }

  if (msg.type === "AUTO_ADVANCE") {
    // Opt-in only. One page at a time, human-paced delay, hard cap. The
    // WAF sees the same human session either way; this only saves clicks.
    const next = findNextPage();
    if (!next) {
      sessionStorage.removeItem(AUTO_STORAGE_KEY);
      sendResponse({ ok: true, advanced: false, reason: "no next page" });
      return;
    }
    const pages = parseInt(sessionStorage.getItem(AUTO_STORAGE_KEY) || "0", 10);
    if (pages >= AUTO_MAX_PAGES) {
      sessionStorage.removeItem(AUTO_STORAGE_KEY);
      sendResponse({ ok: true, advanced: false, reason: "page cap reached" });
      return;
    }
    sendResponse({ ok: true, advanced: true, next: next });
    const delay = 5000 + Math.floor(Math.random() * 3000);
    setTimeout(() => {
      sessionStorage.setItem(AUTO_STORAGE_KEY, String(pages + 1));
      location.assign(next);
    }, delay);
    return;
  }
});
