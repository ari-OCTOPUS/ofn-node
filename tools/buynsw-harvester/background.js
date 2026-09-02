// background.js — service worker: dedup store, download, optional POST to OFN node.
importScripts("mapping.js");

const STORE_KEY = "harvest_store";       // { [tender_id]: record }
const CFG_KEY = "ofn_cfg";               // { endpoint, token, autoPost }

async function getStore() {
  const o = await chrome.storage.local.get(STORE_KEY);
  return o[STORE_KEY] || {};
}
async function setStore(s) {
  await chrome.storage.local.set({ [STORE_KEY]: s });
}

async function addRecords(records) {
  const store = await getStore();
  let added = 0;
  for (const r of records) {
    const id = r.tender_id;
    if (!store[id]) added++;
    // keep richer version (detail pages overwrite thin results-page rows)
    store[id] = mergeRecord(store[id], r);
  }
  await setStore(store);
  const cfg = (await chrome.storage.local.get(CFG_KEY))[CFG_KEY] || {};
  if (cfg.autoPost && cfg.endpoint) await postRecords(records, cfg);
  updateBadge(Object.keys(store).length);
  return { added, total: Object.keys(store).length };
}

function mergeRecord(a, b) {
  if (!a) return b;
  const out = { ...a };
  for (const k of Object.keys(b)) {
    const v = b[k];
    if (v !== "" && v !== null && v !== undefined) {
      if (out[k] === "" || out[k] === null || out[k] === undefined) out[k] = v;
      else if (k === "raw") out[k] = { ...out[k], ...v };
      else if (k.startsWith("_") || k === "supplier_name" || k === "contact_email") out[k] = v || out[k];
    }
  }
  return out;
}

async function postRecords(records, cfg) {
  try {
    const res = await fetch(cfg.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(cfg.token ? { Authorization: `Bearer ${cfg.token}` } : {}),
      },
      body: JSON.stringify({ source: "buysw_web", records }),
    });
    return res.ok;
  } catch (e) {
    console.warn("OFN post failed", e);
    return false;
  }
}

function updateBadge(n) {
  chrome.action.setBadgeText({ text: n ? String(n) : "" });
  chrome.action.setBadgeBackgroundColor({ color: "#0b6" });
}

function toCsv(records) {
  const cols = [
    "tender_id", "kind", "title", "buyer_name", "supplier_name", "location",
    "category", "closing_at", "published_at", "amount_text",
    "contact_email", "contact_phone", "abn", "_painting_hint",
    "_in_service_area", "source_url",
  ];
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  return [cols.join(",")]
    .concat(records.map((r) => cols.map((c) => esc(r[c])).join(",")))
    .join("\n");
}

async function download(kind) {
  const store = await getStore();
  const records = Object.values(store);
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  let dataUrl, filename;
  if (kind === "csv") {
    dataUrl = "data:text/csv;charset=utf-8," + encodeURIComponent(toCsv(records));
    filename = `buysw-leads-${stamp}.csv`;
  } else {
    dataUrl = "data:application/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify({ source: "buysw_web", count: records.length, records }, null, 2));
    filename = `buysw-leads-${stamp}.json`;
  }
  await chrome.downloads.download({ url: dataUrl, filename, saveAs: true });
  return records.length;
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    if (msg.type === "ADD_RECORDS") sendResponse(await addRecords(msg.records || []));
    else if (msg.type === "GET_COUNT") sendResponse({ total: Object.keys(await getStore()).length });
    else if (msg.type === "DOWNLOAD") sendResponse({ n: await download(msg.kind) });
    else if (msg.type === "CLEAR") { await setStore({}); updateBadge(0); sendResponse({ ok: true }); }
    else if (msg.type === "POST_ALL") {
      const cfg = (await chrome.storage.local.get(CFG_KEY))[CFG_KEY] || {};
      const ok = cfg.endpoint ? await postRecords(Object.values(await getStore()), cfg) : false;
      sendResponse({ ok });
    }
    else if (msg.type === "AUTO_DONE") sendResponse({ ok: true });
    // Selector-locking loop: persist the popup's DOM_DUMP so it can be sent
    // to the agent and tuned against the real page structure.
    else if (msg.type === "SAVE_DEBUG") {
      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
      const dataUrl = "data:application/json;charset=utf-8," +
        encodeURIComponent(JSON.stringify(msg.data || {}, null, 2));
      await chrome.downloads.download({
        url: dataUrl, filename: `buysw-debug-${stamp}.json`, saveAs: true,
      });
      sendResponse({ ok: true });
    }
    else sendResponse({ ok: false });
  })();
  return true;
});
