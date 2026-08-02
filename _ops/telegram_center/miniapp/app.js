// Octopus MiniApp Ã¢â‚¬â€ read-only cockpit. No secret in frontend. Actions disabled (Phase 7, not wired).
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

  function setAuth(state){
    authBadge.textContent = state;
    authBadge.className = "badge " + (state==="configured"||state==="live" ? "live" : (state==="dev-mode"?"staged":"blocked"));
  }
  function setHalted(h){
    statusDot.className = "dot" + (h ? " halted" : "");
  }

  function renderHome(){
    api("/api/state").then(function(d){
      if(d.status==="error"){ content.innerHTML = '<div class="err">Ã˜Â®Ã˜Â·Ã˜Â§: '+esc(d.reason)+'</div>'; return; }
      setHalted(d.halted);
      setAuth(devMode ? "dev-mode" : (d.auth_status||"unknown"));
      var flags = Object.keys(d.active_flags||{}).map(function(k){
        return '<span class="flag '+(d.active_flags[k]?"on":"")+'">'+esc(k)+"="+(d.active_flags[k]?"1":"0")+'</span>';
      }).join("");
      var w = (d.miniapp_url_configured===false) ? '<div class="warn">MiniApp URL Ã˜ÂªÃ™â€ Ã˜Â¸Ã›Å’Ã™â€¦ Ã™â€ Ã˜Â´Ã˜Â¯Ã™â€¡ Ã¢â‚¬â€ OCTOPUS_MINIAPP_URL</div>' : '';
      if(d.auth_status==="CONFIG_NEEDED") w += '<div class="warn">Auth config Ã™â€ Ã˜Â§Ã™â€šÃ˜Âµ Ã¢â‚¬â€ TG_CENTER_BOT_TOKEN / TELEGRAM_OWNER_CHAT_ID</div>';
      if(d.projectf_status && d.projectf_status.indexOf("BLOCKED")>=0) w += '<div class="warn">Project-F: Ã˜Â¨Ã˜Â¯Ã™Ë†Ã™â€  credential Ã¢â‚¬â€ BLOCKED</div>';
      warn.innerHTML = w;
      content.innerHTML =
        '<div class="card"><h2>Cockpit <span class="badge live">commit '+esc(d.commit||"?")+'</span></h2>'+
        '<div class="kv">'+
        '<span class="k">halted</span><span>'+(d.halted?"Ã˜Â¨Ã™â€žÃ™â€¡":"Ã˜Â®Ã›Å’Ã˜Â±")+'</span>'+
        '<span class="k">frozen</span><span>'+(d.frozen?"Ã˜Â¨Ã™â€žÃ™â€¡":"Ã˜Â®Ã›Å’Ã˜Â±")+'</span>'+
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
        '<div class="muted" style="margin-top:8px">actions: owner-gated (Phase 7) Ã¢â‚¬â€ Ã˜Â¯Ã˜Â± Ã˜Â§Ã›Å’Ã™â€  Ã™â€ Ã˜Â³Ã˜Â®Ã™â€¡ disabled.</div></div>';
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
        var l=legs[k]; return "<tr><td>"+esc(k)+"</td><td>"+esc(l.live)+'</td><td>'+(l.signal?esc(l.signal):"Ã¢â‚¬â€")+'</td><td>'+(l.note?esc(l.note).slice(0,40):"Ã¢â‚¬â€")+"</td></tr>";
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
        return "<tr><td>"+esc(it.id)+"</td><td>"+esc(it.type)+'</td><td><span class="badge '+esc(it.status)+'">'+esc(it.status)+"</span></td><td>"+esc(it.command||it.path||it.endpoint||"Ã¢â‚¬â€")+"</td></tr>";
      }).join("");
      content.innerHTML = '<div class="card"><h2>UI Registry <span class="badge">'+items.length+' items</span></h2>'+
        '<table><tr><th>id</th><th>type</th><th>status</th><th>cmd/path</th></tr>'+rows+'</table></div>';
    });
  }

  function renderTruth(){
    api("/api/current-truth").then(function(d){
      content.innerHTML = '<div class="card"><h2>Current Truth</h2>'+
        (d.preview?'<pre>'+esc(d.preview)+'</pre>':'<div class="muted">'+esc(d.status)+(d.reason?": "+esc(d.reason):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">read-only Ã¢â‚¬â€ '+esc(d.path||"")+'</div></div>';
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
        '<div class="card"><h2>Create Lead</h2><div class="formgrid"><input id="leadHandle" placeholder="handle Ã™â€¦Ã˜Â«Ã™â€ž @name"><select id="leadStage"><option>new</option><option>warm</option><option>hot</option><option>subscribed</option><option>vip</option><option>churn_risk</option></select><input id="leadTags" placeholder="tags comma separated"><button id="leadCreate" '+(enabled?'':'disabled')+'>Create local lead</button><div class="result" id="leadResult">'+(enabled?'ready':'owner-auth required')+'</div></div></div>'+
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

  var renderers = {home:renderHome,studio:renderStudio,outbound:renderOutbound,approvals:renderApprovals,legs:renderLegs,value:renderValue,registry:renderRegistry,truth:renderTruth};
  function render(name){ (renderers[name]||renderHome)(); }

  // boot
  setAuth(devMode ? "dev-mode" : "Ã¢â‚¬Â¦");
  render("home");
})();
