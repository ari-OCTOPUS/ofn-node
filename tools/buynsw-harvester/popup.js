// buy.nsw Harvester — popup controller for the recovered pack's protocol
// (SCRAPE_PAGE / START_AUTO / STOP_AUTO / DOM_DUMP to the content script;
//  ADD_RECORDS / GET_COUNT / DOWNLOAD / CLEAR / SAVE_DEBUG / POST_ALL to
//  the service worker). State lives in the worker's storage; this is thin.

"use strict";

const statusEl = document.getElementById("status");
const CFG_KEY = "ofn_cfg";

function setStatus(text) {
  statusEl.textContent = text;
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) {
    setStatus("تب فعلی پیدا نشد.");
    return null;
  }
  if (!/^https:\/\/([a-z0-9-]+\.)?buy\.nsw\.gov\.au\//.test(tab.url || "")) {
    setStatus("این ابزار فقط روی صفحات buy.nsw.gov.au کار می‌کند.");
    return null;
  }
  return tab;
}

function sendToTab(tabId, message) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, message, (resp) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
        return;
      }
      resolve(resp || { ok: false, error: "پاسخی نرسید" });
    });
  });
}

function sendToWorker(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, (resp) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
        return;
      }
      resolve(resp || { ok: false, error: "پاسخی نرسید" });
    });
  });
}

async function refreshCount() {
  const resp = await sendToWorker({ type: "GET_COUNT" });
  if (resp && typeof resp.total === "number") {
    setStatus("بافر: " + resp.total + " رکورد");
  }
}

async function scrapeOnce() {
  const tab = await activeTab();
  if (!tab) return;
  setStatus("در حال خواندن صفحه…");
  const resp = await sendToTab(tab.id, { type: "SCRAPE_PAGE" });
  if (!resp || resp.error) {
    setStatus("خطا در خواندن صفحه: " + ((resp && resp.error) || "?"));
    return;
  }
  const records = (resp && resp.records) || [];
  if (!records.length) {
    setStatus(
      "رکوردی پیدا نشد. اگر باید باشد، «دامپ دیباگ DOM» را بزن و فایلش را بفرست.");
    return;
  }
  const merge = await sendToWorker({
    type: "ADD_RECORDS", records: records,
  });
  const hint = records.filter((r) => r._painting_hint).length;
  setStatus(
    "حالت: " + (resp.mode || "?") + " | در این صفحه: " + records.length +
    " | پیش‌نمایش نقاشی: " + hint +
    "\nجدید: " + ((merge && merge.added) || 0) +
    " | کل بافر: " + ((merge && merge.total) || 0));
}

async function startAuto() {
  const tab = await activeTab();
  if (!tab) return;
  const maxPages = Math.max(1, Math.min(40,
    parseInt(document.getElementById("maxPages").value || "15", 10) || 15));
  const resp = await sendToTab(tab.id, { type: "START_AUTO", maxPages });
  setStatus(resp && resp.ok
    ? "برداشت خودکار شروع شد (حداکثر " + maxPages + " صفحه، مکث انسانی)."
    : "خطا: " + ((resp && resp.error) || "?"));
}

async function stopAuto() {
  const tab = await activeTab();
  if (!tab) return;
  await sendToTab(tab.id, { type: "STOP_AUTO" });
  setStatus("برداشت خودکار متوقف شد.");
}

async function domDump() {
  const tab = await activeTab();
  if (!tab) return;
  setStatus("در حال دامپ…");
  const resp = await sendToTab(tab.id, { type: "DOM_DUMP" });
  if (!resp || resp.error) {
    setStatus("خطا در دامپ: " + ((resp && resp.error) || "?"));
    return;
  }
  await sendToWorker({ type: "SAVE_DEBUG", data: resp });
  setStatus(
    "دامپ ذخیره شد — linkCount: " + (resp.linkCount ?? "?") +
    " | nextPage: " + (resp.nextPage || "—"));
}

async function download(kind) {
  const resp = await sendToWorker({ type: "DOWNLOAD", kind: kind });
  if (resp && typeof resp.n === "number" && resp.n > 0) {
    setStatus("خروجی " + kind.toUpperCase() + " ذخیره شد (" + resp.n + " رکورد).");
  } else {
    setStatus("بافر خالی است — اول «برداشت» بزن.");
  }
}

async function loadCfg() {
  const o = await chrome.storage.local.get(CFG_KEY);
  const cfg = o[CFG_KEY] || {};
  document.getElementById("endpoint").value = cfg.endpoint || "";
  document.getElementById("token").value = cfg.token || "";
  document.getElementById("autoPost").checked = !!cfg.autoPost;
}

async function saveCfg() {
  const cfg = {
    endpoint: document.getElementById("endpoint").value.trim(),
    token: document.getElementById("token").value.trim(),
    autoPost: document.getElementById("autoPost").checked,
  };
  await chrome.storage.local.set({ [CFG_KEY]: cfg });
  setStatus(cfg.endpoint
    ? "تنظیمات ذخیره شد." + (cfg.autoPost ? " (ارسال خودکار روشن)" : "")
    : "تنظیمات پاک شد (خاموش).");
}

async function postAll() {
  const resp = await sendToWorker({ type: "POST_ALL" });
  setStatus(resp && resp.ok
    ? "به نود ارسال شد."
    : "ارسال نشد — endpoint تنظیم شده؟");
}

document.getElementById("scrape").addEventListener("click", scrapeOnce);
document.getElementById("startAuto").addEventListener("click", startAuto);
document.getElementById("stopAuto").addEventListener("click", stopAuto);
document.getElementById("debug").addEventListener("click", domDump);
document.getElementById("exportJson").addEventListener("click", () => download("json"));
document.getElementById("exportCsv").addEventListener("click", () => download("csv"));
document.getElementById("clear").addEventListener("click", async () => {
  await sendToWorker({ type: "CLEAR" });
  setStatus("بافر پاک شد.");
});
document.getElementById("saveCfg").addEventListener("click", saveCfg);
document.getElementById("postAll").addEventListener("click", postAll);

refreshCount();
loadCfg();
