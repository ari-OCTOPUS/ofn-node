// Octopus MiniApp — read-only cockpit. No secret in frontend. Actions disabled (Phase 7, not wired).
// Dev mode when Telegram.WebApp absent.
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

  function api(path){
    return fetch(path).then(function(r){
      if(!r.ok) throw new Error("HTTP "+r.status);
      return r.json();
    }).catch(function(e){
      return {status:"error", reason:e.message};
    });
  }
  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }

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

  var renderers = {home:renderHome,outbound:renderOutbound,approvals:renderApprovals,legs:renderLegs,value:renderValue,registry:renderRegistry,truth:renderTruth};
  function render(name){ (renderers[name]||renderHome)(); }

  // boot
  setAuth(devMode ? "dev-mode" : "…");
  render("home");
})();
