#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_cockpit_ui — کاکپیتِ Mini App نباید دروغ بگوید.

⚠️ ۲۰۲۶-۰۸-۰۶ — بازنویسیِ کامل بعد از یک ری‌دیزاینِ چندکامیتیِ ۲۰۲۶-۰۸-۰۴..۰۵.

نسخهٔ قبلی (۲۰۲۶-۰۸-۰۳) روی معماریِ **قدیم** نوشته شده بود: ۱۲ تب (studio/
brain/governor/obsidian/next/outbound/legs/value/registry/truth/…)، یک
`/api/ops` ترکیبی که چهار بخش (brain/governor/obsidian/next_steps) را یک‌جا
می‌داد، یک گریدِ tile با `data-state`، پالتِ فرمان (Ctrl/Cmd+K)، کشِ محلی با
برچسبِ stale، coalescing/debounce، و `window.__cockpit` برای دیپ‌لینک.

بین ۰۸-۰۳ و ۰۸-۰۵ کاکپیت کاملاً بازطراحی شد (نگاه کن به `git log --oneline
-- miniapp/app.js`: «شش اقدام مسلح شد»، «ترکیبِ فضایی با قرصِ اختاپوس»،
«بازطراحیِ تریاژ»، «تبِ ششم (کارها)»). این نبود که چند رشتهٔ لنگر جابه‌جا شده
باشد — کلِ مدلِ داده و DOM عوض شد:

  · تب‌ها حالا ۶ تااند: home/approvals/money/leads/tasks/system (برچسبِ
    فارسی: خانه/تأییدها/پول/لیدها/کارها/سیستم). studio/brain/governor/
    obsidian/next/outbound/legs/value/registry/truth دیگر تبِ جدا نیستند؛
    برخی‌شان (برای مثال brain/governor/obsidian/legs/truth/registry) حالا
    **پنلِ زیرِ تبِ سیستم**اند (`stack()`)، بقیه (studio/next) کدشان کاملاً
    حذف یا جایگزین شده.
  · `/api/ops` ِ ترکیبی دیگر از UI صدا زده نمی‌شود؛ هر پنل مسیرِ اختصاصیِ
    خودش را می‌خواند (`/api/ops/brain`، `/api/governor`، `/api/obsidian`،
    `/api/legs`، `/api/ops/tasks`، `/api/ops/leads`، …).
  · پالت، کشِ محلی، debounce/coalescing، و `window.__cockpit` — هیچ‌کدام
    در app.js ِ فعلی وجود ندارند (صفر رخداد؛ با grep تأیید شد).
  · هدرِ triState/badge3/badgeClass با یک `tri()` سه‌حالتی و یک
    `panelGuard()` عمومی جایگزین شده که همان قاعده را برای همهٔ پنل‌های
    تازه یک‌جا اجرا می‌کند.
  · `renderStudio` (صاحبِ HEADER_LITERAL ِ قدیمیِ اقدام‌ها) از جدولِ
    `renderers` برداشته شده — کدش هنوز در فایل هست ولی **صداکنندهٔ صفر**
    دارد (دقیقاً همان الگویی که این ریپو بارها دیده). سه اقدامش
    (lead.create/update_stage، task.create) جای تازه‌شان را در تبِ
    لیدها/کارها گرفته‌اند، با apiPost ِ مستقیم (نه از راهِ act()).

این فایل هر دو لایه را نگه می‌دارد ولی هر آزمونی که معادلِ تمیزی نداشت
**حذف شد، نه تحریف**. فهرستِ دقیقِ چه چیزی حذف شد و چرا، بالای هر بخش
آمده. چیزی که این تست **نمی‌سنجد** (صادقانه):

  · رندرِ واقعیِ مرورگر، CSS، RTL. گاردِ read-only ِ معتبر سمتِ سرور است
    (`/api/actions` → 403 owner_auth_required)، نه چیزی که این‌جا سنجیده
    شود.
  · Telegram WebApp واقعی و امضایِ initData.
  · تعاملِ پیچیدهٔ DOM (چیپ‌های انتخابی، شمارشِ معکوسِ تأیید/رد، یادداشتِ
    لید) — درایورِ Node این فایل یک DOM ِ **مسطح** دارد (بدونِ درختِ واقعیِ
    parent/child)، پس `querySelector` فقط `#id` را حل می‌کند، نه selectorِ
    ترکیبی (`.chip.on`، `.titem .pend`). کدِ app.js خودش روی نبودِ این‌ها
    fallback دارد (مثلاً stage/kind/priority پیش‌فرض می‌گیرند)، پس این
    محدودیت کرش نمی‌سازد — فقط یعنی نمی‌توانیم چیپ‌ها را تست کنیم.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness  # noqa: E402

ENV = harness.setup("miniapp-cockpit-ui")   # قبل از هر importی که state می‌نویسد

MINIAPP = _HERE.parent / "telegram_center" / "miniapp"
APP_JS = MINIAPP / "app.js"
INDEX_HTML = MINIAPP / "index.html"
GATEWAY_PY = _HERE.parent / "telegram_center" / "miniapp_gateway.py"
STYLE_CSS = MINIAPP / "style.css"

# ── لنگرهای یکتا ────────────────────────────────────────────────────────────
# هرکدام دقیقاً یک بار در app.js می‌آید؛ جهش روی همین رشته‌ها تست را می‌کُشد.
# (نسخهٔ ۰۸-۰۳: HEADER_LITERAL شکلِ inline ِ `if(tg && tg.initData)` داشت؛
# حالا داخلِ helper ِ `tgHeaders()` است.)
HEADER_LITERAL = 'h["X-Tg-Init-Data"] = tg.initData;'
SINGLE_POST_SITE = 'apiPost("/api/actions", {action:action, payload:payload||{},'

_SRC_CACHE = {}


def src(p: Path) -> str:
    key = str(p)
    if key not in _SRC_CACHE:
        _SRC_CACHE[key] = p.read_text("utf-8")
    return _SRC_CACHE[key]


def _reset_src_cache():
    _SRC_CACHE.clear()


# ── درایورِ Node ────────────────────────────────────────────────────────────
# یک DOM ِ کوچک ولی صادق: innerHTML واقعاً ذخیره می‌شود، id ها از همان HTML
# برداشت می‌شوند (پس اگر app.js فرمی نسازد، دکمه‌اش هم پیدا نمی‌شود)، و fetch
# هر فراخوانی را با هدرهایش ثبت می‌کند.
#
# ⚠️ ۰۸-۰۶ — دو اضافه نسبت به نسخهٔ قبلی، هر دو زیرساختیِ عمومی‌اند (نه
# متعلق به یک ویژگیِ خاص): `querySelectorAll`/`querySelector`/`appendChild`
# روی El و `querySelector`/`createElement`/`body` روی document. app.js ِ
# جدید این‌ها را همه‌جا صدا می‌زند (renderLeadOps/renderTasks/toast/…)؛
# نسخهٔ قبلیِ درایور اصلاً نداشتشان، پس **هر** سناریویی که یک بار render("home")
# را رد می‌کرد (یعنی همه‌شان) با `TypeError: el.querySelectorAll is not a
# function` کرش می‌کرد — یک باگِ زیرساختیِ درایور، نه چیزی دربارهٔ app.js.
# پیاده‌سازی عمداً مینیمال است: چون این DOM ِ مسطح درختِ parent/child واقعی
# ندارد، `querySelector`/`querySelectorAll` فقط `#id` را حل می‌کنند (از
# رجیستریِ سراسری‌ای که harvest() پر می‌کند) و برای هر selector ِ دیگر
# (کلاس، ترکیبی) امن و بی‌کرش خالی/null برمی‌گردانند — دقیقاً همان رفتاری که
# یک DOM ِ واقعی روی چیزی که پیدا نمی‌کند دارد (نه throw).
_DRIVER = r"""
"use strict";
const fs = require("fs");
const APP = process.argv[2], INDEX = process.argv[3], SCENARIO = process.argv[4], FIXTURE = process.argv[5];
const out = {scenario: SCENARIO};

const registry = new Map();
const focusLog = [];
const fetchLog = [];
let routes = {};

function El(id, cls){
  this.id = id || ""; this._innerHTML = ""; this.textContent = ""; this.className = cls || "";
  this.value = ""; this.children = []; this._attrs = {}; this._listeners = {}; this.style = {};
  const self = this;
  this.classList = {
    add(c){ const s = new Set(String(self.className).split(/\s+/).filter(Boolean)); s.add(c); self.className = [...s].join(" "); },
    remove(c){ const s = new Set(String(self.className).split(/\s+/).filter(Boolean)); s.delete(c); self.className = [...s].join(" "); },
    contains(c){ return String(self.className).split(/\s+/).filter(Boolean).indexOf(c) >= 0; }
  };
}
Object.defineProperty(El.prototype, "innerHTML", {
  get(){ return this._innerHTML; },
  set(v){ this._innerHTML = String(v); harvest(this._innerHTML); }
});
El.prototype.setAttribute = function(k, v){ this._attrs[k] = String(v); };
El.prototype.getAttribute = function(k){ return this._attrs[k] === undefined ? null : this._attrs[k]; };
El.prototype.removeAttribute = function(k){ delete this._attrs[k]; };
El.prototype.addEventListener = function(t, f){ (this._listeners[t] = this._listeners[t] || []).push(f); };
El.prototype.dispatch = function(t, ev){ (this._listeners[t] || []).forEach(f => f(ev || {})); };
El.prototype.focus = function(){ focusLog.push(this.id); };
El.prototype.closest = function(sel){ const c = String(sel).replace(/^\./, ""); return this.classList.contains(c) ? this : null; };
// ── DOM ِ مسطح: فقط #id حل می‌شود؛ بقیه امن و خالی برمی‌گردد ────────────
El.prototype.querySelectorAll = function(_sel){ return []; };
El.prototype.querySelector = function(sel){
  const m = /^#([A-Za-z0-9_-]+)$/.exec(String(sel || "").trim());
  return m && registry.has(m[1]) ? registry.get(m[1]) : null;
};
El.prototype.appendChild = function(child){
  this.children.push(child);
  if(child && child.id) registry.set(child.id, child);
  return child;
};
// 2026-08-16 (AUTOFLOW S6): app.js هدر را با insertBefore می‌سازد — استاب DOM
// باید قرارداد امروزِ مرورگر را پیاده کند (رفعِ زیرساختِ تست، نه تغییر app.js)
El.prototype.insertBefore = function(child, ref){
  if(!ref){ this.children.push(child); }
  else {
    const i = this.children.indexOf(ref);
    if(i === -1){ this.children.push(child); } else { this.children.splice(i, 0, child); }
  }
  if(child && child.id) registry.set(child.id, child);
  return child;
};
El.prototype.removeChild = function(child){
  const i = this.children.indexOf(child);
  if(i !== -1){ this.children.splice(i, 1); }
  return child;
};

function ensure(id, cls){ if(!registry.has(id)) registry.set(id, new El(id, cls)); return registry.get(id); }
function harvest(html){
  const re = /id="([^"]+)"/g; let m;
  while((m = re.exec(html)) !== null){ ensure(m[1]); }
}

const indexHtml = fs.readFileSync(INDEX, "utf8");
harvest(indexHtml);
const tabsEl = ensure("tabs");
// ⚠️ ۲۰۲۶-۰۸-۰۹: قبلاً `data-tab="X">` را می‌خواست — یعنی بلافاصله بعد از
// data-tab باید `>` می‌آمد. فازِ ARIA-tablist (role/id/aria-selected/
// aria-controls/tabindex بینِ data-tab و `>`) این را برای **هر نُه** تب
// شکسته بود؛ tabsEl.children خالی می‌ماند و هر clickTab بعدی روی
// `undefined.closest` کرش می‌کرد — باگِ زیرساختِ تست، نه app.js/index.html
// واقعی (که ARIA عمداً و تست‌شده آن‌جاست).
const tabRe = /<div class="tab([^"]*)" data-tab="([^"]+)"[^>]*>([^<]*)<\/div>/g;
let tm;
while((tm = tabRe.exec(indexHtml)) !== null){
  const el = new El("", "tab" + tm[1]);
  el.setAttribute("data-tab", tm[2]);
  el.textContent = tm[3];
  tabsEl.children.push(el);
}
out.tab_keys = tabsEl.children.map(t => t.getAttribute("data-tab"));
out.tab_labels = tabsEl.children.map(t => t.textContent);

const store = new Map();
const localStorage = {
  getItem(k){ return store.has(k) ? store.get(k) : null; },
  setItem(k, v){ store.set(k, String(v)); },
  removeItem(k){ store.delete(k); }
};

const documentStub = {
  _listeners: {},
  getElementById(id){ return registry.has(id) ? registry.get(id) : null; },
  addEventListener(t, f){ (this._listeners[t] = this._listeners[t] || []).push(f); },
  dispatch(t, ev){ (this._listeners[t] || []).forEach(f => f(ev || {})); },
  querySelector(sel){
    const m = /^#([A-Za-z0-9_-]+)$/.exec(String(sel || "").trim());
    return m && registry.has(m[1]) ? registry.get(m[1]) : null;
  },
  createElement(_tag){ return new El("", ""); }
};
documentStub.body = new El("", "");

function resp(status, body){
  return {ok: status >= 200 && status < 300, status: status, json: () => Promise.resolve(body)};
}
function fetchStub(url, opts){
  opts = opts || {};
  fetchLog.push({url: String(url), method: String(opts.method || "GET"),
                 headers: Object.assign({}, opts.headers || {}), body: opts.body || null});
  const r = routes[String(url)];
  if(r === undefined) return Promise.resolve(resp(404, {status: "not_found"}));
  if(typeof r === "function") return r();
  if(r === "throw") return Promise.reject(new Error("network down"));
  return Promise.resolve(resp(r.status === undefined ? 200 : r.status, r.body));
}

const windowStub = {localStorage: localStorage, Telegram: undefined};
// 2026-08-16 (AUTOFLOW S6): بنرِ وضعیتِ app.js هر ۶۰s یک setInterval واقعی می‌سازد
// که حلقهٔ رویداد node را زنده نگه می‌دارد و driver هرگز خارج نمی‌شد (TimeoutExpired
// ۹۰s). در محیطِ تست، تایمرِ تکرارشوندهٔ واقعی لازم نیست — no-op با برگرداندن id صفر.
global.setInterval = function(){ return 0; };
const flush = async (n) => { for(let i = 0; i < (n || 16); i++){ await new Promise(r => setImmediate(r)); } };

function nowIso(){
  const d = new Date(), p = n => (n < 10 ? "0" : "") + n;
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + "T" +
         p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
}

// ── فیکسچرهای مشترک — شکلِ فعلیِ هر مسیر، نه شکلِ قدیمیِ /api/ops ──────────
const STATE_OK = {status: "ok", halted: false, frozen: false, beat: 23091,
  epoch_mode: "allostatic", ts: nowIso(), month: {key: "2026-08"}, conflicts: [],
  active_flags: {OCTOPUS_WIRE_TG_CONTROL: true}, auth_status: "configured",
  miniapp_url_configured: true, commit: "abc1234",
  cardiac: {status: "ok", pct: 10, cap: 100, spent: 10, depleted: false, resting: false},
  arbiter: {color: "GREEN"}, recall_reach: {events: 1, reach_median: 1},
  germline_alert: "ok", germline_lag_h: 0.1};
const APPROVALS_OK = {status: "ok", pending: [], count: 0, decisions: []};
const TASKS_OK = {status: "ok", tasks_total: 0, task_status: {}, items: []};
const GOVERNOR_OK = {policy_doc: "x", canonical_provider: "y",
  canonical_choke_point: "z", drift_status: {status: "aligned", declared_paths: []}};
const OBSIDIAN_OK = {missing: [], checked: 5};
const LEGS_OK = {status: "ok", legs: {lead: {live: true}}};
const LEADS_OK = {status: "ok", leads_total: 0, lead_stages: {}, items: []};

function boot(){
  const code = fs.readFileSync(APP, "utf8");
  const fn = new Function("window", "document", "fetch", code);
  fn(windowStub, documentStub, fetchStub);
}
function withOwner(){ windowStub.Telegram = {WebApp: {initData: "INIT_DATA_TOKEN_XYZ", expand(){}, setHeaderColor(){}}}; }
function html(id){ const e = registry.get(id); return e ? e.innerHTML : null; }
// تبی که با stack() ساخته می‌شود (approvals/money/leads/system) محتوایش را
// در sec0..secN می‌گذارد، نه در content مستقیم — home تنها استثناست.
function stackContent(){
  let s = "", i = 0;
  while(registry.has("sec" + i)){ s += (registry.get("sec" + i).innerHTML || ""); i++; }
  return s;
}
function clickTab(key){
  const t = tabsEl.children.filter(x => x.getAttribute("data-tab") === key)[0];
  tabsEl.dispatch("click", {target: t});
}

(async function(){
try {
  if(SCENARIO === "header"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/approvals": {body: APPROVALS_OK},
              "/api/ops/tasks": {body: TASKS_OK}, "/api/governor": {body: GOVERNOR_OK},
              "/api/obsidian": {body: OBSIDIAN_OK}, "/api/legs": {body: LEGS_OK}};
    boot(); await flush();
    out.fetch_count = fetchLog.length;
    out.headers = fetchLog.map(f => f.headers["X-Tg-Init-Data"]);
    out.urls = fetchLog.map(f => f.url);
  }

  else if(SCENARIO === "no_post_on_render"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/approvals": {body: APPROVALS_OK},
              "/api/ops/tasks": {body: TASKS_OK}, "/api/governor": {body: GOVERNOR_OK},
              "/api/obsidian": {body: OBSIDIAN_OK}, "/api/legs": {body: LEGS_OK},
              "/api/ops/leads": {body: LEADS_OK}};
    boot(); await flush();
    for(const k of out.tab_keys){ clickTab(k); await flush(); }
    out.post_count = fetchLog.filter(f => f.method === "POST").length;
    out.rendered_tabs = out.tab_keys.length;
  }

  else if(SCENARIO === "owner_actions"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops/leads": {body: LEADS_OK},
              "/api/ops/tasks": {body: TASKS_OK},
              "/api/actions": {body: {ok: true, status: "APPLIED", lead_id: "lead:1"}}};
    boot(); await flush();

    clickTab("leads"); await flush();
    const handle = registry.get("nlHandle"); if(handle) handle.value = "@someone";
    const nlGo = registry.get("nlGo");
    out.lead_button_found = !!nlGo;
    if(nlGo) nlGo.dispatch("click", {});
    await flush();

    clickTab("tasks"); await flush();
    const title = registry.get("ntTitle"); if(title) title.value = "پیگیریِ لید";
    const ntGo = registry.get("ntGo");
    out.task_button_found = !!ntGo;
    if(ntGo) ntGo.dispatch("click", {});
    await flush();

    const posts = fetchLog.filter(f => f.method === "POST");
    out.post_count = posts.length;
    out.post_urls = posts.map(p => p.url);
    out.post_bodies = posts.map(p => p.body);
    out.post_headers = posts.map(p => p.headers["X-Tg-Init-Data"]);
  }

  else if(SCENARIO === "readonly_no_client_gate"){
    // بدونِ initData ِ تلگرام. سؤال: آیا کلاینت خودش دکمه را قفل می‌کند؟
    windowStub.Telegram = undefined;
    routes = {"/api/state": {body: STATE_OK}, "/api/ops/leads": {body: LEADS_OK},
              "/api/actions": {body: {ok: true, status: "APPLIED"}}};
    boot(); await flush();
    clickTab("leads"); await flush();
    out.leads_tab_html = stackContent();
    const handle = registry.get("nlHandle"); if(handle) handle.value = "@readonly";
    const nlGo = registry.get("nlGo");
    out.lead_button_found = !!nlGo;
    if(nlGo) nlGo.dispatch("click", {});
    await flush();
    const posts = fetchLog.filter(f => f.method === "POST");
    out.post_count = posts.length;
    out.post_headers = posts.map(p => p.headers["X-Tg-Init-Data"]);
  }

  else if(SCENARIO === "governor_escape"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK},
              "/api/governor": {body: Object.assign({}, GOVERNOR_OK,
                {policy_doc: '<img src=x onerror="boom()">&<b>bold</b>'})}};
    boot(); await flush();
    clickTab("system"); await flush();
    out.system_tab_html = stackContent();
  }

  else if(SCENARIO === "lifecycle_missing_id"){
    withOwner();
    routes = {
      "/api/state": {body: STATE_OK},
      "/api/approvals": {body: APPROVALS_OK},
      "/api/lifecycle": {body: {
        status: "ok",
        by_stage: {value: {STALLED: 2}},
        total_cards: {value: 2},
        stalled_list: [
          {created_ts: 1787960000, age_days: 4},
          {rfc_id: "RFC-test-1", created_ts: 1787960100, age_days: 4}
        ],
        stalled_list_truncated: 0,
        sources: ["fixture"]
      }}
    };
    boot(); await flush();
    clickTab("approvals"); await flush();
    out.lifecycle_html = stackContent();
  }

  else { out.error = "unknown scenario"; }
} catch(e){ out.error = String(e && e.stack || e); }
process.stdout.write(JSON.stringify(out));
})();
"""


def _node() -> str:
    exe = shutil.which("node")
    assert exe, ("node پیدا نشد — لایهٔ اجرایی این تست بدونِ Node معنا ندارد. "
                 "این را «سبز» نمی‌شماریم؛ صریح قرمز است تا کسی پوششِ کاذب فرض نکند.")
    return exe


_DRIVER_PATH = None


def _driver_path() -> Path:
    global _DRIVER_PATH
    if _DRIVER_PATH is None:
        d = Path(tempfile.mkdtemp(prefix="cockpit-ui-"))
        p = d / "driver.js"
        p.write_text(_DRIVER, encoding="utf-8", newline="\n")
        _DRIVER_PATH = p
    return _DRIVER_PATH


def run_scenario(name: str, app_js: "Path | None" = None,
                 fixture: "Path | str | None" = None) -> dict:
    exe = _node()
    app = str(app_js or APP_JS)
    cmd = [exe, str(_driver_path()), app, str(INDEX_HTML), name]
    if fixture is not None:
        cmd.append(str(fixture))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90, encoding="utf-8")
    assert r.returncode == 0, f"node خطا داد ({r.returncode}): {r.stderr[:800]}"
    assert r.stdout.strip(), f"درایور چیزی چاپ نکرد. stderr={r.stderr[:400]}"
    d = json.loads(r.stdout)
    assert not d.get("error"), f"{name}: {d.get('error')}"
    return d


# ══ لایهٔ ۱: ناوردای متنی ═══════════════════════════════════════════════════

def t_a_the_init_data_header_literal_survives_verbatim():
    """قراردادِ غیرقابلِ‌مذاکره: هدر دقیقاً به همین شکل نوشته شده باشد.

    شکلِ ۰۸-۰۳ (`if(tg && tg.initData)` بی‌واسطه) با helper ِ `tgHeaders()`
    جایگزین شده؛ رفتار یکی است (هدر فقط وقتی initData هست فرستاده می‌شود)
    ولی قرارداد صریح و گرپ‌شدنی است."""
    s = src(APP_JS)
    assert "function tgHeaders(" in s, "helper ِ tgHeaders حذف شده"
    assert HEADER_LITERAL in s, "لیترالِ هدرِ X-Tg-Init-Data از app.js حذف/تغییر کرده"
    assert s.count('"X-Tg-Init-Data"') == 1, "هدر باید فقط یک نقطهٔ تعریف داشته باشد"


def t_b_the_tristate_helper_never_renders_unknown_as_green():
    """۰۸-۰۳: `triState`/`badge3`/`badgeClass` — هیچ‌کدام دیگر در app.js نیست
    (grep تأیید کرد: صفر رخداد برای هر سه). جانشین‌شان `tri()` است: یک
    تابعِ سه‌حالتیِ واحد که null/undefined را به بجِ «unknown» می‌برد، نه به
    yes/no. این تست معادلِ تازه را می‌سنجد، نه اسمِ کهنه را."""
    s = src(APP_JS)
    for dead in ("function triState(", "function badge3(", "function badgeClass("):
        assert dead not in s, f"{dead} برگشته؟ این تست باید آپدیت شود، نه اینکه صرفاً پاس کند"
    assert "function tri(" in s, "helper ِ سه‌حالتیِ جانشین (tri) نیست"
    m = re.search(r"function tri\(v, yes, no\)\{(.*?)\n  \}", s, re.S)
    assert m, "بدنهٔ tri() پیدا نشد"
    body = m.group(1)
    assert 'if(v===null||v===undefined) return \'<span class="badge unknown">' in body, \
        "tri() دیگر null/undefined را به بجِ unknown نمی‌برد"
    css = src(STYLE_CSS)
    assert ".badge.unknown{" in css, "کلاسِ unknown در CSS تعریف نشده"
    unk_blocks = re.findall(r"\.badge\.unknown\{([^}]*)\}", css)
    assert unk_blocks, "بدنهٔ .badge.unknown پیدا نشد"
    for blk in unk_blocks:
        assert "--cyan" not in blk and "--green" not in blk, \
            "کلاسِ unknown رنگِ زنده گرفته — دقیقاً همان حالتِ شکست"


def t_c_panel_guard_never_lets_bad_or_missing_data_render_as_healthy():
    """۰۸-۰۳ این قاعده را با ~۱۰ سناریوی جدا روی `/api/ops` ِ ترکیبی می‌سنجید
    (unknown_not_green، degraded_and_ok، section_present_without_status، …).
    آن endpoint دیگر از UI صدا زده نمی‌شود (grep: صفر `api("/api/ops")` ِ
    بدونِ زیرمسیر در app.js فعلی) — یعنی آن ده سناریو موضوعِ صداکننده‌شان را
    از دست داده‌اند، نه معادلی دارند که بشود لنگرِ تازه رویش گذاشت.

    قاعده‌ای که آن ده سناریو می‌سنجیدند («status:error/unknown هرگز سبز
    نمی‌شود») امروز در یک گاردِ **مشترک** برای همهٔ پنل‌های تازه متمرکز شده:
    `panelGuard()`. این تست همان قاعده را روی خودِ گارد می‌سنجد — ارزان‌تر
    از اجرای Node با فیکسچرهای per-endpoint، و چون یک گاردِ واحد است (نه ده
    وصلهٔ موردی)، یک تست کلِ پنج مسیرِ مصرف‌کننده‌اش (brain/governor/
    obsidian/registry/legs) را می‌پوشاند.

    ⚠️ ۲۰۲۶-۰۸-۰۹: `renderLegs` تا امروز از این گارد رد نمی‌شد — با
    `/api/legs` ِ status:"unknown" (business_legs گم) قرصِ «۰ از ۰» با تُنِ
    live (سبز) می‌ساخت. اضافه شد تا این فایل دوباره پنج‌تایی را بپوشاند."""
    s = src(APP_JS)
    m = re.search(r"function panelGuard\(title, d\)\{(.*?)\n  \}", s, re.S)
    assert m, "panelGuard() پیدا نشد"
    body = m.group(1)
    for bad_status in ('s === "error"', 's === "unknown_schema"', 's === "unknown"',
                       's === "disabled"', 's === "not_found"'):
        assert bad_status in body, f"panelGuard دیگر {bad_status} را نمی‌شناسد"
    # هیچ‌کدام از شاخه‌های بد نباید کلاسِ «زنده» (live) بدهند
    for m2 in re.finditer(r'pill\("[^"]*",\s*"([a-z]+)"\)', body):
        assert m2.group(1) != "live", "شاخهٔ دادهٔ بد/نامعلوم رنگِ live گرفته"
    assert body.rstrip().endswith("return null;"), \
        "شاخهٔ پیش‌فرضِ panelGuard دیگر null نیست — یعنی داده ممکن است بی‌بررسی رد شود"
    consumers = ["renderBrain(", "renderGovernor(", "renderObsidian(", "renderRegistry(",
                "renderLegs("]
    for c in consumers:
        assert c in s, f"{c} حذف شده"
    for c in consumers:
        fn_m = re.search(re.escape(c) + r"el\)\{(.*?)\n  \}", s, re.S)
        assert fn_m and "panelGuard(" in fn_m.group(1), \
            f"{c} دیگر از panelGuard رد نمی‌شود — می‌تواند دادهٔ بد را سبز نشان دهد"


def t_d_every_mutation_targets_the_one_gated_endpoint():
    """۰۸-۰۳ فرض می‌کرد `apiPost` دقیقاً یک صداکننده دارد (از راهِ `act()`)
    و یک `PALETTE_GATE` جدا برای پالت. هر دو دیگر درست نیست:

      · پالت از app.js حذف شده (grep: صفر «palette»/«Palette») — چیزی برای
        گیت‌کردن نمانده.
      · `apiPost` امروز ۳ صداکننده دارد، نه ۱: `act()` (مسیرِ زنده — همهٔ
        شش اقدامِ allowlist‌شده از این‌جا رد می‌شوند) + دو صداکنندهٔ داخلِ
        `renderStudio` که **مردهٔ دست‌نخورده** است — تابعش هست ولی از جدولِ
        `renderers` برداشته شده (کامنتِ خودِ فایل: «renderStudio از این‌جا
        برداشته شد»)، پس هیچ تبی صدایش نمی‌زند. این تست آن دو را جدا
        می‌کند: تأکید روی «همه به /api/actions می‌روند»، نه «فقط یک‌بار
        تعریف شده‌اند» — چون دومی الان به‌خاطرِ کدِ مرده رد می‌شود، نه چون
        قرارداد شکسته.

    ⚠️ ۲۰۲۶-۰۸-۰۹: دکمهٔ «ری‌استارتِ کامل» یک صداکنندهٔ لیترالِ سوم اضافه
    کرد — `apiPost("/api/restart", ...)`. «فقط /api/actions» دیگر درست
    نیست. به‌جای هاردکدکردنِ یک فهرستِ دومِ موازی (که خودش دقیقاً به همین
    شکل کهنه شد)، حالا از خودِ allowlistِ POST در miniapp_gateway.py
    می‌خواند — یک منبعِ حقیقت، نه دو کپی که می‌توانند از هم جدا بیفتند."""
    s = src(APP_JS)
    assert SINGLE_POST_SITE in s, "تکْ‌نقطهٔ act()->apiPost عوض شده"
    gw = src(GATEWAY_PY)
    gm = re.search(r"p not in \(([^)]*)\):\s*\n\s*return 405", gw)
    assert gm, "allowlistِ POST در miniapp_gateway.py پیدا نشد — این تست کور شده"
    allowed = set(x.strip() for x in gm.group(1).split(","))
    calls = re.findall(r"apiPost\(\s*(\"[^\"]*\")", s)
    assert calls, "هیچ فراخوانِ apiPost یافت نشد"
    bad = sorted(set(c for c in calls if c not in allowed))
    assert not bad, f"apiPost به مسیرِ خارج از allowlistِ سرور می‌رود: {bad} (مجاز: {sorted(allowed)})"
    assert "function renderStudio(" in s, \
        "renderStudio حذف شده — اگر عمدی است این تست را به‌روز کن (دیگر کدِ مرده نیست)"
    assert '"renderers = {' not in s.replace(" ", "")  # sanity: فقط برای اطمینان از فرمت
    m = re.search(r"var renderers = \{([^}]*)\}", s)
    assert m and "studio" not in m.group(1), \
        "studio به جدولِ renderers برگشته — یعنی renderStudio دیگر مرده نیست، این تست باید عوض شود"
    for bad in ('method:"PUT"', 'method:"DELETE"', "method: 'POST'"):
        assert bad not in s, f"مسیرِ نوشتنِ دیگری در فرانت: {bad}"


def t_e_index_html_has_every_current_tab_and_the_gateway_injection_anchor():
    """۰۸-۰۳ ۱۲ تب با برچسبِ انگلیسی می‌خواست (Cockpit/Ops/Brain/…) و یک
    دکمه/ظرفِ پالت. هر دو دیگر واقعیت ندارند: تب‌ها ۶تا شده‌اند و برچسبِ
    فارسی گرفته‌اند؛ پالت حذف شده. `</body>` نگه داشته شده چون هنوز واقعی
    است — `miniapp_gateway.py` هنوز با `body.replace(b"</body>", …)` روی
    همین لنگر اسنیپتِ initData را تزریق می‌کند (فایلِ دیگری، این‌جا فقط
    وجودِ لنگر سنجیده می‌شود)."""
    h = src(INDEX_HTML)
    tabs_fa = {"home": "خانه", "approvals": "تأییدها", "money": "پول",
               "leads": "لیدها", "tasks": "کارها", "system": "سیستم"}
    for key, label in tabs_fa.items():
        assert f'data-tab="{key}"' in h, f"تبِ {key} در index.html نیست"
        assert f'>{label}</div>' in h, f"برچسبِ فارسیِ تبِ {key} ({label}) نیست"
    for dead_key in ("studio", "brain", "governor", "obsidian", "next",
                     "outbound", "legs", "value", "registry", "truth"):
        assert f'data-tab="{dead_key}"' not in h, \
            f"تبِ {dead_key} برگشته — اگر عمدی است این تست را به‌روز کن"
    assert "paletteBtn" not in h and 'id="palette"' not in h, \
        "دکمه/ظرفِ پالت برگشته — اگر عمدی است این تست را به‌روز کن"
    assert "</body>" in h, "لنگرِ تزریقِ initData ِ gateway از بین رفته"


def t_f_no_secret_value_lands_in_the_frontend():
    """نامِ متغیرِ محیطی مجاز است (مالک باید بداند کدام env را ست کند)؛
    **مقدار** هرگز. پس این تست دنبالِ الگویِ مقدار و انتساب می‌گردد، نه نام.

    (نسخهٔ اولِ همین تست صرفاً نام را ممنوع کرده بود و روی متنِ راهنمای خودِ
    مالک قرمز شد — یک منفیِ کاذب که اگر «رفع» می‌شد، راهنما را می‌کُشت.)"""
    for p in (APP_JS, INDEX_HTML, STYLE_CSS):
        s = src(p)
        assert not re.search(r"\b\d{8,12}:AA[A-Za-z0-9_-]{20,}", s), f"{p.name}: الگویِ توکنِ بات"
        assert not re.search(r"\bsk-[A-Za-z0-9_-]{20,}", s), f"{p.name}: کلیدِ sk-*"
        assert not re.search(r"\b[0-9a-fA-F]{64}\b", s), f"{p.name}: هگزِ ۶۴کاراکتری"
        for name in ("TG_CENTER_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID"):
            for m in re.finditer(re.escape(name), s):
                tail = s[m.end():m.end() + 4]
                assert not re.match(r"\s*[:=]", tail), \
                    f"{p.name}: به {name} مقدار داده شده — فقط نام مجاز است"
        assert "Bearer " not in s and "Authorization" not in s, f"{p.name}: هدرِ اعتبارنامه در فرانت"


# ══ لایهٔ ۲: اجرای واقعی در Node ════════════════════════════════════════════
#
# ۰۸-۰۳ حدودِ ۲۰ سناریو داشت — بیشترشان روی زیرساختی می‌ایستادند که دیگر
# نیست: `window.__cockpit` (gotoTab/runCommand/bootTab برای پالت و
# دیپ‌لینک)، کشِ localStorage با برچسبِ stale، coalescing (`inflight`)،
# debounce، و گریدِ tile ِ `/api/ops`. هر پنج‌تا با grep روی app.js صفر
# رخداد دادند. حذف شدند، نه بازنویسی — چون بازنویسیِ صادقانه یعنی ساختنِ
# fixture برای ~۱۵ endpoint ِ جدا و یک موتورِ selector ِ واقعی برای DOM
# (این درایور درختِ parent/child ندارد)، که خودش یک پروژهٔ جداست، نه رفعِ
# لنگرِ حرفی. فهرستِ دقیق:
#   · پالت/Ctrl+K (palette_html) — عنصر از UI حذف شده.
#   · دیپ‌لینکِ #tab= (deep_link) — window.location/hash هیچ‌جا خوانده نمی‌شود.
#   · کشِ محلی + برچسبِ stale (stale_cache، error_body_is_not_cached) —
#     صفر رخداد برای localStorage.setItem/getItem در app.js.
#   · coalescing/debounce (coalesce) — صفر رخداد برای inflight/
#     REFRESH_DEBOUNCE_MS/scheduleRefresh.
#   · نقاشیِ دیرهنگام روی تبِ عوض‌شده (paint_guard) — هیچ render ِ فعلی
#     چک نمی‌کند که تبش هنوز فعال است؛ این گارد واقعاً از کد رفته (نه
#     فقط لنگرش)، یعنی یک واپس‌روی است، ولی رفعش کارِ app.js است نه تست.
#   · گریدِ `<div class="tile st-X">` روی `/api/ops` ِ ترکیبی (unknown_
#     not_green، degraded_and_ok، section_present_without_status،
#     partial_next_is_not_allclear، stale_beat_is_degraded، state_error_
#     is_unknown، sub_endpoint_probe_once، honesty_edges، live_payload،
#     envelope_status_must_not_leak) — این ده‌تا یک واحد بودند چون همه از
#     همان یک endpoint می‌خواندند؛ قاعدهٔ مشترک‌شان («بد/نامعلوم هرگز سبز
#     نمی‌شود») در لایهٔ ۱ به‌عنوانِ t_c روی panelGuard() نگه داشته شد.
#
# نگه‌داشته/جایگزین‌شده: هدر-روی-هر-درخواست، رندرِ صرف بدونِ POST، تکْ‌نقطهٔ
# اقدامِ مالک (حالا با دو اقدامِ واقعی: lead.create/task.create)، و escape
# — به‌علاوهٔ یک تستِ تازه که رفتارِ **واقعیِ** امروز را دربارهٔ read-only
# مستند می‌کند (چون بنرِ متنیِ قدیمی دیگر در مسیرِ زنده نیست).

def t_g_the_header_is_on_every_single_request():
    d = run_scenario("header")
    assert d["fetch_count"] >= 6, d  # viewHome تنها خودش شش مسیر می‌خواند
    assert all(h == "INIT_DATA_TOKEN_XYZ" for h in d["headers"]), d["headers"]
    assert "/api/state" in d["urls"], d["urls"]


def t_h_rendering_never_mutates_anything():
    # ⚠️ ۲۰۲۶-۰۸-۰۹: قبلاً `== 6` هاردکد بود (نوشته‌شده وقتی ۶ تب بود).
    # تبِ هفتم/هشتم/نهم (notifications/scans/ask، ۰۸-۰۷..۰۸-۰۸) اضافه شدند
    # و این عدد هرگز به‌روز نشد — همان الگویی که این فایل خودش بارها
    # هشدار داده: عددِ ثابت جای سنجهٔ زنده. حالا از خودِ index.html می‌خواند.
    expected = len(re.findall(r'data-tab="[^"]+"', src(INDEX_HTML)))
    d = run_scenario("no_post_on_render")
    assert d["rendered_tabs"] == expected, (d["rendered_tabs"], expected)
    assert d["post_count"] == 0, "رندرِ صرف یک POST تولید کرد — سطحِ خواندن نباید بنویسد"


def t_i_owner_actions_post_only_to_the_gated_endpoint():
    """جانشینِ t_n ِ قدیمی. آن یکی یک دکمهٔ دیفالتِ فرضی (`leadCreate`) در
    تبِ studio ِ حذف‌شده کلیک می‌کرد. این نسخه دو اقدامِ **واقعاً زنده** را
    از دو تبِ واقعی امتحان می‌کند: ساختِ لید (تبِ لیدها) و ساختِ کار (تبِ
    کارها). هر دو باید فقط از `act()` رد شوند: هدر روی هر دو، action_id
    ست، و مقصد همیشه `/api/actions`."""
    d = run_scenario("owner_actions")
    assert d["lead_button_found"] is True, "دکمهٔ ساختِ لید (#nlGo) پیدا نشد"
    assert d["task_button_found"] is True, "دکمهٔ ساختِ کار (#ntGo) پیدا نشد"
    assert d["post_count"] == 2, (d["post_count"], d["post_urls"])
    assert d["post_urls"] == ["/api/actions", "/api/actions"], d["post_urls"]
    assert d["post_headers"] == ["INIT_DATA_TOKEN_XYZ", "INIT_DATA_TOKEN_XYZ"], d["post_headers"]
    lead_body = json.loads(d["post_bodies"][0])
    assert lead_body["action"] == "lead.create", lead_body
    assert lead_body["payload"]["handle"] == "@someone", lead_body
    assert lead_body["action_id"].startswith("mini:lead.create:"), lead_body
    task_body = json.loads(d["post_bodies"][1])
    assert task_body["action"] == "task.create", task_body
    assert task_body["payload"]["title"] == "پیگیریِ لید", task_body
    assert task_body["action_id"].startswith("mini:task.create:"), task_body


def t_j_without_owner_auth_the_client_does_not_block_mutating_taps():
    """۰۸-۰۳ فرض می‌کرد بدونِ initData دکمه‌ها `disabled` می‌شوند و یک بنرِ
    «Read-only Mode» ظاهر می‌شود. آن رفتار فقط داخلِ `renderStudio` ِ
    مرده بود (خودِ t_d این را نشان داد). در مسیرهای **زنده**ٔ امروز
    (renderLeadOps) هیچ گیتِ سمتِ کلاینت نیست: دکمه فعال می‌ماند و کلیک
    واقعاً POST می‌زند.

    این یک واپس‌روی نسبت به قبل است (بدونِ initData، درخواست هیچ هدرِ
    X-Tg-Init-Data ای هم ندارد — چون `tgHeaders()` وقتی initData نیست
    کلید را اصلاً اضافه نمی‌کند)، ولی رفعش تغییرِ app.js می‌خواهد که خارج
    از دامنهٔ این تست است. این تست عمداً **رفتارِ واقعی** را قفل می‌کند تا
    اگر یک روز درست شد (یا بدتر شد)، این‌جا قرمز شود — نه اینکه بی‌صدا رد
    شود."""
    d = run_scenario("readonly_no_client_gate")
    assert d["lead_button_found"] is True, "دکمهٔ ساختِ لید در حالتِ بدونِ initData رندر نشد"
    idx = d["leads_tab_html"].find('id="nlGo"')
    assert idx >= 0, "دکمهٔ #nlGo در HTML نیست"
    tag_end = d["leads_tab_html"].find(">", idx)
    assert "disabled" not in d["leads_tab_html"][idx:tag_end], (
        "این‌جا انتظار می‌رفت disabled نباشد (رفتارِ فعلی) — اگر گاردِ سمتِ "
        "کلاینت اضافه شده، این تست را با خیالِ راحت به سمتِ «باید disabled "
        "باشد» برگردان.")
    assert d["post_count"] == 1, (
        "بدونِ initData، کلیک دیگر POST نزد — یعنی یک گاردِ سمتِ کلاینت "
        "اضافه شده؛ این تست را به‌روز کن (خبرِ خوب است، ولی رفتار عوض شده)")
    assert d["post_headers"] == [None], (
        "درخواستِ بدونِ initData باید هیچ X-Tg-Init-Data ای نداشته باشد "
        "(نه حتی رشتهٔ خالی) — سرور تنها گاردِ معتبر است")


def t_k_backend_values_are_html_escaped_before_they_are_painted():
    """`esc()` یک گارد است، پس باید جهشی داشته باشد که بکُشدش.

    جانشینِ t_zz ِ قدیمی که از پاکتِ `/api/ops` ِ حذف‌شده استفاده می‌کرد؛
    این نسخه از `/api/governor` (زیرِ تبِ سیستم، پنلِ زنده) همان تزریق را
    امتحان می‌کند."""
    d = run_scenario("governor_escape")
    c = d["system_tab_html"]
    assert "&lt;img src=x onerror=&quot;boom()&quot;&gt;" in c, "مقدارِ بک‌اند escape نشد"
    assert "<img src=x" not in c, "markup ِ خام وارد DOM شد"
    assert "<b>bold</b>" not in c, "تگِ خام از مقدارِ بک‌اند رد شد"


def t_l_lifecycle_card_without_id_is_read_only_not_undefined():
    d = run_scenario("lifecycle_missing_id")
    html = d["lifecycle_html"]
    facts = {
        "undefined_rendered": "undefined" in html,
        "approve_buttons": html.count('class="ryes"'),
        "reject_buttons": html.count('class="rno"'),
    }
    assert not facts["undefined_rendered"], html
    assert facts["approve_buttons"] == 1, html
    assert facts["reject_buttons"] == 1, html
    assert 'data-pid="RFC-test-1"' in html, html
    assert "شناسهٔ تصمیم در پاسخ نیست" in html, html


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_cockpit_ui: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
