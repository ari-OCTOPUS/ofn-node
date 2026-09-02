// OFN buy.nsw Harvester — popup controller. Thin: all state lives in the
// service worker's session buffer; this only routes clicks to messages.

"use strict";

const statusEl = document.getElementById("status");

function setStatus(text) {
  statusEl.textContent = text;
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({
    active: true, currentWindow: true,
  });
  if (!tab || !tab.id) {
    setStatus("تب فعلی پیدا نشد.");
    return null;
  }
  if (!/^https:\/\/(www\.)?buy\.nsw\.gov\.au\//.test(tab.url || "")) {
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
  const resp = await sendToWorker({ type: "GET_BUFFER" });
  if (resp && typeof resp.total === "number") {
    setStatus(
      "بافر: " + resp.total + " رکورد" +
      " (پیش‌نمایش نقاشی: " + resp.previewKept + ")");
  }
}

async function harvestOnce() {
  const tab = await activeTab();
  if (!tab) return;
  setStatus("در حال خواندن صفحه…");
  const resp = await sendToTab(tab.id, { type: "HARVEST_PAGE" });
  if (!resp || !resp.ok) {
    setStatus("خطا در خواندن صفحه: " + ((resp && resp.error) || "?"));
    return;
  }
  if (!resp.found) {
    setStatus(
      "هیچ لینک /notices/ در این صفحه پیدا نشد. " +
      "اگر فکر می‌کنید باید باشد، «دامپ دیباگ DOM» را بزنید و خروجی را بفرستید.");
    return;
  }
  const merge = await sendToWorker({
    type: "RECORDS", records: resp.records, url: resp.url,
  });
  setStatus(
    "در این صفحه: " + resp.found + " | پیش‌نمایش نقاشی: " + resp.previewKept +
    "\nجدید در بافر: " + (merge && merge.added) +
    " | کل بافر: " + (merge && merge.total));
  if (document.getElementById("auto").checked) {
    const adv = await sendToTab(tab.id, { type: "AUTO_ADVANCE" });
    if (adv && adv.advanced) {
      setStatus("صفحهٔ بعدی تا چند ثانیه… (" + (adv.next || "") + ")");
    } else {
      setStatus((statusEl.textContent || "") +
        "\nصفحه‌بندی تمام شد: " + ((adv && adv.reason) || "?"));
    }
  }
}

async function exportJson() {
  const resp = await sendToWorker({ type: "EXPORT_JSON" });
  setStatus(resp && resp.ok
    ? "بچ JSON ذخیره شد (" + resp.records + " رکورد). آن را به ingest بدهید."
    : "خطا: " + ((resp && resp.error) || "?"));
}

async function exportCsv() {
  const resp = await sendToWorker({ type: "EXPORT_CSV" });
  setStatus(resp && resp.ok
    ? "CSV ذخیره شد (" + resp.records + " رکورد)."
    : "خطا: " + ((resp && resp.error) || "?"));
}

async function debugDump() {
  const tab = await activeTab();
  if (!tab) return;
  setStatus("در حال دامپ…");
  const resp = await sendToTab(tab.id, { type: "DEBUG_DUMP" });
  if (!resp || !resp.ok) {
    setStatus("خطا در دامپ: " + ((resp && resp.error) || "?"));
    return;
  }
  await sendToWorker({ type: "DOWNLOAD_DEBUG", data: resp });
  setStatus(
    "دامپ ذخیره شد — linkCount: " + resp.linkCount +
    " | nextPage: " + (resp.nextPage || "—"));
}

async function clearBuffer() {
  await sendToWorker({ type: "CLEAR" });
  setStatus("بافر پاک شد.");
}

document.getElementById("harvest").addEventListener("click", harvestOnce);
document.getElementById("exportJson").addEventListener("click", exportJson);
document.getElementById("exportCsv").addEventListener("click", exportCsv);
document.getElementById("debug").addEventListener("click", debugDump);
document.getElementById("clear").addEventListener("click", clearBuffer);

refreshCount();
