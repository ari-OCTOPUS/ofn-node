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
  var coreLead = document.getElementById("coreLead");
  var coreSub = document.getElementById("coreSub");
  var eye = document.getElementById("eye");

  // ── پوستهٔ Mini Apps 2.0 (فاز ۳، ۲۰۲۶-۰۸-۰۴) ─────────────────────────
  // تا امروز کلِ یکپارچگیِ تلگرام یک خط بود: expand + setHeaderColor. یعنی
  // روی گوشی محتوا **زیرِ نُچ** می‌رفت، تمام‌صفحه نبود، و در پس‌زمینه هم
  // poll می‌کرد. منطقش عمداً در `tg_shell.js` است تا در node واقعاً تست شود
  // (۱۳ تست) — نه با assert ِ متنی روی همین فایل.
  if (tg) { try { tg.setHeaderColor("#050914"); } catch(e){} }
  var shell = (window.OctopusShell || {});
  var appActive = true;
  var shellReport = shell.initShell ? shell.initShell(tg, {
    setVar: function(k, v){
      try { document.documentElement.style.setProperty(k, v); } catch(e){}
    },
    setTheme: function(name){
      try { document.documentElement.setAttribute("data-theme", name); } catch(e){}
    },
    onActive: function(on){
      appActive = !!on;
      // ⚠️ این‌جا اولش «در پس‌زمینه poll نکن» نوشته بودم — ولی این اپ اصلاً
      // تایمرِ poll ندارد (فقط روی کلیکِ تب render می‌کند). قلابی که وانمود
      // کند کاری می‌کند، خودش یک دروغِ آینده است. کارِ **واقعاً** مفید این
      // است: وقتی مالک برمی‌گردد، دادهٔ روی صفحه کهنه است ⇒ همان تبِ فعال
      // دوباره رندر شود.
      if (!on) { return; }
      try {
        var act = document.querySelector("#tabs .tab.active");
        if (act) { render(act.getAttribute("data-tab")); }
      } catch(e){}
    },
    onFullscreen: function(on){
      try { document.body.classList.toggle("fullscreen", !!on); } catch(e){}
    }
  }) : {caps:{}, wired:[], mode:"none"};

  // دکمه‌ها فقط وقتی ساخته می‌شوند که کلاینت واقعاً پشتیبانی کند — دکمه‌ای
  // که کار نکند بدتر از نبودنش است.
  (function(){
    var host = document.getElementById("hdrBtns") || document.querySelector("h1");
    if (!host) { return; }
    function addBtn(title, label, fn){
      var b = document.createElement("button");
      b.className = "palbtn"; b.title = title; b.textContent = label;
      b.addEventListener("click", fn);
      host.appendChild(b);
    }
    if (shellReport.caps && shellReport.caps.fullscreen) {
      addBtn("تمام‌صفحه", "⛶", function(){ shell.toggleFullscreen(tg); });
    }
    if (shellReport.caps && shellReport.caps.homeScreen) {
      addBtn("افزودن به صفحهٔ اصلی", "📌", function(){ shell.addToHomeScreen(tg); });
    }
    // ── سوییچِ پوستهٔ بصری ────────────────────────────────────────────
    // من نمی‌توانم این اپ را روی گوشیِ مالک ببینم (مرورگرم به آن دامنه
    // دسترسی ندارد)، پس به‌جای حدس‌زدن، سه پوسته را می‌سازم و **خودش**
    // بینشان سوییچ می‌کند. انتخابش می‌ماند.
    var SKINS = [["neon","نئون"],["glass","شیشه‌ای"],["depth","عمق"]];
    function applySkin(id){
      try{
        document.documentElement.setAttribute("data-skin", id);
        localStorage.setItem("octo-skin", id);
      }catch(e){}
      var b = document.getElementById("skinBtn");
      var lbl = (SKINS.filter(function(x){return x[0]===id;})[0]||SKINS[0])[1];
      if(b) b.textContent = lbl;
    }
    // رأیِ مالک: «سبکِ نئون عالی بود». پس نئون فقط پیش‌فرض نیست — انتخابِ
    // ذخیره‌شدهٔ قدیمی هم یک‌بار به آن ریست می‌شود، وگرنه کسی که قبلاً
    // «شیشه‌ای» را امتحان کرده روی همان گیر می‌ماند و رأیش اعمال نمی‌شود.
    var saved;
    try{
      if(localStorage.getItem("octo-skin-v2") !== "1"){
        localStorage.setItem("octo-skin", "neon");
        localStorage.setItem("octo-skin-v2", "1");
      }
      saved = localStorage.getItem("octo-skin");
    }catch(e){}
    var cur = SKINS.map(function(x){return x[0];}).indexOf(saved);
    if(cur < 0) cur = 0;
    var sb = document.createElement("button");
    sb.className = "palbtn skinbtn"; sb.id = "skinBtn";
    sb.title = "تعویضِ پوستهٔ بصری";
    sb.addEventListener("click", function(){
      cur = (cur + 1) % SKINS.length; applySkin(SKINS[cur][0]);
    });
    host.appendChild(sb);
    applySkin(SKINS[cur][0]);
  })();

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

  // ── لایهٔ اقدام ───────────────────────────────────────────────────────────
  // ⚠️ هرگز خوش‌بینانه نیست. موتور شش وضع برمی‌گرداند (APPLIED / DUPLICATE /
  // BLOCKED / CONFLICT / DENIED / ERROR) و هر کدام معنای متفاوتی دارد؛ اگر
  // همه را «✅ شد» نشان دهم، همان کارتِ رسیدِ جعلیِ ۰۸-۰۴ را دوباره ساخته‌ام.
  // BLOCKED معمولاً `allowed` هم دارد — همان را نشان می‌دهم تا مالک بداند
  // چه چیزی مجاز بود، نه فقط اینکه رد شد.
  var ACT_TONE = {APPLIED:"ok", DONE:"ok", DUPLICATE:"warn", BLOCKED:"bad",
                  CONFLICT:"warn", DENIED:"bad", ERROR:"bad"};
  var ACT_FA = {APPLIED:"ثبت شد", DONE:"انجام شد", DUPLICATE:"قبلاً همین ثبت شده بود",
                BLOCKED:"رد شد", CONFLICT:"تداخل", DENIED:"اجازه نداری", ERROR:"خطا"};
  function actionIdOf(action, payload){
    // idempotency key ِ صریح: دو تپِ سریعِ ADHD نباید دو ردیف بسازد.
    // بدونِ این، موتور از hash ِ payload می‌سازد که برای «همان کار، دوباره»
    // درست است ولی برای «انگشتم لرزید» هم همان — که همان‌جا می‌خواهیمش.
    return "mini:" + action + ":" + JSON.stringify(payload||{});
  }
  function act(action, payload, btn){
    if(btn){ btn.disabled = true; btn.setAttribute("data-busy","1"); }
    if(tg && tg.HapticFeedback){ try{ tg.HapticFeedback.impactOccurred("light"); }catch(e){} }
    return apiPost("/api/actions", {action:action, payload:payload||{},
                                    action_id: actionIdOf(action, payload)})
      .then(function(r){
        var st = String((r&&r.status)||"ERROR").toUpperCase();
        var tone = ACT_TONE[st] || "warn";
        var msg = ACT_FA[st] || st;
        if(st==="BLOCKED" && r && r.reason){
          msg += " — " + ltr(String(r.reason));
          if(r.allowed && r.allowed.length) msg += " · مجاز: " + r.allowed.map(ltr).join(" ");
        }
        toast(msg, tone);
        if(tg && tg.HapticFeedback){
          try{ tg.HapticFeedback.notificationOccurred(tone==="ok"?"success":"error"); }catch(e){}
        }
        return r;
      })
      .then(function(r){ if(btn){ btn.disabled=false; btn.removeAttribute("data-busy"); } return r; });
  }
  var _toastT = null;
  function toast(msg, tone){
    var w = document.getElementById("toast");
    if(!w){ w = document.createElement("div"); w.id = "toast"; document.body.appendChild(w); }
    w.className = "toast " + (tone||"warn") + " show";
    w.innerHTML = /[؀-ۿ]/.test(msg) ? msg : esc(msg);
    if(_toastT) clearTimeout(_toastT);
    _toastT = setTimeout(function(){ w.className = "toast " + (tone||"warn"); }, 4200);
  }

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

  function setCore(lead, sub){
    if(coreLead) coreLead.textContent = lead;
    if(coreSub) coreSub.textContent = sub || "";
  }
  function setAuth(state){ /* وضع در خطِ هسته می‌نشیند، نه یک نشانِ جدا */ }
  // چشمِ اختاپوس = وضعِ هسته. درخشش یعنی زنده؛ خاکستری یعنی متوقف.
  // استعاره باید **حقیقت** بگوید، وگرنه فقط تزئین است.
  function setHalted(h){
    if(eye) eye.setAttribute("class", "eye" + (h ? " halted" : ""));
  }

  function renderHome(el){
    el = el || content;
    api("/api/state").then(function(d){
      if(d.status==="error"){ el.innerHTML = '<div class="err">خطا: '+esc(d.reason)+'</div>'; return; }
      setHalted(d.halted);
      setAuth(devMode ? "dev-mode" : (d.auth_status||"unknown"));
      var flags = Object.keys(d.active_flags||{}).map(function(k){
        return '<span class="flag '+(d.active_flags[k]?"on":"")+'">'+esc(k)+"="+(d.active_flags[k]?"1":"0")+'</span>';
      }).join("");
      var w = (d.miniapp_url_configured===false) ? '<div class="warn">MiniApp URL تنظیم نشده — OCTOPUS_MINIAPP_URL</div>' : '';
      if(d.auth_status==="CONFIG_NEEDED") w += '<div class="warn">Auth config ناقص — TG_CENTER_BOT_TOKEN / TELEGRAM_OWNER_CHAT_ID</div>';
      if(d.projectf_status && d.projectf_status.indexOf("BLOCKED")>=0) w += '<div class="warn">Project-F: بدون credential — BLOCKED</div>';
      warn.innerHTML = w;
      el.innerHTML =
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

  function renderOutbound(el){
    el = el || content;
    api("/api/outbound").then(function(d){
      if(d.status==="error"||d.status==="no_wal_db"){
        el.innerHTML = '<div class="card">'+secHead("ارسالِ بیرونی")+
          '<div class="muted">'+esc(d.status)+(d.note?": "+esc(d.note):"")+'</div></div>'; return;
      }
      var c = d.counts||{}, ks = Object.keys(c);
      var TONE = {sent:"cyan", queued:"warm", failed:"hot", cancelled:"unk"};
      el.innerHTML = '<div class="card">'+secHead("ارسالِ بیرونی")+
        '<div class="ringrow">'+arcs(ks.map(function(k){
          return {n:c[k], tone:TONE[k]||"warm"}; }))+'</div>'+
        (ks.length?orbs(ks.map(function(k){
          return {name:k, short:k, n:c[k], tone:TONE[k]||"warm"}; })):'')+
        '</div>';
    });
  }

  function renderApprovals(el){
    el = el || content;
    api("/api/approvals").then(function(d){
      var pend = d.pending||[], n = Number(d.count||pend.length||0);
      var body = n ? '<div class="list">'+pend.slice(0,8).map(function(p){
          return '<div class="li orbline"><span class="od hot"></span>'+
            '<span class="grow">'+ltr(p.proposal_id)+'</span>'+
            '<span class="muted">'+esc(p.kind||"")+'</span>'+
            (p.amount_aud!==undefined?'<span class="amt">'+fa(p.amount_aud)+'</span>':'')+'</div>';
        }).join("")+'</div>'
        : '<div class="muted" style="text-align:center">صف خالی است</div>';
      el.innerHTML = '<div class="card">'+secHead("صفِ تأیید")+
        '<div class="ringrow">'+ring(n, Math.max(n,5), "منتظرِ تو", n?"hot":"cyan")+'</div>'+
        body+'</div>';
    });
  }

  function renderLegs(el){
    el = el || content;
    api("/api/legs").then(function(d){
      var legs = d.legs||{}, ks = Object.keys(legs);
      var up = ks.filter(function(k){ return legs[k].live===true; }).length;
      var down = ks.filter(function(k){ return legs[k].live===false; });
      // رأیِ مالک: صفحهٔ سیستم خودش یک **اختاپوسِ کامل** شود. تشخیصِ مکانی —
      // هر پا همیشه در همان موضعِ ساعت است، پس با تکرار جایش را حفظ می‌کنی
      // و دیگر لازم نیست اسم بخوانی.
      el.innerHTML = '<div class="card">'+
        secHead("پاها", pill(fa(up)+" از "+fa(ks.length), up===ks.length?"live":(down.length?"blocked":"staged")))+
        '<div class="sysdial">'+dialSVG(legs, false, up, ks.length||1, true)+'</div>'+
        (down.length ? '<div class="muted" style="text-align:center">خاموش: '+
            down.slice(0,4).map(ltr).join(" · ")+'</div>' : '')+
        '<details class="det"><summary>فهرستِ کاملِ پاها</summary>'+
        (ks.length ? orbs(ks.map(function(k){
            var l = legs[k];
            return {name:k, short:k.slice(0,10),
                    tone: l.live===false?"hot":(l.live?"up":"unk")};
          })) : '<div class="muted">'+esc(d.status||"نامعلوم")+'</div>')+
        '</details></div>';
    });
  }

  function renderValue(el){
    el = el || content;
    api("/api/value").then(function(d){
      var per = d.events_per_leg||{}, tot = Number(d.total||0);
      var ks = Object.keys(per);
      var mx = ks.reduce(function(a,k){ return Math.max(a, per[k]); }, 1);
      el.innerHTML = '<div class="card">'+secHead("دفترِ ارزش")+
        '<div class="ringrow">'+ring(tot, Math.max(tot,10), "رویداد", "cyan")+'</div>'+
        (ks.length ? orbs(ks.map(function(k){
            return {name:k, short:k.slice(0,9), n:per[k],
                    tone: per[k]>=mx*0.6?"up":(per[k]>0?"warm":"unk")};
          })) : '<div class="muted" style="text-align:center">هنوز رویدادی ثبت نشده</div>')+
        '</div>';
    });
  }

  function renderRegistry(el){
    el = el || content;
    api("/api/ui-registry").then(function(d){
      var items = d.items||[];
      var rows = items.map(function(it){
        return "<tr><td>"+esc(it.id)+"</td><td>"+esc(it.type)+'</td><td><span class="badge '+esc(it.status)+'">'+esc(it.status)+"</span></td><td>"+esc(it.command||it.path||it.endpoint||"—")+"</td></tr>";
      }).join("");
      el.innerHTML = '<div class="card"><h2>UI Registry <span class="badge">'+items.length+' items</span></h2>'+
        '<table><tr><th>id</th><th>type</th><th>status</th><th>cmd/path</th></tr>'+rows+'</table></div>';
    });
  }

  function renderTruth(el){
    el = el || content;
    api("/api/current-truth").then(function(d){
      el.innerHTML = '<div class="card"><h2>Current Truth</h2>'+
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

  function renderPF(el){
    el = el || content;
    el.innerHTML = '<div class="loading">در حال بارگذاری Project-F…</div>';
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
        el.innerHTML = '<div class="card"><h2>Project-F</h2>'+
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

      el.innerHTML = html;
    });
  }

  function renderStudio(el){
    el = el || content;
    Promise.all([api("/api/state"), api("/api/ops")]).then(function(all){
      var st = all[0] || {}; var ops = all[1] || {};
      var enabled = (!devMode && st.auth_status === "configured");
      setAuth(devMode ? "dev-mode" : (st.auth_status||"unknown"));
      el.innerHTML = '<div class="card"><h2>Ops Studio <span class="badge '+(enabled?'live':'blocked')+'">'+(enabled?'owner-actions':'read-only')+'</span></h2>'+
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

  // ── چهار تبی که تا امروز رندرکننده نداشتند (۲۰۲۶-۰۸-۰۴) ──────────────
  // تپ روی Brain/Governor/Obsidian/Next محتوای **Cockpit** را نشان می‌داد و
  // تب هم فعال می‌شد: نه خطا، نه پیام. یعنی مالک فکر می‌کرد Brain همین است.
  // داده‌ها سمتِ سرور از قبل بودند؛ فقط صدا زده نمی‌شدند.
  // ── ایزولهٔ bidi ────────────────────────────────────────────────────
  // ⚠️ باگِ دیده‌شده روی گوشیِ مالک: `ask()` به‌صورت `()ask` و
  // `_ops/cortex/model_router.py` به‌صورت `ops/cortex/model_router.py_`
  // رندر می‌شد. در متنِ RTL، پرانتز و آندرلاینِ ابتدای رشتهٔ لاتین به
  // انتهایش پرتاب می‌شوند. تنها رفعِ درست، ایزوله‌کردنِ خودِ تکه است.
  function ltr(v){
    var t = String(v==null?"":v);
    if(!t) return "—";
    return '<span class="mono" dir="ltr">'+esc(t)+'</span>';
  }
  // مقدار: لاتین/مسیر/کد ⇒ ایزوله؛ فارسی ⇒ همان‌طور
  function val(v){
    if(v===null||v===undefined||v==="") return '<span class="muted">—</span>';
    if(v===true) return '<span class="ok">بله</span>';
    if(v===false) return '<span class="muted">خیر</span>';
    var t = String(v);
    if(typeof v === "object"){ t = JSON.stringify(v); if(t==="{}"||t==="[]") return '<span class="muted">—</span>'; }
    return /[؀-ۿ]/.test(t) ? esc(t.slice(0,140)) : ltr(t.slice(0,140));
  }
  // برچسب‌های فنی → فارسیِ خوانا. کلیدِ ترجمه‌نشده خودش را نشان می‌دهد
  // (به‌جای اینکه بی‌صدا انگلیسی بماند و کسی متوجهِ جاافتادنش نشود).
  var LBL = {
    reachable:"در دسترس", reason:"دلیل", source:"منبع", ticks:"تیک",
    errors:"خطا", last_tick:"آخرین تیک", generation:"نسل",
    missing_fields:"فیلدهای غایب", available:"در دسترس",
    policy_doc:"سندِ سیاست", canonical_provider:"ارائه‌دهندهٔ مرجع",
    canonical_choke_point:"گلوگاهِ مرجع", drift_status:"وضعِ رانش",
    checked:"بررسی‌شده", missing_count:"شمارِ گمشده",
    vault_config_dir:"پوشهٔ پیکربندی", tasks_total:"کلِ کارها"
  };
  function lbl(k){ return LBL[k] || String(k).replace(/_/g," "); }
  // یک ردیف: برچسبِ کم‌رنگ + مقدارِ برجسته. جای <table> ِ خام.
  function row(k, v){
    return '<div class="row"><span class="k">'+esc(lbl(k))+'</span>'+
           '<span class="v">'+val(v)+'</span></div>';
  }
  function rows(obj, keys){
    obj = obj || {};
    return (keys||Object.keys(obj)).map(function(k){ return row(k, obj[k]); }).join("");
  }
  // نسخهٔ گردِ کارت — سرِ بخش نشانِ چشمِ اختاپوس می‌گیرد
  function card2(title, pill, body){
    return '<div class="card">'+secHead(title, pill)+body+'</div>';
  }
  function card(title, pill, body){
    return '<div class="card"><div class="ch"><h2>'+esc(title)+'</h2>'+(pill||"")+'</div>'+body+'</div>';
  }
  function pill(text, kind){
    return '<span class="badge '+(kind||"")+'">'+esc(text)+'</span>';
  }

  function renderBrain(el){
    el = el || content;
    api("/api/ops/brain").then(function(d){
      var b = d.brain||{}, dm = b.daemon||{};
      el.innerHTML = card2("مغز", pill(b.available?"در دسترس":"در دسترس نیست", b.available?"live":"blocked"),
        (b.reason?'<div class="muted">'+esc(b.reason)+'</div>':'')+
        rows(dm, ["reachable","source","ticks","errors","last_tick","generation"]));
    });
  }
  function renderGovernor(el){
    el = el || content;
    api("/api/governor").then(function(d){
      var ds = d.drift_status||{}, st = ds.status;
      el.innerHTML = card2("ناظر", pill(st||"نامعلوم", st==="ok"?"live":(st?"staged":"unknown")),
        rows(d, ["policy_doc","canonical_provider","canonical_choke_point"])+
        row("مسیرهای اعلام‌شده", (ds.declared_paths||[]).length));
    });
  }
  function renderObsidian(el){
    el = el || content;
    api("/api/obsidian").then(function(d){
      var miss = d.missing||[];
      el.innerHTML = card2("ابسیدین", pill(miss.length?miss.length+" گمشده":"کامل", miss.length?"staged":"live"),
        (miss.length?'<div class="list">'+miss.map(function(m){
            return '<div class="li">'+ltr(m)+'</div>'; }).join("")+'</div>'
                    :'<div class="muted">همهٔ سندهای مرجع سرِ جایشان‌اند</div>')+
        row("checked", d.checked));
    });
  }
  function renderNext(el){
    el = el || content;
    api("/api/ops/tasks").then(function(d){
      var st = d.task_status||{}, ks = Object.keys(st);
      el.innerHTML = card2("قدمِ بعدی", pill(d.tasks_total||0, ks.length?"staged":"live"),
        ks.length ? rows(st) : '<div class="muted">هیچ کارِ بازی نیست</div>');
    });
  }

  // ── پنج نمای مرکب (۲۰۲۶-۰۸-۰۴) ───────────────────────────────────────
  // سیزده تب روی گوشی یعنی هشت‌تایش بیرونِ صفحه. و بدتر: تب‌ها بر اساسِ
  // **جایی که داده از آن می‌آید** چیده شده بودند، نه تصمیمی که مالک می‌گیرد.
  // «Truth» و «UI Registry» و «Legs» سه پنجرهٔ تشخیصی‌اند، نه سه تصمیم.
  function stack(el, fns){
    el.innerHTML = fns.map(function(_,i){ return '<div id="sec'+i+'"></div>'; }).join("");
    fns.forEach(function(fn,i){ try{ fn(document.getElementById("sec"+i)); }catch(e){} });
  }
  // ── تریاژ (۲۰۲۶-۰۸-۰۴) ─────────────────────────────────────────────────
  // صفحه به‌جای «چه چیزهایی هست» می‌گوید «الان چه کار کن». حداکثر سه کارت،
  // مرتب‌شده بر اساسِ فوریت؛ هرچه سالم است در یک خطِ آرام جمع می‌شود.
  // شدت با **اندازه** کدگذاری می‌شود نه فقط رنگ، و فقط کارتِ اول دکمهٔ
  // پرشده دارد — یک انتخابِ آشکار در هر صفحه.
  // ── زبانِ دایره: اجزای گردِ مشترکِ همهٔ تب‌ها ─────────────────────────
  // رأیِ مالک: «پاهای اختاپوس و ساختارهای گرد همه‌جای کنترل‌پنل باشند، هر جا
  // خلاقیتی متفاوت ولی همه حولِ اختاپوس» — چون ذهنش **شکلِ هندسی و الگوی
  // حسی** را از تصویر می‌گیرد، نه از جدول. پس عدد باید **شکل** شود.
  // هر جزء داده‌محور است: اگر عددی پشتش نباشد ساخته نمی‌شود.

  // حلقهٔ درصدی با عددِ وسط — برای «چقدر از چقدر»
  function ring(val, max, label, tone, size){
    size = size || 118;
    var r = 44, C = 2*Math.PI*r;
    var f = max ? Math.max(0, Math.min(1, val/max)) : 0;
    return '<div class="ringwrap" style="width:'+size+'px">'+
      '<svg class="ring '+(tone||"cyan")+'" viewBox="0 0 110 110">'+
        '<circle class="rt" cx="55" cy="55" r="'+r+'" fill="none" stroke-width="9"/>'+
        '<circle class="rp" cx="55" cy="55" r="'+r+'" fill="none" stroke-width="9"'+
          ' stroke-linecap="round" stroke-dasharray="'+(C*f).toFixed(1)+' '+(C*(1-f)).toFixed(1)+'"'+
          ' transform="rotate(-90 55 55)"/>'+
        '<circle class="rc" cx="55" cy="55" r="30"/>'+
      '</svg>'+
      '<div class="ringnum">'+fa(val)+'</div>'+
      '<div class="ringlbl">'+esc(label)+'</div></div>';
  }

  // ردیفِ گرهٔ گرد — برای مجموعه‌های کوچک (وضعِ پاها، مراحلِ قیف)
  function orbs(items){
    return '<div class="orbs">'+items.map(function(it){
      return '<div class="orb '+(it.tone||"unk")+'" title="'+esc(it.name)+'">'+
        '<span class="od"></span><span class="on">'+esc(it.short||it.name)+'</span>'+
        (it.n!==undefined?'<span class="ov">'+fa(it.n)+'</span>':'')+'</div>';
    }).join("")+'</div>';
  }

  // کمانِ بخش‌بندی‌شده — برای توزیع (حالت‌های ارسال، مراحل)
  function arcs(segs){
    var tot = segs.reduce(function(a,b){return a+(b.n||0);},0) || 1;
    var r=44, C=2*Math.PI*r, off=0, out="";
    segs.forEach(function(sg){
      var f=(sg.n||0)/tot;
      out += '<circle class="ap '+(sg.tone||"cyan")+'" cx="55" cy="55" r="'+r+'" fill="none"'+
        ' stroke-width="11" stroke-dasharray="'+(C*f-1.5).toFixed(1)+' '+(C*(1-f)+1.5).toFixed(1)+'"'+
        ' stroke-dashoffset="'+(-C*off).toFixed(1)+'" transform="rotate(-90 55 55)"/>';
      off += f;
    });
    return '<div class="ringwrap" style="width:126px"><svg class="ring" viewBox="0 0 110 110">'+
      '<circle class="rt" cx="55" cy="55" r="'+r+'" fill="none" stroke-width="11"/>'+out+
      '<circle class="rc" cx="55" cy="55" r="28"/></svg>'+
      '<div class="ringnum">'+fa(tot)+'</div></div>';
  }

  // نشانِ کوچکِ اختاپوس برای سرِ هر بخش — همان چشم، در ابعادِ ریز
  function mini(tone){
    return '<svg class="minieye '+(tone||"cyan")+'" viewBox="0 0 24 24" aria-hidden="true">'+
      '<circle class="mr" cx="12" cy="12" r="10.5" fill="none" stroke-width="1.4"/>'+
      '<circle class="mi" cx="12" cy="12" r="5.4"/>'+
      '<circle class="mp" cx="12" cy="12" r="2.1"/></svg>';
  }
  function secHead(title, pill){
    return '<div class="ch">'+mini()+'<h2>'+esc(title)+'</h2>'+(pill||"")+'</div>';
  }

  // ── قرصِ اختاپوس ──────────────────────────────────────────────────────
  // ⚠️ استعاره باید **حساب** باشد نه تصویرسازی: هر بازو یک پای واقعی است و
  // رنگش وضعِ همان پا؛ حلقهٔ بیرونی نسبتِ فلگ‌های فعال را می‌کشد؛ چشم وقتی
  // ارگانیسم متوقف است فولادِ بی‌جان می‌شود. اگر عددی پشتش نباشد، فقط
  // تزئین است — و مالک همان را «ساده و زشت» می‌نامد.
  var ARM_A = [-90,-45,0,45,90,135,180,-135];   // هشت موضعِ ثابتِ ساعت
  function dialSVG(legs, halted, flagsOn, flagsAll){
    var names = Object.keys(legs||{}).slice(0,8);
    var R=110, cx=R, cy=R, bez=62, lens=57, iris=43, pup=33;
    var frac = flagsAll ? Math.max(0,Math.min(1, flagsOn/flagsAll)) : 0;
    var C = 2*Math.PI*(bez+16);
    // ── بازوی رباتیکِ اختاپوس ────────────────────────────────────────
    // خطِ خمیدهٔ ساده «پا» نبود. بازوی واقعی سه چیز دارد که در لوگو هست و
    // باید ساخته شود: **باریک‌شوندگی** از بُن به نوک · **پیچش** فزاینده ·
    // و **بندبندی** (حلقهٔ مفصل + بادکش). با چند قطعهٔ متوالی که پهنایشان
    // کم می‌شود ساخته می‌شود — چون stroke-width در SVG در طولِ یک path
    // تغییر نمی‌کند.
    var arms = "";
    var STEPS = 9;
    for(var i=0;i<8;i++){
      var a0 = ARM_A[i]*Math.PI/180;
      var curl = (i%2 ? 1 : -1) * 1.15;      // یکی‌درمیان خلافِ جهت ⇒ حسِ زنده
      var reach = 46, w0 = 9.5;
      var nm = names[i];
      var st = nm ? (legs[nm].live===false ? "down" : (legs[nm].live ? "up" : "unk")) : "none";
      var seg = "", joints = "", suck = "", pts = [];
      for(var k=0;k<=STEPS;k++){
        var t = k/STEPS;
        var a = a0 + curl*Math.pow(t,1.35);
        var r = bez + 1 + reach*t;
        pts.push([cx+Math.cos(a)*r, cy+Math.sin(a)*r, a, t]);
      }
      for(var k=0;k<STEPS;k++){
        var P=pts[k], Q=pts[k+1];
        var w = w0*(1 - 0.74*P[3]);
        var ln = ' x1="'+P[0].toFixed(1)+'" y1="'+P[1].toFixed(1)+
                 '" x2="'+Q[0].toFixed(1)+'" y2="'+Q[1].toFixed(1)+'"';
        // «استخوان» = بدنهٔ پیوستهٔ بازو؛ روی آن مهره‌های انرژی می‌دوند.
        // بدونِ استخوان، انیمیشن بازو را تکه‌تکه نشان می‌دهد.
        seg += '<line class="bone"'+ln+' stroke-width="'+w.toFixed(2)+'" stroke-linecap="round"/>'+
               '<line'+ln+' stroke-width="'+w.toFixed(2)+'" stroke-linecap="round"/>';
        // مفصلِ رباتیک: حلقهٔ کوچک روی هر بند
        if(k%2===0 && k<STEPS-1){
          joints += '<circle class="jt" cx="'+Q[0].toFixed(1)+'" cy="'+Q[1].toFixed(1)+
                    '" r="'+(w*0.42).toFixed(2)+'"/>';
        }
        // بادکشِ لبهٔ داخلی
        if(k>1){
          var perp = P[2] + Math.PI/2*(curl>0?-1:1);
          var sx = P[0]+Math.cos(perp)*(w*0.52), sy = P[1]+Math.sin(perp)*(w*0.52);
          suck += '<circle class="sk" cx="'+sx.toFixed(1)+'" cy="'+sy.toFixed(1)+
                  '" r="'+Math.max(0.9,(w*0.20)).toFixed(2)+'"/>';
        }
      }
      var tip = pts[STEPS];
      arms += '<g class="arm '+st+'">'+seg+joints+suck+
        '<circle class="node" cx="'+tip[0].toFixed(1)+'" cy="'+tip[1].toFixed(1)+'" r="5.2"/>'+
        '<circle class="core" cx="'+tip[0].toFixed(1)+'" cy="'+tip[1].toFixed(1)+'" r="1.9"/></g>';
    }
    // شکاف‌های سرخابیِ روی بدنه — مستقیم از لوگو
    var slits = "";
    [-62,-28,28,62,118,152,208,242].forEach(function(d){
      var a=d*Math.PI/180;
      slits += '<line class="slit" x1="'+(cx+Math.cos(a)*(bez-9)).toFixed(1)+'" y1="'+(cy+Math.sin(a)*(bez-9)).toFixed(1)+
        '" x2="'+(cx+Math.cos(a)*(bez-2)).toFixed(1)+'" y2="'+(cy+Math.sin(a)*(bez-2)).toFixed(1)+'"/>';
    });
    return '<svg class="dial'+(halted?" halted":"")+'" viewBox="0 0 '+(R*2)+' '+(R*2)+'" aria-hidden="true">'+
      '<defs>'+
        '<linearGradient id="steel" x1="0" y1="0" x2="0" y2="1">'+
          '<stop offset="0" stop-color="#9db0c8"/><stop offset=".5" stop-color="#4e5f78"/>'+
          '<stop offset="1" stop-color="#7d90a8"/></linearGradient>'+
        '<radialGradient id="iris" cx="50%" cy="34%" r="72%">'+
          '<stop offset="0" stop-color="#d6faff"/><stop offset=".42" stop-color="#22d3ee"/>'+
          '<stop offset="1" stop-color="#0a4d63"/></radialGradient>'+
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%">'+
          '<stop offset="0" stop-color="#a855f7" stop-opacity=".55"/>'+
          '<stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>'+
      '</defs>'+
      '<circle class="aura" cx="'+cx+'" cy="'+cy+'" r="'+(bez+30)+'" fill="url(#glow)"/>'+
      arms +
      '<circle class="track" cx="'+cx+'" cy="'+cy+'" r="'+(bez+16)+'" fill="none" stroke-width="3.5"/>'+
      '<circle class="prog" cx="'+cx+'" cy="'+cy+'" r="'+(bez+16)+'" fill="none" stroke-width="3.5"'+
        ' stroke-linecap="round" stroke-dasharray="'+(C*frac).toFixed(1)+' '+(C*(1-frac)).toFixed(1)+'"'+
        ' transform="rotate(-90 '+cx+' '+cy+')"/>'+
      '<circle class="bezel" cx="'+cx+'" cy="'+cy+'" r="'+bez+'" fill="url(#steel)"/>'+
      slits +
      '<circle class="lens" cx="'+cx+'" cy="'+cy+'" r="'+lens+'"/>'+
      '<circle class="irisring" cx="'+cx+'" cy="'+cy+'" r="'+iris+'" fill="none" stroke="url(#iris)" stroke-width="16"/>'+
      '<circle cx="'+cx+'" cy="'+cy+'" r="'+iris+'" fill="none" stroke="#050914" stroke-opacity=".5" stroke-width="16" stroke-dasharray="2.3 10"/>'+
      '<circle class="pupil" cx="'+cx+'" cy="'+cy+'" r="'+pup+'"/>'+
      '<circle class="spark" cx="'+cx+'" cy="'+cy+'" r="9"/>'+
      '<ellipse cx="'+(cx-24)+'" cy="'+(cy-34)+'" rx="20" ry="10" fill="#fff" opacity=".10" transform="rotate(-28 '+(cx-24)+' '+(cy-34)+')"/>'+
      '</svg>';
  }

  function triCard(sev, verb, why, act, small, z){
    return '<div class="tri '+sev+(small?" small":"")+(z?" "+z:"")+'"><div class="band"></div>'+
      '<div class="in"><h3 class="verb">'+esc(verb)+'</h3>'+
      '<div class="why">'+why+'</div>'+
      (act?'<button class="act" data-go="'+esc(act.tab)+'">'+esc(act.label)+'</button>':'')+
      '</div></div>';
  }
  function viewHome(el){
    el = el || content;
    el.innerHTML = '<div class="loading">در حال بارگذاری…</div>';
    Promise.all([api("/api/state"), api("/api/approvals"), api("/api/ops/tasks"),
                 api("/api/governor"), api("/api/obsidian"), api("/api/legs")])
      .then(function(a){
        var st=a[0]||{}, ap=a[1]||{}, tk=a[2]||{}, gv=a[3]||{}, ob=a[4]||{}, lg=a[5]||{};
        if(st.status==="error"){ el.innerHTML='<div class="err">خطا: '+esc(st.reason)+'</div>'; return; }
        setHalted(st.halted);
        setCore(st.halted?"ارگانیسم متوقف است":"ارگانیسم زنده است",
                (devMode?"حالتِ dev · ":"")+"ضربان "+fa(st.beat)+" · "+esc(st.epoch_mode||""));

        var need=[], calm=[];
        function push(sev,verb,why,act){ need.push({sev:sev,verb:verb,why:why,act:act}); }

        if(st.halted) push("hot","ارگانیسم متوقف است","تا برداشتنِ ترمز هیچ کاری جلو نمی‌رود.",null);
        var apc = Number(ap.count||0);
        if(apc>0) push("hot", fa(apc)+" تأیید منتظرِ توست",
                       "تا تصمیم نگیری، این‌ها همان‌جا می‌مانند.", {tab:"approvals",label:"برو به تأییدها"});
        else calm.push("صفِ تأیید خالی است");

        var tstat = tk.task_status||{};
        var tks = Number(tk.tasks_total||0) - Number(tstat.done||0);
        if(tks>0) push("warm", fa(tks)+" کارِ باز", "منتظرِ توست.", {tab:"tasks",label:"دیدنِ کارها"});
        else calm.push("هیچ کارِ بازی نیست");

        // علائمِ حیاتی فقط وقتی **بحرانی** باشند به خانه می‌آیند — وگرنه
        // جای‌شان تبِ سیستم است. خانه صفِ تریاژ است، نه داشبورد.
        var cd = st.cardiac||{};
        if(cd.depleted) push("hot","بودجهٔ ضربانِ امروز تمام شد",
          "ارگانیسم فقط ضربانِ پایه می‌زند — کارِ ارزشمند جلو نمی‌رود.",
          {tab:"system",label:"دیدنِ علائمِ حیاتی"});
        else if(cd.status==="ok" && cd.pct!==null && cd.pct>85)
          push("warm","بودجهٔ ضربان "+fa(cd.pct)+"٪ خرج شده",
            "تا آخرِ روز چیزِ زیادی نمانده.", {tab:"system",label:"دیدنِ علائمِ حیاتی"});
        else if(cd.stale) calm.push("بودجهٔ ضربان امروز به‌روز نشده");

        var arb = st.arbiter||{};
        if(arb.color==="RED") push("warm","سه قلب واگرا شده‌اند",
          "داورِ نبض RED است — ولی سایه است و هنوز هیچ اثری بر نبض ندارد.",
          {tab:"system",label:"دیدنِ داور"});
        else if(arb.color) calm.push("داورِ نبض: "+(ARB_FA[arb.color]||arb.color));

        if(st.germline_alert && st.germline_alert!=="ok")
          push("warm","ژرم‌لاین عقب افتاده",
            "تأخیر: "+fa(st.germline_lag_h)+" ساعت.", {tab:"system",label:"دیدنِ علائمِ حیاتی"});

        var dr=(gv.drift_status||{}).status;
        if(dr && dr!=="ok") push("warm","ناظر انحراف می‌بیند",
          "سندِ سیاست با کد نمی‌خواند: "+ltr(String(dr)), {tab:"system",label:"دیدنِ ناظر"});
        else if(dr) calm.push("ناظر بی‌انحراف");

        var miss=(ob.missing||[]).length;
        if(miss>0) push("warm", fa(miss)+" سندِ مرجع گم است",
          "ابسیدین اینها را پیدا نکرد.", {tab:"system",label:"دیدنِ ابسیدین"});
        else calm.push("سندهای مرجع کامل");

        var legs=lg.legs||{}, dead=Object.keys(legs).filter(function(k){ return legs[k].live===false; });
        if(dead.length) push("warm", fa(dead.length)+" پا خاموش است",
          dead.slice(0,3).map(ltr).join(" · "), {tab:"system",label:"دیدنِ پاها"});
        else if(Object.keys(legs).length) calm.push("همهٔ پاها زنده");

        need.sort(function(x,y){ return (x.sev==="hot"?0:1)-(y.sev==="hot"?0:1); });
        var show = need.slice(0,3), rest = need.length-show.length;

        // قرص بالای همه — چشمِ اختاپوس با هشت بازوی واقعی
        var fl = st.active_flags||{};
        var flOn = Object.keys(fl).filter(function(k){return fl[k];}).length;
        var html = '<div class="dialwrap" id="dialWrap">'+
          dialSVG(legs, st.halted, flOn, Object.keys(fl).length)+
          '<div class="dialcap">'+fa(flOn)+' از '+fa(Object.keys(fl).length)+' فلگ فعال</div></div>';
        if(!show.length){
          html += '<div class="calm"><div class="big">هیچ کاری با تو نیست</div>'+
                  '<div class="sm">همه‌چیز سرِ جایش است.</div></div>';
        } else {
          html += show.map(function(c,i){
            // کلاسِ عمق: فوری جلو، بعدی‌ها عقب‌تر و نرم‌تر. فاصله خودش پیام است.
            return triCard(c.sev, c.verb, c.why, i===0?c.act:null, i>0, "z"+i);
          }).join("");
          if(rest>0) calm.unshift(fa(rest)+" موردِ کم‌فوریت‌ترِ دیگر");
        }
        if(calm.length){
          html += '<details class="quiet"><summary>'+fa(calm.length)+' چیزِ دیگر سالم است</summary>'+
                  '<div class="inner">'+calm.map(function(c){
                    return '<div class="row"><span class="k">✓</span><span class="v">'+
                      (/[؀-ۿ]/.test(c)?esc(c):c)+'</span></div>'; }).join("")+
                  '</div></details>';
        }
        html += '<details class="quiet"><summary>وضعِ فنی</summary><div class="inner">'+
          row("commit", st.commit)+row("halted", st.halted)+row("frozen", st.frozen)+
          row("epoch", st.epoch_mode)+row("ts", st.ts)+
          '</div></details>';
        el.innerHTML = html;
        [].forEach.call(el.querySelectorAll(".act"), function(b){
          b.addEventListener("click", function(){ goTab(b.getAttribute("data-go")); });
        });
      });
  }
  // ── علائمِ حیاتی ───────────────────────────────────────────────────────────
  // این سه از قبل روی دیسک بودند و allowlist ِ /api/state دورشان می‌ریخت، و
  // رنگِ داور اصلاً هیچ‌جا ثبت نمی‌شد. جای‌شان این‌جاست نه خانه: خانه یعنی
  // «چه چیزی با توست»، بدن یعنی «حالِ ارگانیسم». فقط وقتی یکی‌شان بحرانی
  // شود، به‌صورتِ کارتِ تریاژ به خانه می‌آید.
  var ARB_FA = {GREEN:"هماهنگ", AMBER:"کشمکش", RED:"واگرا"};
  var ARB_TONE = {GREEN:"ok", AMBER:"amber", RED:"bad"};
  function renderVitals(el){
    el.innerHTML = "";
    api("/api/state").then(function(st){
      st = st || {};
      var c = st.cardiac || {}, ar = st.arbiter || {}, rr = st.recall_reach || {};
      var h = secHead("علائمِ حیاتی");
      var body = "";

      // ۱) بودجهٔ ضربان — تنها حلقه‌ای که مخرجِ واقعی دارد
      if(c.status === "ok" && c.pct !== null && c.pct !== undefined){
        body += ring(c.spent, c.cap, "ضربان از "+fa(c.cap),
                     c.depleted ? "bad" : (c.pct > 80 ? "amber" : "cyan"), 118);
      } else {
        // کهنه یا غایب ⇒ حلقه نمی‌کشم. حلقهٔ بی‌مخرج تزئین است، و حلقهٔ
        // دیروز از حلقه‌نداشتن بدتر — چون شبیهِ امروز دیده می‌شود.
        body += '<div class="ringwrap dim" style="width:118px">'+
          '<div class="ringnum">—</div><div class="ringlbl">بودجهٔ ضربان<br>'+
          (c.stale ? "دادهٔ "+ltr(String(c.date||"?"))+"، نه امروز" : "خوانده نشد")+
          '</div></div>';
      }

      // ۲) تأخیرِ ژرم‌لاین — ساعت، نه درصد. مخرج ندارد پس گره است نه حلقه.
      var gl = st.germline_lag_h;
      body += orbs([{name:"ژرم‌لاین",
                     short: gl===null||gl===undefined ? "نامعلوم" : ltr(Number(gl).toFixed(2))+" ساعت",
                     tone: st.germline_alert==="ok" ? "ok" :
                           (gl===null||gl===undefined ? "unk" : "warn")}]);

      // ۳) دسترسیِ حافظه + رنگِ داور
      body += orbs([
        {name:"رویدادهای حافظه", short:"حافظه", n: rr.events,
         tone: rr.events ? "ok" : "unk"},
        {name:"داورِ نبض", short: ARB_FA[ar.color] || "نامعلوم",
         tone: ARB_TONE[ar.color] || "unk"}
      ]);
      h += '<div class="vitals">'+body+'</div>';

      // متن پشتِ تاشو — شکل بالا، عدد پایین
      h += '<details class="det"><summary>عددهایش</summary><div class="inner">'+
        row("بودجه", c.status==="ok" ? fa(c.spent)+" از "+fa(c.cap)+
            (c.stale?" (کهنه)":"") : "خوانده نشد")+
        row("استراحت", c.resting)+
        row("تأخیرِ ژرم‌لاین (ساعت)", gl)+
        row("هشدارِ ژرم‌لاین", st.germline_alert)+
        row("میانهٔ دسترسیِ حافظه", rr.reach_median)+
        row("دورهٔ مؤثرِ داور (ثانیه)", ar.effective_period_s)+
        row("رانندهٔ داور", ar.driver)+
        row("قلب‌های حاضر", ar.n_present)+
        // ⚠️ این خط باربر است: رنگِ داور امروز **سایه** است. اگر مالک فکر کند
        // نبضِ زنده را می‌راند، یک تصمیمِ غلط روی یک عددِ بی‌اثر می‌گیرد.
        row("سیمِ داور", ar.wire_open ? "زنده — نبض را می‌راند" :
                                        "سایه — فقط مشاهده، هیچ اثری بر نبض ندارد")+
      '</div></details>';
      el.innerHTML = h;
    });
  }

  // ── تبِ کارها ─────────────────────────────────────────────────────────────
  // چرا این تبِ ششم است: `task.create` و `task.done` دو تا از شش اقدامِ
  // allowlist‌شده‌اند و هیچ خانه‌ای نداشتند (لیدها و پول خانه دارند). بدونِ
  // این تب، آن دو اقدام فقط در رجیستری وجود داشتند نه در دسترسِ مالک.
  var TASK_KINDS = ["general","followup","manual_send","content_prepare",
                    "content_post","check_payment","review_campaign"];
  var KIND_FA = {general:"عمومی", followup:"پیگیری", manual_send:"ارسالِ دستی",
                 content_prepare:"آماده‌سازیِ محتوا", content_post:"انتشارِ محتوا",
                 check_payment:"چکِ پرداخت", review_campaign:"مرورِ کمپین"};
  var PRIO_FA = {1:"فوری", 2:"مهم", 3:"عادی", 4:"وقتی شد", 5:"روزی"};

  function renderTasks(el){
    el.innerHTML = '<div class="loading">در حال بارگذاری…</div>';
    api("/api/ops/tasks").then(function(t){
      t = t || {};
      if(t.status==="error"){ el.innerHTML='<div class="err">خطا: '+esc(t.reason)+'</div>'; return; }
      var items = t.items;                      // ⚠️ null ≠ [] — پایین جدا می‌شوند
      var stat = t.task_status || {};
      var open = Number(t.tasks_total||0) - Number(stat.done||0);

      // شکل‌ها بالا: یک حلقهٔ «باز از کل» و گره‌های وضع
      var html = secHead("کارها", pill(fa(open)+" باز", open>0?"warn":"ok"));
      html += '<div class="vitals">'+
        ring(open, Math.max(Number(t.tasks_total||0),1), "باز", open>0?"amber":"cyan", 112)+
        orbs(Object.keys(stat).map(function(k){
          return {name:k, short:(k==="done"?"انجام":k==="open"?"باز":ltr(k)), n:stat[k],
                  tone:(k==="done"?"ok":"warn")};
        }))+'</div>';

      if(items === null || items === undefined){
        html += '<div class="err">فهرستِ کارها خوانده نشد — پایگاهِ ops در دسترس نیست. '+
                'شمارشِ بالا از منبعِ دیگری است، پس ممکن است با فهرست نخواند.</div>';
      } else if(!items.length){
        html += '<div class="calm"><div class="big">هیچ کارِ بازی نیست</div>'+
                '<div class="sm">پایین یکی بساز.</div></div>';
      } else {
        html += '<div class="tasklist">'+items.map(function(it){
          var p = Number(it.priority||3);
          return '<div class="titem p'+p+'">'+
            '<button class="tdone" data-id="'+esc(it.id)+'" aria-label="انجام شد">✓</button>'+
            '<div class="tbody"><div class="tt">'+esc(it.title||"—")+'</div>'+
            '<div class="tm">'+esc(KIND_FA[it.kind]||ltr(String(it.kind||"")))+
            ' · '+esc(PRIO_FA[p]||fa(p))+
            (it.due_at?' · تا '+ltr(String(it.due_at)):'')+'</div></div></div>';
        }).join("")+'</div>';
      }

      // فرمِ ساخت پشتِ تاشو — شکل بالا، متن پایین (رأیِ مالک)
      html += '<details class="det"><summary>کارِ تازه بساز</summary><div class="inner">'+
        '<input class="fin" id="ntTitle" type="text" placeholder="عنوانِ کار" maxlength="240">'+
        '<div class="chips" id="ntKind">'+TASK_KINDS.map(function(k,i){
          return '<button class="chip'+(i===0?" on":"")+'" data-v="'+k+'">'+esc(KIND_FA[k])+'</button>';
        }).join("")+'</div>'+
        '<div class="chips" id="ntPrio">'+[1,2,3,4,5].map(function(p){
          return '<button class="chip'+(p===3?" on":"")+'" data-v="'+p+'">'+esc(PRIO_FA[p])+'</button>';
        }).join("")+'</div>'+
        '<button class="go" id="ntGo">بساز</button>'+
      '</div></details>';
      el.innerHTML = html;

      [].forEach.call(el.querySelectorAll(".tdone"), function(b){
        b.addEventListener("click", function(){
          act("task.done", {task_id:b.getAttribute("data-id")}, b).then(function(r){
            if(r && r.ok) renderTasks(el);          // فقط وقتی واقعاً شد
          });
        });
      });
      [].forEach.call(el.querySelectorAll(".chips"), function(g){
        g.addEventListener("click", function(e){
          var c = e.target.closest(".chip"); if(!c) return;
          [].forEach.call(g.children, function(x){ x.classList.remove("on"); });
          c.classList.add("on");
        });
      });
      var go = el.querySelector("#ntGo");
      if(go) go.addEventListener("click", function(){
        var title = (el.querySelector("#ntTitle")||{}).value || "";
        if(!title.trim()){ toast("عنوان خالی است", "bad"); return; }
        var k = el.querySelector("#ntKind .chip.on"), p = el.querySelector("#ntPrio .chip.on");
        act("task.create", {title:title.trim(),
                            kind:(k?k.getAttribute("data-v"):"general"),
                            priority:Number(p?p.getAttribute("data-v"):3)}, go)
          .then(function(r){ if(r && r.ok) renderTasks(el); });
      });
    });
  }

  function goTab(name){
    var t = document.querySelector('#tabs .tab[data-tab="'+name+'"]');
    if(!t) return;
    [].forEach.call(tabs.children, function(x){x.classList.remove("active");});
    t.classList.add("active");
    render(name);
  }
  function viewApprovals(el){ stack(el||content, [renderApprovals]); }
  function viewMoney(el){ stack(el||content, [renderValue, renderOutbound]); }
  function viewLeads(el){ stack(el||content, [renderPF]); }
  function viewSystem(el){ stack(el||content, [renderLegs, renderVitals, renderBrain, renderGovernor, renderObsidian, renderTruth, renderRegistry, renderStudio]); }

  function viewTasks(el){ stack(el||content, [renderTasks]); }

  var renderers = {home:viewHome,approvals:viewApprovals,money:viewMoney,
                   leads:viewLeads,tasks:viewTasks,system:viewSystem};
  // ⚠️ سکوت را بلند کن. نسخهٔ قبلی `renderers[name]||renderHome` بود، پس یک تبِ
  // بی‌رندرکننده **بی‌صدا** محتوای خانه را نشان می‌داد — کلاسِ باگی که کلِ امروز
  // دنبالش بودیم، این‌بار در UI. حالا تبِ ناشناخته خودش را اعلام می‌کند.
  function render(name){
    var fn = renderers[name];
    if(!fn){
      el.innerHTML = '<div class="card"><h2>این تب هنوز رندرکننده ندارد</h2>'+
        '<div class="muted">تبِ «'+esc(name)+'» در HTML هست ولی هیچ تابعی آن را نمی‌سازد. '+
        'این پیام عمدی است: قبلاً بی‌صدا صفحهٔ خانه نشان داده می‌شد.</div></div>';
      return;
    }
    fn();
  }

  // boot
  setAuth(devMode ? "dev-mode" : "…");
  render("home");
})();
