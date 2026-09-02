// OFN buy.nsw Harvester — service worker.
//
// Keeps a session-scoped buffer of harvested records (deduped by
// detail_url/notice_uuid), builds the batch JSON that the Python ingest
// gate (ofn/agents/h1_buysw_dom.py) consumes, and saves it via the
// downloads API. No network egress: records never leave the machine
// except as a file the human chooses to save.

"use strict";

importScripts("mapping.js");

const BUFFER_KEY = "ofn_buynsw_buffer";

async function readBuffer() {
  const store = await chrome.storage.session.get(BUFFER_KEY);
  return Array.isArray(store[BUFFER_KEY]) ? store[BUFFER_KEY] : [];
}

async function writeBuffer(records) {
  await chrome.storage.session.set({ [BUFFER_KEY]: records });
  await updateBadge(records.length);
}

async function updateBadge(count) {
  try {
    await chrome.action.setBadgeText({ text: count > 0 ? String(count) : "" });
    await chrome.action.setBadgeBackgroundColor({ color: "#1a5fb4" });
  } catch (e) {
    // Badge is cosmetic; never fail a harvest because of it.
  }
}

async function mergeRecords(records, fromUrl) {
  const buffer = await readBuffer();
  const byKey = new Map(buffer.map((r) => [r.detail_url || r.notice_uuid, r]));
  let added = 0;
  for (const rec of records || []) {
    if (!rec || !rec.title || !rec.detail_url) continue;
    const key = rec.detail_url || rec.notice_uuid;
    if (!key || byKey.has(key)) continue;
    byKey.set(key, rec);
    added += 1;
  }
  const merged = Array.from(byKey.values());
  await writeBuffer(merged);
  return { added: added, total: merged.length, from: fromUrl || "" };
}

function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return (
    d.getUTCFullYear() +
    String(d.getUTCMonth() + 1).padStart(2, "0") +
    p(d.getUTCDate()) +
    "-" +
    p(d.getUTCHours()) +
    p(d.getUTCMinutes()) +
    p(d.getUTCSeconds())
  );
}

async function download(filename, mime, text) {
  const url =
    "data:" + mime + ";charset=utf-8," + encodeURIComponent(text);
  await chrome.downloads.download({
    url: url,
    filename: filename,
    saveAs: true,
  });
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      if (!msg || typeof msg.type !== "string") return;

      if (msg.type === "RECORDS") {
        sendResponse(await mergeRecords(msg.records, msg.url));
        return;
      }

      if (msg.type === "GET_BUFFER") {
        const buffer = await readBuffer();
        const kept = buffer.filter(OFNMapping.previewKeep);
        sendResponse({ total: buffer.length, previewKept: kept.length });
        return;
      }

      if (msg.type === "EXPORT_JSON") {
        const buffer = await readBuffer();
        if (!buffer.length) {
          sendResponse({ ok: false, error: "بافر خالی است" });
          return;
        }
        const batch = OFNMapping.buildBatch(
          buffer, msg.url || "", new Date().toISOString());
        await download(
          "buynsw-harvest-" + stamp() + ".json",
          "application/json",
          JSON.stringify(batch, null, 2));
        sendResponse({ ok: true, records: batch.records.length });
        return;
      }

      if (msg.type === "EXPORT_CSV") {
        const buffer = await readBuffer();
        if (!buffer.length) {
          sendResponse({ ok: false, error: "بافر خالی است" });
          return;
        }
        await download(
          "buynsw-harvest-" + stamp() + ".csv",
          "text/csv",
          OFNMapping.toCSV(buffer));
        sendResponse({ ok: true, records: buffer.length });
        return;
      }

      if (msg.type === "DOWNLOAD_DEBUG") {
        await download(
          "buynsw-debug-" + stamp() + ".json",
          "application/json",
          JSON.stringify(msg.data || {}, null, 2));
        sendResponse({ ok: true });
        return;
      }

      if (msg.type === "CLEAR") {
        await writeBuffer([]);
        sendResponse({ ok: true });
        return;
      }
    } catch (e) {
      try {
        sendResponse({ ok: false, error: String(e && e.message || e) });
      } catch (_) {
        // Listener already answered; nothing more to do.
      }
    }
  })();
  return true; // async sendResponse
});

chrome.runtime.onInstalled.addListener(() => updateBadge(0));
chrome.runtime.onStartup.addListener(() => updateBadge(0));
