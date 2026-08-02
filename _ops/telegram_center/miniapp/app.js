// Octopus MiniApp — کاکپیتِ مالک. هیچ secret در فرانت‌اند نیست.
// قانونِ اصلیِ این سطح: «ندانستن» هرگز سبز کشیده نمی‌شود. هر نشانگر سه حالت
// دارد — ok / degraded / unknown — و نبودِ داده همیشه unknown است، نه ok.
// هر تغییرِ حالت (mutation) فقط از مسیرِ owner-gated ِ /api/actions می‌گذرد؛
// پالت فرمان یک میان‌بُر است، نه درِ دومِ ورود.
// حالتِ dev/read-only وقتی است که Telegram.WebApp.initData نباشد.
(function(){
  "use strict";
  var tg = window.Telegram && window.Telegram.WebApp;
  var devMode = !tg || !tg.initData;
  var content = document.getElementById("content");
  var warn = document.getElementById("warn");
  var authBadge = document.getElementById("authBadge");
  var statusDot = document.getElementById("statusDot");
  var paletteEl = document.getElementById("palette");
  var paletteBtn = document.getElementById("paletteBtn");

  // متنِ دقیقِ حالتِ فقط-خواندنی (تستِ گارد به همین رشته لنگر انداخته).
  var READONLY_BANNER_TEXT = "Read-only Mode — open from Telegram /ui to enable actions";
  var PALETTE_MUTATING_NEEDS_OWNER = "owner-auth required";
  var CACHE_KEY_OPS = "octopus.cockpit.cache.v1";
  var FRESH_MAX_MS = 15 * 60 * 1000;      // نبضِ کهنه‌تر از این = degraded
  var CACHE_MAX_MS = 24 * 60 * 60 * 1000; // کشِ قدیمی‌تر از این اصلاً نمایش داده نمی‌شود
  var REFRESH_DEBOUNCE_MS = 400;

  if (tg) { try { tg.expand(); tg.setHeaderColor("#0f1117"); } catch(e){} }

  // ── تب‌ها ───────────────────────────────────────────────────────────────
  // فقط تبِ فعال رندر می‌شود. `activeTab` تنها منبعِ حقیقتِ «الان کدام تب؟»
  // است و هر پاسخِ دیرهنگامِ تبِ قبلی با آن رد می‌شود (تابع paint).
  var tabs = document.getElementById("tabs");
  var activeTab = "home";
  tabs.addEventListener("click", function(e){
    var t = e.target.closest(".tab"); if(!t) return;
    [].forEach.call(tabs.children, function(x){x.classList.remove("active");});
    t.classList.add("active");
    activeTab = t.getAttribute("data-tab");
    render(activeTab);
  });

  function gotoTab(name){
    if(activeTab === name){ render(name); return; }
    [].forEach.call(tabs.children, function(x){
      if(x.getAttribute("data-tab") === name){ x.classList.add("active"); }
      else { x.classList.remove("active"); }
    });
    activeTab = name;
    render(name);
  }

  // ── شبکه ────────────────────────────────────────────────────────────────
  function tgHeaders(extra){
    var h = extra || {};
    h["X-Tg-Init-Data"] = window.Telegram?.WebApp?.initData || "";
    return h;
  }

  // coalescing: دو صداکننده در یک لحظه = یک درخواستِ واقعی.
  var inflight = {};
  function api(path){
    if(inflight[path]) return inflight[path];
    var p = fetch(path, {headers: tgHeaders({})}).then(function(r){
      if(!r.ok) throw new Error("HTTP "+r.status);
      return r.json();
    }).then(function(d){
      cacheWrite(path, d);
      return d;
    }).catch(function(e){
      return {status:"error", reason:e.message};
    }).then(function(d){
      delete inflight[path];
      return d;
    });
    inflight[path] = p;
    return p;
  }

  // زیرمسیرهای اختیاری (/api/ops/brain و …). اگر gateway آن‌ها را نشناسد 404
  // می‌دهد؛ یک‌بار می‌فهمیم و دیگر هرگز صدایشان نمی‌زنیم. null یعنی «نیست» —
  // که صداکننده آن را unknown می‌خواند، نه خطا و قطعاً نه ok.
  var subMissing = {};
  function apiOptional(path){
    if(subMissing[path]) return Promise.resolve(null);
    if(inflight[path]) return inflight[path];
    var p = fetch(path, {headers: tgHeaders({})}).then(function(r){
      if(r.status === 404 || r.status === 405){ subMissing[path] = true; return null; }
      if(!r.ok) return null;
      return r.json();
    }).catch(function(){
      return null;
    }).then(function(d){
      delete inflight[path];
      return d;
    });
    inflight[path] = p;
    return p;
  }

  function apiPost(path, payload){
    return fetch(path, {method:"POST", headers:tgHeaders({"Content-Type":"application/json"}), body:JSON.stringify(payload||{})}).then(function(r){
      return r.json().catch(function(){ return {ok:false,status:"ERROR",reason:"bad_json"}; });
    }).catch(function(e){ return {ok:false,status:"ERROR",reason:e.message}; });
  }

  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }

  // ── کشِ آخرین پاسخِ سالم ────────────────────────────────────────────────
  // عددِ کهنه‌ای که تازه نشان داده شود دروغ است؛ عددِ کهنه‌ای که «کهنه» برچسب
  // بخورد مفید است. پس هر خواندنِ کش با زمانِ ثبتش برمی‌گردد.
  function cacheAll(){
    try {
      var raw = window.localStorage && window.localStorage.getItem(CACHE_KEY_OPS);
      var obj = raw ? JSON.parse(raw) : {};
      return (obj && typeof obj === "object") ? obj : {};
    } catch(e){ return {}; }
  }
  function cacheWrite(path, data){
    try {
      if(!window.localStorage) return;
      if(!data || data.status === "error") return;   // خطا هرگز کش نمی‌شود
      var all = cacheAll();
      all[path] = {ts: Date.now(), data: data};
      window.localStorage.setItem(CACHE_KEY_OPS, JSON.stringify(all));
    } catch(e){ /* کش هرگز سرویس را نمی‌کشد */ }
  }
  function cacheRead(path){
    var row = cacheAll()[path];
    if(!row || !row.data) return null;
    var age = Date.now() - Number(row.ts || 0);
    if(!(age >= 0) || age > CACHE_MAX_MS) return null;
    return {data: row.data, ts: Number(row.ts||0), ageMs: age};
  }

  // خواندنِ «با پشتوانه»: اگر fetch شکست خورد، آخرین پاسخِ سالمِ کش‌شده با
  // برچسبِ صریحِ stale برمی‌گردد.
  function apiWithFallback(path){
    return api(path).then(function(d){
      if(d && d.status === "error"){
        var c = cacheRead(path);
        if(c) return {__stale:true, __ts:c.ts, __reason:d.reason, data:c.data};
        return {__stale:false, __ts:0, __reason:d.reason, data:d};
      }
      return {__stale:false, __ts:Date.now(), data:d};
    });
  }

  function fmtTime(ts){
    if(!ts) return "—";
    try {
      var d = new Date(Number(ts));
      var p = function(n){ return (n<10?"0":"")+n; };
      return p(d.getHours())+":"+p(d.getMinutes())+":"+p(d.getSeconds());
    } catch(e){ return "—"; }
  }
  function staleNote(res){
    if(!res || !res.__stale) return "";
    return '<div class="stale">داده از کشِ محلی — آخرین به‌روزرسانیِ سالم: '+
      esc(fmtTime(res.__ts))+' · last updated '+esc(fmtTime(res.__ts))+
      ' (stale'+(res.__reason?": "+esc(res.__reason):"")+')</div>';
  }

  // ── سه‌حالته ────────────────────────────────────────────────────────────
  // تنها جایی که یک مقدار به رنگ ترجمه می‌شود. هرچه اینجا نشناسد unknown است.
  function triState(v){
    if(v === true) return "ok";
    if(v === false) return "degraded";
    var s = String(v == null ? "" : v).toLowerCase().trim();
    if(s === "") return "unknown";
    if(s === "ok" || s === "live" || s === "green" || s === "configured" ||
       s === "healthy" || s === "on" || s === "active" || s === "fresh") return "ok";
    if(s === "degraded" || s === "warn" || s === "warning" || s === "amber" ||
       s === "stale" || s === "config_needed" || s === "blocked" || s === "halted" ||
       s === "error" || s === "off" || s === "down" || s === "missing_data") return "degraded";
    return "unknown";     // شکِ باقی‌مانده = unknown، هرگز ok
  }
  function badgeClass(state){
    if(state === "ok") return "live";
    if(state === "degraded") return "staged";
    return "unknown";     // کلاسِ خاکستریِ خط‌چین — هیچ‌وقت سبز
  }
  function badge3(state, label){
    var st = (state === "ok" || state === "degraded") ? state : "unknown";
    return '<span class="badge '+badgeClass(st)+'" data-state="'+st+'">'+esc(label)+'</span>';
  }
  function stateWord(state){
    return state === "ok" ? "سالم" : (state === "degraded" ? "نیازمندِ توجه" : "نامعلوم");
  }

  // نبضِ ORGANISM-STATE به وقتِ **محلی** و بدون offset نوشته می‌شود. اگر با
  // new Date(str) پارس شود بعضی موتورها UTC فرض می‌کنند و یک اختلافِ چندساعته
  // بی‌صدا وارد می‌شود. پس اجزا را صریح می‌سازیم.
  function parseLocalIso(s){
    var m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})/.exec(String(s||""));
    if(!m) return null;
    return new Date(+m[1], +m[2]-1, +m[3], +m[4], +m[5], +m[6]).getTime();
  }

  // ── خوانندهٔ بخش‌ها ──────────────────────────────────────────────────────
  // یک بخش (brain/governor/obsidian/next) ممکن است هنوز در بک‌اند نباشد.
  // نبودنش = unknown. `pick` اولین کلیدِ موجود را برمی‌گرداند وگرنه undefined.
  function pick(obj, keys){
    if(!obj || typeof obj !== "object") return undefined;
    for(var i=0;i<keys.length;i++){
      if(Object.prototype.hasOwnProperty.call(obj, keys[i]) && obj[keys[i]] != null) return obj[keys[i]];
    }
    return undefined;
  }
  function section(ops, names){
    var s = pick(ops, names);
    return (s && typeof s === "object") ? s : null;
  }
  function sectionState(sec){
    if(!sec) return "unknown";
    if(Array.isArray(sec)) return "unknown";      // فهرست یک وضعیت نیست
    var raw = pick(sec, ["status", "state", "health"]);
    if(raw !== undefined) return triState(raw);
    // شکل‌های واقعیِ read-model ِ /api/ops کلیدِ `status` ندارند ولی جوابِ
    // **معلوم** می‌دهند. «معلومِ بد» degraded است نه unknown — این دو را یکی
    // کردن همان‌قدر دروغ است که سبزکردنِ نامعلوم.
    var avail = pick(sec, ["available", "reachable", "configured"]);
    if(avail === true) return "ok";
    if(avail === false) return "degraded";
    var drift = pick(sec, ["drift_status", "drift", "drift_report"]);
    if(drift && typeof drift === "object"){
      var ds = String(pick(drift, ["status"]) || "").toLowerCase();
      if(ds === "drift" || ds === "mismatch") return "degraded";
      if(ds) return triState(ds);
    }
    if(typeof sec.missing_count === "number" && typeof sec.checked === "number"){
      return (sec.missing_count === 0 && sec.checked > 0) ? "ok" : "degraded";
    }
    return "unknown";
  }

  // پاکتِ زیرمسیر: `/api/ops/brain` → {status:"ok", section:"brain", brain:{…}}
  // اینجا `status:"ok"` یعنی «درخواست موفق بود»، نه «مغز سالم است». اگر پاکت
  // را به‌جای محتوا بخوانیم، یک مغزِ available:false سبز کشیده می‌شود —
  // دقیقاً همان دروغی که این سطح برای حذفش ساخته شده. پاکتِ ناشناخته = null.
  function unwrapSub(resp){
    if(!resp || typeof resp !== "object") return null;
    var name = resp.section;
    if(name && Object.prototype.hasOwnProperty.call(resp, name)){
      var inner = resp[name];
      return (inner && typeof inner === "object") ? inner : null;
    }
    return null;
  }

  // ── نشانگرهای بردِ وضعیت ────────────────────────────────────────────────
  // هر نشانگر منبعش را اعلام می‌کند تا «سبز روی هیچ» ممکن نباشد.
  function badgeWave1(st, ops){
    var explicit = section(ops, ["wave1", "wave_1"]);
    if(explicit) return {state: sectionState(explicit), detail: String(pick(explicit,["detail","note"]) || "")};
    var flags = st && st.active_flags;
    if(!flags || typeof flags !== "object") return {state:"unknown", detail:"active_flags نیامد"};
    var want = ["OCTOPUS_WIRE_TG_CONTROL","OCTOPUS_WIRE_LEAD_OUTBOUND_WAL","OCTOPUS_WIRE_VALUE_LEDGER"];
    var have = 0, known = 0;
    for(var i=0;i<want.length;i++){
      if(Object.prototype.hasOwnProperty.call(flags, want[i])){ known++; if(flags[want[i]]) have++; }
    }
    if(known === 0) return {state:"unknown", detail:"هیچ فلگِ Wave 1 گزارش نشد"};
    if(known < want.length) return {state:"degraded", detail:have+"/"+known+" روشن (ناقص‌گزارش)"};
    if(have === want.length) return {state:"ok", detail:have+"/"+want.length+" روشن"};
    return {state:"degraded", detail:have+"/"+want.length+" روشن"};
  }
  // Owner Auth دو منبع دارد و اولویت با read-model ِ /api/ops است
  // (`owner_auth.configured`)؛ `/api/state.auth_status` پشتیبانِ قدیمی‌تر.
  // هیچ‌کدام نبود ⇒ unknown.
  function badgeOwnerAuth(st, ops){
    var oa = section(ops, ["owner_auth"]);
    var configured;
    if(oa && typeof oa.configured === "boolean") configured = oa.configured;
    else if(st && st.auth_status !== undefined) configured = (String(st.auth_status) === "configured");
    if(configured === undefined) return {state:"unknown", detail:"owner_auth/auth_status نیامد"};
    if(!configured){
      var why = oa ? ("token:"+String(oa.bot_token||"?")+" · owner:"+String(oa.owner_id||"?"))
                   : String(st.auth_status);
      return {state:"degraded", detail:why};
    }
    if(devMode) return {state:"degraded", detail:"configured ولی بدونِ initData (read-only)"};
    return {state:"ok", detail:"configured + initData"};
  }
  function badgeDaemon(st){
    if(!st || st.status === "error") return {state:"unknown", detail:"/api/state نیامد"};
    if(st.halted === true) return {state:"degraded", detail:"halted"};
    var ts = parseLocalIso(st.ts);
    if(ts == null) return {state:"unknown", detail:"ts نیامد"};
    var age = Date.now() - ts;
    if(age > FRESH_MAX_MS) return {state:"degraded", detail:"نبضِ کهنه ("+Math.round(age/60000)+" دقیقه)"};
    if(age < -FRESH_MAX_MS) return {state:"degraded", detail:"ts از آینده — ساعتِ ناهمگام"};
    return {state:"ok", detail:"beat "+String(st.beat==null?"?":st.beat)};
  }
  function badgeFromSection(ops, names, missingNote){
    var sec = section(ops, names);
    if(!sec) return {state:"unknown", detail: missingNote};
    var detail = pick(sec, ["detail","note","summary","reason"]);
    if(detail === undefined && sec.drift_status && typeof sec.drift_status === "object"){
      detail = "drift: " + String(pick(sec.drift_status, ["status"]) || "?");
    }
    if(detail === undefined && typeof sec.missing_count === "number"){
      detail = sec.missing_count + " غایب از " + String(sec.checked==null?"?":sec.checked);
    }
    return {state: sectionState(sec), detail: String(detail == null ? "" : detail).slice(0, 160)};
  }

  var BOARD = [
    {key:"wave1",    label:"Wave 1"},
    {key:"auth",     label:"Owner Auth"},
    {key:"brain",    label:"4D Brain"},
    {key:"daemon",   label:"Daemon"},
    {key:"governor", label:"Governor"},
    {key:"obsidian", label:"Obsidian"}
  ];
  function boardStates(st, ops){
    return {
      wave1:    badgeWave1(st, ops),
      auth:     badgeOwnerAuth(st, ops),
      brain:    badgeFromSection(ops, ["brain","brain_4d","fourd_brain"], "بخشِ brain در /api/ops نیست"),
      daemon:   badgeDaemon(st),
      governor: badgeFromSection(ops, ["governor"], "بخشِ governor در /api/ops نیست"),
      obsidian: badgeFromSection(ops, ["obsidian","vault"], "بخشِ obsidian در /api/ops نیست")
    };
  }
  function boardHtml(states){
    return '<div class="board">' + BOARD.map(function(b){
      var s = states[b.key] || {state:"unknown", detail:""};
      return '<div class="tile st-'+badgeClass(s.state)+'">'+
        '<div class="tl">'+esc(b.label)+'</div>'+
        '<div class="tb">'+badge3(s.state, stateWord(s.state))+'</div>'+
        '<div class="td">'+esc(s.detail||"—")+'</div></div>';
    }).join("") + '</div>';
  }

  // ── Next Best Action ────────────────────────────────────────────────────
  // چهار سنجه. هرکدام که نیامده باشد unknown است و «همه‌چیز مرتب» فقط وقتی
  // گفته می‌شود که **هر چهار** سنجه واقعاً آمده و صفر باشند.
  var NBA_FIELDS = [
    {keys:["followups_due","followups_due_today","today_followups"], fa:"پیگیری‌های سررسیدشده", verb:"پیگیری کن"},
    {keys:["leads_needing_stage","leads_needing_stage_update","stale_leads"], fa:"لیدهای نیازمندِ به‌روزرسانیِ مرحله", verb:"مرحله را به‌روز کن"},
    {keys:["drafts_pending","pending_drafts"], fa:"پیش‌نویس‌های منتظرِ تأیید", verb:"صفِ ارسالِ دستی را باز کن"},
    {keys:["consolidation_stale_days","consolidation_staleness_days","consolidation_age_days"], fa:"کهنگیِ تجمیع (روز)", verb:"تجمیع را اجرا کن"}
  ];
  // نکتهٔ قرارداد (۲۰۲۶-۰۸-۰۳): `next_steps` در /api/ops یک **فهرستِ نقشهٔ راه**
  // است ({id,title,status,evidence})، نه شمارنده‌های NBA. فهرست را به‌جای
  // شمارنده خواندن یعنی ساختنِ عدد از هیچ — پس صریحاً ردش می‌کنیم و هر چهار
  // سنجه «نامعلوم» می‌مانند تا وقتی منبعِ واقعی‌شان بیاید.
  function countsSource(ops, nextSec){
    var src = nextSec || section(ops, ["next_steps","next","next_best_action"]);
    if(Array.isArray(src)) return null;
    return src;
  }
  function nbaRows(ops, nextSec){
    var src = countsSource(ops, nextSec);
    return NBA_FIELDS.map(function(f){
      var v = pick(src, f.keys);
      if(v === undefined) return {fa:f.fa, verb:f.verb, state:"unknown", value:null};
      var n = Number(v);
      if(!isFinite(n)) return {fa:f.fa, verb:f.verb, state:"unknown", value:null};
      return {fa:f.fa, verb:f.verb, state:(n > 0 ? "degraded" : "ok"), value:n};
    });
  }
  function nbaHeadline(rows){
    var known = rows.filter(function(r){ return r.state !== "unknown"; });
    if(known.length === 0) return {state:"unknown", text:"شمارنده‌های اقدام هنوز منبعی ندارند — نه در /api/ops و نه در زیرمسیرها. (next_steps یک فهرستِ نقشهٔ راه است، نه شمارنده.)"};
    var due = known.filter(function(r){ return r.value > 0; });
    if(due.length === 0){
      if(known.length < rows.length) return {state:"unknown", text:"بخشی از سنجه‌ها نیامده — «همه‌چیز مرتب» قابلِ ادعا نیست."};
      return {state:"ok", text:"هیچ اقدامِ سررسیدشده‌ای نیست."};
    }
    due.sort(function(a,b){ return b.value - a.value; });
    return {state:"degraded", text:due[0].verb+" — "+due[0].fa+": "+due[0].value};
  }
  function nbaHtml(ops, nextSec){
    var rows = nbaRows(ops, nextSec);
    var head = nbaHeadline(rows);
    return '<div class="card"><h2>Next Best Action '+badge3(head.state, stateWord(head.state))+'</h2>'+
      '<div class="nba-head">'+esc(head.text)+'</div>'+
      '<div class="nba">'+ rows.map(function(r){
        return '<div class="nba-row"><span class="nba-k">'+esc(r.fa)+'</span>'+
          '<span class="nba-v">'+(r.state==="unknown"?"نامعلوم (unknown)":esc(String(r.value)))+'</span>'+
          badge3(r.state, stateWord(r.state))+'</div>';
      }).join("") + '</div></div>';
  }

  // ── رنگِ سربرگ ──────────────────────────────────────────────────────────
  function setAuth(state){
    authBadge.textContent = state;
    authBadge.className = "badge " + (state==="configured"||state==="live" ? "live" : (state==="dev-mode"?"staged":"unknown"));
  }
  function setHalted(h){
    statusDot.className = "dot" + (h ? " halted" : "");
  }
  function banners(extra){
    var b = "";
    if(devMode){
      b += '<div class="warn readonly">'+esc(READONLY_BANNER_TEXT)+
           '<div class="muted">حالتِ فقط-خواندنی — برای فعال‌شدنِ اقدام‌ها از داخلِ تلگرام با /ui باز کن.</div></div>';
    }
    warn.innerHTML = b + (extra || "");
  }

  // ── رندرِ محافظت‌شده ────────────────────────────────────────────────────
  // پاسخِ دیرهنگامِ یک تب هرگز روی تبِ فعلی نقاشی نمی‌کند.
  function paint(tab, html){
    if(activeTab !== tab) return false;
    content.innerHTML = html;
    return true;
  }
  function skeleton(rows){
    var n = rows || 3, out = "";
    for(var i=0;i<n;i++){ out += '<div class="sk-row"></div>'; }
    return '<div class="card skeleton"><div class="sk-head"></div>'+out+'</div>';
  }
  function showSkeleton(tab, rows){
    if(activeTab === tab) content.innerHTML = skeleton(rows);
  }
  function errCard(title, res){
    var d = (res && res.data) || {};
    return '<div class="card"><h2>'+esc(title)+' '+badge3("unknown","نامعلوم")+'</h2>'+
      '<div class="muted">پاسخی نیامد'+(d.reason?": "+esc(d.reason):"")+' — این «سالم» نیست، «نامعلوم» است.</div></div>';
  }

  // ── تبِ Cockpit ─────────────────────────────────────────────────────────
  function renderHome(){
    showSkeleton("home", 4);
    Promise.all([apiWithFallback("/api/state"), apiWithFallback("/api/ops")]).then(function(all){
      var sres = all[0], ores = all[1];
      var d = sres.data || {}, ops = ores.data || {};
      setHalted(d.halted);
      setAuth(devMode ? "dev-mode" : (d.auth_status || "unknown"));
      var w = "";
      if(d.miniapp_url_configured === false) w += '<div class="warn">MiniApp URL تنظیم نشده — OCTOPUS_MINIAPP_URL</div>';
      if(d.auth_status === "CONFIG_NEEDED") w += '<div class="warn">Auth config ناقص — TG_CENTER_BOT_TOKEN / TELEGRAM_OWNER_CHAT_ID</div>';
      if(d.projectf_status && String(d.projectf_status).indexOf("BLOCKED") >= 0) w += '<div class="warn">Project-F: بدونِ credential — BLOCKED</div>';
      banners(w);
      var states = boardStates(d, ops);
      var flags = Object.keys(d.active_flags||{}).map(function(k){
        return '<span class="flag '+(d.active_flags[k]?"on":"")+'">'+esc(k)+"="+(d.active_flags[k]?"1":"0")+'</span>';
      }).join("");
      paint("home",
        staleNote(sres) + staleNote(ores) +
        '<div class="card"><h2>Cockpit <span class="badge live">commit '+esc(d.commit||"?")+'</span></h2>'+
        boardHtml(states)+
        '<div class="kv">'+
        '<span class="k">halted</span><span>'+(d.halted?"بله":"خیر")+'</span>'+
        '<span class="k">frozen</span><span>'+(d.frozen?"بله":"خیر")+'</span>'+
        '<span class="k">beat</span><span>'+esc(d.beat)+'</span>'+
        '<span class="k">epoch</span><span>'+esc(d.epoch_mode)+'</span>'+
        '<span class="k">ts</span><span>'+esc(d.ts)+'</span>'+
        '<span class="k">month</span><span>'+esc((d.month&&d.month.key)||"?")+'</span>'+
        '<span class="k">conflicts</span><span>'+esc(JSON.stringify(d.conflicts))+'</span>'+
        '</div></div>'+
        nbaHtml(ops, null)+
        '<div class="card"><h2>Active Flags</h2><div>'+flags+'</div></div>');
    });
  }

  // ── تب‌های Brain / Governor / Obsidian / Next ───────────────────────────
  // هرکدام اول زیرمسیرِ اختصاصی را امتحان می‌کند؛ اگر gateway نشناسد، بخشِ
  // متناظر در /api/ops؛ اگر آن هم نبود → unknown با دلیلِ صریح.
  function loadSection(subPath, opsKeys){
    return apiOptional(subPath).then(function(sub){
      var inner = unwrapSub(sub);
      if(inner) return {sec: inner, src: subPath};
      return apiWithFallback("/api/ops").then(function(res){
        var sec = section(res.data || {}, opsKeys);
        return {sec: sec, src: sec ? "/api/ops" : null, stale: res};
      });
    });
  }
  function kvTable(sec){
    var keys = Object.keys(sec || {});
    if(!keys.length) return '<div class="muted">خالی</div>';
    return '<div class="kv">' + keys.map(function(k){
      var v = sec[k];
      var text = (v && typeof v === "object") ? JSON.stringify(v) : String(v);
      return '<span class="k">'+esc(k)+'</span><span>'+esc(text.slice(0,300))+'</span>';
    }).join("") + '</div>';
  }
  function renderSectionTab(tab, title, subPath, opsKeys, missingNote){
    showSkeleton(tab, 3);
    loadSection(subPath, opsKeys).then(function(r){
      var st = r.sec ? sectionState(r.sec) : "unknown";
      var body = r.sec ? kvTable(r.sec)
        : '<div class="muted">'+esc(missingNote)+' — تا وقتی این بخش نیاید، وضعیت «نامعلوم» است و سبز نمی‌شود.</div>';
      paint(tab, (r.stale ? staleNote(r.stale) : "") +
        '<div class="card"><h2>'+esc(title)+' '+badge3(st, stateWord(st))+'</h2>'+
        body +
        '<div class="muted" style="margin-top:8px">منبع: '+esc(r.src || "— (هیچ منبعی پاسخ نداد)")+'</div></div>');
    });
  }
  function renderBrain(){
    renderSectionTab("brain", "4D Brain", "/api/ops/brain", ["brain","brain_4d","fourd_brain"],
      "بخشِ brain هنوز در /api/ops نیست و /api/ops/brain هم سرو نمی‌شود");
  }
  function renderGovernor(){
    showSkeleton("governor", 3);
    loadSection("/api/ops/governor", ["governor"]).then(function(r){
      var st = r.sec ? sectionState(r.sec) : "unknown";
      var drift = r.sec ? pick(r.sec, ["drift_status","drift","drift_report"]) : undefined;
      var driftHtml = (drift === undefined)
        ? '<div class="muted">Drift Report نیامد — نامعلوم (unknown).</div>'
        : ((drift && typeof drift === "object") ? kvTable(drift) : '<div>'+esc(String(drift))+'</div>');
      paint("governor", (r.stale ? staleNote(r.stale) : "") +
        '<div class="card"><h2>Governor '+badge3(st, stateWord(st))+'</h2>'+
        (r.sec ? kvTable(r.sec) : '<div class="muted">بخشِ governor هنوز در /api/ops نیست.</div>')+
        '<div class="muted" style="margin-top:8px">منبع: '+esc(r.src || "— (هیچ منبعی پاسخ نداد)")+'</div></div>'+
        '<div class="card" id="driftCard"><h2>Drift Report '+badge3(drift===undefined?"unknown":triState(pick(drift||{},["status"])), stateWord(drift===undefined?"unknown":triState(pick(drift||{},["status"]))))+'</h2>'+
        driftHtml+'</div>');
    });
  }
  function renderObsidian(){
    renderSectionTab("obsidian", "Obsidian / Vault", "/api/ops/obsidian", ["obsidian","vault"],
      "بخشِ obsidian هنوز در /api/ops نیست و /api/ops/obsidian هم سرو نمی‌شود");
  }
  function renderNext(){
    showSkeleton("next", 4);
    loadSection("/api/ops/next", ["next_steps","next","next_best_action"]).then(function(r){
      return apiWithFallback("/api/ops").then(function(res){
        var ops = res.data || {};
        var road = r.sec || section(ops, ["next_steps","next","next_best_action"]);
        var roadHtml;
        if(Array.isArray(road)){
          roadHtml = '<table><tr><th>مرحله</th><th>وضعیت</th><th>شاهد</th></tr>' +
            road.map(function(it){
              var s = triState(pick(it, ["status"]));
              return '<tr><td>'+esc(pick(it,["title","id"])||"?")+'</td>'+
                     '<td>'+badge3(s, String(pick(it,["status"])||"?"))+'</td>'+
                     '<td>'+esc(String(pick(it,["evidence","note"])||"—")).slice(0,80)+'</td></tr>';
            }).join("") + '</table>';
        } else if(road){
          roadHtml = kvTable(road);
        } else {
          roadHtml = '<div class="muted">بخشِ next_steps نیامد.</div>';
        }
        paint("next", (r.stale ? staleNote(r.stale) : "") + staleNote(res) +
          nbaHtml(ops, r.sec) +
          '<div class="card"><h2>نقشهٔ راه (next_steps) '+badge3(road?"ok":"unknown", road?"موجود":"نامعلوم")+'</h2>'+
          roadHtml+
          '<div class="muted" style="margin-top:8px">منبع: '+esc(r.src || "/api/ops")+
          ' — این فهرستِ مراحل است، نه شمارنده‌های «بهترین اقدامِ بعدی».</div></div>');
      });
    });
  }

  // ── تب‌های موجودِ مالک (دست‌نخورده در رفتار) ────────────────────────────
  function renderOutbound(){
    showSkeleton("outbound", 2);
    apiWithFallback("/api/outbound").then(function(res){
      var d = res.data || {};
      if(d.status==="error"||d.status==="no_wal_db"){
        paint("outbound", staleNote(res) + '<div class="card"><h2>Outbound / G-03 '+badge3(d.status==="error"?"unknown":"degraded", stateWord(d.status==="error"?"unknown":"degraded"))+'</h2><div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div></div>'); return;
      }
      var rows = Object.keys(d.counts||{}).map(function(k){ return "<tr><td>"+esc(k)+"</td><td>"+d.counts[k]+"</td></tr>"; }).join("");
      paint("outbound", staleNote(res) + '<div class="card"><h2>Outbound / G-03 <span class="badge">total '+esc(d.total)+'</span></h2>'+
        '<table><tr><th>state</th><th>count</th></tr>'+rows+'</table>'+
        '<div class="muted" style="margin-top:8px">اقدام‌ها owner-gated‌اند — در این نسخه disabled.</div></div>');
    });
  }

  function renderApprovals(){
    showSkeleton("approvals", 2);
    apiWithFallback("/api/approvals").then(function(res){
      var d = res.data || {};
      var rows = (d.pending||[]).map(function(p){ return "<tr><td>"+esc(p.proposal_id)+"</td><td>"+esc(p.kind)+"</td><td>"+esc(p.amount_aud)+"</td></tr>"; }).join("");
      paint("approvals", staleNote(res) + '<div class="card"><h2>Approvals <span class="badge">'+esc(d.count||0)+'</span></h2>'+
        (rows ? '<table><tr><th>proposal</th><th>kind</th><th>amount</th></tr>'+rows+'</table>' : '<div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">approve/reject: owner-gated (disabled)</div></div>');
    });
  }

  function renderLegs(){
    showSkeleton("legs", 3);
    apiWithFallback("/api/legs").then(function(res){
      var d = res.data || {};
      var legs = d.legs||{};
      var rows = Object.keys(legs).map(function(k){
        var l=legs[k]; return "<tr><td>"+esc(k)+"</td><td>"+esc(l.live)+'</td><td>'+(l.signal?esc(l.signal):"—")+'</td><td>'+(l.note?esc(l.note).slice(0,40):"—")+"</td></tr>";
      }).join("");
      paint("legs", staleNote(res) + '<div class="card"><h2>Legs / Agents</h2>'+
        (rows?'<table><tr><th>leg</th><th>live</th><th>signal</th><th>note</th></tr>'+rows+'</table>':'<div class="muted">'+esc(d.status||"unknown")+'</div>')+'</div>');
    });
  }

  function renderValue(){
    showSkeleton("value", 2);
    apiWithFallback("/api/value").then(function(res){
      var d = res.data || {};
      var rows = Object.keys(d.events_per_leg||{}).map(function(k){ return "<tr><td>"+esc(k)+"</td><td>"+d.events_per_leg[k]+"</td></tr>"; }).join("");
      paint("value", staleNote(res) + '<div class="card"><h2>Value Ledger <span class="badge">total '+esc(d.total||0)+'</span></h2>'+
        (rows?'<table><tr><th>leg</th><th>events</th></tr>'+rows+'</table>':'<div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">auto-delete: '+esc(d.auto_delete===false?"off":"?")+'</div></div>');
    });
  }

  function renderRegistry(){
    showSkeleton("registry", 3);
    apiWithFallback("/api/ui-registry").then(function(res){
      var d = res.data || {};
      var items = d.items||[];
      var rows = items.map(function(it){
        return "<tr><td>"+esc(it.id)+"</td><td>"+esc(it.type)+'</td><td><span class="badge '+esc(it.status)+'">'+esc(it.status)+"</span></td><td>"+esc(it.command||it.path||it.endpoint||"—")+"</td></tr>";
      }).join("");
      paint("registry", staleNote(res) + '<div class="card"><h2>UI Registry <span class="badge">'+items.length+' items</span></h2>'+
        '<table><tr><th>id</th><th>type</th><th>status</th><th>cmd/path</th></tr>'+rows+'</table></div>');
    });
  }

  function renderTruth(){
    showSkeleton("truth", 3);
    apiWithFallback("/api/current-truth").then(function(res){
      var d = res.data || {};
      paint("truth", staleNote(res) + '<div class="card"><h2>Current Truth</h2>'+
        (d.preview?'<pre>'+esc(d.preview)+'</pre>':'<div class="muted">'+esc(d.status)+(d.reason?": "+esc(d.reason):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">read-only — '+esc(d.path||"")+'</div></div>');
    });
  }

  // ── تبِ Ops (Ops Studio ِ مالک، تکمیل‌شده) ──────────────────────────────
  // تنها نقطهٔ تغییرِ حالت در کلِ این فایل. هر دکمه و هر آیتمِ پالت از همین
  // یک تابع می‌گذرد؛ پس گیتِ مالک یک جا است، نه پخش‌شده.
  function submitAction(action, payload, resultId){
    var el = document.getElementById(resultId);
    if(el) el.textContent = "…";
    return apiPost("/api/actions", {action:action, payload:payload}).then(function(r){
      if(el) el.textContent = JSON.stringify(r, null, 2);
      return r;
    });
  }
  function actionsEnabled(st){
    return (!devMode && st && st.auth_status === "configured");
  }
  var pendingFocus = null;
  var pendingTaskKind = null;
  function focusPending(){
    if(!pendingFocus) return;
    var el = document.getElementById(pendingFocus);
    pendingFocus = null;
    if(el && el.focus) { try { el.focus(); } catch(e){} }
  }
  function val(id){ var e = document.getElementById(id); return e ? e.value : ""; }

  function renderStudio(){
    showSkeleton("studio", 3);
    Promise.all([apiWithFallback("/api/state"), apiWithFallback("/api/ops")]).then(function(all){
      var st = all[0].data || {}, ops = all[1].data || {};
      var enabled = actionsEnabled(st);
      setAuth(devMode ? "dev-mode" : (st.auth_status||"unknown"));
      banners("");
      var dis = enabled ? '' : 'disabled';
      var ready = enabled ? 'ready' : PALETTE_MUTATING_NEEDS_OWNER;
      var kinds = ["followup","manual_send","content_prepare","content_post","check_payment","review_campaign","general"];
      var kindSel = kinds.map(function(k){
        var sel = (pendingTaskKind === k) ? ' selected' : '';
        return '<option'+sel+'>'+k+'</option>';
      }).join("");
      pendingTaskKind = null;
      var queue = section(ops, ["manual_send_queue","manual_send"]);
      var qState = queue ? sectionState(queue) : "unknown";
      var taskStatus = ops.task_status && typeof ops.task_status === "object" ? ops.task_status : null;

      paint("studio", staleNote(all[0]) + staleNote(all[1]) +
        '<div class="card"><h2>Ops Studio '+badge3(enabled?"ok":"degraded", enabled?"owner-actions":"read-only")+'</h2>'+
        '<div class="kv"><div class="k">leads</div><div>'+esc(ops.leads_total||0)+'</div><div class="k">tasks</div><div>'+esc(ops.tasks_total||0)+'</div><div class="k">value events</div><div>'+esc(ops.value_events_total||0)+'</div></div>'+
        '<div class="muted" style="margin-top:8px">اتوماسیونِ OnlyFans/Fansly مسدود است. این‌جا فقط CRM/تسکِ محلی است.</div></div>'+

        '<div class="card" id="manualSendCard"><h2>Manual Send Queue '+badge3(qState, stateWord(qState))+'</h2>'+
        (queue ? kvTable(queue)
               : (taskStatus ? '<div class="kv">'+Object.keys(taskStatus).map(function(k){ return '<span class="k">'+esc(k)+'</span><span>'+esc(taskStatus[k])+'</span>'; }).join("")+'</div>'+
                               '<div class="muted">صفِ اختصاصی نیامد — این شمارشِ کلیِ تسک‌هاست، نه صفِ ارسالِ دستی.</div>'
                             : '<div class="muted">صفِ ارسالِ دستی نیامد — نامعلوم (unknown). برای ساختِ کارِ ارسالِ دستی از فرمِ زیر با kind=manual_send استفاده کن.</div>'))+
        '</div>'+

        '<div class="card"><h2>Create Lead</h2><div class="formgrid">'+
        '<input id="leadHandle" placeholder="handle مثلاً @name" '+dis+'>'+
        '<select id="leadStage" '+dis+'><option>new</option><option>warm</option><option>hot</option><option>subscribed</option><option>vip</option><option>churn_risk</option></select>'+
        '<input id="leadTags" placeholder="tags با کاما جدا شود" '+dis+'>'+
        '<button id="leadCreate" '+dis+'>Create local lead</button>'+
        '<div class="result" id="leadResult">'+esc(ready)+'</div></div></div>'+

        '<div class="card"><h2>Create Task</h2><div class="formgrid">'+
        '<input id="taskTitle" placeholder="عنوانِ کار" '+dis+'>'+
        '<select id="taskKind" '+dis+'>'+kindSel+'</select>'+
        '<button id="taskCreate" '+dis+'>Create task</button>'+
        '<div class="result" id="taskResult">'+esc(ready)+'</div></div></div>'+

        '<div class="card"><h2>Record Money</h2><div class="formgrid">'+
        '<input id="valueEvent" placeholder="رویداد مثلاً quote_accepted" '+dis+'>'+
        '<input id="valueLeg" placeholder="leg مثلاً lead" '+dis+'>'+
        '<input id="valueScore" placeholder="output_score عدد" '+dis+'>'+
        '<button id="valueCreate" '+dis+'>Record value event</button>'+
        '<div class="result" id="valueResult">'+esc(ready)+'</div></div></div>');

      var lb = document.getElementById("leadCreate");
      if(lb){ lb.addEventListener("click", function(){
        submitAction("lead.create", {handle:val("leadHandle"), stage:val("leadStage"), tags:val("leadTags"), platform:"onlyfans", source:"manual"}, "leadResult");
      });}
      var tb = document.getElementById("taskCreate");
      if(tb){ tb.addEventListener("click", function(){
        submitAction("task.create", {title:val("taskTitle"), kind:val("taskKind")}, "taskResult");
      });}
      var vb = document.getElementById("valueCreate");
      if(vb){ vb.addEventListener("click", function(){
        submitAction("value.record_event", {event:val("valueEvent"), leg:val("valueLeg") || "ops_studio", output_score:val("valueScore")}, "valueResult");
      });}
      focusPending();
    });
  }

  // ── پالتِ فرمان ─────────────────────────────────────────────────────────
  // آیتمِ «تغییردهنده» هرگز خودش POST نمی‌کند: فقط تبِ Ops را باز می‌کند و
  // روی همان کنترلِ owner-gated ِ موجود فوکوس می‌گذارد. یعنی پالت میان‌بُر
  // است، نه مسیرِ دوم.
  var COMMANDS = [
    {id:"lead.create",  label:"Create Lead",              fa:"ساختِ لید",                mutating:true,  run:function(){ pendingFocus="leadHandle";  gotoTab("studio"); }},
    {id:"task.create",  label:"Create Task",              fa:"ساختِ کار",                mutating:true,  run:function(){ pendingFocus="taskTitle";   gotoTab("studio"); }},
    {id:"value.record", label:"Record Money",             fa:"ثبتِ پول/ارزش",            mutating:true,  run:function(){ pendingFocus="valueEvent";  gotoTab("studio"); }},
    {id:"queue.manual", label:"Open Manual Send Queue",   fa:"صفِ ارسالِ دستی",          mutating:false, run:function(){ pendingTaskKind="manual_send"; gotoTab("studio"); }},
    {id:"brain.status", label:"Show Brain Status",        fa:"وضعیتِ مغزِ ۴بعدی",        mutating:false, run:function(){ gotoTab("brain"); }},
    {id:"followups",    label:"Show Today Followups",     fa:"پیگیری‌های امروز",         mutating:false, run:function(){ gotoTab("next"); }},
    {id:"drift",        label:"Show Drift Report",        fa:"گزارشِ دریفت",             mutating:false, run:function(){ gotoTab("governor"); }},
    {id:"nba",          label:"Show Next Best Action",    fa:"بهترین اقدامِ بعدی",       mutating:false, run:function(){ gotoTab("next"); }}
  ];
  var paletteOpen = false;
  function paletteHtml(filter){
    var f = String(filter||"").toLowerCase();
    var items = COMMANDS.filter(function(c){
      return !f || c.label.toLowerCase().indexOf(f) >= 0 || c.fa.indexOf(filter) >= 0;
    });
    return '<div class="pal-box">'+
      '<input id="palInput" placeholder="فرمان… (Ctrl/Cmd+K)" value="'+esc(filter||"")+'">'+
      '<div class="pal-list" id="palList">'+
      (items.length ? items.map(function(c){
        var blocked = c.mutating && devMode;
        return '<div class="pal-item'+(blocked?" blocked":"")+'" data-cmd="'+esc(c.id)+'"'+(blocked?' data-disabled="1"':'')+'>'+
          '<span class="pal-l">'+esc(c.label)+'</span>'+
          '<span class="pal-fa">'+esc(c.fa)+'</span>'+
          (c.mutating ? '<span class="badge '+(blocked?"unknown":"staged")+'">'+esc(blocked?PALETTE_MUTATING_NEEDS_OWNER:"owner-gated")+'</span>' : '<span class="badge">read</span>')+
          '</div>';
      }).join("") : '<div class="muted">چیزی پیدا نشد</div>')+
      '</div><div class="muted">Esc برای بستن</div></div>';
  }
  function openPalette(){
    paletteOpen = true;
    paletteEl.className = "palette open";
    paletteEl.innerHTML = paletteHtml("");
    var inp = document.getElementById("palInput");
    if(inp && inp.focus){ try { inp.focus(); } catch(e){} }
  }
  function closePalette(){
    paletteOpen = false;
    paletteEl.className = "palette";
    paletteEl.innerHTML = "";
  }
  function runCommand(id){
    for(var i=0;i<COMMANDS.length;i++){
      if(COMMANDS[i].id === id){
        if(COMMANDS[i].mutating && devMode) return false;   // گیتِ مالک، در پالت هم
        closePalette();
        COMMANDS[i].run();
        return true;
      }
    }
    return false;
  }
  if(paletteBtn){ paletteBtn.addEventListener("click", function(){ paletteOpen ? closePalette() : openPalette(); }); }
  if(paletteEl){
    paletteEl.addEventListener("click", function(e){
      var it = e.target.closest && e.target.closest(".pal-item");
      if(!it) { if(e.target === paletteEl) closePalette(); return; }
      if(it.getAttribute("data-disabled") === "1") return;
      runCommand(it.getAttribute("data-cmd"));
    });
    paletteEl.addEventListener("input", function(e){
      if(!e.target || e.target.id !== "palInput") return;
      var list = document.getElementById("palList");
      if(!list) return;
      var v = e.target.value;
      var tmp = paletteHtml(v);
      var m = /<div class="pal-list" id="palList">([\s\S]*)<\/div><div class="muted">/.exec(tmp);
      list.innerHTML = m ? m[1] : "";
    });
  }
  document.addEventListener("keydown", function(e){
    if((e.ctrlKey || e.metaKey) && String(e.key||"").toLowerCase() === "k"){
      if(e.preventDefault) e.preventDefault();
      paletteOpen ? closePalette() : openPalette();
      return;
    }
    if(String(e.key||"") === "Escape" && paletteOpen) closePalette();
  });

  // ── refresh با debounce ────────────────────────────────────────────────
  var refreshTimer = null;
  function scheduleRefresh(){
    if(refreshTimer) clearTimeout(refreshTimer);
    refreshTimer = setTimeout(function(){
      refreshTimer = null;
      render(activeTab);
    }, REFRESH_DEBOUNCE_MS);
  }

  var renderers = {home:renderHome, studio:renderStudio, brain:renderBrain, governor:renderGovernor,
                   obsidian:renderObsidian, next:renderNext, outbound:renderOutbound,
                   approvals:renderApprovals, legs:renderLegs, value:renderValue,
                   registry:renderRegistry, truth:renderTruth};
  function render(name){ (renderers[name]||renderHome)(); }

  // boot
  setAuth(devMode ? "dev-mode" : "…");
  banners("");
  render("home");

  // برای تست/دیباگ از داخلِ همان صفحه — فقط توابعِ خالص، بدونِ هیچ داده‌ای.
  window.__cockpit = {triState:triState, badgeClass:badgeClass, boardStates:boardStates,
                      nbaRows:nbaRows, nbaHeadline:nbaHeadline, runCommand:runCommand,
                      gotoTab:gotoTab, scheduleRefresh:scheduleRefresh, COMMANDS:COMMANDS};
})();
