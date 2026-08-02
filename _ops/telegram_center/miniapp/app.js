// Octopus MiniApp — read-only cockpit. No secret in frontend.
// 2026-08-03: (۱) رشته‌های فارسی که روی دیسک mojibake شده بودند بازنویسی شدند
// (کاربر تا امروز به‌جای متن، بایتِ خراب می‌دید)؛ (۲) تبِ Project-F (PROP-D5
// فاز ۱) اضافه شد — content-free مطلق: فقط شمار/وضعیت، هیچ متنِ درفت.
// Dev mode when Telegram.WebApp absent. Actions: owner-gated only.
(function(){
  "use strict";
  var tg = window.Telegram && window.Telegram.WebApp;
  var devMode = !tg || !tg.initData;
  var content = document.getElementById("content");
  var warn = document.getElementById("warn");
  var authBadge = document.getElementById("authBadge");
  var statusDot = document.getElementById("statusDot");

  if (tg) { try { tg.expand(); tg.setHeaderColor("#0f1117"); } catch(e){} }

  // tabs
  var tabs = document.getElementById("tabs");
  tabs.addEventListener("click", function(e){
    var t = e.target.closest(".tab"); if(!t) return;
    [].forEach.call(tabs.children, function(x){x.classList.remove("active");});
    t.classList.add("active");
    render(t.getAttribute("data-tab"));
  });

  function tgHeaders(extra){ var h=extra||{}; if(tg && tg.initData){ h["X-Tg-Init-Data"] = tg.initData; } return h; }
  function api(path){
    return fetch(path, {headers: tgHeaders({})}).then(function(r){
      if(!r.ok) throw new Error("HTTP "+r.status);
      return r.json();
    }).catch(function(e){
      return {status:"error", reason:e.message};
    });
  }
  function apiPost(path, payload){
    return fetch(path, {method:"POST", headers:tgHeaders({"Content-Type":"application/json"}), body:JSON.stringify(payload||{})}).then(function(r){
      return r.json().catch(function(){ return {ok:false,status:"ERROR",reason:"bad_json"}; });
    }).catch(function(e){ return {ok:false,status:"ERROR",reason:e.message}; });
  }
  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }

  // عدد/شناسه داخل متنِ راست‌به‌چپ باید ایزولهٔ bidi بگیرد وگرنه جای ارقام می‌پرد
  function fa(n){
    if(n===null||n===undefined) return "—";
    return "⁦"+String(n)+"⁩";
  }
  // سه‌حالتی: null یعنی «نمی‌دانم»، نه «امن»
  function tri(v, yes, no){
    if(v===null||v===undefined) return '<span class="badge blocked">نامعلوم</span>';
    return v ? esc(yes) : esc(no);
  }

  function setAuth(state){
    authBadge.textContent = state;
    authBadge.className = "badge " + (state==="configured"||state==="live" ? "live" : (state==="dev-mode"?"staged":"blocked"));
  }
  function setHalted(h){
    statusDot.className = "dot" + (h ? " halted" : "");
  }

  function renderHome(){
    api("/api/state").then(function(d){
      if(d.status==="error"){ content.innerHTML = '<div class="err">خطا: '+esc(d.reason)+'</div>'; return; }
      setHalted(d.halted);
      setAuth(devMode ? "dev-mode" : (d.auth_status||"unknown"));
      var flags = Object.keys(d.active_flags||{}).map(function(k){
        return '<span class="flag '+(d.active_flags[k]?"on":"")+'">'+esc(k)+"="+(d.active_flags[k]?"1":"0")+'</span>';
      }).join("");
      var w = (d.miniapp_url_configured===false) ? '<div class="warn">MiniApp URL تنظیم نشده — OCTOPUS_MINIAPP_URL</div>' : '';
      if(d.auth_status==="CONFIG_NEEDED") w += '<div class="warn">Auth config ناقص — TG_CENTER_BOT_TOKEN / TELEGRAM_OWNER_CHAT_ID</div>';
      if(d.projectf_status && d.projectf_status.indexOf("BLOCKED")>=0) w += '<div class="warn">Project-F: بدون credential — BLOCKED</div>';
      warn.innerHTML = w;
      content.innerHTML =
        '<div class="card"><h2>Cockpit <span class="badge live">commit '+esc(d.commit||"?")+'</span></h2>'+
        '<div class="kv">'+
        '<span class="k">halted</span><span>'+(d.halted?"بله":"خیر")+'</span>'+
        '<span class="k">frozen</span><span>'+(d.frozen?"بله":"خیر")+'</span>'+
        '<span class="k">beat</span><span>'+esc(d.beat)+'</span>'+
        '<span class="k">epoch</span><span>'+esc(d.epoch_mode)+'</span>'+
        '<span class="k">ts</span><span>'+esc(d.ts)+'</span>'+
        '<span class="k">month</span><span>'+esc((d.month&&d.month.key)||"?")+'</span>'+
        '<span class="k">conflicts</span><span>'+esc(JSON.stringify(d.conflicts))+'</span>'+
        '</div></div>'+
        '<div class="card"><h2>Active Flags</h2><div>'+flags+'</div></div>';
    });
  }

  function renderOutbound(){
    api("/api/outbound").then(function(d){
      if(d.status==="error"||d.status==="no_wal_db"){
        content.innerHTML = '<div class="card"><h2>Outbound / G-03</h2><div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div></div>'; return;
      }
      var rows = Object.keys(d.counts||{}).map(function(k){ return "<tr><td>"+esc(k)+"</td><td>"+d.counts[k]+"</td></tr>"; }).join("");
      content.innerHTML = '<div class="card"><h2>Outbound / G-03 <span class="badge">total '+esc(d.total)+'</span></h2>'+
        '<table><tr><th>state</th><th>count</th></tr>'+rows+'</table>'+
        '<div class="muted" style="margin-top:8px">actions: owner-gated (Phase 7) — در این نسخه disabled.</div></div>';
    });
  }

  function renderApprovals(){
    api("/api/approvals").then(function(d){
      var rows = (d.pending||[]).map(function(p){ return "<tr><td>"+esc(p.proposal_id)+"</td><td>"+esc(p.kind)+"</td><td>"+esc(p.amount_aud)+"</td></tr>"; }).join("");
      content.innerHTML = '<div class="card"><h2>Approvals <span class="badge">'+esc(d.count||0)+'</span></h2>'+
        (rows ? '<table><tr><th>proposal</th><th>kind</th><th>amount</th></tr>'+rows+'</table>' : '<div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">approve/reject: owner-gated (disabled)</div></div>';
    });
  }

  function renderLegs(){
    api("/api/legs").then(function(d){
      var legs = d.legs||{};
      var rows = Object.keys(legs).map(function(k){
        var l=legs[k]; return "<tr><td>"+esc(k)+"</td><td>"+esc(l.live)+'</td><td>'+(l.signal?esc(l.signal):"—")+'</td><td>'+(l.note?esc(l.note).slice(0,40):"—")+"</td></tr>";
      }).join("");
      content.innerHTML = '<div class="card"><h2>Legs / Agents</h2>'+
        (rows?'<table><tr><th>leg</th><th>live</th><th>signal</th><th>note</th></tr>'+rows+'</table>':'<div class="muted">'+esc(d.status||"unknown")+'</div>')+'</div>';
    });
  }

  function renderValue(){
    api("/api/value").then(function(d){
      var rows = Object.keys(d.events_per_leg||{}).map(function(k){ return "<tr><td>"+esc(k)+"</td><td>"+d.events_per_leg[k]+"</td></tr>"; }).join("");
      content.innerHTML = '<div class="card"><h2>Value Ledger <span class="badge">total '+esc(d.total||0)+'</span></h2>'+
        (rows?'<table><tr><th>leg</th><th>events</th></tr>'+rows+'</table>':'<div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">auto-delete: '+esc(d.auto_delete===false?"off":"?")+'</div></div>';
    });
  }

  function renderRegistry(){
    api("/api/ui-registry").then(function(d){
      var items = d.items||[];
      var rows = items.map(function(it){
        return "<tr><td>"+esc(it.id)+"</td><td>"+esc(it.type)+'</td><td><span class="badge '+esc(it.status)+'">'+esc(it.status)+"</span></td><td>"+esc(it.command||it.path||it.endpoint||"—")+"</td></tr>";
      }).join("");
      content.innerHTML = '<div class="card"><h2>UI Registry <span class="badge">'+items.length+' items</span></h2>'+
        '<table><tr><th>id</th><th>type</th><th>status</th><th>cmd/path</th></tr>'+rows+'</table></div>';
    });
  }

  function renderTruth(){
    api("/api/current-truth").then(function(d){
      content.innerHTML = '<div class="card"><h2>Current Truth</h2>'+
        (d.preview?'<pre>'+esc(d.preview)+'</pre>':'<div class="muted">'+esc(d.status)+(d.reason?": "+esc(d.reason):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">read-only — '+esc(d.path||"")+'</div></div>';
    });
  }

  // ── Project-F (PROP-D5 فاز ۱) — فقط خواندن، فقط شمار. هیچ متنِ درفت. ──
  function pfLight(l){
    if(!l || !l.light || l.light==="unknown") return '<span class="badge blocked">نامعلوم</span>';
    var cls = l.light==="green" ? "live" : (l.light==="red" ? "blocked" : "staged");
    return '<span class="badge '+cls+'">'+esc(l.light)+'</span>';
  }
  function pfStale(f){ return (f && f.stale) ? ' <span class="badge blocked">کهنه</span>' : ''; }

  function renderPF(){
    content.innerHTML = '<div class="loading">در حال بارگذاری Project-F…</div>';
    Promise.all([api("/api/pf/status"), api("/api/pf/gates"), api("/api/pf/queue"),
                 api("/api/pf/kpi"), api("/api/pf/guards"), api("/api/pf/capabilities")])
    .then(function(all){
      var st=all[0]||{}, gt=all[1]||{}, q=all[2]||{}, kpi=all[3]||{}, gd=all[4]||{}, cap=all[5]||{};

      // یک پیامِ صریح به‌جای کارت‌های نیمه‌خالی — کاربر باید بداند «چرا خالی است».
      if(st.status==="error"){
        var r = String(st.reason||"");
        var msg, hint;
        if(/404/.test(r)){
          msg = "مسیرهای Project-F خاموش‌اند.";
          hint = "روشن‌کردن: <code>OCTOPUS_PF_MINIAPP=1</code> سپس ری‌استارتِ gateway.";
        } else if(/403/.test(r)){
          msg = "دسترسی رد شد — این کارت‌ها فقط با حسابِ مالک و از داخلِ تلگرام باز می‌شوند.";
          hint = devMode
            ? "الان در حالتِ dev هستی (بدونِ initData ِ تلگرام). از دکمهٔ Mini App در چتِ بات بازش کن."
            : "اگر از تلگرام آمده‌ای: <code>TG_CENTER_BOT_TOKEN</code> / <code>TELEGRAM_OWNER_CHAT_ID</code> را چک کن.";
        } else if(/503/.test(r)){
          msg = "کلیدِ کشتار فعال است (STOP-MINIAPP).";
          hint = "تا برداشته‌نشدنِ فایل، هیچ داده‌ای سرو نمی‌شود — این عمدی است.";
        } else {
          msg = "gateway جواب نداد: " + esc(r);
          hint = "سرویسِ 8774 و تونل را بررسی کن.";
        }
        content.innerHTML = '<div class="card"><h2>Project-F</h2>'+
          '<div class="warn">'+esc(msg)+'</div><div class="muted">'+hint+'</div>'+
          '<div class="muted" style="margin-top:8px">عمداً هیچ کارتِ نیمه‌خالی رندر نشد — دادهٔ نداشته را جعل نمی‌کنیم.</div></div>';
        return;
      }

      var unk = (st.unknown_fields||[]);
      var html = '';

      // کارت ۱ — نبض
      html += '<div class="card"><h2>Project-F <span class="badge '+(st.mode==="propose-only"?"staged":"blocked")+'">'+esc(st.mode||"?")+'</span></h2>'+
        '<div class="kv">'+
        '<span class="k">درفت‌های پارتنر</span><span>'+fa(st.drafts_count)+'</span>'+
        '<span class="k">DM منتظر بازبینی</span><span>'+fa(st.dm_pending)+'</span>'+
        '<span class="k">پستِ آمادهٔ ارسال دستی</span><span>'+fa(st.acq_ready)+'</span>'+
        '<span class="k">full stop</span><span>'+tri(st.full_stop,"بله","خیر")+'</span>'+
        '<span class="k">کارمای کافی</span><span>'+tri(st.karma_met,"بله","هنوز نه")+'</span>'+
        '<span class="k">اجرای بیرونی</span><span>'+(st.outward_execution?"⚠️ روشن":"خاموش")+'</span>'+
        '</div>'+
        (unk.length? '<div class="warn">نامعلوم‌ها (فایل غایب/خراب — صفرِ جعلی نساختیم): '+esc(unk.join("، "))+'</div>' : '')+
        '</div>';

      // کارت ۲ — گیت‌ها و بلاکرهای انسانی
      var gates = gt.gates||{};
      var grows = Object.keys(gates).map(function(k){
        var g=gates[k];
        return "<tr><td>"+esc(k)+"</td><td>"+esc(g.status)+"</td><td>"+esc(g.eval)+"</td></tr>";
      }).join("");
      html += '<div class="card"><h2>گیت‌ها'+pfStale(gt.freshness)+'</h2>'+
        (gt.status==="ok" ?
          '<div class="kv">'+
          '<span class="k">بلاکرِ اصلی</span><span>'+esc(gt.primary_blocker)+'</span>'+
          '<span class="k">Security Gate</span><span>'+esc(gt.security_gate)+'</span>'+
          '<span class="k">رأی‌های منتظر</span><span>'+fa(gt.pending_human_verdicts)+'</span>'+
          '<span class="k">مهرِ GATE-STAMP-GO</span><span>'+(gt.gate_stamp_go_file?"هست":"نیست ⇒ قفل")+'</span>'+
          '</div>'+
          (grows?'<table><tr><th>gate</th><th>status</th><th>eval</th></tr>'+grows+'</table>':'')
          : '<div class="muted">'+esc(gt.status)+(gt.reason?": "+esc(gt.reason):"")+'</div>')+
        '</div>';

      // کارت ۳ — صف‌ها (شمار و شناسه؛ هیچ متنی)
      function qRow(title, b){
        if(!b) return '';
        if(b.status!=="ok") return '<tr><td>'+esc(title)+'</td><td colspan="2" class="muted">'+esc(b.reason||b.status)+'</td></tr>';
        var counts = Object.keys(b.counts||{}).map(function(k){ return esc(k)+"="+fa(b.counts[k]); }).join(" · ") || "—";
        return '<tr><td>'+esc(title)+'</td><td>'+counts+'</td><td>'+fa(b.total)+'</td></tr>';
      }
      html += '<div class="card"><h2>صف‌ها</h2>'+
        '<table><tr><th>صف</th><th>وضعیت‌ها</th><th>کل</th></tr>'+
        qRow("پست (acquisition)", q.acquisition)+
        qRow("DM", q.dm)+
        qRow("درفت پارتنر", q.studio_drafts)+
        '</table>'+
        '<div class="muted" style="margin-top:8px">متنِ درفت عمداً از مرزِ پوشهٔ پروژه عبور نمی‌کند (قاعدهٔ #۷). تأیید/رد از تلگرام: <code>/pf_ok</code> · <code>/dm_ok</code></div></div>';

      // کارت ۴ — KPI با چراغ
      if(kpi.status==="ok"){
        var m = kpi.metrics||{}, L = kpi.lights||{};
        var krows = Object.keys(m).map(function(k){
          return "<tr><td>"+esc(k)+"</td><td>"+fa(m[k])+"</td><td>"+pfLight(L[k])+"</td><td>"+esc((L[k]&&L[k].action)||"—")+"</td></tr>";
        }).join("");
        html += '<div class="card"><h2>KPI هفتگی'+pfStale(kpi.freshness)+' <span class="badge">هفتهٔ '+esc(kpi.week_start)+'</span></h2>'+
          '<table><tr><th>سنجه</th><th>مقدار</th><th>چراغ</th><th>اقدامِ قرمز</th></tr>'+krows+'</table>'+
          '<div class="muted" style="margin-top:8px">آستانه‌ها hard-coded از kpi-dashboard-spec — ‏UI بازتعریفشان نمی‌کند.</div></div>';
      } else {
        html += '<div class="card"><h2>KPI هفتگی</h2><div class="muted">'+esc(kpi.status)+(kpi.note?" — "+esc(kpi.note):"")+'</div></div>';
      }

      // کارت ۵ — گاردها
      var cl = gd.channel_locks||{}, wu = gd.warmup||{};
      var crows = Object.keys(cl.channels||{}).map(function(k){
        var c=cl.channels[k];
        return "<tr><td>"+esc(k)+"</td><td>"+fa(c.warnings)+"</td><td>"+(c.locked?"🔒 قفل":"باز")+"</td></tr>";
      }).join("");
      html += '<div class="card"><h2>گاردها</h2>'+
        '<div class="kv">'+
        '<span class="k">full stop</span><span>'+tri(cl.full_stop===undefined?null:cl.full_stop,"بله","خیر")+'</span>'+
        '<span class="k">کارمای Reddit</span><span>'+fa(wu.karma)+' / '+fa(wu.threshold)+'</span>'+
        '</div>'+
        (crows?'<table><tr><th>کانال</th><th>اخطار</th><th>وضعیت</th></tr>'+crows+'</table>':'<div class="muted">'+esc(cl.reason||cl.status||"—")+'</div>')+
        '</div>';

      // کارت ۶ — قابلیت‌ها (هرگز دکمهٔ مرده)
      var caps = (cap.capabilities||[]).map(function(c){
        return "<tr><td>"+esc(c.name)+'</td><td><span class="badge '+(c.level==="green"?"live":(c.level==="red"?"blocked":"staged"))+'">'+esc(c.level)+"</span></td><td>"+(c.executable?"فعال":"🔒 قفل")+"</td><td>"+esc(c.reason)+"</td></tr>";
      }).join("");
      html += '<div class="card"><h2>قابلیت‌ها <span class="badge '+(cap.outward_allowed?"live":"blocked")+'">'+(cap.outward_allowed?"outward باز":"outward قفل")+'</span></h2>'+
        (caps?'<table><tr><th>قابلیت</th><th>سطح</th><th>اجرا</th><th>چرا</th></tr>'+caps+'</table>':'<div class="muted">—</div>')+
        '<div class="muted" style="margin-top:8px">منبع: '+esc(cap.source||"?")+' — هیچ دکمهٔ مرده‌ای رندر نمی‌شود.</div></div>';

      content.innerHTML = html;
    });
  }

  function renderStudio(){
    Promise.all([api("/api/state"), api("/api/ops")]).then(function(all){
      var st = all[0] || {}; var ops = all[1] || {};
      var enabled = (!devMode && st.auth_status === "configured");
      setAuth(devMode ? "dev-mode" : (st.auth_status||"unknown"));
      content.innerHTML = '<div class="card"><h2>Ops Studio <span class="badge '+(enabled?'live':'blocked')+'">'+(enabled?'owner-actions':'read-only')+'</span></h2>'+
        '<div class="kv"><div class="k">leads</div><div>'+esc(ops.leads_total||0)+'</div><div class="k">tasks</div><div>'+esc(ops.tasks_total||0)+'</div><div class="k">value events</div><div>'+esc(ops.value_events_total||0)+'</div></div>'+
        '<div class="muted" style="margin-top:8px">OnlyFans/Fansly automation is blocked. This is local CRM/task workflow.</div></div>'+
        '<div class="card"><h2>Create Lead</h2><div class="formgrid"><input id="leadHandle" placeholder="handle مثل @name"><select id="leadStage"><option>new</option><option>warm</option><option>hot</option><option>subscribed</option><option>vip</option><option>churn_risk</option></select><input id="leadTags" placeholder="tags comma separated"><button id="leadCreate" '+(enabled?'':'disabled')+'>Create local lead</button><div class="result" id="leadResult">'+(enabled?'ready':'owner-auth required')+'</div></div></div>'+
        '<div class="card"><h2>Create Task</h2><div class="formgrid"><input id="taskTitle" placeholder="task title"><select id="taskKind"><option>followup</option><option>manual_send</option><option>content_prepare</option><option>content_post</option><option>review_campaign</option><option>general</option></select><button id="taskCreate" '+(enabled?'':'disabled')+'>Create task</button><div class="result" id="taskResult">'+(enabled?'ready':'owner-auth required')+'</div></div></div>';
      var lb = document.getElementById("leadCreate");
      if(lb){ lb.addEventListener("click", function(){
        var payload = {handle:document.getElementById("leadHandle").value, stage:document.getElementById("leadStage").value, tags:document.getElementById("leadTags").value, platform:"onlyfans", source:"manual"};
        apiPost("/api/actions", {action:"lead.create", payload:payload}).then(function(r){ document.getElementById("leadResult").textContent = JSON.stringify(r,null,2); });
      });}
      var tb = document.getElementById("taskCreate");
      if(tb){ tb.addEventListener("click", function(){
        var payload = {title:document.getElementById("taskTitle").value, kind:document.getElementById("taskKind").value};
        apiPost("/api/actions", {action:"task.create", payload:payload}).then(function(r){ document.getElementById("taskResult").textContent = JSON.stringify(r,null,2); });
      });}
    });
  }

  var renderers = {home:renderHome,studio:renderStudio,outbound:renderOutbound,approvals:renderApprovals,legs:renderLegs,value:renderValue,registry:renderRegistry,truth:renderTruth,pf:renderPF};
  function render(name){ (renderers[name]||renderHome)(); }

  // boot
  setAuth(devMode ? "dev-mode" : "…");
  render("home");
})();
