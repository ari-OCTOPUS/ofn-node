// popup.js — UI glue.
const $ = (id) => document.getElementById(id);
const status = (m) => { $("status").textContent = m; };

async function activeTab() {
  const [t] = await chrome.tabs.query({ active: true, currentWindow: true });
  return t;
}
async function toContent(msg) {
  const t = await activeTab();
  if (!t || !/buy\.nsw\.gov\.au/.test(t.url || "")) {
    status("⚠️ اول یک صفحه‌ی buy.nsw را باز کن.");
    return null;
  }
  return chrome.tabs.sendMessage(t.id, msg).catch(() => {
    status("⚠️ صفحه را رفرش کن تا اکستنشن لود شود.");
    return null;
  });
}

async function refreshCount() {
  const r = await chrome.runtime.sendMessage({ type: "GET_COUNT" });
  $("count").textContent = r ? r.total : 0;
}

$("scrape").onclick = async () => {
  const res = await toContent({ type: "SCRAPE_PAGE" });
  if (!res) return;
  const r = await chrome.runtime.sendMessage({ type: "ADD_RECORDS", records: res.records, mode: res.mode });
  status(`+${r.added} تازه (${res.mode}) · مجموع ${r.total}`);
  refreshCount();
};

$("auto").onclick = async () => {
  const res = await toContent({ type: "START_AUTO", maxPages: 40 });
  if (res && res.ok) status("Auto شروع شد — پنجره را باز بگذار.");
};
$("stop").onclick = async () => { await toContent({ type: "STOP_AUTO" }); status("Auto متوقف شد."); };

$("dljson").onclick = async () => { const r = await chrome.runtime.sendMessage({ type: "DOWNLOAD", kind: "json" }); status(`دانلود ${r.n} رکورد.`); };
$("dlcsv").onclick = async () => { const r = await chrome.runtime.sendMessage({ type: "DOWNLOAD", kind: "csv" }); status(`دانلود ${r.n} رکورد.`); };
$("post").onclick = async () => { const r = await chrome.runtime.sendMessage({ type: "POST_ALL" }); status(r.ok ? "به نود ارسال شد ✓" : "ارسال ناموفق — تنظیمات را چک کن."); };
$("clear").onclick = async () => { await chrome.runtime.sendMessage({ type: "CLEAR" }); status("انبار پاک شد."); refreshCount(); };

$("savecfg").onclick = async () => {
  await chrome.storage.local.set({ ofn_cfg: {
    endpoint: $("endpoint").value.trim(),
    token: $("token").value.trim(),
    autoPost: $("autopost").checked,
  }});
  status("تنظیمات ذخیره شد.");
};

$("dump").onclick = async () => {
  const res = await toContent({ type: "DOM_DUMP" });
  if (res) $("dumpout").textContent = JSON.stringify(res, null, 2);
};

(async () => {
  const cfg = (await chrome.storage.local.get("ofn_cfg")).ofn_cfg || {};
  $("endpoint").value = cfg.endpoint || "";
  $("token").value = cfg.token || "";
  $("autopost").checked = !!cfg.autoPost;
  refreshCount();
})();
