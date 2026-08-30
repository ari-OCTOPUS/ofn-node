// ============================================================
// LunarCrush API v4 - Maximum Data Scraper
// Individual Plan: 10 req/min → max 1 req per 6 seconds
// ============================================================

const BASE_URL = "https://lunarcrush.com/api4/public";

let allData = {
  meta: { fetchedAt: null, totalRequests: 0, errors: [] },
  coins_list: null,
  coins_detail: {},
  coins_timeseries: {},
  topics_list: null,
  categories_list: null,
  creators_list: null,
};

let totalRequests = 0;   // کل درخواست‌های برنامه‌ریزی شده
let doneRequests  = 0;   // درخواست‌های انجام شده (برای progress واقعی)
let abortFlag = false;   // رفع نقص ۱۱: لغو اجرای قدیمی

// ============================================================
// هسته اصلی: fetch با retry و rate-limit
// ============================================================
async function apiCall(endpoint, params = {}) {
  const apiKey = document.getElementById("apiKey").value.trim();
  if (!apiKey) throw new Error("API Key وارد نشده!");
  if (abortFlag) throw new Error("ABORTED");

  const url = new URL(BASE_URL + endpoint);
  Object.keys(params).forEach(k => url.searchParams.set(k, params[k]));

  for (let attempt = 1; attempt <= 3; attempt++) {
    if (abortFlag) throw new Error("ABORTED");
    try {
      const res = await fetch(url.toString(), {
        headers: { Authorization: "Bearer " + apiKey }
      });

      if (res.status === 429) {
        // رفع نقص ۲: خواندن هدر Retry-After
        const retryAfter = parseInt(res.headers.get("Retry-After") || "") || (20 * attempt);
        setStatus(`⏳ Rate limit خورد، ${retryAfter} ثانیه صبر...`);
        await sleep(retryAfter * 1000);
        continue;
      }
      if (res.status === 401) throw new Error("API Key نامعتبر است (401)");
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`HTTP ${res.status}: ${err.slice(0, 120)}`);
      }

      const json = await res.json();
      allData.meta.totalRequests++;
      doneRequests++;
      // رفع نقص ۴: progress بر اساس درخواست‌های واقعی
      setProgress(Math.min(Math.round((doneRequests / totalRequests) * 95), 95));
      return json;

    } catch (e) {
      if (e.message === "ABORTED" || e.message.includes("401")) throw e;
      if (attempt === 3) throw e;
      await sleep(5000);
    }
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function setStatus(msg) { document.getElementById("statusText").textContent = msg; }
function setProgress(pct) { document.getElementById("progressFill").style.width = pct + "%"; }

// ============================================================
// رفع نقص ۳: تست سلامت API Key قبل از شروع اصلی
// ============================================================
async function validateApiKey() {
  setStatus("🔑 بررسی API Key...");
  try {
    await apiCall("/coins/list/v1", { limit: 1 });
    return true;
  } catch (e) {
    if (e.message.includes("401") || e.message.includes("نامعتبر")) {
      setStatus("❌ API Key اشتباه است! لطفاً کلید خود را بررسی کنید.");
      return false;
    }
    if (e.message.includes("402")) {
      setStatus("❌ پلن شما به این endpoint دسترسی ندارد (402). نیاز به ارتقا.");
      return false;
    }
    throw e;
  }
}

// ============================================================
// مرحله ۱: لیست ارزها
// ============================================================
async function fetchCoinsList() {
  setStatus("📋 دریافت لیست ارزها...");
  const limit = parseInt(document.getElementById("limit").value) || 100;
  // نکته: v1 پارامتر sort=galaxy_score رو نادیده می‌گیره، پس client-side سورت می‌کنیم
  const data = await apiCall("/coins/list/v1", {
    limit: Math.min(limit, 1000)
  });
  // سورت نزولی بر اساس galaxy_score (با fallback به market_cap)
  if (data?.data && Array.isArray(data.data)) {
    data.data.sort((a, b) => {
      const ga = Number(a.galaxy_score) || 0;
      const gb = Number(b.galaxy_score) || 0;
      if (gb !== ga) return gb - ga;
      return (Number(b.market_cap) || 0) - (Number(a.market_cap) || 0);
    });
  }
  allData.coins_list = data;
  await sleep(6200);
  return data?.data || [];
}

// ============================================================
// مرحله ۲: جزئیات + time series — رفع نقص ۱: استفاده از coin.id
// chunk=2 → هر chunk = 4 req → 25s فاصله بین chunk‌ها
// ============================================================
async function fetchCoinDetails(coins) {
  const topN = parseInt(document.getElementById("topCoins").value) || 20;
  const topCoins = coins.slice(0, topN);
  setStatus(`📊 دریافت جزئیات ${topCoins.length} ارز...`);

  const chunks = chunkArray(topCoins, 2);

  for (let i = 0; i < chunks.length; i++) {
    if (abortFlag) return;
    const chunk = chunks[i];

    // sequential (نه موازی) تا rate limit کنترل‌پذیر باشه
    for (const coin of chunk) {
      if (abortFlag) return;
      try {
        // رفع نقص ۱: استفاده از id عددی به جای symbol
        const coinId = coin.id || coin.symbol?.toLowerCase();

        // درخواست ۱: جزئیات
        const detail = await apiCall(`/coins/${coinId}/v1`);
        allData.coins_detail[coin.symbol] = detail;
        await sleep(6200);

        // درخواست ۲: time series (1 ماه، روزانه) - v1 برای پلن Individual
        const ts = await apiCall(`/coins/${coinId}/time-series/v1`, {
          interval: "1m",   // رفع نقص ۱۵: 1 ماه به جای 1 هفته
          bucket: "day"
        });
        allData.coins_timeseries[coin.symbol] = ts;
        await sleep(6200);

      } catch (e) {
        if (e.message === "ABORTED") return;
        allData.meta.errors.push(`${coin.symbol}: ${e.message}`);
      }
    }

    const done = Math.min((i + 1) * 2, topCoins.length);
    setStatus(`📊 ${done} / ${topCoins.length} ارز دریافت شد...`);

    if (i < chunks.length - 1) {
      for (let s = 25; s > 0; s--) {
        if (abortFlag) return;
        setStatus(`⏳ ${done}/${topCoins.length} ارز - صبر ${s}s...`);
        await sleep(1000);
      }
    }
  }
}

// ============================================================
// مرحله ۳-۵: Topics، Categories، Creators
// ============================================================
async function fetchTopics() {
  setStatus("💬 دریافت topics ترند...");
  try {
    // topics/list/v1 پارامتر limit نمی‌پذیره
    allData.topics_list = await apiCall("/topics/list/v1");
    await sleep(6200);
  } catch (e) {
    if (e.message !== "ABORTED") allData.meta.errors.push("topics: " + e.message);
  }
}

async function fetchCategories() {
  setStatus("🏷️ دریافت categories...");
  try {
    // categories/list/v1 پارامتر limit نمی‌پذیره
    allData.categories_list = await apiCall("/categories/list/v1");
    await sleep(6200);
  } catch (e) {
    if (e.message !== "ABORTED") allData.meta.errors.push("categories: " + e.message);
  }
}

async function fetchCreators() {
  setStatus("🎯 دریافت top influencers...");
  try {
    // creators/list/v1 پارامتر sort نمی‌پذیره
    allData.creators_list = await apiCall("/creators/list/v1");
    await sleep(6200);
  } catch (e) {
    if (e.message !== "ABORTED") allData.meta.errors.push("creators: " + e.message);
  }
}

// ============================================================
// تابع اصلی
// ============================================================
async function startFetch() {
  const apiKey = document.getElementById("apiKey").value.trim();
  if (!apiKey) { alert("❌ لطفاً API Key را وارد کنید!"); return; }

  const topN    = parseInt(document.getElementById("topCoins").value) || 20;
  const listN   = parseInt(document.getElementById("limit").value) || 100;

  // رفع نقص ۱۱: لغو اجرای قبلی
  abortFlag = false;

  // محاسبه دقیق totalRequests برای progress واقعی (رفع نقص ۴)
  // 1 (validate) + 1 (list) + topN*2 (detail+ts) + 3 (topics+cats+creators)
  totalRequests = 1 + 1 + topN * 2 + 3;
  doneRequests  = 0;

  const estMin = Math.ceil((totalRequests) / 10) + Math.ceil(topN * 2 / 10) * 0.4;

  allData = {
    meta: { fetchedAt: new Date().toISOString(), totalRequests: 0, errors: [], plan: "Individual (10 req/min)" },
    coins_list: null, coins_detail: {}, coins_timeseries: {},
    topics_list: null, categories_list: null, creators_list: null,
  };

  document.getElementById("fetchBtn").disabled = true;
  document.getElementById("stopBtn").classList.remove("hidden");
  document.getElementById("statusBox").classList.remove("hidden");
  document.getElementById("resultsCard").classList.add("hidden");
  setProgress(0);
  setStatus(`🚀 شروع... (~${Math.round(estMin)} دقیقه)`);

  try {
    // رفع نقص ۳: اعتبارسنجی کلید
    const valid = await validateApiKey();
    if (!valid || abortFlag) return;
    await sleep(6200);

    const coins = await fetchCoinsList();
    if (abortFlag) return;

    await fetchCoinDetails(coins);
    if (abortFlag) return;

    await fetchTopics();
    await fetchCategories();
    await fetchCreators();

    // رفع نقص ۱۰: نمایش خطاها به کاربر در پایان
    if (allData.meta.errors.length > 0) {
      setStatus(`✅ تمام شد — ${allData.meta.errors.length} خطای جزئی (در بخش تحلیل قابل مشاهده است)`);
    } else {
      setStatus("✅ همه داده‌ها با موفقیت دریافت شد!");
    }
    setProgress(100);
    renderResults(coins);

  } catch (e) {
    if (e.message !== "ABORTED") setStatus("❌ خطا: " + e.message);
    else setStatus("⛔ توسط کاربر متوقف شد.");
  } finally {
    document.getElementById("fetchBtn").disabled = false;
    document.getElementById("stopBtn").classList.add("hidden");
  }
}

function stopFetch() {
  abortFlag = true;
  setStatus("⛔ در حال توقف...");
}

// ============================================================
// رندر نتایج
// ============================================================
function renderResults(coins) {
  document.getElementById("resultsCard").classList.remove("hidden");

  // رفع نقص ۱۰: نمایش خطاها در UI
  const errHtml = allData.meta.errors.length
    ? `<div class="stat-chip error-chip" title="${allData.meta.errors.join('\n')}">⚠️ خطاها: <span>${allData.meta.errors.length}</span></div>`
    : "";

  document.getElementById("resultStats").innerHTML = `
    <div class="stat-chip">ارزهای دریافتی: <span>${coins.length}</span></div>
    <div class="stat-chip">جزئیات کامل: <span>${Object.keys(allData.coins_detail).length}</span></div>
    <div class="stat-chip">Time Series: <span>${Object.keys(allData.coins_timeseries).length}</span></div>
    <div class="stat-chip">کل Requests: <span>${allData.meta.totalRequests}</span></div>
    ${errHtml}
  `;

  const tbody = document.getElementById("coinsBody");
  tbody.innerHTML = "";

  coins.forEach((c, i) => {
    // رفع نقص ۶: تابع کمکی برای parse امن
    const change  = safeFloat(c.percent_change_24h);
    const signal  = getSignal(c);
    // رفع نقص ۵: محافظت از همه فیلدها
    const gs      = c.galaxy_score != null ? Number(c.galaxy_score).toFixed(1) : "-";
    const altRank = c.alt_rank != null ? c.alt_rank : "-";

    const row = `
      <tr>
        <td>${i + 1}</td>
        <td><strong>${esc(c.symbol)}</strong></td>
        <td>${esc(c.name)}</td>
        <td>$${formatNum(c.price)}</td>
        <td class="${change >= 0 ? 'change-up' : 'change-down'}">${change >= 0 ? '▲' : '▼'} ${Math.abs(change).toFixed(2)}%</td>
        <td>$${formatBigNum(c.market_cap)}</td>
        <td>${gs}</td>
        <td>${altRank}</td>
        <td>${formatBigNum(c.social_volume_24h)}</td>
        <td><span class="signal-${signal.type}">${signal.label}</span></td>
      </tr>`;
    tbody.insertAdjacentHTML("beforeend", row);
  });

  document.getElementById("marketData").textContent  = JSON.stringify(allData.coins_list, null, 2);
  document.getElementById("globalData").textContent  = JSON.stringify({
    topics: allData.topics_list,
    categories: allData.categories_list,
    creators: allData.creators_list
  }, null, 2);
}

// ============================================================
// سیگنال — رفع نقص ۷: آستانه‌ها از UI خوانده می‌شن
// ============================================================
function getSignal(coin) {
  const gsThresh  = parseInt(document.getElementById("gsThreshold")?.value  || 60);
  const arThresh  = parseInt(document.getElementById("arThreshold")?.value  || 50);

  const gs     = coin.galaxy_score || 0;
  const alt    = coin.alt_rank     || 9999;
  const change = safeFloat(coin.percent_change_24h);
  const sent   = coin.sentiment    || 50;

  if (gs >= gsThresh && alt <= arThresh && change > 0 && sent >= 60)
    return { type: "buy",  label: "🟢 خرید" };
  if (gs <= (gsThresh - 25) || change < -5)
    return { type: "sell", label: "🔴 فروش" };
  return { type: "hold", label: "🔵 نگه‌دار" };
}

// ============================================================
// خروجی‌ها
// ============================================================
function exportJSON() {
  downloadFile(JSON.stringify(allData, null, 2), "application/json",
    `lunarcrush_${dateStr()}.json`);
}

function exportCSV() {
  const coins = allData.coins_list?.data || [];
  if (!coins.length) return alert("داده‌ای برای خروجی نیست!");

  const headers = [
    "rank","symbol","name","price","percent_change_24h","percent_change_7d",
    "percent_change_30d","market_cap","volume_24h","galaxy_score",
    "galaxy_score_previous","alt_rank","alt_rank_previous",
    "social_volume_24h","social_dominance","market_dominance","sentiment","signal"
  ];

  const rows = coins.map((c, i) => {
    const sig = getSignal(c);
    return [
      i + 1, c.symbol, c.name, c.price,
      c.percent_change_24h, c.percent_change_7d, c.percent_change_30d,
      c.market_cap, c.volume_24h,
      c.galaxy_score, c.galaxy_score_previous,
      c.alt_rank, c.alt_rank_previous,
      c.social_volume_24h, c.social_dominance,
      c.market_dominance, c.sentiment,
      sig.type   // رفع نقص ۸: type به جای label
    ].map(v => `"${v ?? ""}"`).join(",");
  });

  downloadFile([headers.join(","), ...rows].join("\n"), "text/csv;charset=utf-8;",
    `lunarcrush_coins_${dateStr()}.csv`);
}

function exportAnalysis() {
  const coins = allData.coins_list?.data || [];
  const topBuy  = coins.filter(c => getSignal(c).type === "buy").slice(0, 10);
  const topSell = coins.filter(c => getSignal(c).type === "sell").slice(0, 10);

  const report = {
    generated_at: new Date().toISOString(),
    plan: "Individual (10 req/min)",
    settings: {
      gs_threshold: document.getElementById("gsThreshold")?.value || 60,
      ar_threshold: document.getElementById("arThreshold")?.value || 50,
    },
    summary: {
      total_coins: coins.length,
      buy_signals:  coins.filter(c => getSignal(c).type === "buy").length,
      sell_signals: coins.filter(c => getSignal(c).type === "sell").length,
      hold_signals: coins.filter(c => getSignal(c).type === "hold").length,
    },
    top_buy_candidates: topBuy.map(c => ({
      symbol: c.symbol, name: c.name, price: c.price,
      change_24h: c.percent_change_24h, change_7d: c.percent_change_7d,
      galaxy_score: c.galaxy_score, alt_rank: c.alt_rank,
      social_volume: c.social_volume_24h, sentiment: c.sentiment
    })),
    top_sell_candidates: topSell.map(c => ({
      symbol: c.symbol, name: c.name, price: c.price,
      change_24h: c.percent_change_24h, galaxy_score: c.galaxy_score,
    })),
    errors: allData.meta.errors
  };

  downloadFile(JSON.stringify(report, null, 2), "application/json",
    `lunarcrush_analysis_${dateStr()}.json`);
}

// ============================================================
// کمکی‌ها
// ============================================================
function safeFloat(v) {
  // رفع نقص ۶: parse امن برای هر فرمتی
  if (v == null) return 0;
  const n = parseFloat(String(v).replace(/,/g, ""));
  return isNaN(n) ? 0 : n;
}

// رفع نقص ۹: escape برای جلوگیری از XSS
function esc(s) {
  if (s == null) return "-";
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function downloadFile(content, type, filename) {
  const blob = new Blob([content], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
}

function showTab(name) {
  ["coins","market","global"].forEach(t => {
    document.getElementById("tab-" + t).classList.toggle("hidden", t !== name);
  });
  document.querySelectorAll(".tab").forEach((b, i) => {
    b.classList.toggle("active", ["coins","market","global"][i] === name);
  });
}

function formatNum(n) {
  if (!n) return "0";
  if (n < 0.001) return n.toExponential(4);
  if (n < 1) return parseFloat(n).toFixed(6);
  return parseFloat(n).toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function formatBigNum(n) {
  if (!n) return "0";
  if (n >= 1e12) return (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9)  return (n / 1e9).toFixed(2)  + "B";
  if (n >= 1e6)  return (n / 1e6).toFixed(2)  + "M";
  if (n >= 1e3)  return (n / 1e3).toFixed(2)  + "K";
  return String(n);
}

function chunkArray(arr, size) {
  const res = [];
  for (let i = 0; i < arr.length; i += size) res.push(arr.slice(i, i + size));
  return res;
}

function dateStr() {
  return new Date().toISOString().slice(0,19).replace(/[T:]/g,"-");
}
