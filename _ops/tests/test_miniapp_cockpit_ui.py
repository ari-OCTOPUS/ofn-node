#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_cockpit_ui — کاکپیتِ Mini App نباید دروغ بگوید.

این فایل دو لایه دارد و عمداً هر دو را دارد:

  ۱) گرپِ ناوردا روی app.js/index.html/style.css — ارزان، ولی فقط «هست/نیست»
     را می‌گوید. یک گرپِ تنها هرگز نمی‌گوید کد **چه می‌کند**.
  ۲) اجرایِ واقعیِ app.js داخلِ Node با یک DOM/fetch ِ ساختگی. این لایه رفتار
     را می‌سنجد: هدر روی هر درخواست، رنگِ نشانگر روی دادهٔ غایب، ننوشتنِ تبِ
     کهنه روی تبِ فعال، قفلِ read-only، کشِ برچسب‌خورده، و اینکه تغییرِ حالت
     فقط از /api/actions می‌گذرد.

چیزی که این تست **نمی‌سنجد** (صادقانه، تا کسی پوششِ کاذب فرض نکند):
  · رندرِ واقعیِ مرورگر، CSS، RTL و اینکه دکمهٔ disabled واقعاً کلیک نمی‌گیرد.
    گاردِ واقعیِ read-only در مرورگر همان attribute ِ `disabled` است؛ اینجا
    فقط حضورش در HTML سنجیده می‌شود. گاردِ **معتبر** سمتِ سرور است
    (`/api/actions` → 403 owner_auth_required) که تستِ خودش را دارد.
  · Telegram WebApp واقعی و امضایِ initData.
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
STYLE_CSS = MINIAPP / "style.css"

# ── لنگرهای یکتا ────────────────────────────────────────────────────────────
# هرکدام دقیقاً یک بار در app.js می‌آید؛ جهش روی همین رشته‌ها تست را می‌کُشد.
HEADER_LITERAL = '"X-Tg-Init-Data": window.Telegram?.WebApp?.initData || ""'
PAINT_GUARD = 'if(activeTab !== tab) return false;'
TRISTATE_FALLBACK = 'return "unknown";     // شکِ باقی‌مانده = unknown، هرگز ok'
PALETTE_GATE = 'if(COMMANDS[i].mutating && devMode) return false;'
SINGLE_POST_SITE = 'return apiPost("/api/actions", {action:action, payload:payload})'
COALESCE = 'if(inflight[path]) return inflight[path];'

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
El.prototype.addEventListener = function(t, f){ (this._listeners[t] = this._listeners[t] || []).push(f); };
El.prototype.dispatch = function(t, ev){ (this._listeners[t] || []).forEach(f => f(ev || {})); };
El.prototype.focus = function(){ focusLog.push(this.id); };
El.prototype.closest = function(sel){ const c = String(sel).replace(/^\./, ""); return this.classList.contains(c) ? this : null; };

function ensure(id, cls){ if(!registry.has(id)) registry.set(id, new El(id, cls)); return registry.get(id); }
function harvest(html){
  const re = /id="([^"]+)"/g; let m;
  while((m = re.exec(html)) !== null){ ensure(m[1]); }
}

const indexHtml = fs.readFileSync(INDEX, "utf8");
harvest(indexHtml);
const tabsEl = ensure("tabs");
const tabRe = /<div class="tab([^"]*)" data-tab="([^"]+)">([^<]*)<\/div>/g;
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
  dispatch(t, ev){ (this._listeners[t] || []).forEach(f => f(ev || {})); }
};

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
const flush = async (n) => { for(let i = 0; i < (n || 12); i++){ await new Promise(r => setImmediate(r)); } };

const STATE_OK = {status: "ok", halted: false, frozen: false, beat: 23091,
  epoch_mode: "allostatic", ts: nowIso(), month: {key: "2026-08"}, conflicts: [],
  active_flags: {OCTOPUS_WIRE_TG_CONTROL: true, OCTOPUS_WIRE_LEAD_OUTBOUND_WAL: true, OCTOPUS_WIRE_VALUE_LEDGER: true},
  auth_status: "configured", miniapp_url_configured: true, commit: "abc1234"};
const OPS_BARE = {status: "ok", leads_total: 3, tasks_total: 1, value_events_total: 0,
  lead_stages: {new: 3}, task_status: {open: 1}, value_events_per_leg: {}};

function nowIso(){
  const d = new Date(), p = n => (n < 10 ? "0" : "") + n;
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + "T" +
         p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
}

function boot(){
  const code = fs.readFileSync(APP, "utf8");
  const fn = new Function("window", "document", "fetch", code);
  fn(windowStub, documentStub, fetchStub);
}
function withOwner(){ windowStub.Telegram = {WebApp: {initData: "INIT_DATA_TOKEN_XYZ", expand(){}, setHeaderColor(){}}}; }
function html(id){ const e = registry.get(id); return e ? e.innerHTML : null; }
function clickTab(key){
  const t = tabsEl.children.filter(x => x.getAttribute("data-tab") === key)[0];
  tabsEl.dispatch("click", {target: t});
}

(async function(){
try {
  if(SCENARIO === "header"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};
    boot(); await flush();
    out.fetch_count = fetchLog.length;
    out.headers = fetchLog.map(f => f.headers["X-Tg-Init-Data"]);
    out.urls = fetchLog.map(f => f.url);
  }

  else if(SCENARIO === "unknown_not_green"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};
    boot(); await flush();
    out.content = html("content");
  }

  else if(SCENARIO === "degraded_and_ok"){
    withOwner();
    const ops = Object.assign({}, OPS_BARE, {
      brain: {status: "ok", detail: "4d online"},
      governor: {status: "degraded", detail: "budget tight"},
      obsidian: {status: "ok", detail: "vault synced"},
      next_steps: {followups_due: 2, leads_needing_stage: 0, drafts_pending: 0, consolidation_stale_days: 0}});
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: ops}};
    boot(); await flush();
    out.content = html("content");
  }

  else if(SCENARIO === "live_payload"){
    // fixture از خروجیِ **واقعیِ** miniapp_state.dispatch_api می‌آید، نه از
    // چیزی که من حدس زده‌ام. اگر لِینِ read-model شکلِ داده را عوض کند، این
    // سناریو همان لحظه می‌ترکد.
    withOwner();
    const fx = JSON.parse(fs.readFileSync(FIXTURE, "utf8"));
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: fx.ops},
              "/api/ops/brain": {body: fx.sub_brain}};
    boot(); await flush();
    out.content = html("content");
    windowStub.__cockpit.gotoTab("brain"); await flush();
    out.brain_tab = html("content");
    windowStub.__cockpit.gotoTab("next"); await flush();
    out.next_tab = html("content");
    windowStub.__cockpit.gotoTab("governor"); await flush();
    out.governor_tab = html("content");
  }

  else if(SCENARIO === "envelope_status_must_not_leak"){
    // پاکتِ زیرمسیر status:"ok" دارد ولی محتوایش available:false است.
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE},
              "/api/ops/brain": {body: {status: "ok", section: "brain",
                                        brain: {available: false, reason: "daemon_state.json غایب"}}}};
    boot(); await flush();
    windowStub.__cockpit.gotoTab("brain"); await flush();
    out.brain_tab = html("content");
  }

  else if(SCENARIO === "section_present_without_status"){
    withOwner();
    // بخش **هست** ولی هیچ کلیدِ status/state/health ندارد. این حالت با «بخش
    // نیست» فرق دارد و مسیرِ کدِ دیگری را می‌رود — پس تستِ خودش را می‌خواهد.
    const ops = Object.assign({}, OPS_BARE, {
      brain: {detail: "some detail, no status key"},
      governor: {status: "ok"},
      obsidian: {note: "no status here either"}});
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: ops}};
    boot(); await flush();
    out.content = html("content");
  }

  else if(SCENARIO === "partial_next_is_not_allclear"){
    withOwner();
    const ops = Object.assign({}, OPS_BARE, {next_steps: {followups_due: 0, drafts_pending: 0}});
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: ops}};
    boot(); await flush();
    out.content = html("content");
  }

  else if(SCENARIO === "readonly"){
    windowStub.Telegram = undefined;                 // بدونِ initData
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};
    boot(); await flush();
    out.warn = html("warn");
    clickTab("studio"); await flush();
    out.content = html("content");
    out.palette_gate_blocked = (windowStub.__cockpit.runCommand("lead.create") === false);
    out.readonly_cmd_ok = (windowStub.__cockpit.runCommand("brain.status") === true);
  }

  else if(SCENARIO === "owner_actions"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE},
              "/api/actions": {body: {ok: true, status: "APPLIED", lead_id: "lead:1"}}};
    boot(); await flush();
    clickTab("studio"); await flush();
    out.content = html("content");
    const btn = registry.get("leadCreate");
    out.button_found = !!btn;
    const handle = registry.get("leadHandle"); if(handle) handle.value = "@someone";
    if(btn) btn.dispatch("click", {});
    await flush();
    const posts = fetchLog.filter(f => f.method === "POST");
    out.post_count = posts.length;
    out.post_urls = posts.map(p => p.url);
    out.post_bodies = posts.map(p => p.body);
    out.post_headers = posts.map(p => p.headers["X-Tg-Init-Data"]);
    out.result_text = registry.get("leadResult") ? registry.get("leadResult").textContent : null;
  }

  else if(SCENARIO === "paint_guard"){
    withOwner();
    let releaseState = null;
    routes = {
      "/api/state": () => new Promise(r => { releaseState = () => r(resp(200, STATE_OK)); }),
      "/api/ops": {body: OPS_BARE},
      "/api/legs": {body: {status: "ok", legs: {lead: {live: true, signal: "sig-lead"}}}}
    };
    boot();                       // renderHome شروع شد ولی /api/state معلق است
    clickTab("legs"); await flush();
    out.after_switch = html("content");
    if(releaseState) releaseState();
    await flush(20);
    out.after_late_resolve = html("content");
  }

  else if(SCENARIO === "coalesce"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};
    boot();                       // home: /api/state + /api/ops
    clickTab("studio");           // studio: همان دو مسیر، در همان tick
    await flush();
    const c = {};
    fetchLog.forEach(f => { c[f.url] = (c[f.url] || 0) + 1; });
    out.counts = c;
  }

  else if(SCENARIO === "stale_cache"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};
    boot(); await flush();
    out.fresh = html("content");
    routes = {"/api/state": "throw", "/api/ops": "throw"};
    windowStub.__cockpit.gotoTab("home"); await flush();
    out.stale = html("content");
    out.cache_key_present = store.has("octopus.cockpit.cache.v1");
  }

  else if(SCENARIO === "sub_endpoint_probe_once"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};  // زیرمسیرها = 404
    boot(); await flush();
    windowStub.__cockpit.gotoTab("brain"); await flush();
    out.brain_1 = html("content");
    windowStub.__cockpit.gotoTab("home"); await flush();
    windowStub.__cockpit.gotoTab("brain"); await flush();
    out.brain_probe_calls = fetchLog.filter(f => f.url === "/api/ops/brain").length;
    out.brain_2 = html("content");
  }

  else if(SCENARIO === "palette_html"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE}};
    boot(); await flush();
    registry.get("paletteBtn").dispatch("click", {});
    out.palette = html("palette");
    out.palette_class = registry.get("palette").className;
    // کلیکِ واقعی روی یک آیتم از مسیرِ delegation
    const item = {getAttribute: k => (k === "data-cmd" ? "brain.status" : null),
                  closest: sel => (sel === ".pal-item" ? item : null)};
    registry.get("palette").dispatch("click", {target: item});
    await flush();
    out.after_item_click = html("content");
    out.palette_after = html("palette");
    out.post_count = fetchLog.filter(f => f.method === "POST").length;
    // Ctrl+K
    documentStub.dispatch("keydown", {ctrlKey: true, key: "k", preventDefault(){}});
    out.palette_after_ctrlk = registry.get("palette").className;
  }

  else if(SCENARIO === "no_post_on_render"){
    withOwner();
    routes = {"/api/state": {body: STATE_OK}, "/api/ops": {body: OPS_BARE},
              "/api/outbound": {body: {status: "ok", counts: {sent: 1}, total: 1}},
              "/api/approvals": {body: {status: "ok", pending: [], count: 0}},
              "/api/legs": {body: {status: "ok", legs: {}}},
              "/api/value": {body: {status: "ok", events_per_leg: {}, total: 0}},
              "/api/ui-registry": {body: {items: []}},
              "/api/current-truth": {body: {status: "ok", preview: "x"}}};
    boot(); await flush();
    for(const k of out.tab_keys){ clickTab(k); await flush(); }
    out.post_count = fetchLog.filter(f => f.method === "POST").length;
    out.rendered_tabs = out.tab_keys.length;
  }

  else if(SCENARIO === "stale_beat_is_degraded"){
    withOwner();
    const old = Object.assign({}, STATE_OK, {ts: "2020-01-01T00:00:00"});
    routes = {"/api/state": {body: old}, "/api/ops": {body: OPS_BARE}};
    boot(); await flush();
    out.content = html("content");
  }

  else if(SCENARIO === "state_error_is_unknown"){
    withOwner();
    routes = {"/api/state": {status: 500, body: {status: "error"}}, "/api/ops": {status: 500, body: {}}};
    boot(); await flush();
    out.content = html("content");
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
                 fixture: "Path | None" = None) -> dict:
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


TILE_RE = re.compile(
    r'<div class="tile st-(?P<cls>[a-z]+)"><div class="tl">(?P<label>[^<]+)</div>'
    r'<div class="tb"><span class="badge (?P<badge>[a-z]+)" data-state="(?P<state>[a-z]+)"')


def tiles(html: str) -> dict:
    return {m.group("label"): (m.group("cls"), m.group("badge"), m.group("state"))
            for m in TILE_RE.finditer(html or "")}


# ══ لایهٔ ۱: ناوردای متنی ═══════════════════════════════════════════════════

def t_a_the_init_data_header_literal_survives_verbatim():
    """قراردادِ غیرقابلِ‌مذاکره: هدر دقیقاً به همین شکل نوشته شده باشد.

    شکلِ قدیمی (`if(tg && tg.initData)`) هدر را وقتی خالی بود اصلاً نمی‌فرستاد؛
    شکلِ جدید همیشه می‌فرستد (رشتهٔ خالی) و gateway هم `or ""` می‌کند — پس
    رفتار یکی است ولی قرارداد صریح و گرپ‌شدنی."""
    s = src(APP_JS)
    assert HEADER_LITERAL in s, "لیترالِ هدرِ X-Tg-Init-Data از app.js حذف/تغییر کرده"
    assert s.count('"X-Tg-Init-Data"') == 1, "هدر باید فقط یک نقطهٔ تعریف داشته باشد"


def t_b_three_state_helpers_exist_and_unknown_is_not_green():
    s = src(APP_JS)
    assert "function triState(" in s, "helper ِ سه‌حالته نیست"
    assert "function badge3(" in s and "function badgeClass(" in s
    assert TRISTATE_FALLBACK in s, "پیش‌فرضِ triState دیگر unknown نیست"
    # badgeClass هرگز برای حالتِ غیرِ ok کلاسِ سبز ندهد
    m = re.search(r"function badgeClass\(state\)\{(.*?)\n  \}", s, re.S)
    assert m, "badgeClass پیدا نشد"
    body = m.group(1)
    assert 'if(state === "ok") return "live";' in body
    assert body.rstrip().endswith('return "unknown";     // کلاسِ خاکستریِ خط‌چین — هیچ‌وقت سبز') or \
        'return "unknown";' in body.split('if(state === "degraded")')[-1], "شاخهٔ پیش‌فرضِ badgeClass unknown نیست"
    css = src(STYLE_CSS)
    assert ".badge.unknown{" in css, "کلاسِ unknown در CSS تعریف نشده"
    assert "var(--green)" not in css.split(".badge.unknown{")[1].split("}")[0], \
        "کلاسِ unknown سبز رنگ شده — دقیقاً همان حالتِ شکست"


def t_c_paint_is_guarded_by_the_active_tab():
    s = src(APP_JS)
    assert PAINT_GUARD in s, "گاردِ «فقط تبِ فعال نقاشی می‌شود» نیست"
    # هیچ رندری نباید مستقیم به content.innerHTML بنویسد جز مسیرهای مجاز
    direct = re.findall(r"content\.innerHTML\s*=", s)
    assert len(direct) == 2, (
        f"نوشتنِ مستقیم روی content.innerHTML باید فقط در paint() و showSkeleton() باشد؛ {len(direct)} مورد پیدا شد")


def t_d_every_mutation_goes_through_one_owner_gated_call_site():
    s = src(APP_JS)
    assert SINGLE_POST_SITE in s, "تکْ‌نقطهٔ submitAction عوض شده"
    assert s.count("apiPost(") == 2, "apiPost باید فقط یک تعریف و یک صداکننده داشته باشد"
    assert s.count('apiPost("/api/actions"') == 1, "بیش از یک مسیرِ POST به /api/actions"
    assert PALETTE_GATE in s, "گیتِ مالک داخلِ پالت نیست"
    # هیچ متدِ POST/PUT/DELETE ِ دیگری در فایل نباشد
    for bad in ('method:"PUT"', 'method:"DELETE"', "method: 'POST'"):
        assert bad not in s, f"مسیرِ نوشتنِ دیگری در فرانت: {bad}"


def t_e_readonly_and_disabled_paths_exist():
    s = src(APP_JS)
    assert "Read-only Mode — open from Telegram /ui to enable actions" in s, "متنِ read-only عوض شده"
    assert "var dis = enabled ? '' : 'disabled';" in s, "مسیرِ disabled ِ کنترل‌ها نیست"
    assert s.count("' "+"+dis+"+"'") >= 0  # noqa — فقط برای خوانایی
    assert s.count("+dis+") >= 6, "همهٔ کنترل‌های تغییردهنده مسیرِ disabled ندارند"
    css = src(STYLE_CSS)
    assert "input:disabled" in css and "button:disabled" in css


def t_f_perf_helpers_exist():
    s = src(APP_JS)
    assert COALESCE in s, "coalescing ِ درخواستِ همزمان نیست"
    assert "REFRESH_DEBOUNCE_MS" in s and "function scheduleRefresh(" in s, "debounce نیست"
    assert "function skeleton(" in s and "function showSkeleton(" in s, "skeleton نیست"
    assert "CACHE_KEY_OPS" in s and "function cacheRead(" in s and "function cacheWrite(" in s, "کشِ محلی نیست"
    assert "function staleNote(" in s and "last updated" in s, "برچسبِ «آخرین به‌روزرسانی» نیست"


def t_g_index_html_has_every_required_tab_and_the_palette_button():
    h = src(INDEX_HTML)
    for key in ("home", "studio", "brain", "governor", "obsidian", "next",
                "outbound", "approvals", "legs", "value", "registry", "truth"):
        assert f'data-tab="{key}"' in h, f"تبِ {key} در index.html نیست"
    for label in ("Cockpit", "Ops", "Brain", "Governor", "Obsidian", "Next",
                  "Outbound", "Approvals", "Legs", "Value", "UI Registry", "Truth"):
        assert f">{label}</div>" in h, f"برچسبِ تبِ {label} نیست"
    assert 'id="paletteBtn"' in h and 'id="palette"' in h, "دکمه/ظرفِ پالت نیست"
    assert "</body>" in h, "gateway اسنیپتِ initData را قبل از </body> تزریق می‌کند"


def t_h_no_secret_value_lands_in_the_frontend():
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

def t_i_the_header_is_on_every_single_request():
    d = run_scenario("header")
    assert d["fetch_count"] >= 2, d
    assert all(h == "INIT_DATA_TOKEN_XYZ" for h in d["headers"]), d["headers"]
    assert "/api/state" in d["urls"] and "/api/ops" in d["urls"], d["urls"]


def t_j_missing_sections_render_unknown_never_green():
    """قلبِ ماجرا: /api/ops بدونِ brain/governor/obsidian/next_steps.

    اگر این سه نشانگر سبز شوند، کلِ این سطح بی‌ارزش است — چون دقیقاً وقتی
    دروغ می‌گوید که مالک بیشترین اتکا را دارد."""
    d = run_scenario("unknown_not_green")
    tl = tiles(d["content"])
    for label in ("Wave 1", "Owner Auth", "4D Brain", "Daemon", "Governor", "Obsidian"):
        assert label in tl, f"نشانگرِ {label} رندر نشد: {sorted(tl)}"
    for label in ("4D Brain", "Governor", "Obsidian"):
        cls, badge, state = tl[label]
        assert state == "unknown", f"{label} روی دادهٔ غایب {state} شد"
        assert badge == "unknown" and cls == "unknown", (label, cls, badge)
        assert badge != "live", f"{label} سبز کشیده شد روی دادهٔ غایب"
    assert "نامعلوم (unknown)" in d["content"], "سنجه‌های NBA بدونِ داده «نامعلوم» نشدند"
    assert "هیچ اقدامِ سررسیدشده‌ای نیست" not in d["content"], \
        "«همه‌چیز مرتب» روی دادهٔ غایب ادعا شد"


def t_k_present_sections_do_render_ok_and_degraded():
    """قرینهٔ تستِ بالا: اگر داده **باشد**، سبز و کهربایی واقعاً می‌آیند.

    بدونِ این، یک پیاده‌سازیِ «همیشه unknown» هم تستِ قبلی را پاس می‌کرد."""
    d = run_scenario("degraded_and_ok")
    tl = tiles(d["content"])
    assert tl["4D Brain"][2] == "ok", tl["4D Brain"]
    assert tl["4D Brain"][1] == "live", tl["4D Brain"]
    assert tl["Governor"][2] == "degraded", tl["Governor"]
    assert tl["Obsidian"][2] == "ok", tl["Obsidian"]
    assert "پیگیری کن" in d["content"], "پیشنهادِ NBA روی دادهٔ واقعی نیامد"


def t_ka_a_section_that_exists_but_reports_no_status_is_unknown():
    """«بخش نیست» و «بخش هست ولی status ندارد» دو مسیرِ کدِ متفاوت‌اند.

    این تست از جهش‌آزمایی زاده شد: جهشِ `raw === undefined → "ok"` زنده ماند،
    چون هیچ سناریویی بخشِ بی‌status نمی‌ساخت. یعنی یک تکه از گاردِ «سبزِ روی
    هیچ» اصلاً دیده نمی‌شد."""
    d = run_scenario("section_present_without_status")
    tl = tiles(d["content"])
    assert tl["4D Brain"][2] == "unknown", tl["4D Brain"]
    assert tl["4D Brain"][1] != "live", "بخشِ بدونِ status سبز شد"
    assert tl["Obsidian"][2] == "unknown", tl["Obsidian"]
    assert tl["Governor"][2] == "ok", ("قرینه: بخشِ دارای status باید ok شود", tl["Governor"])


def t_l_a_partially_reported_next_section_is_never_all_clear():
    """دو تا از چهار سنجه آمده و صفرند. این «مرتب» نیست، «نامعلوم» است."""
    d = run_scenario("partial_next_is_not_allclear")
    assert "قابلِ ادعا نیست" in d["content"], d["content"][:400]
    assert "هیچ اقدامِ سررسیدشده‌ای نیست" not in d["content"]


def t_m_without_initdata_the_surface_is_read_only():
    d = run_scenario("readonly")
    assert "Read-only Mode — open from Telegram /ui to enable actions" in (d["warn"] or ""), d["warn"]
    c = d["content"]
    for el in ('id="leadHandle"', 'id="leadCreate"', 'id="taskTitle"', 'id="valueEvent"'):
        idx = c.find(el)
        assert idx >= 0, f"{el} رندر نشد"
        tag_end = c.find(">", idx)
        assert "disabled" in c[idx:tag_end], f"{el} در حالتِ read-only disabled نیست"
    assert "owner-auth required" in c
    assert d["palette_gate_blocked"] is True, "پالت در حالتِ read-only فرمانِ تغییردهنده را اجرا کرد"
    assert d["readonly_cmd_ok"] is True, "فرمانِ فقط-خواندنی هم مسدود شد — این زیاده‌روی است"
    assert "خطا" not in c and "HTTP 4" not in c, "به‌جای پیامِ آرام، خطای خام نشان داده شد"


def t_n_owner_actions_post_exactly_once_to_the_gated_endpoint():
    d = run_scenario("owner_actions")
    assert d["button_found"] is True
    assert d["post_count"] == 1, (d["post_count"], d["post_urls"])
    assert d["post_urls"] == ["/api/actions"], d["post_urls"]
    body = json.loads(d["post_bodies"][0])
    assert body["action"] == "lead.create", body
    assert body["payload"]["handle"] == "@someone", body
    assert d["post_headers"] == ["INIT_DATA_TOKEN_XYZ"], d["post_headers"]
    assert "APPLIED" in (d["result_text"] or ""), d["result_text"]


def t_o_a_late_response_never_paints_over_the_current_tab():
    """پاسخِ کندِ تبِ قبلی نباید محتوای تبِ فعلی را عوض کند.

    این همان اشتباهی است که در UIهای تب‌دار «عددِ اشتباه زیرِ عنوانِ درست»
    می‌سازد — بدترین شکلِ دروغ، چون هیچ‌کس شک نمی‌کند."""
    d = run_scenario("paint_guard")
    assert "Legs / Agents" in d["after_switch"], d["after_switch"][:300]
    assert "Legs / Agents" in d["after_late_resolve"], "پاسخِ دیرهنگامِ home روی legs نقاشی کرد"
    assert "Wave 1" not in d["after_late_resolve"], "بردِ تبِ home روی تبِ legs نشست"
    assert "Next Best Action" not in d["after_late_resolve"]


def t_p_simultaneous_requests_for_one_path_are_coalesced():
    d = run_scenario("coalesce")
    assert d["counts"].get("/api/state") == 1, d["counts"]
    assert d["counts"].get("/api/ops") == 1, d["counts"]


def t_q_a_failed_fetch_falls_back_to_cache_but_says_it_is_stale():
    d = run_scenario("stale_cache")
    assert d["cache_key_present"] is True, "چیزی کش نشد"
    assert "stale" not in d["fresh"], "پاسخِ تازه به‌اشتباه stale برچسب خورد"
    assert "commit abc1234" in d["fresh"]
    assert "stale" in d["stale"], "پاسخِ کش‌شده بدونِ برچسبِ کهنگی نشان داده شد"
    assert "last updated" in d["stale"], "زمانِ آخرین به‌روزرسانی نیامد"
    assert "commit abc1234" in d["stale"], "کش استفاده نشد"


def t_r_absent_sub_endpoints_are_probed_once_and_degrade_to_unknown():
    d = run_scenario("sub_endpoint_probe_once")
    assert d["brain_probe_calls"] == 1, \
        f"زیرمسیرِ ۴۰۴ باید فقط یک‌بار پروب شود، شد {d['brain_probe_calls']}"
    assert 'data-state="unknown"' in d["brain_1"], d["brain_1"][:300]
    assert "نامعلوم" in d["brain_2"]


def t_s_the_palette_lists_every_command_and_keeps_the_gate():
    d = run_scenario("palette_html")
    for label in ("Create Lead", "Create Task", "Record Money", "Open Manual Send Queue",
                  "Show Brain Status", "Show Today Followups", "Show Drift Report",
                  "Show Next Best Action"):
        assert label in d["palette"], f"فرمانِ «{label}» در پالت نیست"
    assert d["palette_class"] == "palette open"
    assert "4D Brain" in d["after_item_click"], "کلیک روی آیتمِ پالت تب را عوض نکرد"
    assert d["palette_after"] == "", "پالت بعد از اجرای فرمان بسته نشد"
    assert d["post_count"] == 0, \
        "پالت خودش POST زد — پالت میان‌بُر است، نه درِ دومِ ورود"
    assert d["palette_after_ctrlk"] == "palette open", "Ctrl/Cmd+K پالت را باز نکرد"


def t_t_rendering_never_mutates_anything():
    d = run_scenario("no_post_on_render")
    assert d["rendered_tabs"] == 12, d["rendered_tabs"]
    assert d["post_count"] == 0, "رندرِ صرف یک POST تولید کرد — سطحِ خواندن نباید بنویسد"


def t_u_a_stale_heartbeat_is_degraded_not_ok():
    d = run_scenario("stale_beat_is_degraded")
    tl = tiles(d["content"])
    assert tl["Daemon"][2] == "degraded", tl["Daemon"]
    assert "نبضِ کهنه" in d["content"]


def t_v_a_dead_backend_is_unknown_not_ok():
    d = run_scenario("state_error_is_unknown")
    tl = tiles(d["content"])
    assert tl["Daemon"][2] == "unknown", tl["Daemon"]
    assert tl["Wave 1"][2] == "unknown", tl["Wave 1"]
    for label in ("4D Brain", "Governor", "Obsidian"):
        assert tl[label][2] == "unknown", (label, tl[label])
    assert tl["Owner Auth"][2] == "unknown", tl["Owner Auth"]


def _live_ops_fixture() -> "tuple[Path, dict]":
    """خروجیِ **واقعیِ** read-model را می‌گیرد و به درایور می‌دهد.

    این تفاوتِ «تستِ نویسنده و خواننده با هم» است با «تستِ fixture ِ خودساخته»:
    اگر لِینِ read-model فردا کلیدی را عوض کند، این round-trip می‌ترکد؛ یک
    fixture ِ دست‌ساز تا ابد سبز می‌ماند و هیچ‌چیز نمی‌گوید."""
    sys.path.insert(0, str(_HERE.parent / "telegram_center"))
    import miniapp_state  # noqa: WPS433
    ops = json.loads(miniapp_state.dispatch_api("/api/ops")[1].decode("utf-8"))
    sub_brain = json.loads(miniapp_state.dispatch_api("/api/ops/brain")[1].decode("utf-8"))
    d = Path(tempfile.mkdtemp(prefix="cockpit-fx-"))
    p = d / "ops.json"
    p.write_text(json.dumps({"ops": ops, "sub_brain": sub_brain}, ensure_ascii=False),
                 encoding="utf-8", newline="\n")
    return p, ops


def t_w_the_real_ops_payload_never_paints_green_over_missing_data():
    """قرارداد را با خروجیِ زندهٔ read-model می‌سنجد، نه با حدسِ من.

    ادعاها state-independent‌اند: هرچه در payload باشد، رابطه‌ی «دادهٔ معلومِ
    بد ⇒ غیرِ سبز» و «دادهٔ غایب ⇒ نامعلوم» باید برقرار بماند."""
    fx, ops = _live_ops_fixture()
    d = run_scenario("live_payload", fixture=fx)
    tl = tiles(d["content"])
    for label in ("Wave 1", "Owner Auth", "4D Brain", "Daemon", "Governor", "Obsidian"):
        assert label in tl, f"{label} رندر نشد"
        assert tl[label][2] in ("ok", "degraded", "unknown"), tl[label]

    brain = ops.get("brain")
    if isinstance(brain, dict) and brain.get("available") is False:
        assert tl["4D Brain"][2] == "degraded", ("مغزِ available:false نباید ok باشد", tl["4D Brain"])
        assert tl["4D Brain"][1] != "live"
    elif brain is None:
        assert tl["4D Brain"][2] == "unknown", tl["4D Brain"]

    gov = ops.get("governor")
    if isinstance(gov, dict) and isinstance(gov.get("drift_status"), dict) \
            and gov["drift_status"].get("status") == "drift":
        assert tl["Governor"][2] == "degraded", ("drift نباید ok باشد", tl["Governor"])

    obs = ops.get("obsidian")
    if isinstance(obs, dict) and isinstance(obs.get("missing_count"), int):
        want = "ok" if (obs["missing_count"] == 0 and obs.get("checked", 0) > 0) else "degraded"
        assert tl["Obsidian"][2] == want, (obs["missing_count"], obs.get("checked"), tl["Obsidian"])

    oa = ops.get("owner_auth")
    if isinstance(oa, dict) and oa.get("configured") is False:
        assert tl["Owner Auth"][2] == "degraded", tl["Owner Auth"]

    # next_steps ِ واقعی یک فهرست است، نه شمارنده ⇒ هر چهار سنجه نامعلوم
    if isinstance(ops.get("next_steps"), list):
        assert "نامعلوم (unknown)" in d["content"]
        assert "هیچ اقدامِ سررسیدشده‌ای نیست" not in d["content"], \
            "فهرستِ نقشهٔ راه به‌جای شمارنده خوانده شد و «مرتب» اعلام شد"
        assert "نقشهٔ راه (next_steps)" in d["next_tab"], "فهرستِ واقعیِ مراحل رندر نشد"
    assert "منبع: /api/ops/brain" in d["brain_tab"], "زیرمسیرِ موجود استفاده نشد"


def t_x_a_subendpoint_envelope_status_never_becomes_the_sections_health():
    """`{status:"ok", section:"brain", brain:{available:false}}`.

    `status:"ok"` یعنی «درخواست موفق بود». اگر پاکت به‌جای محتوا خوانده شود،
    یک مغزِ مرده سبز کشیده می‌شود — بدترین حالتِ ممکن برای این سطح."""
    d = run_scenario("envelope_status_must_not_leak")
    assert 'data-state="degraded"' in d["brain_tab"], d["brain_tab"][:400]
    assert 'data-state="ok"' not in d["brain_tab"], "پاکتِ status:ok به سلامتِ بخش نشت کرد"
    assert "daemon_state.json غایب" in d["brain_tab"], "دلیل به مالک نشان داده نشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_cockpit_ui: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
