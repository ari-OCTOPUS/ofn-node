// ============================================================
// LunarCrush API v4 — Multi-Asset Social Sentiment Scraper · PRO
// Two-phase: Discovery (lists) → Detail (per-asset endpoints)
// Plan detection + Capability Map + Skip Dead
// ============================================================

const SNAPSHOT_KEY = "lc_snapshots_v1";
const CAPABILITIES_KEY = "lc_capabilities_v1";
const MAX_SNAPSHOTS = 10;

function getBaseUrl() { return (document.getElementById("baseUrl")?.value || "http://localhost:8788/api4").trim(); }
function getDelayMs() { return parseInt(document.getElementById("delayMs")?.value || "600", 10); }

// ============================================================
// ENDPOINT_REGISTRY — every LunarCrush v4 endpoint
// Phase 1: Lists (no params).  Phase 2: Per-entity detail.
// ============================================================
const ENDPOINT_REGISTRY = {
  // ── Lists (Phase 1) ──
  coinsList:     { kind:"list", section:"coins",      path:"/public/coins/list/v2?sort=market_cap_rank&limit=1000",   essential:true  },
  topicsList:    { kind:"list", section:"topics",     path:"/public/topics/list/v1",                                   essential:true  },
  categoriesList:{ kind:"list", section:"categories", path:"/public/categories/list/v1",                               essential:true  },
  creatorsList:  { kind:"list", section:"creators",   path:"/public/creators/list/v1",                                 essential:true  },
  stocksList:    { kind:"list", section:"stocks",     path:"/public/stocks/list/v2?sort=market_cap_rank&limit=500",    essential:false },
  nftsList:      { kind:"list", section:"nfts",       path:"/public/nfts/list/v2?sort=market_cap_rank&limit=200",      essential:false },
  systemChanges: { kind:"list", section:"system",     path:"/public/system/changes",                                   essential:false },

  // ── Per-Coin (Phase 2) ──
  coinDetail:   { kind:"coin", section:"coins", path:"/public/coins/{id}/v1",                                          essential:true  },
  coinTS:       { kind:"coin", section:"coins", path:"/public/coins/{id}/time-series/v2?bucket={bucket}&interval={interval}", essential:true },
  coinMeta:     { kind:"coin", section:"coins", path:"/public/coins/{id}/meta/v1",  optional:"fetchMeta",              essential:false },

  // ── Per-Topic (Phase 2) ──
  topicDetail:  { kind:"topic", section:"topics", path:"/public/topic/{topic}/v1",                                     essential:true  },
  topicTS:      { kind:"topic", section:"topics", path:"/public/topic/{topic}/time-series/v2?bucket={bucket}",         essential:true  },
  topicWhatsup: { kind:"topic", section:"topics", path:"/public/topic/{topic}/whatsup/v1",  optional:"fetchWhatsup",   essential:false },
  topicPosts:   { kind:"topic", section:"topics", path:"/public/topic/{topic}/posts/v1",    optional:"fetchExtras",    essential:false },
  topicNews:    { kind:"topic", section:"topics", path:"/public/topic/{topic}/news/v1",     optional:"fetchExtras",    essential:false },
  topicCreators:{ kind:"topic", section:"topics", path:"/public/topic/{topic}/creators/v1", optional:"fetchExtras",    essential:false },

  // ── Per-Category (Phase 2) ──
  catDetail:    { kind:"category", section:"categories", path:"/public/category/{cat}/v1",                              essential:true  },
  catTopics:    { kind:"category", section:"categories", path:"/public/category/{cat}/topics/v1",                       essential:false },
  catTS:        { kind:"category", section:"categories", path:"/public/category/{cat}/time-series/v1?bucket={bucket}",  essential:true  },
  catPosts:     { kind:"category", section:"categories", path:"/public/category/{cat}/posts/v1",  optional:"fetchExtras", essential:false },
  catNews:      { kind:"category", section:"categories", path:"/public/category/{cat}/news/v1",   optional:"fetchExtras", essential:false },
  catCreators:  { kind:"category", section:"categories", path:"/public/category/{cat}/creators/v1", optional:"fetchExtras", essential:false },

  // ── Per-Creator (Phase 2) ──
  creatorDetail:{ kind:"creator", section:"creators", path:"/public/creator/{network}/{id}/v1",                          essential:true  },
  creatorTS:    { kind:"creator", section:"creators", path:"/public/creator/{network}/{id}/time-series/v1?bucket={bucket}", essential:true  },
  creatorPosts: { kind:"creator", section:"creators", path:"/public/creator/{network}/{id}/posts/v1",  optional:"fetchExtras", essential:false },

  // ── Per-Stock (Phase 2) ──
  stockDetail:  { kind:"stock", section:"stocks", path:"/public/stocks/{id}/v1",                                         essential:false },
  stockTS:      { kind:"stock", section:"stocks", path:"/public/stocks/{id}/time-series/v2?bucket={bucket}&interval={interval}", essential:false },

  // ── Per-NFT (Phase 2) ──
  nftDetail:    { kind:"nft", section:"nfts", path:"/public/nfts/{id}/v1",                                               essential:false },
  nftTS:        { kind:"nft", section:"nfts", path:"/public/nfts/{id}/time-series/v2?bucket={bucket}",                   essential:false },
};

// ============================================================
// State
// ============================================================
let allData = emptyData();
let totalRequests = 0, doneRequests = 0;
let abortFlag = false, countdownTimer = null;
const chartInstances = {};
let activeAssetId = { coin: null, topic: null, category: null, creator: null, stock: null, nft: null };

function emptyData() {
  return {
    meta: { fetchedAt: null, totalRequests: 0, errors: [], unavailable: [], config: null },
    lists: { coins: [], topics: [], categories: [], creators: [], stocks: [], nfts: [], system_changes: [] },
    coins: {},      // keyed by symbol or id
    topics: {},     // keyed by topic slug
    categories: {}, // keyed by category slug
    creators: {},   // keyed by `${network}::${id}`
    stocks: {},
    nfts: {},
  };
}

// ============================================================
// API — fetch with retry, 429 handling, cache
// ============================================================
const API = (() => {
  const cache = new Map();
  function clearCache() { cache.clear(); }

  async function call(path) {
    if (cache.has(path)) return { rows: cache.get(path), cached: true };
    const token = document.getElementById("apiKey").value.trim();
    if (!token) throw new Error("API Key وارد نشده!");
    if (abortFlag) throw new Error("ABORTED");

    const url = getBaseUrl() + path;
    for (let attempt = 1; attempt <= 3; attempt++) {
      if (abortFlag) throw new Error("ABORTED");
      try {
        const res = await fetch(url, { headers: { Authorization: "Bearer " + token, Accept: "application/json" } });

        if (res.status === 429) {
          const retryAfter = parseInt(res.headers.get("Retry-After") || "") || (10 * attempt);
          UI.setStatus(`⏳ Rate limit — ${retryAfter}s صبر...`);
          await sleepCountdown(retryAfter);
          continue;
        }
        if (res.status === 401) { const e = new Error("API Key نامعتبر (401)"); e.code = 401; throw e; }
        if (res.status === 403) { const e = new Error("403 Forbidden — endpoint در پلن شما نیست"); e.code = 403; throw e; }
        if (res.status === 404) { const e = new Error("404 Not Found"); e.code = 404; throw e; }
        if (res.status === 402) { const e = new Error("402 Payment Required — نیاز به ارتقای پلن"); e.code = 402; throw e; }
        if (!res.ok) {
          const body = await res.text().catch(() => res.statusText);
          throw new Error(`HTTP ${res.status}: ${body.slice(0, 120)}`);
        }

        const json = await res.json();
        cache.set(path, json);
        allData.meta.totalRequests++;
        doneRequests++;
        UI.setProgress(Math.min(Math.round((doneRequests / totalRequests) * 100), 100));
        return { rows: json, cached: false };
      } catch (e) {
        if (e.message === "ABORTED" || [401,402,403,404].includes(e.code)) throw e;
        if (attempt === 3) throw e;
        await sleep(2000);
      }
    }
    return { rows: null, cached: false };
  }
  return { call, clearCache };
})();

// ============================================================
// CapabilityManager — track per-endpoint-template results
// ============================================================
const CapabilityManager = {
  get() {
    try { return JSON.parse(localStorage.getItem(CAPABILITIES_KEY) || '{"working":{},"dead":{},"recordedAt":null}'); }
    catch { return { working: {}, dead: {}, recordedAt: null }; }
  },
  set(m) { localStorage.setItem(CAPABILITIES_KEY, JSON.stringify(m)); },
  reset() {
    localStorage.removeItem(CAPABILITIES_KEY);
    UI.log("Capability map پاک شد", "warn");
    renderTierDisplay();
    renderFetchSummary();
  },
  record(templateKey, success) {
    const m = this.get();
    if (success) { m.working[templateKey] = Date.now(); delete m.dead[templateKey]; }
    else { m.dead[templateKey] = Date.now(); delete m.working[templateKey]; }
    m.recordedAt = new Date().toISOString();
    this.set(m);
  },
  isDead(k)    { return !!this.get().dead[k]; },
  isWorking(k) { return !!this.get().working[k]; },

  detectTier() {
    const w = this.get().working;
    const wkeys = Object.keys(w);
    if (!wkeys.length) return { tier: "Unknown", color: "neutral", note: "هنوز fetch نشده" };

    const hasLists = w.coinsList || w.topicsList;
    const hasCoinTS = w.coinTS;
    const hasTopicTS = w.topicTS;
    const hasMeta = w.coinMeta;
    const hasPosts = w.topicPosts || w.catPosts || w.creatorPosts;
    const hasNews = w.topicNews || w.catNews;
    const hasNFT = w.nftsList || w.nftDetail;
    const hasStocks = w.stocksList || w.stockTS;
    const hasWhatsup = w.topicWhatsup;
    const hasCreator = w.creatorDetail;

    // Tier heuristic based on what works
    if (hasNFT && hasStocks && hasPosts && hasNews && hasMeta && hasWhatsup && hasCreator) {
      return { tier: "Founder/Enterprise", color: "bull", note: "همه چیز در دسترس" };
    }
    if (hasPosts && hasNews && (hasCoinTS || hasTopicTS) && hasMeta) {
      return { tier: "Builder", color: "cbull", note: "Posts/News/Meta + Time-Series" };
    }
    if ((hasCoinTS || hasTopicTS) && hasLists) {
      return { tier: "Individual", color: "neutral", note: "Time-series + lists" };
    }
    if (hasLists) {
      return { tier: "Free", color: "cbear", note: "فقط لیست‌های cached" };
    }
    return { tier: "Limited", color: "bear", note: "خیلی محدود" };
  },

  stats() {
    const m = this.get();
    return {
      working: Object.keys(m.working).length,
      dead: Object.keys(m.dead).length,
      recordedAt: m.recordedAt,
      tier: this.detectTier(),
    };
  },
};

// ============================================================
// StorageManager — snapshots
// ============================================================
const StorageManager = {
  list() { try { return JSON.parse(localStorage.getItem(SNAPSHOT_KEY) || "[]"); } catch { return []; } },
  save(name) {
    const snaps = this.list();
    const snap = {
      id: Date.now() + "_" + Math.random().toString(36).slice(2, 8),
      name: name || `Snap ${new Date().toLocaleString("en-GB")}`,
      savedAt: new Date().toISOString(),
      data: allData,
    };
    snaps.unshift(snap);
    while (snaps.length > MAX_SNAPSHOTS) snaps.pop();
    try { localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snaps)); return snap; }
    catch (e) { alert("ذخیره ناموفق: " + e.message); return null; }
  },
  delete(id) {
    localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(this.list().filter(s => s.id !== id)));
  },
  load(id) {
    const snap = this.list().find(s => s.id === id);
    if (!snap) return null;
    allData = snap.data;
    return snap;
  },
};

// ============================================================
// UI helpers
// ============================================================
const UI = {
  setStatus(m) { document.getElementById("statusText").textContent = m; },
  setProgress(pct) {
    document.getElementById("progressFill").style.width = pct + "%";
    document.getElementById("progressCount").textContent = `${doneRequests} / ${totalRequests}`;
  },
  log(msg, type = "info") {
    const box = document.getElementById("logBox");
    const ts = new Date().toLocaleTimeString("en", { hour12: false });
    const div = document.createElement("div");
    div.className = "log-" + type;
    div.textContent = `[${ts}] ${msg}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  },
  addErrorChip(label, msg, isUnavail = false) {
    const wrap = document.createElement("div");
    wrap.className = "tooltip-wrap";
    wrap.innerHTML = `<span class="chip ${isUnavail ? "chip-unavail" : "chip-err"}">${esc(label)} ${isUnavail ? "⊘" : "✕"}</span><span class="tip">${esc(msg)}</span>`;
    document.getElementById("errorChips").appendChild(wrap);
  },
  collapseSettings() {
    document.getElementById("settings-body").classList.add("collapsed");
    document.getElementById("toggleSettingsBtn").textContent = "▸";
  },
};

// ============================================================
// Helpers
// ============================================================
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
async function sleepCountdown(secs) {
  clearInterval(countdownTimer);
  const el = document.getElementById("countdownText");
  let remaining = secs;
  el.textContent = `⏱ ${remaining}s`;
  return new Promise(resolve => {
    countdownTimer = setInterval(() => {
      remaining--;
      if (remaining <= 0) { clearInterval(countdownTimer); el.textContent = ""; resolve(); }
      else el.textContent = `⏱ ${remaining}s`;
    }, 1000);
  });
}
async function waitBetween() { await sleep(getDelayMs()); }
function esc(s) { if (s == null) return "—"; return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function safeFloat(v, fb=null) { if (v==null||v==="") return fb; const n = parseFloat(String(v).replace(/,/g,"")); return isNaN(n)?fb:n; }
function fmtBig(n) { const v=safeFloat(n); if(v==null)return "—"; if(Math.abs(v)>=1e9)return(v/1e9).toFixed(2)+"B"; if(Math.abs(v)>=1e6)return(v/1e6).toFixed(2)+"M"; if(Math.abs(v)>=1e3)return(v/1e3).toFixed(1)+"K"; return v.toFixed(2); }
function fmtPrice(n) { const v=safeFloat(n); if(v==null)return "—"; if(Math.abs(v)>=1)return"$"+v.toLocaleString("en",{maximumFractionDigits:4}); return"$"+v.toFixed(8); }
function fmtPct(n) { const v=safeFloat(n); if(v==null)return "—"; return (v>=0?"+":"")+v.toFixed(2)+"%"; }
function dateStr() { return new Date().toISOString().slice(0,19).replace(/[T:]/g,"-"); }
function downloadFile(content, type, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([content], { type }));
  a.download = filename;
  a.click();
}

// ============================================================
// Path builder — substitute {placeholders}
// ============================================================
function buildPath(template, vars) {
  return template.replace(/\{(\w+)\}/g, (_, k) => encodeURIComponent(vars[k] ?? ""));
}

// ============================================================
// Token validation
// ============================================================
async function validateToken() {
  UI.setStatus("🔑 بررسی API Key...");
  try {
    await API.call("/public/coins/list/v1?limit=1");
    UI.log("API Key معتبر ✓", "ok");
    return true;
  } catch (e) {
    if (e.code === 401) { UI.setStatus("❌ API Key اشتباه"); return false; }
    throw e;
  }
}

// ============================================================
// Phase 1: Discovery — fetch all list endpoints
// ============================================================
async function fetchLists() {
  const config = readConfig();
  const skipDead = document.getElementById("skipDead")?.checked !== false;
  const listEndpoints = Object.entries(ENDPOINT_REGISTRY).filter(([_, ep]) => ep.kind === "list");

  for (const [tplKey, ep] of listEndpoints) {
    if (abortFlag) break;
    if (skipDead && CapabilityManager.isDead(tplKey)) {
      UI.log(`${tplKey}: skip (dead)`, "warn");
      continue;
    }
    // Honor scope limits — limit list pages by max relevant Top-N
    let path = ep.path;
    if (tplKey === "coinsList" && config.topCoins > 0) {
      path = path.replace(/limit=\d+/, `limit=${Math.min(1000, Math.max(100, config.topCoins * 2))}`);
    }

    UI.setStatus(`📋 List: ${tplKey}`);
    UI.log(`Fetching list: ${tplKey}`, "info");
    try {
      const { rows } = await API.call(path);
      const data = rows?.data || rows;
      allData.lists[ep.section] = Array.isArray(data) ? data : (data ? [data] : []);
      CapabilityManager.record(tplKey, allData.lists[ep.section].length > 0);
      UI.log(`${tplKey} → ${allData.lists[ep.section].length} item ✓`, "ok");
    } catch (e) {
      handleFetchError(tplKey, e);
    }
    await waitBetween();
  }
}

// ============================================================
// Phase 2: Detail fetching
// ============================================================
async function fetchDetails() {
  const skipDead = document.getElementById("skipDead")?.checked !== false;
  const opts = readOptionalFlags();
  const bucket = document.getElementById("bucket").value;
  const interval = document.getElementById("interval").value;
  const vars = { bucket, interval };

  // Auto-mode: iterate ALL items in each discovered list
  const allCoins = allData.lists.coins || [];
  for (let i = 0; i < allCoins.length; i++) {
    if (abortFlag) break;
    const c = allCoins[i];
    UI.setStatus(`💰 Coin ${i+1}/${allCoins.length}: ${c.symbol}`);
    await fetchEntityEndpoints("coin", { id: c.id, ...vars }, c.symbol || String(c.id), skipDead, opts);
  }

  const allTopics = allData.lists.topics || [];
  for (let i = 0; i < allTopics.length; i++) {
    if (abortFlag) break;
    const t = allTopics[i];
    UI.setStatus(`🗣 Topic ${i+1}/${allTopics.length}: ${t.topic}`);
    await fetchEntityEndpoints("topic", { topic: t.topic, ...vars }, t.topic, skipDead, opts);
  }

  const allCats = allData.lists.categories || [];
  for (let i = 0; i < allCats.length; i++) {
    if (abortFlag) break;
    const c = allCats[i];
    UI.setStatus(`📂 Category ${i+1}/${allCats.length}: ${c.category}`);
    await fetchEntityEndpoints("category", { cat: c.category, ...vars }, c.category, skipDead, opts);
  }

  const allCreators = allData.lists.creators || [];
  for (let i = 0; i < allCreators.length; i++) {
    if (abortFlag) break;
    const c = allCreators[i];
    const network = c.creator_network || "twitter";
    const id = c.creator_id?.split("::")[1] || c.creator_name;
    UI.setStatus(`👤 Creator ${i+1}/${allCreators.length}: ${c.creator_name}`);
    await fetchEntityEndpoints("creator", { network, id, ...vars }, `${network}::${id}`, skipDead, opts);
  }

  const allStocks = allData.lists.stocks || [];
  for (let i = 0; i < allStocks.length; i++) {
    if (abortFlag) break;
    const s = allStocks[i];
    UI.setStatus(`📈 Stock ${i+1}/${allStocks.length}: ${s.symbol}`);
    await fetchEntityEndpoints("stock", { id: s.id, ...vars }, s.symbol || String(s.id), skipDead, opts);
  }

  const allNfts = allData.lists.nfts || [];
  for (let i = 0; i < allNfts.length; i++) {
    if (abortFlag) break;
    const n = allNfts[i];
    UI.setStatus(`🖼 NFT ${i+1}/${allNfts.length}: ${n.name || n.id}`);
    await fetchEntityEndpoints("nft", { id: n.id, ...vars }, n.name || String(n.id), skipDead, opts);
  }
}

async function fetchEntityEndpoints(kind, vars, storageKey, skipDead, opts) {
  const sectionMap = { coin: "coins", topic: "topics", category: "categories", creator: "creators", stock: "stocks", nft: "nfts" };
  const section = sectionMap[kind];
  if (!allData[section][storageKey]) allData[section][storageKey] = {};

  const entries = Object.entries(ENDPOINT_REGISTRY).filter(([_, ep]) => ep.kind === kind);
  for (const [tplKey, ep] of entries) {
    if (abortFlag) break;
    if (ep.optional && !opts[ep.optional]) continue;
    if (skipDead && CapabilityManager.isDead(tplKey)) continue;

    const path = buildPath(ep.path, vars);
    try {
      const { rows } = await API.call(path);
      // Store under section[storageKey][tplKey]
      allData[section][storageKey][tplKey] = rows?.data ?? rows;
      const hasData = !!rows && (Array.isArray(rows.data) ? rows.data.length > 0 : !!rows.data);
      CapabilityManager.record(tplKey, hasData);
    } catch (e) {
      handleFetchError(`${tplKey}[${storageKey}]`, e, tplKey);
    }
    await waitBetween();
  }
}

function handleFetchError(label, e, templateKey = null) {
  if (e.message === "ABORTED") return;
  if (e.code === 403 || e.code === 404 || e.code === 402) {
    UI.log(`${label}: ${e.message.slice(0,80)} (skip)`, "warn");
    allData.meta.unavailable.push({ endpoint: label, msg: e.message });
    UI.addErrorChip(label, e.message, true);
    if (templateKey) CapabilityManager.record(templateKey, false);
  } else {
    UI.log(`${label}: ${e.message}`, "err");
    allData.meta.errors.push({ endpoint: label, msg: e.message });
    UI.addErrorChip(label, e.message, false);
  }
}

// ============================================================
// Fetch-count estimator
// ============================================================
function estimateRequestCount() {
  const c = readConfig();
  const opts = readOptionalFlags();
  const skipDead = document.getElementById("skipDead")?.checked !== false;
  const isDead = k => skipDead && CapabilityManager.isDead(k);

  let n = 0;
  // Lists
  Object.keys(ENDPOINT_REGISTRY).filter(k => ENDPOINT_REGISTRY[k].kind === "list").forEach(k => { if (!isDead(k)) n++; });
  // Per-kind detail counts
  const perKind = (kind, topN) => Object.entries(ENDPOINT_REGISTRY).filter(([_,e]) => e.kind === kind).reduce((acc, [k,e]) => {
    if (e.optional && !opts[e.optional]) return acc;
    if (isDead(k)) return acc;
    return acc + 1;
  }, 0) * topN;
  n += perKind("coin",     c.topCoins);
  n += perKind("topic",    c.topTopics);
  n += perKind("category", c.topCats);
  n += perKind("creator",  c.topCreators);
  n += perKind("stock",    c.topStocks);
  n += perKind("nft",      c.topNfts);
  return n + 1; // +1 token test
}

// Default caps when lists haven't been discovered yet (for estimator only).
// Actual fetch uses real list lengths discovered in Phase 1.
const DEFAULT_LIST_ESTIMATES = {
  coins: 100, topics: 50, categories: 30, creators: 50, stocks: 100, nfts: 50,
};

function readConfig() {
  // Use actual list sizes if Discovery already happened, else use defaults
  const lst = allData.lists || {};
  return {
    topCoins:     (lst.coins     && lst.coins.length)     || DEFAULT_LIST_ESTIMATES.coins,
    topTopics:    (lst.topics    && lst.topics.length)    || DEFAULT_LIST_ESTIMATES.topics,
    topCats:      (lst.categories&& lst.categories.length)|| DEFAULT_LIST_ESTIMATES.categories,
    topCreators:  (lst.creators  && lst.creators.length)  || DEFAULT_LIST_ESTIMATES.creators,
    topStocks:    (lst.stocks    && lst.stocks.length)    || DEFAULT_LIST_ESTIMATES.stocks,
    topNfts:      (lst.nfts      && lst.nfts.length)      || DEFAULT_LIST_ESTIMATES.nfts,
    interval:     document.getElementById("interval").value,
    bucket:       document.getElementById("bucket").value,
  };
}
function readOptionalFlags() {
  return {
    fetchExtras:  document.getElementById("fetchExtras")?.checked,
    fetchMeta:    document.getElementById("fetchMeta")?.checked,
    fetchWhatsup: document.getElementById("fetchWhatsup")?.checked,
  };
}

// ============================================================
// Main fetch flow
// ============================================================
async function startFetch() {
  const token = document.getElementById("apiKey").value.trim();
  if (!token) { alert("❌ API Key وارد کن!"); return; }
  abortFlag = false;
  doneRequests = 0;
  totalRequests = estimateRequestCount();
  document.getElementById("logBox").innerHTML = "";
  document.getElementById("errorChips").innerHTML = "";
  allData = emptyData();
  allData.meta.fetchedAt = new Date().toISOString();
  allData.meta.config = readConfig();
  API.clearCache();

  document.getElementById("fetchBtn").disabled = true;
  document.getElementById("discoverBtn").disabled = true;
  document.getElementById("stopBtn").classList.remove("hidden");
  document.getElementById("statusBox").classList.remove("hidden");
  document.getElementById("resultsCard").classList.add("hidden");
  UI.setProgress(0);
  UI.setStatus(`🚀 شروع... ${totalRequests} درخواست`);

  try {
    if (!await validateToken()) return;
    await waitBetween();
    await fetchLists();
    if (!abortFlag) await fetchDetails();

    if (!abortFlag) {
      const tier = CapabilityManager.detectTier();
      UI.setStatus(`✅ تمام شد — Plan: ${tier.tier} · ${allData.meta.errors.length} خطا · ${allData.meta.unavailable.length} غیر در دسترس`);
      UI.setProgress(100);
      document.getElementById("countdownText").textContent = "";
      renderResults();
      renderTierDisplay();
      renderFetchSummary();
      UI.collapseSettings();
    } else {
      UI.setStatus("⛔ متوقف شد.");
      renderTierDisplay();
      if (Object.keys(allData.coins).length || allData.lists.coins.length) renderResults();
    }
  } catch (e) {
    if (e.message !== "ABORTED") UI.setStatus("❌ خطا: " + e.message);
  } finally {
    document.getElementById("fetchBtn").disabled = false;
    document.getElementById("discoverBtn").disabled = false;
    document.getElementById("stopBtn").classList.add("hidden");
    clearInterval(countdownTimer);
  }
}

async function discoverOnly() {
  const token = document.getElementById("apiKey").value.trim();
  if (!token) { alert("❌ API Key وارد کن!"); return; }
  abortFlag = false;
  doneRequests = 0;
  totalRequests = 8;  // 7 lists + token test
  document.getElementById("logBox").innerHTML = "";
  document.getElementById("errorChips").innerHTML = "";
  allData = emptyData();
  allData.meta.fetchedAt = new Date().toISOString();
  API.clearCache();

  document.getElementById("fetchBtn").disabled = true;
  document.getElementById("discoverBtn").disabled = true;
  document.getElementById("stopBtn").classList.remove("hidden");
  document.getElementById("statusBox").classList.remove("hidden");
  UI.setProgress(0);

  try {
    if (!await validateToken()) return;
    await waitBetween();
    await fetchLists();
    if (!abortFlag) {
      const tier = CapabilityManager.detectTier();
      const total = (allData.lists.coins?.length || 0) + (allData.lists.topics?.length || 0)
                  + (allData.lists.categories?.length || 0) + (allData.lists.creators?.length || 0)
                  + (allData.lists.stocks?.length || 0) + (allData.lists.nfts?.length || 0);
      UI.setStatus(`✅ Discovery تمام شد — Plan: ${tier.tier} · ${total} item کشف شد`);
      UI.setProgress(100);
      renderResults();
      renderTierDisplay();
      renderAutoScopeDisplay();
      renderFetchSummary();
    }
  } catch (e) {
    UI.setStatus("❌ خطا: " + e.message);
  } finally {
    document.getElementById("fetchBtn").disabled = false;
    document.getElementById("discoverBtn").disabled = false;
    document.getElementById("stopBtn").classList.add("hidden");
  }
}

function stopFetch() { abortFlag = true; clearInterval(countdownTimer); UI.setStatus("⛔ در حال توقف..."); }

// ============================================================
// Render results
// ============================================================
function renderResults() {
  document.getElementById("resultsCard").classList.remove("hidden");
  const coinsCount = Object.keys(allData.coins).length;
  const topicsCount = Object.keys(allData.topics).length;
  const catsCount = Object.keys(allData.categories).length;
  const credsCount = Object.keys(allData.creators).length;
  const stocksCount = Object.keys(allData.stocks).length;
  const nftsCount = Object.keys(allData.nfts).length;

  const errHtml = allData.meta.errors.length ? `<div class="stat-chip error-chip">⚠️ خطا: <span>${allData.meta.errors.length}</span></div>` : "";
  const unavHtml = allData.meta.unavailable.length ? `<div class="stat-chip unavail-chip">⊘ غیر در دسترس: <span>${allData.meta.unavailable.length}</span></div>` : "";

  document.getElementById("resultStats").innerHTML = `
    <div class="stat-chip">Coins detail: <span>${coinsCount}</span></div>
    <div class="stat-chip">Topics detail: <span>${topicsCount}</span></div>
    <div class="stat-chip">Categories: <span>${catsCount}</span></div>
    <div class="stat-chip">Creators: <span>${credsCount}</span></div>
    <div class="stat-chip">Stocks: <span>${stocksCount}</span></div>
    <div class="stat-chip">NFTs: <span>${nftsCount}</span></div>
    <div class="stat-chip">Requests: <span>${allData.meta.totalRequests}</span></div>
    ${errHtml}${unavHtml}
  `;

  // Completeness
  const expected = totalRequests || 1;
  const ok = doneRequests - allData.meta.unavailable.length - allData.meta.errors.length;
  const pct = Math.max(0, Math.min(100, Math.round((ok / expected) * 100)));
  document.getElementById("completenessText").textContent = `${ok} / ${expected} (${pct}%)`;
  const fill = document.getElementById("completenessFill");
  fill.style.width = pct + "%";
  fill.className = pct >= 75 ? "fill-good" : pct >= 50 ? "fill-med" : "fill-bad";

  // Tabs
  const tabs = [];
  if (allData.lists.coins.length || coinsCount) tabs.push({ k: "coins", l: "💰 Coins" });
  if (allData.lists.topics.length || topicsCount) tabs.push({ k: "topics", l: "🗣 Topics" });
  if (allData.lists.categories.length || catsCount) tabs.push({ k: "categories", l: "📂 Categories" });
  if (allData.lists.creators.length || credsCount) tabs.push({ k: "creators", l: "👤 Creators" });
  if (allData.lists.stocks.length || stocksCount) tabs.push({ k: "stocks", l: "📈 Stocks" });
  if (allData.lists.nfts.length || nftsCount) tabs.push({ k: "nfts", l: "🖼 NFTs" });
  tabs.push({ k: "signal", l: "⚡ Signal" });
  tabs.push({ k: "charts", l: "📈 Charts" });

  document.getElementById("resultTabs").innerHTML = tabs.map((t, i) => `<button class="tab ${i===0?"active":""}" onclick="showTab('${t.k}')">${t.l}</button>`).join("");
  document.getElementById("tabsContent").innerHTML = tabs.map((t, i) => `<div id="tab-${t.k}" class="tab-content ${i===0?"":"hidden"}">${renderTabContent(t.k)}</div>`).join("");
}

function showTab(name) {
  document.querySelectorAll('#tabsContent .tab-content').forEach(el => el.classList.add("hidden"));
  const el = document.getElementById("tab-" + name); if (el) el.classList.remove("hidden");
  document.querySelectorAll('#resultTabs .tab').forEach(b => b.classList.remove("active"));
  const idx = Array.from(document.querySelectorAll('#resultTabs .tab')).find(b => b.textContent.toLowerCase().includes(name) || b.onclick.toString().includes(name));
  if (idx) idx.classList.add("active");
  if (name === "charts") setTimeout(renderCharts, 50);
}

function renderTabContent(kind) {
  switch (kind) {
    case "coins": return renderCoinsTab();
    case "topics": return renderTopicsTab();
    case "categories": return renderCategoriesTab();
    case "creators": return renderCreatorsTab();
    case "stocks": return renderStocksTab();
    case "nfts": return renderNftsTab();
    case "signal": return renderSignalTab();
    case "charts": return renderChartsTab();
  }
  return "";
}

// ── Coins tab ──
function renderCoinsTab() {
  const list = allData.lists.coins || [];
  if (!list.length) return `<div class="empty-tab">لیست coins موجود نیست.</div>`;
  const detailKeys = Object.keys(allData.coins);
  return `
    <div class="list-detail-grid">
      <div class="list-panel">
        <h3>📋 Top ${list.length} Coins (snapshot)</h3>
        <table class="lc-table">
          <thead><tr><th>#</th><th>Coin</th><th>Price</th><th>24h</th><th>Galaxy</th><th>AltRank</th><th>Sentiment</th><th>Social Dom</th></tr></thead>
          <tbody>${list.slice(0, 200).map(c => `
            <tr ${detailKeys.includes(c.symbol||String(c.id))?'class="has-detail" onclick="selectAsset(\'coin\',\''+esc(c.symbol||c.id)+'\')"':""}>
              <td>${c.market_cap_rank ?? "—"}</td>
              <td><strong>${esc(c.symbol)}</strong><br/><small class="muted">${esc(c.name)}</small></td>
              <td>${fmtPrice(c.price)}</td>
              <td class="${c.percent_change_24h>=0?"change-up":"change-down"}">${fmtPct(c.percent_change_24h)}</td>
              <td>${c.galaxy_score?.toFixed?.(1) ?? "—"}</td>
              <td>${c.alt_rank ?? "—"}</td>
              <td>${c.sentiment ?? "—"}%</td>
              <td>${c.social_dominance?.toFixed?.(2) ?? "—"}%</td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
      <div class="detail-panel" id="detailPanel-coin">
        ${renderEntityDetail("coin", activeAssetId.coin || detailKeys[0])}
      </div>
    </div>
  `;
}

// ── Topics tab ──
function renderTopicsTab() {
  const list = allData.lists.topics || [];
  if (!list.length) return `<div class="empty-tab">لیست topics موجود نیست.</div>`;
  const detailKeys = Object.keys(allData.topics);
  return `
    <div class="list-detail-grid">
      <div class="list-panel">
        <h3>📋 Top ${list.length} Topics</h3>
        <table class="lc-table">
          <thead><tr><th>#</th><th>Topic</th><th>Contributors</th><th>Posts</th><th>Interactions 24h</th></tr></thead>
          <tbody>${list.slice(0, 200).map(t => `
            <tr ${detailKeys.includes(t.topic)?'class="has-detail" onclick="selectAsset(\'topic\',\''+esc(t.topic)+'\')"':""}>
              <td>${t.topic_rank ?? "—"}</td>
              <td><strong>${esc(t.title || t.topic)}</strong></td>
              <td>${fmtBig(t.num_contributors)}</td>
              <td>${fmtBig(t.num_posts)}</td>
              <td>${fmtBig(t.interactions_24h)}</td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
      <div class="detail-panel" id="detailPanel-topic">
        ${renderEntityDetail("topic", activeAssetId.topic || detailKeys[0])}
      </div>
    </div>
  `;
}

function renderCategoriesTab() {
  const list = allData.lists.categories || [];
  if (!list.length) return `<div class="empty-tab">لیست categories موجود نیست.</div>`;
  const detailKeys = Object.keys(allData.categories);
  return `
    <div class="list-detail-grid">
      <div class="list-panel">
        <h3>📋 Top ${list.length} Categories</h3>
        <table class="lc-table">
          <thead><tr><th>#</th><th>Category</th><th>Contributors</th><th>Social Dom</th><th>Posts</th></tr></thead>
          <tbody>${list.slice(0, 200).map(c => `
            <tr ${detailKeys.includes(c.category)?'class="has-detail" onclick="selectAsset(\'category\',\''+esc(c.category)+'\')"':""}>
              <td>${c.category_rank ?? "—"}</td>
              <td><strong>${esc(c.title || c.category)}</strong></td>
              <td>${fmtBig(c.num_contributors)}</td>
              <td>${c.social_dominance?.toFixed?.(2) ?? "—"}%</td>
              <td>${fmtBig(c.num_posts)}</td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
      <div class="detail-panel" id="detailPanel-category">
        ${renderEntityDetail("category", activeAssetId.category || detailKeys[0])}
      </div>
    </div>
  `;
}

function renderCreatorsTab() {
  const list = allData.lists.creators || [];
  if (!list.length) return `<div class="empty-tab">لیست creators موجود نیست.</div>`;
  const detailKeys = Object.keys(allData.creators);
  return `
    <div class="list-detail-grid">
      <div class="list-panel">
        <h3>📋 Top ${list.length} Creators</h3>
        <table class="lc-table">
          <thead><tr><th>#</th><th>Creator</th><th>Network</th><th>Followers</th><th>Interactions 24h</th></tr></thead>
          <tbody>${list.slice(0, 200).map(c => {
            const id = (c.creator_id||"").split("::")[1] || c.creator_name;
            const key = `${c.creator_network||"twitter"}::${id}`;
            return `<tr ${detailKeys.includes(key)?'class="has-detail" onclick="selectAsset(\'creator\',\''+esc(key)+'\')"':""}>
              <td>${c.creator_rank ?? "—"}</td>
              <td><strong>${esc(c.creator_display_name || c.creator_name)}</strong><br/><small class="muted">@${esc(c.creator_name)}</small></td>
              <td>${esc(c.creator_network)}</td>
              <td>${fmtBig(c.creator_followers)}</td>
              <td>${fmtBig(c.interactions_24h)}</td>
            </tr>`;
          }).join("")}</tbody>
        </table>
      </div>
      <div class="detail-panel" id="detailPanel-creator">
        ${renderEntityDetail("creator", activeAssetId.creator || detailKeys[0])}
      </div>
    </div>
  `;
}

function renderStocksTab() {
  const list = allData.lists.stocks || [];
  if (!list.length) return `<div class="empty-tab">لیست stocks موجود نیست.</div>`;
  const detailKeys = Object.keys(allData.stocks);
  return `
    <div class="list-detail-grid">
      <div class="list-panel">
        <h3>📋 Top ${list.length} Stocks</h3>
        <table class="lc-table">
          <thead><tr><th>#</th><th>Stock</th><th>Price</th><th>24h</th><th>Galaxy</th><th>AltRank</th><th>Sentiment</th></tr></thead>
          <tbody>${list.slice(0, 200).map(s => `
            <tr ${detailKeys.includes(s.symbol||String(s.id))?'class="has-detail" onclick="selectAsset(\'stock\',\''+esc(s.symbol||s.id)+'\')"':""}>
              <td>${s.market_cap_rank ?? "—"}</td>
              <td><strong>${esc(s.symbol)}</strong><br/><small class="muted">${esc(s.name)}</small></td>
              <td>${fmtPrice(s.price)}</td>
              <td class="${s.percent_change_24h>=0?"change-up":"change-down"}">${fmtPct(s.percent_change_24h)}</td>
              <td>${s.galaxy_score?.toFixed?.(1) ?? "—"}</td>
              <td>${s.alt_rank ?? "—"}</td>
              <td>${s.sentiment ?? "—"}%</td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
      <div class="detail-panel" id="detailPanel-stock">
        ${renderEntityDetail("stock", activeAssetId.stock || detailKeys[0])}
      </div>
    </div>
  `;
}

function renderNftsTab() {
  const list = allData.lists.nfts || [];
  if (!list.length) return `<div class="empty-tab">لیست NFTs موجود نیست.</div>`;
  const detailKeys = Object.keys(allData.nfts);
  return `
    <div class="list-detail-grid">
      <div class="list-panel">
        <h3>📋 Top ${list.length} NFT collections</h3>
        <table class="lc-table">
          <thead><tr><th>#</th><th>NFT</th><th>Floor</th><th>Volume 24h</th><th>Social Dom</th></tr></thead>
          <tbody>${list.slice(0, 200).map(n => `
            <tr ${detailKeys.includes(n.name||String(n.id))?'class="has-detail" onclick="selectAsset(\'nft\',\''+esc(n.name||n.id)+'\')"':""}>
              <td>${n.market_cap_rank ?? "—"}</td>
              <td><strong>${esc(n.name)}</strong></td>
              <td>${fmtPrice(n.floor_price ?? n.lunar_floor_price)}</td>
              <td>${fmtBig(n.volume_24h)}</td>
              <td>${n.social_dominance?.toFixed?.(2) ?? "—"}%</td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
      <div class="detail-panel" id="detailPanel-nft">
        ${renderEntityDetail("nft", activeAssetId.nft || detailKeys[0])}
      </div>
    </div>
  `;
}

function selectAsset(kind, key) {
  activeAssetId[kind] = key;
  const panel = document.getElementById(`detailPanel-${kind}`);
  if (panel) panel.innerHTML = renderEntityDetail(kind, key);
}

function renderEntityDetail(kind, key) {
  const sectionMap = { coin: "coins", topic: "topics", category: "categories", creator: "creators", stock: "stocks", nft: "nfts" };
  const section = sectionMap[kind];
  if (!key) return `<div class="empty-tab">یک item از سمت چپ انتخاب کن</div>`;
  const detail = allData[section][key];
  if (!detail) return `<div class="empty-tab">داده‌ای برای ${esc(key)} نیست</div>`;

  let html = `<h3>${esc(key)}</h3>`;

  // Show all template responses available for this entity
  for (const [tplKey, tplData] of Object.entries(detail)) {
    const tpl = ENDPOINT_REGISTRY[tplKey];
    html += `<details class="entity-section" open><summary>${tplKey} ${tpl?.label || ""}</summary>`;
    if (Array.isArray(tplData)) {
      html += renderTimeSeriesTable(tplData);
    } else if (typeof tplData === "object" && tplData) {
      html += renderKVTable(tplData);
    } else {
      html += `<pre class="json-preview">${esc(JSON.stringify(tplData, null, 2))}</pre>`;
    }
    html += `</details>`;
  }
  return html;
}

function renderTimeSeriesTable(arr) {
  if (!arr.length) return `<em class="muted">خالی</em>`;
  const sample = arr[arr.length - 1];
  const cols = Object.keys(sample).slice(0, 12);
  return `<div class="ts-wrap"><table class="lc-table mini-table"><thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${
    arr.slice(-50).reverse().map(r => `<tr>${cols.map(c => `<td>${formatCellVal(c, r[c])}</td>`).join("")}</tr>`).join("")
  }</tbody></table></div>`;
}

function renderKVTable(obj) {
  return `<table class="lc-table kv-table"><tbody>${
    Object.entries(obj).slice(0, 50).map(([k, v]) => `<tr><td><strong>${esc(k)}</strong></td><td>${formatCellVal(k, v)}</td></tr>`).join("")
  }</tbody></table>`;
}

function formatCellVal(key, v) {
  if (v == null) return "—";
  if (typeof v === "object") return `<small class="muted">${esc(JSON.stringify(v).slice(0, 100))}</small>`;
  if (typeof v === "boolean") return v ? "✓" : "✗";
  if (key === "time" && typeof v === "number") return new Date(v * 1000).toLocaleString("en-GB");
  if (key.includes("price") || key === "close" || key === "open" || key === "high" || key === "low") return fmtPrice(v);
  if (key.includes("percent") || key.endsWith("_pct")) return fmtPct(v);
  if (typeof v === "number" && Math.abs(v) >= 1000) return fmtBig(v);
  if (typeof v === "string" && v.length > 80) return esc(v.slice(0, 80)) + "…";
  return esc(v);
}

// ============================================================
// Signal tab — derive bullish/bearish per coin from social metrics
// ============================================================
function renderSignalTab() {
  // For each coin with detail+ts, compute a signal
  const coinKeys = Object.keys(allData.coins);
  if (!coinKeys.length) {
    return `<div class="empty-tab">برای محاسبه سیگنال نیاز به detail+time-series برای coins داره. اول fetch کامل کن.</div>`;
  }
  const signals = coinKeys.map(k => computeCoinSignal(k)).filter(Boolean);
  signals.sort((a, b) => b.score - a.score);

  const aggScore = signals.length ? signals.reduce((s, x) => s + x.score, 0) / signals.length : 0;
  let aggVerdict, aggClass;
  if (aggScore >= 5) { aggVerdict = "MARKET STRONG BULLISH"; aggClass = "verdict-bull"; }
  else if (aggScore >= 2) { aggVerdict = "MARKET BULLISH"; aggClass = "verdict-cbull"; }
  else if (aggScore <= -5) { aggVerdict = "MARKET STRONG BEARISH"; aggClass = "verdict-bear"; }
  else if (aggScore <= -2) { aggVerdict = "MARKET BEARISH"; aggClass = "verdict-cbear"; }
  else { aggVerdict = "MARKET NEUTRAL"; aggClass = "verdict-neutral"; }

  return `
    <div class="verdict-card ${aggClass}">
      <div class="verdict-emoji">🌐</div>
      <div style="flex:1">
        <div class="verdict-title">${esc(aggVerdict)}</div>
        <div class="verdict-score">Aggregate Score: ${aggScore.toFixed(2)} · ${signals.length} coins</div>
      </div>
    </div>
    <h3 class="section-title">🏆 رتبه‌بندی Social Signal</h3>
    <table class="lc-table">
      <thead><tr><th>#</th><th>Coin</th><th>Galaxy</th><th>AltRank Δ</th><th>Sentiment</th><th>Social Dom Δ7d</th><th>Score</th><th>Verdict</th></tr></thead>
      <tbody>${signals.map((s, i) => `
        <tr>
          <td>${i+1}</td>
          <td><strong>${esc(s.symbol)}</strong></td>
          <td>${s.galaxy.toFixed(1)}</td>
          <td class="${s.altRankChange<=0?"change-up":"change-down"}">${s.altRankChange>=0?"+":""}${s.altRankChange.toFixed(0)}</td>
          <td>${s.sentiment}%</td>
          <td class="${s.socialDomChange>=0?"change-up":"change-down"}">${fmtPct(s.socialDomChange)}</td>
          <td><strong>${s.score>=0?"+":""}${s.score.toFixed(2)}</strong></td>
          <td><span class="chip chip-${s.label}">${esc(s.verdict)}</span></td>
        </tr>`).join("")}</tbody>
    </table>
  `;
}

function computeCoinSignal(symbolKey) {
  const detail = allData.coins[symbolKey]?.coinDetail;
  const ts = allData.coins[symbolKey]?.coinTS;
  if (!detail) return null;

  const galaxy = safeFloat(detail.galaxy_score) ?? 50;
  const altRankNow = safeFloat(detail.alt_rank) ?? 0;
  const sentiment = safeFloat(detail.sentiment) ?? 50;

  // Compare to time-series for trend
  let altRankChange = 0, socialDomChange = 0, galaxyChange = 0;
  if (Array.isArray(ts) && ts.length >= 7) {
    const recent = ts[ts.length - 1];
    const past = ts[Math.max(0, ts.length - 8)];
    if (recent && past) {
      altRankChange = (safeFloat(recent.alt_rank) ?? 0) - (safeFloat(past.alt_rank) ?? 0);
      const sdNow = safeFloat(recent.social_dominance) ?? 0;
      const sdPast = safeFloat(past.social_dominance) ?? 0;
      socialDomChange = sdPast ? ((sdNow - sdPast) / sdPast) * 100 : 0;
      galaxyChange = (safeFloat(recent.galaxy_score) ?? 0) - (safeFloat(past.galaxy_score) ?? 0);
    }
  }

  // Scoring (each component -2 to +2, weighted)
  // Galaxy: 0=very bear, 50=neutral, 100=very bull
  const galaxyScore = ((galaxy - 50) / 50) * 2;  // -2 to +2
  // AltRank decrease = good (going up in rank)
  const altRankScore = altRankChange < -50 ? 2 : altRankChange < -10 ? 1 : altRankChange > 50 ? -2 : altRankChange > 10 ? -1 : 0;
  // Sentiment
  const sentimentScore = sentiment >= 75 ? 2 : sentiment >= 60 ? 1 : sentiment <= 25 ? -2 : sentiment <= 40 ? -1 : 0;
  // Social dominance rising = attention
  const socialScore = socialDomChange > 30 ? 2 : socialDomChange > 10 ? 1 : socialDomChange < -30 ? -2 : socialDomChange < -10 ? -1 : 0;
  // Galaxy momentum
  const galaxyMomScore = galaxyChange >= 10 ? 1 : galaxyChange <= -10 ? -1 : 0;

  const score = galaxyScore + altRankScore + sentimentScore + socialScore + galaxyMomScore;
  let verdict, label;
  if (score >= 5) { verdict = "STRONG BULLISH"; label = "bull"; }
  else if (score >= 2) { verdict = "BULLISH"; label = "bull"; }
  else if (score <= -5) { verdict = "STRONG BEARISH"; label = "bear"; }
  else if (score <= -2) { verdict = "BEARISH"; label = "bear"; }
  else { verdict = "NEUTRAL"; label = "neutral"; }

  return { symbol: symbolKey, galaxy, sentiment, altRankChange, socialDomChange, galaxyChange, score, verdict, label };
}

// ============================================================
// Charts tab — Galaxy/AltRank/Sentiment over time per coin
// ============================================================
function renderChartsTab() {
  const coinKeys = Object.keys(allData.coins).filter(k => Array.isArray(allData.coins[k]?.coinTS));
  if (!coinKeys.length) return `<div class="empty-tab">داده time-series برای رسم نمودار نیست.</div>`;
  return `
    <div class="charts-header">
      <label>Coin: </label>
      <select id="chartCoinSelect" onchange="renderChartsForCoin(this.value)">
        ${coinKeys.map(k => `<option value="${esc(k)}">${esc(k)}</option>`).join("")}
      </select>
    </div>
    <div class="chart-grid">
      <div class="chart-box"><h3 id="ch-title-1">Galaxy Score & AltRank</h3><canvas id="ch-galaxy"></canvas></div>
      <div class="chart-box"><h3 id="ch-title-2">Price & Sentiment</h3><canvas id="ch-sentiment"></canvas></div>
      <div class="chart-box"><h3 id="ch-title-3">Interactions</h3><canvas id="ch-interactions"></canvas></div>
      <div class="chart-box"><h3 id="ch-title-4">Social Dominance</h3><canvas id="ch-social"></canvas></div>
    </div>
  `;
}

function renderCharts() {
  const sel = document.getElementById("chartCoinSelect");
  if (sel?.value) renderChartsForCoin(sel.value);
}

function renderChartsForCoin(symbol) {
  const ts = allData.coins[symbol]?.coinTS;
  if (!Array.isArray(ts)) return;
  Object.values(chartInstances).forEach(c => c?.destroy?.());

  document.getElementById("ch-title-1").textContent = `${symbol} — Galaxy & AltRank`;
  document.getElementById("ch-title-2").textContent = `${symbol} — Price & Sentiment`;
  document.getElementById("ch-title-3").textContent = `${symbol} — Interactions`;
  document.getElementById("ch-title-4").textContent = `${symbol} — Social Dominance`;

  const labels = ts.map(r => new Date((r.time||0)*1000).toLocaleDateString("en-GB"));
  buildLineChart("ch-galaxy", labels,
    [
      { label: "Galaxy Score", data: ts.map(r => safeFloat(r.galaxy_score)), color: "#0ea5e9", axis: "y" },
      { label: "AltRank", data: ts.map(r => safeFloat(r.alt_rank)), color: "#f59e0b", axis: "y1" },
    ], true);
  buildLineChart("ch-sentiment", labels,
    [
      { label: "Price", data: ts.map(r => safeFloat(r.close)), color: "#22c55e", axis: "y" },
      { label: "Sentiment %", data: ts.map(r => safeFloat(r.sentiment)), color: "#a78bfa", axis: "y1" },
    ], true);
  buildLineChart("ch-interactions", labels,
    [
      { label: "Interactions", data: ts.map(r => safeFloat(r.interactions)), color: "#ec4899", axis: "y" },
      { label: "Posts Created", data: ts.map(r => safeFloat(r.posts_created)), color: "#eab308", axis: "y1" },
    ], true);
  buildLineChart("ch-social", labels,
    [
      { label: "Social Dominance", data: ts.map(r => safeFloat(r.social_dominance)), color: "#06b6d4", axis: "y" },
      { label: "Market Dominance", data: ts.map(r => safeFloat(r.market_dominance)), color: "#84cc16", axis: "y1" },
    ], true);
}

function buildLineChart(canvasId, labels, datasets, dual) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  chartInstances[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: datasets.map(d => ({
        label: d.label, data: d.data, borderColor: d.color, backgroundColor: d.color + "20",
        yAxisID: d.axis, borderWidth: 1.6, pointRadius: 0, tension: 0.2,
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#94a3b8", font: { size: 11 } } },
        tooltip: { backgroundColor: "#0f172a", titleColor: "#e2e8f0", bodyColor: "#94a3b8" },
      },
      scales: {
        x: { ticks: { color: "#64748b", maxTicksLimit: 8 }, grid: { color: "#1e293b" } },
        y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
        y1: dual ? { position: "right", ticks: { color: "#94a3b8" }, grid: { drawOnChartArea: false } } : undefined,
      },
    },
  });
}

// ============================================================
// Tier display + fetch summary
// ============================================================
function renderTierDisplay() {
  const stats = CapabilityManager.stats();
  const tier = stats.tier;
  const box = document.getElementById("tierDisplay");
  if (!box) return;
  if (stats.working === 0 && stats.dead === 0) {
    box.innerHTML = `<div class="tier-empty">⓪ هنوز fetch نشده — پلن تشخیص داده نشده</div>`;
    return;
  }
  const ago = stats.recordedAt ? new Date(stats.recordedAt).toLocaleString("en-GB") : "—";
  box.innerHTML = `
    <div class="tier-row">
      <div class="tier-info">
        <div class="tier-label-mini">Plan Tier تشخیص داده شد</div>
        <div class="tier-badge-big tier-${tier.color}">${esc(tier.tier)}</div>
        <div class="tier-note">${esc(tier.note)}</div>
      </div>
      <div class="tier-stats">
        <div class="tier-stat"><span class="num">${stats.working}</span><span class="lbl">✓ working</span></div>
        <div class="tier-stat"><span class="num">${stats.dead}</span><span class="lbl">✗ dead</span></div>
        <div class="tier-stat-time">آخرین تست: ${ago}</div>
        <button class="btn-mini" onclick="CapabilityManager.reset()">↻ ریست</button>
      </div>
    </div>
  `;
}

function renderFetchSummary() {
  const n = estimateRequestCount();
  const delay = getDelayMs();
  const seconds = Math.ceil(n * delay / 1000);
  const min = Math.floor(seconds / 60), sec = seconds % 60;
  const timeStr = min ? `${min}m ${sec}s` : `${sec}s`;
  const c = readConfig();
  const totalEntities = c.topCoins + c.topTopics + c.topCats + c.topCreators + c.topStocks + c.topNfts;
  const isDiscovered = (allData.lists?.coins?.length || 0) > 0;

  const box = document.getElementById("autoFetchSummary");
  if (!box) return;
  box.innerHTML = `
    <div class="auto-summary-stats">
      <div class="auto-stat"><span class="auto-stat-num">${n}</span><span class="auto-stat-label">${isDiscovered?"کل درخواست (دقیق)":"تخمین درخواست"}</span></div>
      <div class="auto-stat"><span class="auto-stat-num">~${timeStr}</span><span class="auto-stat-label">زمان</span></div>
      <div class="auto-stat"><span class="auto-stat-num">${totalEntities}</span><span class="auto-stat-label">total entities</span></div>
      <div class="auto-stat"><span class="auto-stat-num">${Object.keys(ENDPOINT_REGISTRY).length}</span><span class="auto-stat-label">endpoint types</span></div>
    </div>
    ${!isDiscovered ? `<div class="skip-info">⚠️ بدون Discovery اعداد تخمینی هستن. اول «🔍 فقط Discovery» بزن.</div>` : ""}
  `;

  renderAutoScopeDisplay();
}

function renderAutoScopeDisplay() {
  const box = document.getElementById("autoScopeDisplay");
  if (!box) return;
  const lst = allData.lists || {};
  const total = (lst.coins?.length || 0) + (lst.topics?.length || 0) + (lst.categories?.length || 0)
              + (lst.creators?.length || 0) + (lst.stocks?.length || 0) + (lst.nfts?.length || 0);
  if (total === 0) {
    box.innerHTML = `<em class="muted">برای دیدن دقیق scope، اول «🔍 فقط Discovery» را اجرا کن.</em>`;
    return;
  }
  box.innerHTML = `
    <div class="scope-grid">
      <div class="scope-item"><span class="scope-num">${lst.coins?.length || 0}</span><span class="scope-lbl">💰 Coins</span></div>
      <div class="scope-item"><span class="scope-num">${lst.topics?.length || 0}</span><span class="scope-lbl">🗣 Topics</span></div>
      <div class="scope-item"><span class="scope-num">${lst.categories?.length || 0}</span><span class="scope-lbl">📂 Categories</span></div>
      <div class="scope-item"><span class="scope-num">${lst.creators?.length || 0}</span><span class="scope-lbl">👤 Creators</span></div>
      <div class="scope-item"><span class="scope-num">${lst.stocks?.length || 0}</span><span class="scope-lbl">📈 Stocks</span></div>
      <div class="scope-item"><span class="scope-num">${lst.nfts?.length || 0}</span><span class="scope-lbl">🖼 NFTs</span></div>
    </div>
    <div class="scope-note">✓ تمام ${total} item به‌صورت خودکار در فاز Detail پردازش می‌شوند.</div>
  `;
}

// ============================================================
// Snapshots UI
// ============================================================
function saveSnapshot() {
  const name = prompt("نام Snapshot:", `Snap ${new Date().toLocaleString("en-GB")}`);
  if (name === null) return;
  const s = StorageManager.save(name);
  if (s) { UI.log(`Snapshot ذخیره شد: ${s.name}`, "ok"); renderSnapshots(); }
}
function renderSnapshots() {
  const snaps = StorageManager.list();
  const box = document.getElementById("snapshotsList");
  if (!snaps.length) { box.innerHTML = `<em class="muted">هنوز Snapshot ذخیره نشده.</em>`; return; }
  box.innerHTML = snaps.map(s => `
    <div class="snapshot-item">
      <div class="snap-meta"><strong>${esc(s.name)}</strong>
        <span class="muted"> · ${new Date(s.savedAt).toLocaleString("en-GB")} · ${Object.keys(s.data.coins||{}).length} coins · ${Object.keys(s.data.topics||{}).length} topics</span>
      </div>
      <div class="snap-actions">
        <button class="btn-mini" onclick="loadSnapshot('${s.id}')">↺ Load</button>
        <button class="btn-mini btn-danger" onclick="deleteSnapshot('${s.id}')">حذف</button>
      </div>
    </div>`).join("");
}
function loadSnapshot(id) {
  const s = StorageManager.load(id); if (!s) return alert("یافت نشد");
  UI.log(`Snapshot loaded: ${s.name}`, "ok");
  renderResults();
}
function deleteSnapshot(id) { if (!confirm("حذف؟")) return; StorageManager.delete(id); renderSnapshots(); }
function toggleSnapshots() { document.getElementById("snapshotsBody").classList.toggle("collapsed"); }
function toggleSettings() {
  const b = document.getElementById("settings-body");
  b.classList.toggle("collapsed");
  document.getElementById("toggleSettingsBtn").textContent = b.classList.contains("collapsed") ? "▸" : "▾";
}

// ============================================================
// Exports
// ============================================================
function exportJSON() {
  downloadFile(JSON.stringify(allData, null, 2), "application/json", `lunarcrush_${dateStr()}.json`);
}

function exportCSV() {
  let out = `# LunarCrush Export\n# Generated: ${new Date().toISOString()}\n\n`;
  // Lists
  for (const [section, items] of Object.entries(allData.lists)) {
    if (!items.length) continue;
    out += `\n## ${section.toUpperCase()} LIST\n`;
    const keys = Object.keys(items[0] || {});
    out += keys.join(",") + "\n";
    items.forEach(r => out += keys.map(k => `"${typeof r[k]==="object"?JSON.stringify(r[k]):(r[k]??"")}"`).join(",") + "\n");
  }
  // Per-coin time-series flattened
  for (const [sym, det] of Object.entries(allData.coins)) {
    if (Array.isArray(det.coinTS) && det.coinTS.length) {
      out += `\n## COIN TS: ${sym}\n`;
      const keys = Object.keys(det.coinTS[0]);
      out += keys.join(",") + "\n";
      det.coinTS.forEach(r => out += keys.map(k => `"${r[k]??""}"`).join(",") + "\n");
    }
  }
  downloadFile(out, "text/csv;charset=utf-8;", `lunarcrush_${dateStr()}.csv`);
}

function exportAIPrompt() {
  const tier = CapabilityManager.detectTier();
  const coinKeys = Object.keys(allData.coins);
  const signals = coinKeys.map(k => computeCoinSignal(k)).filter(Boolean).sort((a,b) => b.score - a.score);

  let md = `# LunarCrush Social Signal Analysis Request

## Role
You are a senior social-sentiment crypto analyst specializing in interpreting LunarCrush Galaxy Score™, AltRank™, sentiment, and social dominance trends. Your task is to read the data below and provide actionable insights on attention rotation, sentiment divergence, and coins primed for breakout based on social signal preceding price.

## Data Snapshot
- **Generated:** ${new Date().toISOString().slice(0, 10)}
- **Plan Tier Detected:** ${tier.tier} (${tier.note})
- **Coins analyzed:** ${coinKeys.length}
- **Topics analyzed:** ${Object.keys(allData.topics).length}
- **Categories:** ${Object.keys(allData.categories).length}
- **Total requests:** ${allData.meta.totalRequests}

## Top Coins by Social Signal Score

| # | Coin | Galaxy | AltRank Δ7d | Sentiment | Social Dom Δ | Score | Verdict |
|---|---|---|---|---|---|---|---|
`;
  signals.slice(0, 30).forEach((s, i) => {
    md += `| ${i+1} | ${s.symbol} | ${s.galaxy.toFixed(1)} | ${s.altRankChange>=0?"+":""}${s.altRankChange.toFixed(0)} | ${s.sentiment}% | ${fmtPct(s.socialDomChange)} | ${s.score>=0?"+":""}${s.score.toFixed(2)} | ${s.verdict} |\n`;
  });

  // Trending topics
  const topics = (allData.lists.topics || []).slice(0, 20);
  md += `\n## Top Trending Topics\n\n| Rank | Topic | Contributors | Posts | Interactions 24h |\n|---|---|---|---|---|\n`;
  topics.forEach(t => {
    md += `| ${t.topic_rank} | ${t.title || t.topic} | ${fmtBig(t.num_contributors)} | ${fmtBig(t.num_posts)} | ${fmtBig(t.interactions_24h)} |\n`;
  });

  // Top categories
  const cats = (allData.lists.categories || []).slice(0, 10);
  if (cats.length) {
    md += `\n## Top Trending Categories\n\n| Rank | Category | Social Dominance | Contributors |\n|---|---|---|---|\n`;
    cats.forEach(c => md += `| ${c.category_rank} | ${c.title || c.category} | ${c.social_dominance?.toFixed?.(2)||"—"}% | ${fmtBig(c.num_contributors)} |\n`);
  }

  // Top creators driving attention
  const creds = (allData.lists.creators || []).slice(0, 10);
  if (creds.length) {
    md += `\n## Top Creators by Interactions 24h\n\n| Rank | Creator | Network | Followers | Interactions 24h |\n|---|---|---|---|---|\n`;
    creds.forEach(c => md += `| ${c.creator_rank} | ${c.creator_display_name || c.creator_name} | ${c.creator_network} | ${fmtBig(c.creator_followers)} | ${fmtBig(c.interactions_24h)} |\n`);
  }

  if (allData.meta.unavailable.length) {
    md += `\n## Unavailable Endpoints (not in plan: ${tier.tier})\n`;
    md += `- ${allData.meta.unavailable.slice(0, 20).map(u => u.endpoint).join("\n- ")}\n`;
  }

  md += `\n## What I want from you

1. **Attention rotation read**: Which coins are gaining social dominance while losing market dominance (early breakout setup)?
2. **Sentiment divergence**: Coins where sentiment is dropping while price holds (or vice versa) — flag the divergence.
3. **AltRank momentum plays**: Top 3 coins with sharpest AltRank improvement (lower is better).
4. **Galaxy Score outliers**: Which coins have Galaxy ≥ 70 right now? Are they price/sentiment confirmed?
5. **Topic-driven setups**: Which trending topics correspond to specific coins likely to benefit?
6. **Risk: Spam/manipulation signals**: Any coins where spam ratio is high relative to posts_active?
7. **Trade idea**: Highest-conviction 2-week swing trade given social + sentiment data.

Respond in concise prose with bolded key takeaways. Cite specific Galaxy/AltRank numbers.
`;

  downloadFile(md, "text/markdown;charset=utf-8;", `lunarcrush_ai_${dateStr()}.md`);
}

// ============================================================
// Boot
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  renderSnapshots();
  renderTierDisplay();
  renderFetchSummary();
  // Re-render summary when relevant inputs change
  ["interval","bucket","delayMs","skipDead","fetchExtras","fetchMeta","fetchWhatsup"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", renderFetchSummary);
    if (el && el.tagName === "INPUT" && el.type === "number") el.addEventListener("input", renderFetchSummary);
  });
});
