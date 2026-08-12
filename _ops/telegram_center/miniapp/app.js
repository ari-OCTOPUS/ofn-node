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
  // FIX (deep-scan 2026-08-07): stale-fetch guard — هر render() این را increment
  // می‌کند؛ callback‌های async قبل از نوشتنِ innerHTML چک می‌کنند که آیا هنوز
  // رندرِ فعلی‌اند یا کاربر تب را عوض کرده. اگر stale بودند، silent return.
  var _renderSeq = 0;
  var warn = document.getElementById("warn");
  var coreLead = document.getElementById("coreLead");
  var coreSub = document.getElementById("coreSub");
  var eye = document.getElementById("eye");

  // ── پوستهٔ Mini Apps 2.0 (فاز ۳، ۲۰۲۶-۰۸-۰۴) ─────────────────────────
  // تا امروز کلِ یکپارچگیِ تلگرام یک خط بود: expand + setHeaderColor. یعنی
  // روی گوشی محتوا **زیرِ نُچ** می‌رفت، تمام‌صفحه نبود، و در پس‌زمینه هم
  // poll می‌کرد. منطقش عمداً در `tg_shell.js` است تا در node واقعاً تست شود
  // (۱۳ تست) — نه با assert ِ متنی روی همین فایل.
  // چرومِ خودِ تلگرام هم باید تیره شود — وگرنه هنگامِ باز شدن یک فلاشِ سفید
  // می‌بینی و نوارِ پایین با اپ نمی‌خواند. هر سه اختیاری‌اند (کلاینتِ قدیمی
  // ندارد)، پس هرکدام جدا try می‌شود؛ یک شکست نباید بقیه را بکشد.
  if (tg) {
    try { tg.setHeaderColor("#050914"); } catch(e){}
    try { tg.setBackgroundColor("#050b16"); } catch(e){}
    try { tg.setBottomBarColor("#0a1120"); } catch(e){}
  }
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

  // ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷: بازگشت به تب — رویدادِ استاندارد، بیرونِ
  // Telegram هم (devMode/پیش‌نمایشِ مرورگر). مکملِ onActive بالاست، نه
  // جایگزینش: آن‌جا فقط پشتِ bridge ِ تلگرام سیم‌کشی شده و در devMode
  // اصلاً صدا زده نمی‌شود.
  document.addEventListener("visibilitychange", function(){
    if(document.visibilityState !== "visible") return;
    try {
      var act = document.querySelector("#tabs .tab.active");
      if (act) { render(act.getAttribute("data-tab")); }
    } catch(e){}
  });

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
    /* ⚠️ سوییچِ پوستهٔ بصری **حذف شد** — ۲۰۲۶-۰۸-۰۴. برنگردانش.
     *
     * این‌جا یک دکمه بود که بین سه پوسته (نئون/شیشه‌ای/عمق) می‌چرخید و
     * انتخاب را در `localStorage` نگه می‌داشت. رأیِ صریحِ مالک: «گزینش را
     * پاک کن، نمی‌خواهم تغییرپذیر باشد».
     *
     * دو نکته که هنگامِ حذف پیدا شد و ارزشِ نوشتن دارند:
     *   ۱. برخلافِ دو دکمهٔ بالا، این یکی به هیچ capability گیت نشده بود —
     *      یعنی حتی در حالتِ dev و روی کلاینتِ بی‌قابلیت هم ظاهر می‌شد.
     *   ۲. «ریستِ یک‌بارهٔ نئون» فقط **یک بار در عمرِ دستگاه** اجرا می‌شد
     *      (سنتینلِ octo-skin-v2). پس هر کس یک بار روی «شیشه‌ای» چرخانده
     *      بود، برای همیشه روی همان بالا می‌آمد و رأیِ بعدیِ مالک هیچ اثری
     *      نداشت. یعنی ظاهرِ اپ به یک حالتِ ماندگارِ نامرئیِ per-device
     *      گره خورده بود.
     *
     * هیچ removeItem ِ پاک‌سازی هم اضافه نمی‌شود: وقتی خواننده‌ای نمانده،
     * کلیدها بی‌اثرند، و کدی که برای پاک‌کردن می‌نویسد خودش دوباره ظاهر را
     * به storage وابسته می‌کند. پوسته حالا در CSS ثابت است، بدونِ هیچ
     * selector ِ [data-skin].
     */
  })();

  // tabs — ARIA tablist: role="tab" روی هر برگه، roving tabindex، و کیبورد
  // (چپ/راست/Home/End/Enter) — قبلاً فقط کلیک کار می‌کرد.
  var tabs = document.getElementById("tabs");
  // لایهٔ ۱ — closing guard: هر input با focus = ویرایشِ در حالِ انجام.
  // یک swipe روی iOS اپ را می‌بندد و داده از دست می‌رود. تلگرام هشدار می‌دهد.
  // delegate سراسری: ورودی‌ها بعد از render ساخته می‌شوند، پس focus/blur را
  // روی document گوش می‌دهیم نه روی هر input جداگانه.
  document.addEventListener("focusin", function(e){
    var t = e.target;
    if(t && t.tagName === "INPUT" && t.type === "text"){ enableClosingGuard(true); }
  });
  document.addEventListener("focusout", function(e){
    var t = e.target;
    if(t && t.tagName === "INPUT" && t.type === "text"){ enableClosingGuard(false); }
  });
  function activateTab(t){
    if(!t) return;
    [].forEach.call(tabs.children, function(x){
      x.classList.remove("active");
      x.setAttribute("aria-selected", "false");
      x.setAttribute("tabindex", "-1");
    });
    t.classList.add("active");
    t.setAttribute("aria-selected", "true");
    t.setAttribute("tabindex", "0");
    content.setAttribute("aria-labelledby", t.id);
    render(t.getAttribute("data-tab"));
  }
  tabs.addEventListener("click", function(e){
    var t = e.target.closest(".tab"); if(!t) return;
    activateTab(t);
  });
  tabs.addEventListener("keydown", function(e){
    var cur = e.target.closest(".tab"); if(!cur) return;
    var list = [].slice.call(tabs.children);
    var i = list.indexOf(cur);
    if(i < 0) return;
    var next = null;
    if(e.key === "ArrowRight") next = list[(i + 1) % list.length];
    else if(e.key === "ArrowLeft") next = list[(i - 1 + list.length) % list.length];
    else if(e.key === "Home") next = list[0];
    else if(e.key === "End") next = list[list.length - 1];
    else if(e.key === "Enter" || e.key === " "){ activateTab(cur); e.preventDefault(); return; }
    if(next){ e.preventDefault(); next.focus(); activateTab(next); }
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
  function apiPost(path, payload, timeoutMs){
    // ۲۰۲۶-۰۸-۱۲: بدون abort، Ask روی ollama hang تا ابد «فکر کردن» می‌ماند.
    var ms = (timeoutMs == null) ? 60000 : timeoutMs;
    var ctrl = (typeof AbortController !== "undefined") ? new AbortController() : null;
    var timer = null;
    if (ctrl && ms > 0) {
      timer = setTimeout(function(){ try { ctrl.abort(); } catch(e){} }, ms);
    }
    var opts = {method:"POST", headers:tgHeaders({"Content-Type":"application/json"}),
                body:JSON.stringify(payload||{})};
    if (ctrl) opts.signal = ctrl.signal;
    return fetch(path, opts).then(function(r){
      return r.text().then(function(raw){
        var data = null;
        try { data = raw ? JSON.parse(raw) : null; }
        catch (e) {
          return {ok:false, status:"ERROR", reason:"bad_json",
                  http_status:r.status, preview:String(raw||"").slice(0,120)};
        }
        if(!r.ok){
          if(data && typeof data === "object"){
            if(data.reason == null) data.reason = "http_"+r.status;
            data.ok = false;
            data.http_status = r.status;
            return data;
          }
          return {ok:false, status:"ERROR", reason:"http_"+r.status, http_status:r.status};
        }
        return data || {ok:false, status:"ERROR", reason:"empty_body"};
      });
    }).catch(function(e){
      var name = (e && e.name) || "";
      var msg = (e && e.message) || "network";
      if (name === "AbortError") return {ok:false,status:"ERROR",reason:"client_timeout"};
      return {ok:false,status:"ERROR",reason:msg};
    }).then(function(v){
      if (timer) clearTimeout(timer);
      return v;
    });
  }
  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }

  // ── پلِ SDK ِ بومیِ تلگرام ۲۰۲۶ (لایهٔ ۱، ۲۰۲۶-۰۸-۰۸) ──────────────────
  // اپ تا امروز فقط expand() و HapticFeedback.impactOccurred داشت — ولی
  // تلگرام MainButton، selectionChanged، و enableClosingConfirmation دارد.
  // هر سه با feature-detection (نه فرض) گیت می‌شوند: کلاینتِ قدیمی و
  // حالتِ dev هر دو سالم می‌مانند. یک شکست نباید بقیه را بکشد.
  // منبع: core.telegram.org/bots/webapps (Bot API 7.10+/8.0+/9.x).
  function _tgBtn(){
    // BottomButton در 7.10+ معرفی شد (MainButton نسخهٔ قدیمی‌تر است).
    // هر دو را می‌آزما — کلاینتِ قدیمی به MainButton می‌رسد.
    return (tg && (tg.BottomButton || tg.MainButton)) || null;
  }
  // هشدارِ لمسی هنگام انتخاب (چیپ/radio/checkbox) — متمایز از impactOccurred.
  function hapticSelect(){ try{ if(tg && tg.HapticFeedback){ tg.HapticFeedback.selectionChanged(); } }catch(e){} }
  // تنظیم/پاک‌کردنِ دکمهٔ بومیِ پایین — CTA ِ هر تب.
  // بدونِ متن = مخفی. هر تب در render خودش این را صدا می‌زند.
  var _bottomClick = null;
  function setBottomButton(text, onClick){
    var btn = _tgBtn();
    if(!btn){ return; }                       // کلاینتِ قدیمی یا devMode
    try{
      if(!text){ btn.hide(); if(_bottomClick){ btn.offClick(_bottomClick); _bottomClick=null; } return; }
      if(btn.setText){ btn.setText(text); }
      else if("text" in btn){ btn.text = text; }
      btn.enable();
      btn.show();
      if(_bottomClick){ try{ btn.offClick(_bottomClick); }catch(e){} }
      _bottomClick = onClick;
      try{ btn.onClick(_bottomClick); }catch(e){}
    }catch(e){}
  }
  function hideBottomButton(){ setBottomButton("", null); }
  // بستنِ اپ را هنگام ویرایشِ فرم تأیید می‌گیرد — swipe-to-close هشدار می‌دهد.
  function enableClosingGuard(on){
    try{
      if(on && tg && tg.enableClosingConfirmation){ tg.enableClosingConfirmation(); }
      else if(tg && tg.disableClosingConfirmation){ tg.disableClosingConfirmation(); }
    }catch(e){}
  }

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
    // FIX (deep-scan 2026-08-07): اگر fetch هنگ کند (سرور قبول می‌کند ولی پاسخ
    // نمی‌دهد)، دکمه برای همیشه disabled می‌ماند. ۳۰s watchdog آن را آزاد می‌کند.
    if(btn){ var _btnT = setTimeout(function(){ btn.disabled=false; btn.removeAttribute("data-busy"); }, 30000); }
    if(tg && tg.HapticFeedback){ try{ tg.HapticFeedback.impactOccurred("light"); }catch(e){} }
    return apiPost("/api/actions", {action:action, payload:payload||{},
                                    action_id: actionIdOf(action, payload)})
      .then(function(r){
        if(btn && _btnT) clearTimeout(_btnT);   // watchdog لغو شد — پاسخ آمد
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
  // ⚠️ XSS (فیکس‌شده، اصلاح‌شدهٔ دوم — دو ایجنتِ موازی امروز اینجا برخورد
  // کردند): نسخهٔ اول innerHTML=msg بدونِ شرط بود؛ یک تلاشِ بعدی (هم‌زمان،
  // ایجنتِ دیگر) آن را به textContent=msg عوض کرد چون «هرگز HTML تزریق
  // نمی‌کند». هر دو درست می‌گفتند برای رشتهٔ لفظی، ولی act() (بالاتر) وقتی
  // BLOCKED با reason برمی‌گردد، msg را با ltr(reason) می‌سازد — یعنی msg
  // واقعاً حاویِ `<span dir="ltr">...</span>` است. textContent آن span را
  // به‌صورتِ متنِ خام (خودِ تگ‌ها) نشان می‌داد، نه رندر می‌کرد — رگرسیونِ
  // بصریِ واقعی. راه‌حل: msg را trust کن (قراردادِ innerHTML=html ِ همهٔ
  // این فایل: مقدارِ ورودی از پیش امن است — رشتهٔ لفظیِ ثابت یا از
  // esc()/ltr() ساخته‌شده)، نه escape ی جدید و نه textContent.
  function toast(msg, tone){
    var w = document.getElementById("toast");
    if(!w){ w = document.createElement("div"); w.id = "toast"; document.body.appendChild(w); }
    w.className = "toast " + (tone||"warn") + " show";
    w.innerHTML = msg;
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
    // نبودِ داده حکم نیست: نشانِ «مسدود» صورتی است و شبیهِ ردِ فعال دیده
    // می‌شود. «نمی‌دانم» رنگِ خودش را دارد — فولادِ خنثی.
    if(v===null||v===undefined) return '<span class="badge unknown">نامعلوم</span>';
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
    // سه‌حالته: null یعنی «نمی‌دانم»، که نه درخشش است نه خاکستریِ توقف.
    // قبلاً دوحالته بود و undefined به «زنده» می‌افتاد — یعنی نبودِ داده
    // شبیهِ سلامت دیده می‌شد.
    if(!eye) return;
    eye.setAttribute("class", "eye" + (h === null || h === undefined ? " unknown"
                                       : (h ? " halted" : "")));
  }

  // ⚠️ ۲۰۲۶-۰۸-۰۹ — `renderHome` این‌جا بود و **صداکنندهٔ صفر** داشت: تبِ
  // home از `viewHome` (پایین‌تر، نمایِ تریاژِ فعلی) رد می‌شود، نه از این‌جا.
  // برخلافِ `renderStudio` (که یک تستِ صریح نگهش می‌دارد چون سه اقدامش
  // هنوز مستندسازیِ تاریخی دارند)، این تابع نه تستی داشت نه توضیحی —
  // فقط باقیماندهٔ نسخهٔ پیش از بازطراحیِ تریاژِ ۰۸-۰۴ بود. حذف شد.

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
      d = d || {};
      // ⚠️ `pending: null` یعنی «خوانده نشد»، `pending: []` یعنی «واقعاً هیچ».
      // نسخهٔ قبلی هر دو را با `d.pending||[]` یکی می‌کرد و «صف خالی است»
      // می‌نوشت — یک اطمینانِ فعال از دلِ یک except ِ بلعنده.
      if(d.status !== "ok"){
        el.innerHTML = '<div class="card">'+secHead("صفِ تأیید",
            pill("نامعلوم","unk"))+
          '<div class="err">صفِ تأیید خوانده نشد ('+esc(String(d.status||"?"))+
          (d.reason?" — "+esc(String(d.reason)):"")+
          '). عمداً «خالی» نمی‌نویسم: نبودِ داده با نبودِ کار یکی نیست.</div></div>';
        return;
      }
      var pend = d.pending||[], n = Number(d.count||pend.length||0);
      var body = n ? '<div class="tasklist">'+pend.slice(0,8).map(function(p){
          var id = esc(p.proposal_id);
          var days = p.since ? Math.floor((Date.now()-Date.parse(p.since))/86400000) : null;
          return '<div class="titem p2" data-pid="'+id+'">'+
            '<div class="tbody">'+
              '<div class="tt"><span dir="ltr" class="iso">'+id+'</span></div>'+
              '<div class="tm">'+esc(p.kind||"—")+
                (days!==null?' · '+fa(days)+' روز منتظر':'')+
                (p.amount_aud?' · '+fa(p.amount_aud)+' دلار':'')+'</div>'+
              '<div class="pend" hidden></div>'+
            '</div>'+
            '<button class="pno" data-pid="'+id+'" aria-label="رد">✕</button>'+
            '<button class="pyes" data-pid="'+id+'" aria-label="تأیید">✓</button>'+
            '</div>';
        }).join("")+'</div>'
        : '<div class="muted" style="text-align:center">صف خالی است</div>';
      if(d.sandbox_hidden){
        body += '<div class="muted" style="text-align:center;margin-top:8px">'+
          fa(d.sandbox_hidden)+' کارتِ آزمایشی (sandbox) پنهان شد — حذف نشده‌اند.'+
          '</div>';
      }
      // ⚠️ مخرجِ `Math.max(n,5)` ساختگی بود: کمانِ حلقه هیچ چیزِ واقعی را
      // کد نمی‌کرد. صف سقفِ طبیعی ندارد، پس وقتی عددی برای مقایسه نیست،
      // گره می‌کشم نه حلقه — همان قاعده‌ای که در علائمِ حیاتی گذاشتم.
      // ⚠️ ۲۰۲۶-۰۸-۰۵ — سؤالِ مالک: «تأیید کردم؛ کار کرد و تأثیر داشت؟»
      // تا امروز صفحه بعد از تأیید فقط کارت را ناپدید می‌کرد و هیچ‌وقت
      // نمی‌گفت بعدش چه شد. این بخش همان شکاف را مرئی می‌کند: حکم ثبت شده،
      // ولی `owner-decision` **صفر خواننده** دارد، پس تا وقتی اثرگری نباشد
      // «ثبت شد» تمامِ حقیقت است — و صفحه دقیقاً همین را می‌گوید نه بیشتر.
      var dec = d.decisions||[];
      if(dec.length){
        body += '<div class="secsub">تصمیم‌های اخیرِ تو — و بعدش چه شد</div>';
        body += dec.map(function(x){
          var done = Number(x.effects_after||0) > 0;
          var vfa = x.verdict==="approved" ? "تأیید" :
                    x.verdict==="rejected" ? "رد" : ltr(String(x.verdict||"?"));
          return '<div class="titem '+(done?"ok":"warm")+'">'+
            '<div class="tmain">'+
              '<div class="tid">'+ltr(esc(String(x.proposal_id)))+' · '+vfa+'</div>'+
              '<div class="tage">'+(done
                ? 'اثر ثبت شد — '+ltr(esc(String(x.next_event||"")))
                : 'ثبت شد؛ هنوز هیچ اثری پشتِ آن ثبت نشده')+'</div>'+
            '</div></div>';
        }).join("");
        if(dec.some(function(x){ return !Number(x.effects_after||0); })){
          body += '<div class="cdnote">«اثری ثبت نشده» یعنی حکمِ تو ماندگار است '+
            'ولی هیچ اثرگری هنوز برش نداشته — نه اینکه رد شده باشد.</div>';
        }
      }
      el.innerHTML = '<div class="card">'+secHead("صفِ تأیید")+
        '<div class="vitals">'+orbs([{name:"منتظرِ تو", short:"منتظرِ تو",
                                      n:n, tone:(n?"hot":"ok")}])+'</div>'+
        body+'</div>';
      wireDecisions(el);
    });
  }

  // ── تصمیم با پنجرهٔ لغوِ ۱۰ ثانیه‌ای ─────────────────────────────────────
  // رأیِ مالک (۰۸-۰۵): «تأخیرِ واقعی — ۱۰ ثانیه هیچ اتفاقی نمی‌افتد».
  //
  // یعنی تا ثانیهٔ دهم **هیچ چیزی نوشته نمی‌شود**؛ لغو هیچ ردی در دفتر
  // نمی‌گذارد. جایگزینش این بود که فوری بنویسیم و لغو یک ردیفِ معکوس بزند
  // — که دفتر را دو ردیفه می‌کرد. مالک اولی را انتخاب کرد.
  //
  // ⚠️ عارضه‌ای که باید صادق باشیم: اگر وسطِ شمارش اپ را ببندی یا اینترنت
  // قطع شود، تصمیم **اصلاً ثبت نمی‌شود**. پس متنِ شمارش صریحاً می‌گوید
  // «تا پایانِ شمارش نبند» — کاربر باید عارضه را بداند، نه اینکه بعداً
  // کشفش کند.
  var DECIDE_DELAY_S = 10;
  var _timers = {};
  function clearDecisionTimers(){
    Object.keys(_timers).forEach(function(k){ clearInterval(_timers[k]); delete _timers[k]; });
  }

  // دو خانوادهٔ تصمیم، یک مکانیزم. کارتِ RFC ِ راکد دقیقاً همان پنجرهٔ لغوِ
  // ۱۰ثانیه‌ای را می‌خواهد؛ کپی‌کردنِ arm() یعنی روزی یکی‌شان اصلاح می‌شود و
  // دیگری نه. فقط فعل و کلیدِ payload فرق می‌کنند.
  var DECIDE_SPECS = {
    proposal: {yes:"proposal.approve", no:"proposal.reject", key:"proposal_id",
               yesFa:"تأیید", noFa:"رد", yesSel:".pyes", noSel:".pno"},
    rfc:      {yes:"rfc.approve",      no:"rfc.deny",       key:"rfc_id",
               yesFa:"پذیرش", noFa:"رد", yesSel:".ryes", noSel:".rno"}
  };

  function wireDecisions(root, kind){
    var sp = DECIDE_SPECS[kind || "proposal"];
    function arm(btn, verb, faVerb, tone){
      btn.addEventListener("click", function(){
        var pid = btn.getAttribute("data-pid");
        var card = btn.closest(".titem");
        if(!card) return;   // FIX: null guard — DOM ممکن است re-render شده باشد
        var slot = card.querySelector(".pend");
        // تپِ دوم روی همان دکمه = لغو. ساده‌ترین حرکتی که انگشت می‌شناسد.
        if(_timers[pid]){ cancel(pid, slot, card); return; }
        var left = DECIDE_DELAY_S;
        card.classList.add("armed");
        slot.hidden = false;
        function paint(){
          slot.innerHTML = '<span class="cd '+tone+'">'+faVerb+' تا '+fa(left)+
            ' ثانیهٔ دیگر</span>'+
            '<button class="undo" type="button">لغو</button>'+
            '<div class="cdnote">تا پایانِ شمارش اپ را نبند — قبل از آن هیچ ثبتی نمی‌شود.</div>';
          slot.querySelector(".undo").addEventListener("click", function(){
            cancel(pid, slot, card);
          });
        }
        paint();
        _timers[pid] = setInterval(function(){
          left -= 1;
          if(left > 0){ paint(); return; }
          clearInterval(_timers[pid]); delete _timers[pid];
          slot.innerHTML = '<span class="cd">در حال ثبت…</span>';
          var payload = {}; payload[sp.key] = pid;
          act(verb, payload, btn).then(function(r){
            if(r && r.ok){ render("approvals"); }
            else { slot.hidden = true; card.classList.remove("armed"); }
          });
        }, 1000);
      });
    }
    function cancel(pid, slot, card){
      clearInterval(_timers[pid]); delete _timers[pid];
      slot.hidden = true; slot.innerHTML = "";
      card.classList.remove("armed");
      toast("لغو شد — هیچ چیزی ثبت نشد", "warn");
    }
    [].forEach.call(root.querySelectorAll(sp.yesSel), function(b){
      arm(b, sp.yes, sp.yesFa, "ok");
    });
    [].forEach.call(root.querySelectorAll(sp.noSel), function(b){
      arm(b, sp.no, sp.noFa, "bad");
    });
  }

  // ── چرخهٔ عمرِ کارت‌ها ─────────────────────────────────────────────────────
  // ⚠️ چرا این‌جا و چرا مهم است: `/api/lifecycle` ساخته و تست‌شده بود و
  // **هیچ مصرف‌کننده‌ای نداشت**. یعنی صفِ تأیید به مالک «۰» نشان می‌داد در
  // حالی که ۲۷ کارت راکد بود و قدیمی‌ترینشان روزها عمر داشت. دقیقاً همان
  // الگوی «قابلیت هست، صداکننده نیست».
  //
  // این نما عمداً فقط **شمارش و مهرِ زمان** می‌دهد: متنِ کارت‌ها مادهٔ
  // اعتبارنامه دارد و تنها مقصدِ تونل همین گیت‌وی است. سنجیده شد روی پاسخِ
  // زنده: از ۱۹۳ رشتهٔ واقعیِ کارت‌ها صفر نشتی.
  var STAGE_ORDER = ["PROPOSED","DELIVERED","DECIDED","EFFECTED","MEASURED",
                     "STALLED","UNKNOWN"];
  var STAGE_LC_FA = {PROPOSED:"پیشنهاد", DELIVERED:"رسیده", DECIDED:"تصمیم‌گرفته",
                     EFFECTED:"اعمال‌شده", MEASURED:"سنجیده", STALLED:"راکد",
                     UNKNOWN:"نامعلوم"};

  function renderLifecycle(el){
    el.innerHTML = "";
    api("/api/lifecycle").then(function(d){
      d = d || {};
      if(d.status === "error"){
        // ۴۰۴ این‌جا یعنی فلگ خاموش است — و آن یک تصمیم است نه خرابی.
        el.innerHTML = '<div class="card">'+secHead("چرخهٔ عمر")+
          '<div class="muted">نمای چرخهٔ عمر خاموش است ('+
          esc(String(d.reason||""))+').</div></div>';
        return;
      }
      function v(x){ return (x && typeof x === "object") ? x.value : x; }
      var stages = v(d.by_stage) || {};
      var total = v(d.total_cards);
      var stalled = Number(stages.STALLED || 0);

      var segs = STAGE_ORDER.filter(function(s){ return stages[s]; })
        .map(function(s){
          return {n:stages[s], name:STAGE_LC_FA[s]||s,
                  tone:(s==="STALLED"?"hot":s==="UNKNOWN"?"unk":
                        s==="EFFECTED"?"ok":"warm")};
        });

      var h = secHead("چرخهٔ عمرِ کارت‌ها",
                      pill(stalled?fa(stalled)+" راکد":"بی‌رکود",
                           stalled?"hot":"ok"));
      h += '<div class="vitals">'+
           (segs.length ? arcs(segs) : "")+
           orbs(segs.map(function(s){ return {name:s.name, short:s.name,
                                              n:s.n, tone:s.tone}; }))+
           '</div>';

      // قدیمی‌ترین راکد: عدد به‌تنهایی معنا ندارد، سن دارد.
      var oldest = v(d.oldest_stalled_ts);
      if(stalled && oldest){
        var days = Math.floor((Date.now()/1000 - Number(oldest)) / 86400);
        h += '<div class="tri '+(days>=3?"hot":"warm")+'"><div class="in">'+
          '<div class="verb">قدیمی‌ترین کارتِ راکد '+fa(days)+' روز مانده</div>'+
          '<div class="why">کارتِ راکد یعنی پیشنهادی که نه رد شد نه اعمال — '+
          'تا تصمیم نگیری همان‌جا می‌ماند.</div></div></div>';
      }

      // ⚠️ ۲۰۲۶-۰۸-۰۵ — تا امروز این نما فقط **عدد** می‌داد. «۲۹ راکد» را
      // می‌دیدی و هیچ‌جا نمی‌شد تصمیم گرفت: تنها سطحِ تصمیم دکمهٔ اینلاینِ
      // تلگرام بود و تحویلِ کارت خاموش است. حالا هر کارت یک ردیفِ قابلِ
      // اقدام است، با همان پنجرهٔ لغوِ ۱۰ثانیه‌ایِ صفِ تأیید.
      // بی‌متن می‌ماند: رکوردِ کارت nonce و token دارد و سرور فقط
      // rfc_id/سن را رد می‌کند.
      var sl = d.stalled_list || [], cut = Number(d.stalled_list_truncated||0);
      if(sl.length){
        h += '<div class="secsub">کارت‌های راکد — تصمیمِ توست</div>';
        h += sl.map(function(c){
          var ag = (c.age_days===null||c.age_days===undefined) ? null : Number(c.age_days);
          var tone = ag===null ? "unk" : (ag>=7 ? "hot" : ag>=3 ? "warm" : "ok");
          return '<div class="titem '+tone+'">'+
            '<div class="tmain">'+
              '<div class="tid">'+ltr(esc(String(c.rfc_id)))+'</div>'+
              '<div class="tage">'+(ag===null ? "سنّ نامعلوم"
                                              : fa(ag)+' روز راکد')+'</div>'+
            '</div>'+
            '<div class="tbtns">'+
              '<button class="ryes" type="button" data-pid="'+esc(String(c.rfc_id))+'">پذیرش</button>'+
              '<button class="rno"  type="button" data-pid="'+esc(String(c.rfc_id))+'">رد</button>'+
            '</div>'+
            '<div class="pend" hidden></div></div>';
        }).join("");
        if(cut>0){
          // سقفِ بی‌صدا از «همه را دیدی» غیرقابل‌تشخیص است.
          h += '<div class="muted">'+fa(cut)+' کارتِ راکدِ دیگر نشان داده نشد '+
               '(سقفِ فهرست).</div>';
        }
        h += '<div class="cdnote">پذیرش یعنی «اعمال کن» — دکترِ روزانه '+
             'برش می‌دارد و اثرش با رسید برمی‌گردد. رد یعنی بسته شود.</div>';
      } else if(stalled){
        // عدد می‌گوید راکد هست ولی فهرست خالی است: تناقض را بلند بگو.
        h += '<div class="tri unk"><div class="in">'+
          '<div class="verb">فهرستِ کارت‌های راکد نیامد</div>'+
          '<div class="why">شمارش '+fa(stalled)+' می‌گوید ولی سرور هویتی نداد — '+
          'تا این حل نشود از این‌جا نمی‌شود تصمیم گرفت.</div></div></div>';
      }

      h += '<details class="det"><summary>عددهایش</summary><div class="inner">'+
        row("کلِ کارت‌ها", total)+
        STAGE_ORDER.map(function(s){
          return stages[s] === undefined ? "" : row(STAGE_LC_FA[s]||s, stages[s]);
        }).join("")+
        // منبع را نشان می‌دهم چون قاعدهٔ این پروژه است: هر عدد باید
        // مسیرِ روی دیسکِ خودش را لو بدهد، وگرنه ادعاست.
        row("منبع", (d.sources||[]).length ? ltr((d.sources||[]).join(" · ")) : "—")+
      '</div></details>';
      el.innerHTML = h;
      // بدونِ این خط، دکمه‌ها رسم می‌شوند و هیچ‌کاری نمی‌کنند — همان
      // «گزینش هست کار نمی‌کند» که مالک گزارش داد.
      wireDecisions(el, "rfc");
    });
  }

  function renderLegs(el){
    el = el || content;
    api("/api/legs").then(function(d){
      d = d || {};
      // ⚠️ ۲۰۲۶-۰۸-۰۹ — همان کلاسِ باگی که panelGuard برایش ساخته شد، این‌جا
      // جا افتاده بود: وقتی business_legs از ORGANISM-STATE گم است، سرور
      // `{status:"unknown", legs:{}}` می‌دهد. بدونِ این گارد، `ks.length===0`
      // و `up===ks.length` (۰===۰) هر دو true می‌شدند و قرص «۰ از ۰» را
      // با تُنِ **live** (سبز) رنگ می‌زد — یعنی «نخواندم» شبیهِ «صفر پا،
      // همه سالم» دیده می‌شد. زندهٔ همین لحظه: ORGANISM-STATE.json واقعاً
      // فاقدِ business_legs است.
      var g = panelGuard("پاها", d); if(g){ el.innerHTML = g; return; }
      var legs = d.legs||{}, ks = Object.keys(legs);
      var up = ks.filter(function(k){ return legs[k].live===true; }).length;
      var down = ks.filter(function(k){ return legs[k].live===false; });
      // رأیِ مالک: صفحهٔ سیستم خودش یک **اختاپوسِ کامل** شود. تشخیصِ مکانی —
      // هر پا همیشه در همان موضعِ ساعت است، پس با تکرار جایش را حفظ می‌کنی
      // و دیگر لازم نیست اسم بخوانی.
      el.innerHTML = '<div class="card">'+
        secHead("پاها", pill(fa(up)+" از "+fa(ks.length), up===ks.length?"live":(down.length?"blocked":"staged")))+
        '<div class="sysdial">'+dialSVG(legs, window.__octoHalted, up, ks.length||1, true)+'</div>'+
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

  function renderMoneyCaps(el){
    el = el || content;
    api("/api/money-caps").then(function(d){
      if(!d || d.status==="error"){
        el.innerHTML = '<div class="card"><h2>سقف خرج</h2><div class="warn">خوانده نشد: '+
          esc((d&&d.reason)||"?")+'</div></div>';
        return;
      }
      var w = d.window||{};
      var fl = d.flags_armed||{};
      var claimed = d.claimed;
      var html = '<div class="card">'+secHead("سقف خرج + هدف ماه",
          pill(w.active?"پنجرهٔ آزمون فعال":"سقف پایه", w.active?"warm":"ok"))+
        '<div class="muted">claimed ≠ درآمد · SoT: MONEY-CLAIM-VS-CONFIRM</div>'+
        '<div class="kv">'+
        row("claimed", claimed==null?"۰ / نامعلوم":claimed)+
        row("claimed_is_income", d.claimed_is_income===true?"بله":"خیر")+
        row("ماهانهٔ پایه", "AU$"+fa(d.monthly_default_aud||30))+
        row("روزانه", "AU$"+fa(d.daily_aud||2))+
        row("پنجره USD", (w.usd||"—")+" تا "+(w.until||"—"))+
        row("روز مانده", w.days_left==null?"—":fa(w.days_left))+
        row("VALUE_LEDGER", fl.VALUE_LEDGER)+
        row("MONEY_FSM", fl.MONEY_FSM)+
        row("UNCAPPED", fl.UNCAPPED)+
        row("LIVE-ENABLED", fl.LIVE_ENABLED?"بله":"نه")+
        row("armed≠productive", d.armed_ne_productive?"بله — فلگ روشن ≠ claim":"—")+
        row("بلاکر", d.blocker||"—")+
        '</div></div>';
      el.innerHTML = html;
    });
  }

  function renderRegistry(el){
    el = el || content;
    api("/api/ui-registry").then(function(d){
      var g = panelGuard("UI Registry", d); if(g){ el.innerHTML = g; return; }
      var items = Array.isArray(d.items) ? d.items : [];
      // ⚠️ این جدول از `ui-registry.json` می‌آید — فایلی **دست‌نویس**، نه
      // اسکنِ واقعیِ رابط. پس «status» ِ هر ردیف ادعای نویسندهٔ فایل است نه
      // سنجهٔ زنده. تا وقتی مولدِ واقعی ندارد، همین را صریح می‌گوییم.
      var stale = '<div class="cdnote">این فهرست از یک فایلِ دست‌نویس '+
        'خوانده می‌شود، نه از اسکنِ زندهٔ رابط — وضعیتِ هر ردیف ادعاست، '+
        'نه سنجه.</div>';
      var rows = items.map(function(it){
        return "<tr><td>"+esc(it.id)+"</td><td>"+esc(it.type)+'</td><td><span class="badge '+esc(it.status)+'">'+esc(it.status)+"</span></td><td>"+esc(it.command||it.path||it.endpoint||"—")+"</td></tr>";
      }).join("");
      el.innerHTML = card2("UI Registry", pill(fa(items.length)+" ردیف", "unk"),
        '<div class="tblwrap"><table><tr><th>id</th><th>type</th><th>status</th>'+
        '<th>cmd/path</th></tr>'+rows+'</table></div>'+stale);
    });
  }

  function renderTruth(el){
    el = el || content;
    api("/api/current-truth").then(function(d){
      // 2026-08-12 fix: قبلاً هیچ نشانهٔ کهنگی نبود — فایلی به نامِ «حقیقتِ
      // جاری» می‌توانست روزها بدونِ تغییر بماند و همیشه یکسان نشان داده شود.
      var ageNote = (d.age_s!=null) ? ' <span class="muted">(سن: '+Math.round(d.age_s/60)+'دقیقه)</span>' : '';
      el.innerHTML = '<div class="card"><h2>Current Truth'+pfStale(d)+'</h2>'+
        (d.preview?'<pre>'+esc(d.preview)+'</pre>':'<div class="muted">'+esc(d.status)+(d.reason?": "+esc(d.reason):"")+'</div>')+
        '<div class="muted" style="margin-top:8px">read-only — '+esc(d.path||"")+ageNote+'</div></div>';
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
    var myseq = _renderSeq;
    Promise.all([api("/api/pf/status"), api("/api/pf/gates"), api("/api/pf/queue"),
                 api("/api/pf/kpi"), api("/api/pf/guards"), api("/api/pf/capabilities")])
    .then(function(all){
      if(_renderSeq !== myseq) return;
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
          (grows?'<div class="tblwrap"><table><tr><th>gate</th><th>status</th><th>eval</th></tr>'+grows+'</table></div>':'')
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
        '<div class="tblwrap"><table><tr><th>صف</th><th>وضعیت‌ها</th><th>کل</th></tr>'+
        qRow("پست (acquisition)", q.acquisition)+
        qRow("DM", q.dm)+
        qRow("درفت پارتنر", q.studio_drafts)+
        '</table></div>'+
        '<div class="muted" style="margin-top:8px">متنِ درفت عمداً از مرزِ پوشهٔ پروژه عبور نمی‌کند (قاعدهٔ #۷). تأیید/رد از تلگرام: <code>/pf_ok</code> · <code>/dm_ok</code></div></div>';

      // کارت ۴ — KPI با چراغ
      if(kpi.status==="ok"){
        var m = kpi.metrics||{}, L = kpi.lights||{};
        var krows = Object.keys(m).map(function(k){
          return "<tr><td>"+esc(k)+"</td><td>"+fa(m[k])+"</td><td>"+pfLight(L[k])+"</td><td>"+esc((L[k]&&L[k].action)||"—")+"</td></tr>";
        }).join("");
        html += '<div class="card"><h2>KPI هفتگی'+pfStale(kpi.freshness)+' <span class="badge">هفتهٔ '+esc(kpi.week_start)+'</span></h2>'+
          '<div class="tblwrap"><table><tr><th>سنجه</th><th>مقدار</th><th>چراغ</th><th>اقدامِ قرمز</th></tr>'+krows+'</table></div>'+
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
        (crows?'<div class="tblwrap"><table><tr><th>کانال</th><th>اخطار</th><th>وضعیت</th></tr>'+crows+'</table></div>':'<div class="muted">'+esc(cl.reason||cl.status||"—")+'</div>')+
        '</div>';

      // کارت ۶ — قابلیت‌ها (هرگز دکمهٔ مرده)
      var caps = (cap.capabilities||[]).map(function(c){
        return "<tr><td>"+esc(c.name)+'</td><td><span class="badge '+(c.level==="green"?"live":(c.level==="red"?"blocked":"staged"))+'">'+esc(c.level)+"</span></td><td>"+(c.executable?"فعال":"🔒 قفل")+"</td><td>"+esc(c.reason)+"</td></tr>";
      }).join("");
      html += '<div class="card"><h2>قابلیت‌ها <span class="badge '+(cap.outward_allowed?"live":"blocked")+'">'+(cap.outward_allowed?"outward باز":"outward قفل")+'</span></h2>'+
        (caps?'<div class="tblwrap"><table><tr><th>قابلیت</th><th>سطح</th><th>اجرا</th><th>چرا</th></tr>'+caps+'</table></div>':'<div class="muted">—</div>')+
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

  // ⚠️ ۲۰۲۶-۰۸-۰۵ — کلاسِ باگی که کلِ تبِ سیستم را بی‌اعتبار می‌کرد:
  // `api()` روی هر شکست `{status:"error"}` برمی‌گرداند، ولی چهار پنل از هشت
  // مستقیم می‌رفتند سراغِ `d.missing||[]` یا `d.dead||[]`. یعنی یک ۵۰۰ به
  // آرایهٔ خالی و آرایهٔ خالی به **قرصِ سبز** ترجمه می‌شد. زندهٔ همین امروز:
  // `/api/obsidian` ‏NameError می‌داد و پنل می‌نوشت «کامل — همهٔ سندهای
  // مرجع سرِ جایشان‌اند».
  //
  // یک گاردِ واحد به‌جای هشت وصلهٔ موردی: قاعده را می‌بندد، نه شکاف را.
  // خروجی رشته = پنل نباید ادامه بدهد.
  function panelGuard(title, d){
    d = d || {};
    var s = String(d.status||"");
    if(s === "error" || s === "unknown_schema"){
      return card2(title, pill("خوانده نشد", "hot"),
        '<div class="tri hot"><div class="in">'+
        '<div class="verb">این بخش خوانده نشد</div>'+
        '<div class="why">'+ltr(esc(String(d.reason||s)))+' — تا این حل نشود '+
        'هیچ عددی این‌جا قابلِ اعتماد نیست، پس هیچ‌کدام را نشان نمی‌دهم.'+
        '</div></div></div>');
    }
    if(s === "unknown"){
      // «نمی‌دانم» رنگِ خودش را دارد — نه سبز، نه قرمز.
      return card2(title, pill("نامعلوم", "unk"),
        '<div class="muted">'+esc(String(d.reason||"منبع خوانده نشد"))+'</div>');
    }
    if(s === "disabled" || s === "not_found"){
      return card2(title, pill("خاموش", "unk"),
        '<div class="muted">'+esc(String(d.reason||"این نما فعال نیست"))+
        ' — یک تصمیم است، نه خرابی.</div>');
    }
    return null;
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
      var g = panelGuard("مغز", d); if(g){ el.innerHTML = g; return; }
      var b = d.brain||{}, dm = b.daemon||{}, cx = b.cortex||{};
      var stress = cx.stress||{};
      el.innerHTML = card2("مغز", pill(b.available?"در دسترس":"در دسترس نیست", b.available?"live":"blocked"),
        (b.reason?'<div class="muted">'+esc(b.reason)+'</div>':'')+
        '<div class="muted" style="margin-top:6px">cortex (زنده، ۸۷۷۲)</div>'+
        rows(cx, ["reachable","cycle","coherence","ts"])+
        (stress.level?'<div class="muted">'+esc(stress.level)+' · in_fear: '+esc((stress.in_fear||[]).join("، ")||"—")+'</div>':'')+
        (cx.thought?'<div class="muted" style="margin-top:4px">'+esc(String(cx.thought).slice(0,180))+'</div>':'')+
        '<div class="muted" style="margin-top:10px">۴D (تثبیتِ جداگانه)</div>'+
        rows(dm, ["reachable","source","ticks","errors","last_tick","generation"]));
    });
  }
  function renderGovernor(el){
    el = el || content;
    api("/api/governor").then(function(d){
      var g = panelGuard("ناظر", d); if(g){ el.innerHTML = g; return; }
      var ds = d.drift_status||{}, st = ds.status;
      // ⚠️ واژگانِ نویسنده و خواننده نمی‌خواندند: `_governor_drift` فقط
      // `unknown` / `drift` / **`aligned`** می‌دهد و هرگز `"ok"`. پس قرص
      // ساختاراً نمی‌توانست سبز شود — حالتِ سالم اصلاً قابلِ نمایش نبود.
      // (`ok` هم پذیرفته می‌ماند تا اگر روزی نویسنده عوض شد، این نشکند.)
      var clean = (st==="aligned" || st==="ok");
      el.innerHTML = card2("ناظر", pill(st||"نامعلوم", clean?"live":(st?"staged":"unknown")),
        rows(d, ["policy_doc","canonical_provider","canonical_choke_point"])+
        row("مسیرهای اعلام‌شده", (ds.declared_paths||[]).length));
    });
  }
  function renderObsidian(el){
    el = el || content;
    api("/api/obsidian").then(function(d){
      // ⚠️ زندهٔ ۰۸-۰۵: این مسیر NameError می‌داد و همین پنل «کامل» رنگ
      // می‌زد، چون `d.missing||[]` یک ۵۰۰ را به آرایهٔ خالی و آرایهٔ خالی را
      // به اطمینانِ سبز ترجمه می‌کرد.
      var g = panelGuard("ابسیدین", d); if(g){ el.innerHTML = g; return; }
      // نبودِ کلید ≠ صفرِ گمشده. اگر سرور `missing` نداد، «نمی‌دانم».
      if(!Array.isArray(d.missing)){
        el.innerHTML = card2("ابسیدین", pill("نامعلوم","unk"),
          '<div class="muted">پاسخ فهرستِ گمشده‌ها را نداشت.</div>');
        return;
      }
      var miss = d.missing;
      el.innerHTML = card2("ابسیدین", pill(miss.length?miss.length+" گمشده":"کامل", miss.length?"staged":"live"),
        (miss.length?'<div class="list">'+miss.map(function(m){
            return '<div class="li">'+ltr(m)+'</div>'; }).join("")+'</div>'
                    :'<div class="muted">همهٔ سندهای مرجع سرِ جایشان‌اند</div>')+
        row("checked", d.checked));
    });
  }
  // ⚠️ ۲۰۲۶-۰۸-۰۹ — `renderNext` («قدمِ بعدی») این‌جا بود و صداکنندهٔ صفر
  // داشت: همان دادهٔ task_status امروز در تبِ کارها (`renderTasks`) با
  // جزئیاتِ بیشتر نشان داده می‌شود. بازماندهٔ همان ادغامِ ۰۸-۰۴ که Truth/
  // Registry/Legs را هم به پنلِ زیرِ تبِ سیستم برد. حذف شد.

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
  /* واژگانِ رسمیِ رنگِ حالت. ۲۰۲۶-۰۸-۰۴.
   *
   * چرا اعلامِ صریح به‌جای «هر رشته‌ای که برسد»: ممیزی نشان داد نیمی از
   * tone هایی که این فایل می‌فرستاد **هیچ قاعده‌ای در CSS نداشتند**، یعنی
   * یک حلقهٔ خطر دقیقاً مثلِ حالتِ سالم رندر می‌شد. بدترین شکلِ شکست: هشدار
   * به رنگِ آرامش.
   *
   * و اولین گاردی که برایش نوشتم **کور بود** — با regex دنبالِ رشتهٔ ساده
   * می‌گشت و صداکننده‌هایی را که tone را با ternary می‌دهند نمی‌دید. پس
   * به‌جای دقیق‌ترکردنِ جارو، قاعده بسته شد: فهرست این‌جاست، و هر چیزِ
   * خارج از آن در **زمانِ اجرا** به `unk` می‌افتد — یعنی «نمی‌دانم»، نه
   * سبزِ آرام‌بخش. اشتباهِ آینده هم دیده می‌شود هم بی‌خطر است.
   */
  var TONES = ["ok","up","done","live","cyan","warm","amber","warn","staged",
               "hot","bad","error","unk"];
  function toneOf(t){ return TONES.indexOf(String(t)) >= 0 ? String(t) : "unk"; }

  function ring(val, max, label, t, size){
    size = size || 118;
    var r = 44, C = 2*Math.PI*r;
    var f = max ? Math.max(0, Math.min(1, val/max)) : 0;
    return '<div class="ringwrap" style="width:'+size+'px">'+
      '<svg class="ring '+toneOf(t)+'" viewBox="0 0 110 110">'+
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
    // ⚠️ `short` از `esc()` رد می‌شود، پس **باید متنِ ساده باشد**. چند صداکننده
    // خروجیِ `ltr()` را این‌جا می‌دادند و چون ltr خودش `<span dir=ltr>` می‌سازد،
    // esc آن را escape می‌کرد و کاربر رشتهٔ `<span dir="ltr">…` را به‌صورتِ
    // متنِ خام روی صفحه می‌دید. راهِ درست: متنِ خام بده و بگذار خودِ orbs
    // ایزولهٔ bidi را بزند — یک جا، نه در هر صداکننده.
    return '<div class="orbs">'+items.map(function(it){
      var s = String(it.short==null ? (it.name==null?"":it.name) : it.short);
      var body = /[؀-ۿ]/.test(s)
        ? esc(s)                                        // فارسی: همان‌طور
        : '<span dir="ltr" class="iso">'+esc(s)+'</span>';  // لاتین/عدد: ایزوله
      return '<div class="orb '+toneOf(it.tone)+'" title="'+esc(it.name)+'">'+
        '<span class="od"></span><span class="on">'+body+'</span>'+
        (it.n!==undefined?'<span class="ov">'+fa(it.n)+'</span>':'')+'</div>';
    }).join("")+'</div>';
  }

  // کمانِ بخش‌بندی‌شده — برای توزیع (حالت‌های ارسال، مراحل)
  function arcs(segs){
    // ⚠️ قبلاً `|| 1` روی خودِ tot بود و همان tot هم وسطِ حلقه چاپ می‌شد،
    // پس وقتی هیچ رویدادی نبود، عددِ **۱** نمایش داده می‌شد — یک رقمِ
    // ساخته‌شده که از هیچ داده‌ای نمی‌آمد. گاردِ تقسیم‌بر‌صفر باید فقط
    // مخرج را نجات دهد، نه برچسب را عوض کند.
    var real = segs.reduce(function(a,b){return a+(b.n||0);},0);
    var tot = real || 1;
    var r=44, C=2*Math.PI*r, off=0, out="";
    segs.forEach(function(sg){
      var f=(sg.n||0)/tot;
      out += '<circle class="ap '+toneOf(sg.tone)+'" cx="55" cy="55" r="'+r+'" fill="none"'+
        ' stroke-width="11" stroke-dasharray="'+(C*f-1.5).toFixed(1)+' '+(C*(1-f)+1.5).toFixed(1)+'"'+
        ' stroke-dashoffset="'+(-C*off).toFixed(1)+'" transform="rotate(-90 55 55)"/>';
      off += f;
    });
    return '<div class="ringwrap" style="width:126px"><svg class="ring" viewBox="0 0 110 110">'+
      '<circle class="rt" cx="55" cy="55" r="'+r+'" fill="none" stroke-width="11"/>'+out+
      '<circle class="rc" cx="55" cy="55" r="28"/></svg>'+
      '<div class="ringnum">'+fa(real)+'</div></div>';
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
  function dialSVG(legs, halted, flagsOn, flagsAll){
    // ⚠️ بازنویسیِ هندسه — ۲۰۲۶-۰۸-۰۵، دو ایرادِ هم‌زمان:
    //
    // ۱. مالک: «پاها را به هم نچسبان». علتش `curl` ِ یکی‌درمیانِ خلافِ جهت
    //    بود (`(i%2 ? 1 : -1)`): دو بازوی مجاور به سمتِ هم می‌پیچیدند و
    //    نوکشان روی هم می‌افتاد. حالا همه یک جهت می‌پیچند — مثلِ چرخشِ
    //    خودِ لوگو — پس هیچ دو بازویی به هم نمی‌رسند.
    // ۲. ممیزی: همیشه **هشت** بازو کشیده می‌شد صرف‌نظر از شمارِ پاها، پس
    //    برای هفت پا یک بازوی **خیالی** می‌ماند که از بازوی «وضع نامعلوم»
    //    قابلِ تفکیک نبود. حالا دقیقاً به تعدادِ پاهای واقعی بازو هست و
    //    زاویه‌ها روی ۳۶۰ تقسیم می‌شوند.
    //
    // و برای زیبایی: طولِ بازوها یکی‌درمیان کمی فرق می‌کند، پس نوک‌ها روی
    // یک دایرهٔ کسل‌کننده ننشینند.
    var allNames = Object.keys(legs || {});
    var names = allNames.slice(0, 8);
    var n = names.length || 8;
    var overflow = Math.max(0, allNames.length - names.length);
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
    for(var i=0;i<n;i++){
      // زاویه‌ها روی شمارِ **واقعیِ** پاها پخش می‌شوند، نه هشت‌تای ثابت.
      var a0 = (-90 + i * 360 / n) * Math.PI / 180;
      // همه یک جهت ⇒ چرخشِ هماهنگ، و هیچ دو بازویی به هم نمی‌رسد.
      // دامنه هم از ۱.۱۵ به ۰.۸۲ کم شد تا نوک‌ها بازتر بمانند.
      var curl = 0.82;
      // طولِ یکی‌درمیانِ کمی متفاوت ⇒ نوک‌ها روی یک دایره ننشینند
      var reach = (i % 2 ? 50 : 43), w0 = 9.5;
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
      // پای نهم به بعد بازو ندارد (قرص هشت‌تایی است). بی‌صدا ناپدید نشود —
      // یک عددِ کوچک می‌گوید چند پا در تصویر نیست.
      (overflow ? '<text class="ovf" x="'+cx+'" y="'+(R*2-4)+'" text-anchor="middle">+'+
                  overflow+'</text>' : '')+
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
    var myseq = _renderSeq;   // stale-fetch guard
    Promise.all([api("/api/state"), api("/api/approvals"), api("/api/ops/tasks"),
                 api("/api/governor"), api("/api/obsidian"), api("/api/legs")])
      .then(function(a){
        if(_renderSeq !== myseq) return;   // کاربر تب را عوض کرده — stale، ننویس
        var st=a[0]||{}, ap=a[1]||{}, tk=a[2]||{}, gv=a[3]||{}, ob=a[4]||{}, lg=a[5]||{};
        if(st.status==="error"){ el.innerHTML='<div class="err">خطا: '+esc(st.reason)+'</div>'; return; }
        // ⚠️ `unknown` جدا از `error` است و تا امروز اصلاً گرفته نمی‌شد.
        // وقتی ORGANISM-STATE خوانده نشود، خواننده {status:"unknown"} می‌دهد
        // و `st.halted` تعریف‌نشده است ⇒ falsy ⇒ چشم می‌درخشید و صفحه
        // می‌نوشت «ارگانیسم زنده است». یعنی قاطع‌ترین جملهٔ اپ از **نبودِ
        // داده** ساخته می‌شد. حالا «نمی‌دانم» می‌گوید و همان‌جا می‌ایستد.
        if(st.status==="unknown"){
          setHalted(null);
          window.__octoHalted = null;
          setCore("حالِ ارگانیسم نامعلوم است", esc(st.reason||"وضعیت خوانده نشد"));
          el.innerHTML = '<div class="tri hot"><div class="in">'+
            '<div class="verb">وضعیتِ ارگانیسم خوانده نشد</div>'+
            '<div class="why">'+esc(st.reason||"")+' — تا وقتی این خوانده نشود، '+
            'هیچ عددی روی این صفحه قابلِ اعتماد نیست، پس هیچ‌کدام را نشان نمی‌دهم.'+
            '</div></div></div>';
          return;
        }
        setHalted(st.halted);
        // ⚠️ قرصِ تبِ سیستم halted را **جعلاً false** می‌گرفت، یعنی وقتی
        // ارگانیسم متوقف بود باز هم زنده رندر می‌شد. حالت را یک‌جا نگه
        // می‌دارم تا هر دو قرص یک حقیقت بگویند.
        window.__octoHalted = !!st.halted;
        setCore(st.halted?"ارگانیسم متوقف است":"ارگانیسم زنده است",
                (devMode?"حالتِ dev · ":"")+"ضربان "+fa(st.beat)+" · "+esc(st.epoch_mode||""));

        var need=[], calm=[];
        function push(sev,verb,why,act){ need.push({sev:sev,verb:verb,why:why,act:act}); }

        // قدم ۴۱/۴۴: نقشهٔ مغز صادق روی Home
        calm.push("مغزهای زنده: cortex + business_brain (file-bridge)");
        calm.push("4d/Super-Gov: SPEC_NOT_BUILT — promote نکن");
        calm.push("لایه‌ها = سؤال مهندسی · OCTOPUS-HONESTY");

        if(st.halted) push("hot","ارگانیسم متوقف است","تا برداشتنِ ترمز هیچ کاری جلو نمی‌رود.",null);
        // ⚠️ تیکِ «✓ صفِ تأیید خالی است» فقط وقتی مجاز است که خواننده
        // واقعاً `ok` گفته باشد. وگرنه از نخواندن، اطمینان می‌سازیم.
        var apc = Number(ap.count||0);
        if(ap.status !== "ok"){
          push("warm","صفِ تأیید خوانده نشد",
               "وضع: "+ltr(String(ap.status||"?"))+" — ممکن است چیزی منتظرت باشد و دیده نشود.",
               {tab:"approvals",label:"دیدنِ صف"});
        } else if(apc>0) push("hot", fa(apc)+" تأیید منتظرِ توست",
                       "تا تصمیم نگیری، این‌ها همان‌جا می‌مانند.", {tab:"approvals",label:"برو به تأییدها"});
        else calm.push("صفِ تأیید خالی است");

        var tstat = tk.task_status||{};
        var tks = Number(tk.tasks_total||0) - Number(tstat.done||0);
        // UI-02: calm فقط وقتی status===ok — وگرنه از نخواندن، «سالم» جعل نکن
        if(tk.status !== "ok"){
          push("warm","کارها خوانده نشد",
               "وضع: "+ltr(String(tk.status||"?"))+" — ممکن است کارِ باز دیده نشود.",
               {tab:"tasks",label:"دیدنِ کارها"});
        } else if(tks>0) push("warm", fa(tks)+" کارِ باز", "منتظرِ توست.", {tab:"tasks",label:"دیدنِ کارها"});
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
        // UI-01: drift_status = aligned|drift|unknown — هرگز "ok".
        // aligned را warm نکن (جای دیگر در app.js همین منطق درست شده بود).
        if(dr === "drift") push("warm","ناظر انحراف می‌بیند",
          "سندِ سیاست با کد نمی‌خواند: "+ltr(String(dr)), {tab:"system",label:"دیدنِ ناظر"});
        else if(dr === "aligned" || dr === "ok") calm.push("ناظر بی‌انحراف");
        else if(dr) calm.push("ناظر: "+ltr(String(dr)));

        var miss=(ob.missing||[]).length;
        // UI-02: سند مرجع calm فقط اگر obsidian status===ok
        if(ob.status !== "ok"){
          push("warm","ابسیدین خوانده نشد",
            "وضع: "+ltr(String(ob.status||"?"))+" — نبودِ داده را «کامل» نمی‌خوانیم.",
            {tab:"system",label:"دیدنِ ابسیدین"});
        } else if(miss>0) push("warm", fa(miss)+" سندِ مرجع گم است",
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
          // ⚠️ XSS (فیکس‌شده): اینجا برعکسِ toast() بود — رشتهٔ فارسی escape
          // می‌شد، رشتهٔ غیرِفارسی خام می‌رفت. calm همیشه از رشته‌هایِ لفظیِ
          // ثابت پر می‌شود (بالاتر در همین تابع، calm.push("...")) پس امروز
          // خطرِ زنده‌ای نبود، ولی همیشه escape کردن هزینه‌ای ندارد و اگر
          // یک روز محتوایِ پویا اینجا اضافه شود، از قبل امن است.
          html += '<details class="quiet"><summary>'+fa(calm.length)+' چیزِ دیگر سالم است</summary>'+
                  '<div class="inner">'+calm.map(function(c){
                    return '<div class="row"><span class="k">✓</span><span class="v">'+
                      esc(c)+'</span></div>'; }).join("")+
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
  // ── آینه: اختاپوس دربارهٔ خودش چه می‌داند ────────────────────────────────
  // مالک (۰۸-۰۵): «مهم‌ها را بیاور داخلِ وب‌اپ، تعاملِ اصلی‌ام وب‌اپ است».
  // این اعداد تا امروز فقط با تایپِ دستیِ سه اسکریپت دیده می‌شدند.
  //
  // ⚠️ قیدِ باربر: **غیاب ≠ «نپرید»**. دفترِ خالیِ یک پروسه دو معنی دارد —
  // یا کدش اجرا نشد، یا پروب آن‌جا نصب نبود. اگر دومی را «یتیم» نشان دهم،
  // همان صفرِ جعلی است با لباسِ تازه. پس تا وقتی پروسهٔ پروب‌دار نداریم،
  // این بخش صریحاً می‌گوید «نمی‌دانم» و هیچ عددی از دسترسی نشان نمی‌دهد.
  function renderSelfmap(el){
    el.innerHTML = "";
    api("/api/selfmap").then(function(d){
      d = d || {};
      if(d.status === "error"){
        el.innerHTML = '<div class="err">نقشهٔ خودآگاهی خوانده نشد: '+
                       esc(String(d.reason||""))+'</div>';
        return;
      }
      var r = d.reach || {}, sc = d.scans || {};
      var procs = r.probed_processes || {};
      var nProc = Object.keys(procs).length;

      var h = secHead("آینه", pill(nProc ? fa(nProc)+" پروسهٔ پروب‌دار" : "پروبی نیست",
                                   nProc ? "ok" : "unk"));

      // ── دسترسیِ زمانِ اجرا ──────────────────────────────────────────
      if(!nProc){
        h += '<div class="tri warm"><div class="in">'+
          '<div class="verb">هنوز نمی‌دانم چه کدی واقعاً می‌دود</div>'+
          '<div class="why">پروبِ دسترسی در هیچ پروسه‌ای ثبت نشده. '+
          'تا وقتی پروسه‌ای ری‌استارت نشود، دفتر خالی است — و <b>خالی‌بودنِ '+
          'دفتر یعنی «نمی‌دانم»، نه «هیچ کدی نمی‌دود»</b>.</div></div></div>';
      } else {
        var files = r.files || {};
        var top = Object.keys(files).sort(function(a,b){ return files[b]-files[a]; });
        h += '<div class="vitals">'+
          orbs([{name:"توابعِ دیده‌شده", short:"دیده‌شده",
                 n:r.functions_seen, tone:(r.functions_seen?"ok":"unk")}].concat(
            Object.keys(procs).slice(0,4).map(function(p){
              return {name:p, short:ltrSafe(p), n:procs[p].probes, tone:"up"};
            })))+'</div>';
        if(top.length){
          h += '<details class="det"><summary>پرکارترین فایل‌ها</summary>'+
            '<div class="inner">'+top.slice(0,12).map(function(f){
              return row(f, files[f]);
            }).join("")+'</div></details>';
        }
      }

      // ── اسکن‌های ایستا، با سنِ صریح ─────────────────────────────────
      var LBL = {orphans:"ماژولِ یتیم", weighty:"یتیمِ سنگین",
                 dark_gates:"دروازهٔ تاریک", partial_gates:"دروازهٔ نیمه‌روشن",
                 flags_seen:"کلِ فلگ", flags_live_on:"فلگِ زندهٔ روشن",
                 read_undefined:"فلگِ خوانده‌ولی‌تعریف‌نشده",
                 orphan_state:"فایلِ حالتِ یتیم", untested:"ماژولِ بی‌تست",
                 dead_symbols:"نمادِ مرده", unfinished:"کارِ ناتمام",
                 checks_failed:"چکِ شکست‌خورده", modules_checked:"ماژولِ بررسی‌شده"};
      var any = false;
      ["dark","orphan","self"].forEach(function(k){
        var s = sc[k];
        if(!s || !s.values) return;
        any = true;
        var age = s.age_s;
        // سنِ صریح: عددِ کهنه نباید شبیهِ تازه دیده شود.
        var aged = (age === null || age === undefined) ? "نامعلوم"
                 : (age < 3600 ? fa(Math.round(age/60))+" دقیقه پیش"
                               : fa(Math.round(age/3600))+" ساعت پیش");
        h += '<details class="det"><summary>'+esc({dark:"دروازه‌های تاریک",
              orphan:"یتیم‌ها", self:"خودشناسی"}[k])+' · '+esc(aged)+'</summary>'+
          '<div class="inner">'+Object.keys(s.values).map(function(kk){
            return row(LBL[kk] || kk, s.values[kk]);
          }).join("")+'</div></details>';
      });
      if(!any){
        h += '<div class="err">اسکن‌های ایستا هنوز نتیجه‌ای ندارند — '+
             'مغزِ کاکپیت باید یک بار بدود. عمداً صفر نشان نمی‌دهم.</div>';
      }

      // ── حافظهٔ بلندمدت ────────────────────────────────────────────────
      // ⚠️ ۲۰۲۶-۰۸-۰۵ — تا امشب هیچ سطحی این را نشان نمی‌داد؛ عکسِ درستِ
      // «نه دیتا ذخیره می‌کند» است — ذخیره می‌کند، فقط نامرئی بود.
      var m = d.memory;
      if(m && m.status !== "unknown" && typeof m.total === "number"){
        h += '<details class="det" open><summary>حافظهٔ بلندمدت · '+
             fa(m.total)+' رکورد</summary><div class="inner">'+
          row("فعال", m.active)+row("درانتظارِ تأیید", m.pending)+
          row("پس‌گرفته‌شده", m.retracted)+
          Object.keys(m.by_namespace||{}).map(function(ns){
            return row("فضایِ "+ltr(ns), m.by_namespace[ns]);
          }).join("")+
        '</div></details>';
      } else {
        h += '<div class="tri unk"><div class="in">'+
          '<div class="verb">حافظهٔ بلندمدت خوانده نشد</div>'+
          '<div class="why">'+esc(String((m||{}).reason||""))+'</div></div></div>';
      }
      el.innerHTML = h;
    });
  }
  // نامِ پروسه لاتین است و داخلِ متنِ راست‌به‌چپ می‌پرد
  function ltrSafe(s){ return String(s); }

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
                     short: gl===null||gl===undefined ? "نامعلوم" : Number(gl).toFixed(2)+" ساعت",
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

  // ── ثبتِ رویدادِ ارزش ──────────────────────────────────────────────────────
  // ⚠️ `record_value` در موتور **هیچ اعتبارسنجی‌ای ندارد**: هر leg/event/
  // value_type را می‌پذیرد و پیش‌فرضِ ops_studio/manual_value_event/production
  // می‌گذارد. یعنی یک ورودیِ متنیِ آزاد، دفترِ ارزش را با تایپو آلوده می‌کند و
  // بعد گروه‌بندیِ `value_events_per_leg` بی‌معنا می‌شود. پس UI واژگانِ **بسته**
  // می‌دهد. اعتبارسنجیِ سمتِ سرور کارِ این لِین نیست، ولی این‌جا ثبت می‌شود
  // که چرا چیپ است نه input.
  var VALUE_TYPES = [["production","تولید"],["learning","یادگیری"],
                     ["maintenance","نگهداری"],["risk_reduction","کاهشِ ریسک"]];
  //: نامِ پاها از /api/legs می‌آید — این‌جا هاردکد نمی‌شود، چون مالک گفت
  //: چهار پای بیزنسی بعداً ماژولار عوض می‌شوند.
  function renderValueEntry(el){
    el.innerHTML = "";
    api("/api/legs").then(function(d){
      var legs = Object.keys((d && d.legs) || {});
      if(!legs.length){
        el.innerHTML = '<div class="err">فهرستِ پاها خوانده نشد — بدونِ آن '+
          'رویدادِ ارزش به پای نامعلوم می‌خورد، پس فرم را باز نمی‌کنم.</div>';
        return;
      }
      el.innerHTML = secHead("ثبتِ ارزش")+
        '<details class="det"><summary>رویدادِ تازه</summary><div class="inner">'+
        '<input class="fin" id="veName" type="text" placeholder="چه اتفاقی افتاد؟" maxlength="120">'+
        '<div class="chips" id="veLeg">'+legs.map(function(l,i){
          return '<button class="chip'+(i===0?" on":"")+'" data-v="'+esc(l)+'">'+
                 '<span dir="ltr" class="iso">'+esc(l)+'</span></button>';
        }).join("")+'</div>'+
        '<div class="chips" id="veType">'+VALUE_TYPES.map(function(t,i){
          return '<button class="chip'+(i===0?" on":"")+'" data-v="'+t[0]+'">'+esc(t[1])+'</button>';
        }).join("")+'</div>'+
        '<div class="chips" id="veOut">'+[1,2,3,5,8].map(function(n,i){
          return '<button class="chip'+(i===2?" on":"")+'" data-v="'+n+'">'+
                 'ارزش '+fa(n)+'</button>';
        }).join("")+'</div>'+
        '<button class="go" id="veGo">ثبت کن</button>'+
      '</div></details>';
      [].forEach.call(el.querySelectorAll(".chips"), function(g){
        g.addEventListener("click", function(e){
          var c = e.target.closest(".chip"); if(!c) return;
          [].forEach.call(g.children, function(x){ x.classList.remove("on"); });
          c.classList.add("on");
          hapticSelect();
        });
      });
      var go = el.querySelector("#veGo");
      if(go) go.addEventListener("click", function(){
        var name = (el.querySelector("#veName")||{}).value || "";
        if(!name.trim()){ toast("توضیحِ رویداد خالی است", "bad"); return; }
        function pick(id){ var c = el.querySelector(id+" .chip.on");
                           return c ? c.getAttribute("data-v") : null; }
        act("value.record_event", {
          leg: pick("#veLeg"), event: name.trim(),
          value_type: pick("#veType"),
          output_score: Number(pick("#veOut") || 3)
        }, go).then(function(r){
          if(r && r.ok){ el.querySelector("#veName").value = ""; render("money"); }
        });
      });
    });
  }

  // ── اقدام‌های لید ─────────────────────────────────────────────────────────
  // جانشینِ `renderStudio` که کاملاً انگلیسی بود، دو کلاسِ ناموجود
  // (`.formgrid`/`.kv`) داشت، JSON ِ خام چاپ می‌کرد و `platform:"onlyfans"` را
  // هاردکد کرده بود — یعنی یکی از همان چهار پایی که مالک گفت دیفالت بماند.
  // این‌جا هیچ پای بیزنسی پیش‌فرض نمی‌شود؛ خودِ موتور بدونش هم لید می‌سازد.
  var STAGES = ["new","warm","hot","subscribed","vip","churn_risk","lost","blocked"];
  var STAGE_FA = {new:"تازه", warm:"گرم", hot:"داغ", subscribed:"مشترک",
                  vip:"ویژه", churn_risk:"در خطرِ ریزش", lost:"از‌دست‌رفته",
                  blocked:"مسدود"};

  function renderLeadOps(el){
    el.innerHTML = "";
    api("/api/ops/leads").then(function(d){
      d = d || {};
      var items = d.items, stages = d.lead_stages || {};
      var h = secHead("لیدها", pill(fa(d.leads_total||0)+" لید", (d.leads_total?"ok":"unk")));
      h += '<div class="vitals">'+orbs(STAGES.filter(function(s){ return stages[s]; })
             .map(function(s){ return {name:s, short:STAGE_FA[s]||s, n:stages[s],
                                       tone:(s==="hot"?"hot":s==="churn_risk"?"warm":"ok")}; }))+'</div>';

      if(items === null || items === undefined){
        h += '<div class="err">فهرستِ لیدها خوانده نشد — پایگاهِ ops در دسترس نیست.</div>';
      } else if(items.length){
        h += '<details class="det"><summary>'+fa(items.length)+' لید</summary><div class="inner">'+
          items.map(function(it){
            var id = esc(it.id);
            return '<div class="titem p3"><div class="tbody">'+
              '<div class="tt">'+esc(it.handle||"—")+'</div>'+
              '<div class="tm">'+esc(STAGE_FA[it.stage]||String(it.stage||""))+'</div>'+
              '<div class="noteform" hidden>'+
                '<input class="fin" type="text" placeholder="یادداشت" maxlength="1000">'+
                '<button class="go notego" data-id="'+id+'">ثبتِ یادداشت</button>'+
              '</div></div>'+
              '<button class="tnote" data-id="'+id+'" aria-label="یادداشت">✎</button>'+
              '<button class="tstage" data-id="'+id+'" aria-label="مرحلهٔ بعد">›</button>'+
              '</div>';
          }).join("")+'</div></details>';
      }

      h += '<details class="det"><summary>لیدِ تازه</summary><div class="inner">'+
        '<input class="fin" id="nlHandle" type="text" placeholder="نشانی یا نامِ لید" maxlength="120">'+
        '<div class="chips" id="nlStage">'+STAGES.slice(0,5).map(function(s,i){
          return '<button class="chip'+(i===0?" on":"")+'" data-v="'+s+'">'+esc(STAGE_FA[s])+'</button>';
        }).join("")+'</div>'+
        '<button class="go" id="nlGo">بساز</button>'+
      '</div></details>';
      el.innerHTML = h;

      var go = el.querySelector("#nlGo");
      if(go) go.addEventListener("click", function(){
        var handle = (el.querySelector("#nlHandle")||{}).value || "";
        if(!handle.trim()){ toast("نشانیِ لید خالی است", "bad"); return; }
        var st = el.querySelector("#nlStage .chip.on");
        act("lead.create", {handle:handle.trim(),
                            stage:(st?st.getAttribute("data-v"):"new")}, go)
          .then(function(r){ if(r && r.ok) renderLeadOps(el); });
      });
      [].forEach.call(el.querySelectorAll(".chips"), function(g){
        g.addEventListener("click", function(e){
          var c = e.target.closest(".chip"); if(!c) return;
          [].forEach.call(g.children, function(x){ x.classList.remove("on"); });
          c.classList.add("on");
          hapticSelect();
        });
      });
      // یادداشتِ لید — ششمین اقدام که تا امروز هیچ صداکننده‌ای نداشت.
      // عمداً روی همان کارتِ لید می‌نشیند نه در فرمی جدا: یادداشت همیشه
      // دربارهٔ یک لیدِ مشخص است، پس انتخابِ لید نباید یک گامِ اضافه باشد.
      [].forEach.call(el.querySelectorAll(".tnote"), function(b){
        b.addEventListener("click", function(){
          var box = b.closest(".titem").querySelector(".noteform");
          if(!box) return;
          box.hidden = !box.hidden;
          if(!box.hidden){ var i = box.querySelector("input"); if(i) i.focus(); }
        });
      });
      [].forEach.call(el.querySelectorAll(".notego"), function(b){
        b.addEventListener("click", function(){
          var box = b.closest(".noteform"), inp = box.querySelector("input");
          var txt = (inp||{}).value || "";
          if(!txt.trim()){ toast("یادداشت خالی است", "bad"); return; }
          act("lead.add_note", {lead_id:b.getAttribute("data-id"), note:txt.trim()}, b)
            .then(function(r){ if(r && r.ok){ inp.value=""; box.hidden=true; } });
        });
      });

      // «مرحلهٔ بعد» — لید را یک پله در قیف جلو می‌برد. متنِ آزاد نمی‌خواهد،
      // پس یک تپ کافی است (ADHD: کمترین اصطکاک برای پرتکرارترین کار).
      [].forEach.call(el.querySelectorAll(".tstage"), function(b){
        b.addEventListener("click", function(){
          var id = b.getAttribute("data-id");
          var cur = (items.filter(function(x){ return x.id===id; })[0]||{}).stage;
          var nx = STAGES[Math.min(STAGES.indexOf(cur)+1, STAGES.length-1)];
          if(!nx || nx===cur){ toast("مرحلهٔ آخر است", "warn"); return; }
          act("lead.update_stage", {lead_id:id, stage:nx}, b)
            .then(function(r){ if(r && r.ok) renderLeadOps(el); });
        });
      });
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
          return {name:k, short:(k==="done"?"انجام":k==="open"?"باز":k), n:stat[k],
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
          hapticSelect();
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
      // لایهٔ ۱ — CTA ِ بومی: «+ کارِ تازه»، فرم را باز می‌کند و روی فیلد فوکوس.
      setBottomButton("＋ کارِ تازه", function(){
        var det = el.querySelector("details.det");
        if(det){ det.setAttribute("open",""); }
        var inp = el.querySelector("#ntTitle");
        if(inp){ inp.focus(); enableClosingGuard(true); }   // ویرایش = هشدارِ بستن
      });
    });
  }

  // ── تبِ هفتم: اعلان‌ها (notif_inbox، ۲۰۲۶-۰۸-۰۷) ──────────────────────────
  // ⚠️ مارک‌خواندن **خودکار روی بازشدنِ تب نیست** — دکمهٔ صریح «خواندم».
  // چون آیتم‌های kind=pointer (کارتِ RFC/پیشنهادِ پا) قبل از رفتن به تبِ
  // مقصد نباید از این فهرست گم شوند — مالک باید اول ببیندشان، بعد تصمیم بگیرد.
  var GOTO_TAB_FA = {
    system:"سیستم", approvals:"تأییدها", money:"پول", leads:"لیدها",
    tasks:"کارها", ask:"پرسش", home:"خانه", scans:"اسکن‌ها",
    notifications:"اعلان‌ها"
  };
  function renderNotifications(el){
    el.innerHTML = '<div class="loading">در حال بارگذاری…</div>';
    api("/api/notifications").then(function(d){
      d = d || {};
      if(d.status==="error" || d.status==="unknown"){
        el.innerHTML = '<div class="err">خطا: '+esc(d.reason||d.status)+'</div>';
        return;
      }
      var items = d.items || [];
      var unread = Number(d.unread_count||0);
      var html = secHead("اعلان‌ها", pill(unread>0?fa(unread)+" نخوانده":"همه خوانده شد",
                                          unread>0?"warn":"ok"));
      if(unread>0){
        html += '<button class="go" id="notifMarkAll">همه رو خواندم</button>';
      }
      if(!items.length){
        html += '<div class="calm"><div class="big">صندوق خالی است</div>'+
                '<div class="sm">هیچ اعلانی اینجا ننشسته.</div></div>';
      } else {
        html += '<div class="tasklist">'+items.map(function(it){
          var read = !!it.read;
          var body = it.kind==="pointer" ? "" :
            '<div class="tm">'+esc(String(it.body||"").slice(0,280))+'</div>';
          var goto = (it.meta && it.meta.goto_tab) || "";
          var gotoBtn = goto ? '<button class="chip notifGoto" data-goto="'+esc(goto)+
            '" data-id="'+esc(it.id)+'">برو به تبِ '+esc(GOTO_TAB_FA[goto]||goto)+'</button>' : "";
          var readBtn = read ? "" :
            '<button class="tdone notifRead" data-id="'+esc(it.id)+'" aria-label="خواندم">✓</button>';
          return '<div class="titem'+(read?"":" p1")+'">'+readBtn+
            '<div class="tbody"><div class="tt">'+esc(it.title||"—")+'</div>'+
            body+'<div class="tm">'+ltr(String(it.created_at||"").slice(0,16))+'</div>'+
            (gotoBtn?'<div class="chips">'+gotoBtn+'</div>':'')+
            '</div></div>';
        }).join("")+'</div>';
      }
      el.innerHTML = html;

      // لایهٔ ۱ — CTA ِ بومیِ تلگرام: وقتی اعلانِ نخوانده هست، دکمهٔ پایین
      // صفحه «همه رو خواندم» می‌شود. روی کلاینتِ بدونِ SDK بی‌صدا غیب می‌شود.
      if(unread > 0){
        setBottomButton("✓ "+fa(unread)+" اعلان رو خواندم", function(){
          act("notif.mark_read", {all:true}, null).then(function(r){
            if(r && r.ok) renderNotifications(el);
          });
        });
      } else {
        hideBottomButton();
      }

      [].forEach.call(el.querySelectorAll(".notifRead"), function(b){
        b.addEventListener("click", function(){
          act("notif.mark_read", {ids:[b.getAttribute("data-id")]}, b).then(function(r){
            if(r && r.ok) renderNotifications(el);
          });
        });
      });
      var markAll = el.querySelector("#notifMarkAll");
      if(markAll) markAll.addEventListener("click", function(){
        act("notif.mark_read", {all:true}, markAll).then(function(r){
          if(r && r.ok) renderNotifications(el);
        });
      });
      [].forEach.call(el.querySelectorAll(".notifGoto"), function(b){
        b.addEventListener("click", function(){
          // برو به تبِ مقصد — آیتم را از صندوق پاک نمی‌کند، مالک خودش با
          // «خواندم» تصمیم می‌گیرد (رأیِ طراحی: پینگ را قبل از دیدنِ نتیجه گم نکن).
          goTab(b.getAttribute("data-goto"));
        });
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
  function viewApprovals(el){ stack(el||content, [renderApprovals, renderLifecycle]); }
  function viewMoney(el){ stack(el||content, [renderMoneyCaps, renderValue, renderValueEntry, renderOutbound]); }
  function viewLeads(el){ stack(el||content, [renderLeadOps, renderPF]); }
  // ⚠️ renderStudio از این‌جا برداشته شد: کارتی کاملاً انگلیسی وسطِ صفحهٔ
  // فارسی، با دو کلاسِ ناموجود در CSS، JSON ِ خام به‌جای رسید، و پای
  // بیزنسیِ هاردکدشده. هر سه اقدامش حالا جای درستِ خودش را دارد:
  // lead.create/update_stage در تبِ لیدها، task.create در تبِ کارها.
  // ⚠️ ۲۰۲۶-۰۸-۰۵ — رأیِ مالک: «تبِ سیستم پر از اطلاعات است ولی هیچ‌کدام
  // کار نمی‌کند؛ اول UI ِ آن را مثلِ بقیهٔ صفحات کن.»
  //
  // مشکل معماری بود نه زیبایی: هشت پنلِ خام پشتِ سرِ هم ریخته می‌شدند و
  // خواندنِ صفحه یعنی خواندنِ **همه‌شان**. صفحهٔ خانه دقیقاً همین داده را
  // دارد ولی اول می‌گوید «چه چیزی با توست»، بعد بقیه را می‌خواباند.
  // این‌جا همان قاعده: یک سرِ تریاژ که فقط چیزهای **خوانده‌نشده یا بد** را
  // بالا می‌آورد، بعد پنل‌های تفصیلی سرِ جای همیشگی‌شان.
  function renderSystemHead(el){
    el.innerHTML = '<div class="loading">در حال بارگذاری…</div>';
    var EPS = [["/api/legs","پاها"], ["/api/state","علائمِ حیاتی"],
               ["/api/selfmap","نقشهٔ خودآگاهی"], ["/api/ops/brain","مغز"],
               ["/api/governor","ناظر"], ["/api/obsidian","ابسیدین"],
               ["/api/current-truth","حقیقتِ جاری"], ["/api/ui-registry","رجیستری"]];
    var myseq = _renderSeq;
    Promise.all(EPS.map(function(e){ return api(e[0]); })).then(function(rs){
      if(_renderSeq !== myseq) return;
      var bad = [], unk = [], fine = 0;
      rs.forEach(function(d, i){
        var s = String(((d||{}).status)||"unknown"), name = EPS[i][1];
        if(s==="error" || s==="unknown_schema") bad.push([name, (d||{}).reason||s]);
        else if(s==="unknown") unk.push([name, (d||{}).reason||""]);
        else fine += 1;
      });
      var h = '<div class="card">'+secHead("سلامتِ خودِ صفحه",
        pill(bad.length ? fa(bad.length)+" خوانده نشد"
                        : unk.length ? fa(unk.length)+" نامعلوم" : "هر ۸ خوانده شد",
             bad.length ? "hot" : unk.length ? "unk" : "ok"));
      // چرا این بالاست: تا امروز یک بخشِ ۵۰۰ می‌داد و پنلش **سبز** رنگ
      // می‌زد. حالا اول از همه می‌گوییم کدام بخشِ این صفحه اصلاً خوانده شد.
      if(bad.length){
        h += bad.map(function(b){
          return '<div class="tri hot"><div class="in">'+
            '<div class="verb">«'+esc(b[0])+'» خوانده نشد</div>'+
            '<div class="why">'+ltr(esc(String(b[1])))+' — عددهای این بخش '+
            'پایین‌تر نشان داده نمی‌شوند.</div></div></div>'; }).join("");
      }
      if(unk.length){
        h += '<details class="quiet"><summary>'+fa(unk.length)+
             ' بخش «نمی‌دانم» می‌گوید</summary><div class="inner">'+
             unk.map(function(u){
               return '<div class="row"><span class="k">'+esc(u[0])+
                 '</span><span class="v">'+ltr(esc(String(u[1])))+'</span></div>';
             }).join("")+'</div></details>';
      }
      if(!bad.length && !unk.length){
        h += '<div class="muted">هر هشت بخشِ این صفحه خوانده شد.</div>';
      }
      el.innerHTML = h + '</div>';
    });
  }

  // ۲۰۲۶-۰۸-۰۹ — دکمهٔ ری‌استارتِ کامل: خواستِ مالک بعد از اینکه دستی دید
  // فلگِ تازه‌آرم‌شده تا ری‌استارت اثر ندارد. صفر reimplementation: همان
  // مسیرِ امنِ /restart تلگرام (POST /api/restart → request_restart →
  // کارتِ approval) — این دکمه فقط یک درِ ورودیِ دومِ کوتاه‌تر به همان
  // کارت است، گیتِ تأییدِ مالک را دور نمی‌زند. عمداً آخرِ تب سیستم —
  // پرریسک‌ترین دکمهٔ صفحه، نباید اولین چیزِ دیده‌شده باشد.
  function renderRestartControl(el){
    el.innerHTML = card("🔁 ری‌استارتِ کامل", pill("پرریسک","hot"),
      '<div class="muted">هر ۵ پروسه را تازه می‌کند تا فلگ/کدِ کامیت‌شده لود شود. '+
      'این دکمه فقط کارتِ تأیید می‌سازد — اجرای واقعی فقط بعد از تأییدِ دستیِ '+
      'تو در تلگرام است.</div>'+
      '<button id="restartAllBtn" style="margin-top:10px">درخواستِ ری‌استارتِ کامل</button>'+
      '<div class="result" id="restartResult"></div>');
    var rb = document.getElementById("restartAllBtn");
    if(rb){ rb.addEventListener("click", function(){
      rb.disabled = true;
      var out = document.getElementById("restartResult");
      out.textContent = "در حالِ ثبتِ درخواست…";
      apiPost("/api/restart", {scope:"all"}).then(function(r){
        rb.disabled = false;
        if(r && r.ok){
          out.textContent = "✅ ثبت شد — برای اجرا کارتِ تأیید را توی تلگرام بزن.";
        } else {
          var RS = {already_in_flight:"یه درخواستِ دیگه در جریانه.",
                    "flag-off":"این قابلیت هنوز روشن نیست.",
                    owner_auth_required:"احرازِ هویت شکست خورد."};
          out.textContent = "⚠️ "+(RS[r&&r.reason] || (r&&r.reason) || "خطا");
        }
      });
    });}
  }

  function viewSystem(el){ stack(el||content, [renderSystemHead, renderLegs, renderVitals,
                                               renderSelfmap, renderBrain, renderGovernor,
                                               renderObsidian, renderTruth, renderRegistry,
                                               renderRestartControl]); }

  function viewTasks(el){ stack(el||content, [renderTasks]); }
  function viewNotifications(el){ stack(el||content, [renderNotifications]); }

  // ══ تبِ «اسکن‌ها» (۲۰۲۶-۰۸-۰۸) ════════════════════════════════════════════════
  // دو پنل: اسکنای شناختیِ زنده (self-model/doctor/pulse/BCM/semantic) + لاگِ تغییراتِ ایجنت (git log)
  function renderCognitiveScan(el){
    el = el || content;
    el.innerHTML = '<div class="loading">در حال بارگذاریِ اسکنای شناختی…</div>';
    var myseq = _renderSeq;
    api("/api/cognitive-scan").then(function(d){
      if(_renderSeq !== myseq) return;
      if(!d || d.status === "error"){ el.innerHTML='<div class="err">خطا: '+esc(d&&d.reason||"")+'</div>'; return; }
      var sm = d.self_model||{}, doc = d.doctor||{}, pu = d.pulse||{}, bc = d.bcm||{}, sem = d.semantic||{}, con = d.consolidation||{};
      // 2026-08-12 fix: بک‌اند age_s را برمی‌گرداند ولی اینجا هیچ‌وقت خوانده
      // نمی‌شد — self-model کهنه همیشه به‌رنگِ سبز/تازه نشان داده می‌شد.
      var smStale = sm.age_s!=null && sm.age_s > 3*3600;
      var smTone = sm.error ? 'unk' : (smStale ? 'blocked' : 'ok');
      var smAgeNote = sm.age_s!=null ? ' <span class="muted">(سن: '+Math.round(sm.age_s/60)+'دقیقه)</span>' : '';
      var h = '<div class="card"><h2>🧠 خودآگاهیِ کد'+pill(sm.error?'نامعلوم':(sm.self_awareness_pct||'?')+'٪', smTone)+smAgeNote+'</h2>'+
        '<div class="kv"><div class="k">ماژول‌ها</div><div>'+fa(sm.modules||0)+'</div>'+
        '<div class="k">خطوطِ کد</div><div>'+fa(sm.total_lines||0)+'</div>'+
        '<div class="k">تست‌ها</div><div>'+fa(sm.n_tests||0)+'</div>'+
        '<div class="k">مستند‌نشده</div><div>'+fa(sm.undocumented||0)+'</div></div></div>';
      h += '<div class="card"><h2>🩺 دکتر — خودشناسی'+pill(doc.error?'نامعلوم':'نسخه '+fa(doc.version||0), doc.error?'unk':(doc.stable_cycles>5?'ok':doc.stable_cycles>0?'unk':'hot'))+'</h2>'+
        '<div class="kv"><div class="k">دقتِ خودسنجی</div><div>'+
        (typeof doc.self_accuracy === "number"
          ? fa(Math.round(doc.self_accuracy*100))+'٪'
          : 'نامعلوم')+
        '</div>'+
        '<div class="k">سیکل‌های پایدار</div><div>'+fa(doc.stable_cycles||0)+'</div>'+
        '<div class="k">اصلاحاتِ مالک</div><div>'+fa(doc.owner_corrections||0)+'</div></div></div>';
      var pulseColor = pu.error?'unk':(pu.color==='RED'?'hot':pu.color==='AMBER'?'unk':'ok');
      h += '<div class="card"><h2>🫀 قلب'+pill(pu.error?'نامعلوم':pu.color||'?', pulseColor)+'</h2>'+
        '<div class="kv"><div class="k">دورهٔ نبض</div><div>'+fa(pu.effective_period_s||0)+'s</div>'+
        '<div class="k">راننده</div><div>'+ltr(esc(pu.driver||'—'))+'</div>'+
        '<div class="k">قلب‌های حاضر</div><div>'+fa(pu.n_present||0)+'</div>'+
        '<div class="k">متحرک</div><div>'+fa(pu.n_moving||0)+'</div></div></div>';
      h += '<div class="card"><h2>🧬 یادگیری (BCM)'+pill(bc.error?'نامعلوم':'step '+fa(bc.step||0), bc.error?'unk':'ok')+'</h2>'+
        '<div class="kv"><div class="k">step</div><div>'+fa(bc.step||0)+'</div>'+
        '<div class="k">سیکل‌ها</div><div>'+fa(bc.cycles||0)+'</div></div></div>';
      h += '<div class="card"><h2>💭 حافظهٔ سِمانتیک'+pill(fa(sem.total||0)+' ورودی', 'ok')+'</h2>'+
        '<div class="muted">'+esc(sem.latest_gist||'—')+'</div></div>';
      h += '<div class="card"><h2>🔄 تثبیت'+pill(con.error?'نامعلوم':'n_in='+fa(con.n_in||0), con.error?'unk':(con.n_in>0?'ok':'unk'))+'</h2>'+
        '<div class="muted">آخرین: '+esc(con.last_run||'—')+' · نوت: '+fa(con.n_semantic||0)+'</div></div>';
      el.innerHTML = h;
    });
  }
  function renderAgentLog(el){
    el = el || content;
    el.innerHTML = '<div class="loading">در حال بارگذاریِ لاگِ ایجنت…</div>';
    var myseq = _renderSeq;
    api("/api/agent-log").then(function(d){
      if(_renderSeq !== myseq) return;
      if(!d || d.status === "error"){ el.innerHTML='<div class="err">گیت در دسترس نیست.</div>'; return; }
      var commits = d.commits || [];
      if(!commits.length){ el.innerHTML='<div class="card"><div class="muted">هنوز کامیت‌ای ثبت نشده.</div></div>'; return; }
      var h = '<div class="card"><h2>📜 آخرین تغییراتِ ایجنت'+pill(fa(commits.length)+' کامیت','ok')+'</h2>';
      commits.forEach(function(c){
        var isAgent = c.author && c.author.indexOf('ari-vault') < 0 && c.author.indexOf('Armin') < 0;
        h += '<div class="row" style="margin:6px 0;padding:6px;border-radius:8px;'+
             (isAgent?'background:rgba(99,102,241,0.08)':'')+'">'+
          '<div class="k">'+ltr(esc(c.hash||''))+' · '+esc(c.author||'')+(isAgent?' <span class="badge live">ایجنت</span>':'')+'</div>'+
          '<div class="v">'+esc(c.message||'')+'</div>'+
          '<div class="muted">'+esc(c.date||'')+'</div></div>';
      });
      h += '</div>';
      el.innerHTML = h;
    });
  }
  function viewScans(el){ stack(el||content, [renderCognitiveScan, renderAgentLog]); }

  // ── پرسش (۲۰۲۶-۰۸-۰۸) + همکار پیش‌فرض (۲۰۲۶-۰۸-۱۱ Talk Discovery) ─────
  // وقتی OCTOPUS_WIRE_COLLAB=1 (از window.__OCTOPUS__.wire_collab): پیش‌فرض
  // مسیر پاسخ = 🤝 همکار (/api/collab). Ask و Mirror فقط با انتخاب صریح.
  // همکار = draft پاسخ؛ اثر خارجی از این UI مجاز نیست.
  function renderAsk(el){
    var collabDefault = !!(window.__OCTOPUS__ && window.__OCTOPUS__.wire_collab);
    el.innerHTML = secHead("پرسش از اختاپوس") +
      '<div class="card">'+
      '<div id="askLog" class="asklog"></div>'+
      '<div class="chips">'+
        '<button class="chip'+(collabDefault?" on":"")+'" id="askCollab" type="button">🤝 همکار</button>'+
        '<button class="chip'+(collabDefault?"":" on")+'" id="askPlain" type="button">💬 Ask</button>'+
        '<button class="chip" id="askMirror" type="button">🪞 آینه</button>'+
        '<button class="chip" id="askGuide" type="button">🧭 به کورتکس</button>'+
      '</div>'+
      '<div class="muted askmeta" id="askModeHint">'+(
        collabDefault
          ? "پیش‌فرض: همکار (پاسخ draft · بدون اثر خارجی). Ask/آینه/کورتکس فقط با انتخاب صریح."
          : "همکار خاموش است — پیش‌فرض Ask. روشن‌کردن فقط با رأی مالک."
      )+'</div>'+
      '<input class="fin" id="askQ" type="text" placeholder="از خودِ اختاپوس بپرس… یا با «به کورتکس» یک focus بفرست" maxlength="500">'+
      '<button class="go" id="askGo">بپرس</button>'+
      '</div>';
    var log = el.querySelector("#askLog");
    var input = el.querySelector("#askQ");
    var go = el.querySelector("#askGo");
    var mirrorChip = el.querySelector("#askMirror");
    var collabChip = el.querySelector("#askCollab");
    var plainChip = el.querySelector("#askPlain");
    var guideChip = el.querySelector("#askGuide");
    // فاز R/S — بازیابی چت قبلی (localStorage) قبل از اولین تعامل
    (function restoreAskLog(){
      try {
        var rows = JSON.parse(localStorage.getItem("octopus.asklog.v1") || "[]");
        rows.forEach(function(r){
          if(!r || !r.q) return;
          var row = document.createElement("div");
          row.className = "askturn";
          row.innerHTML = '<div class="askq">'+esc(r.q)+'</div>'+
            '<div class="aska'+(r.bad?" bad":"")+'">'+esc(r.a||"")+'</div>'+
            (r.m ? '<div class="muted askmeta">'+esc(r.m)+'</div>' : '');
          log.appendChild(row);
        });
        log.scrollTop = log.scrollHeight;
      } catch(e){ /* localStorage خراب → خالی */ }
    })();
    // 2026-08-12 — حافظهٔ سرور: گفتگو حالا سرور-ساید هم سیو می‌شود
    // (chat-log.jsonl). این بخش تاریخچهٔ سرور + هدفِ اعلام‌شدهٔ مالک
    // (owner-goal.json) را نشان می‌دهد — همه‌چیز به هم وصل، نه localStorage-only.
    (function loadServerLog(){
      try {
        // UI-08 (DISCOVERY-WIRE 2026-08-12): __OCTOPUS__.init_data هرگز ست
        // نمی‌شود — auth باید از tg.initData/tgHeaders بیاید وگرنه 403 ساکت.
        var sh = tgHeaders({});
        var sx = new XMLHttpRequest();
        sx.open("GET", "/api/chat-log?limit=10", true);
        for(var hk in sh) sx.setRequestHeader(hk, sh[hk]);
        sx.onload = function(){
          if(sx.status !== 200) return;
          try {
            var sd = JSON.parse(sx.responseText);
            if(sd.goal && sd.goal.goal){
              var g = document.createElement("div");
              g.className = "muted askmeta";
              g.innerHTML = '🎯 هدفِ مالک: '+esc(String(sd.goal.goal).slice(0,150));
              log.appendChild(g);
            }
            (sd.turns||[]).forEach(function(t){
              if(!t || !t.text) return;
              var row = document.createElement("div");
              row.className = "askturn";
              var who = t.role === "owner" ? "🧑 مالک" : "🐙 اختاپوس";
              row.innerHTML = '<div class="askq">'+who+' · '+esc(String(t.text).slice(0,220))+'</div>'+
                '<div class="muted askmeta">🧠 حافظهٔ سرور'+
                (t.model_source ? ' · '+esc(t.model_source) : '')+
                (t.ts ? ' · '+esc(String(t.ts).slice(0,16)) : '')+'</div>';
              log.appendChild(row);
            });
            log.scrollTop = log.scrollHeight;
          } catch(e2){ /* JSON خراب → بی‌صدا */ }
        };
        sx.onerror = function(){};
        sx.send();
      } catch(e3){ /* fetch اختیاری — بی‌صدا */ }
    })();
    // mode: "collab" | "ask" | "mirror" | "guide"
    var mode = collabDefault ? "collab" : "ask";
    // 2026-08-12 fix: آخرین حالتِ ایستا (collab/ask) که کاربر صریحاً انتخاب
    // کرده بود — برای برگرداندنِ درست بعدِ guide/mirrorِ یک‌باره؛ قبلاً
    // همیشه به collabDefault برمی‌گشت، حتی اگر کاربر عمداً حالتِ دیگری را
    // روشن کرده بود (مثلاً collabDefault=true ولی کاربر Ask را زده بود).
    var prevMode = mode;
    function paint(){
      collabChip.classList.toggle("on", mode === "collab");
      plainChip.classList.toggle("on", mode === "ask");
      mirrorChip.classList.toggle("on", mode === "mirror");
      if(guideChip) guideChip.classList.toggle("on", mode === "guide");
      var hint = el.querySelector("#askModeHint");
      if(hint && mode === "guide"){
        // 2026-08-12 fix: owner_guidance دیگر متنِ بدونِ کلید را نمی‌پذیرد —
        // باید صریح «focus:» بنویسی، وگرنه رد می‌شود.
        hint.textContent = "به کورتکس: با «focus: متن» بنویس (مثلاً «focus: روی امنیت تمرکز کن») → owner_guidance.jsonl (cortex در cycle می‌خواند · بدون IPC · بدون اثر بیرونی).";
      }
    }
    function setMode(m){
      if(m !== "guide" && m !== "mirror"){ prevMode = m; }
      mode = m; paint(); hapticSelect();
    }
    collabChip.addEventListener("click", function(){ setMode("collab"); });
    plainChip.addEventListener("click", function(){ setMode("ask"); });
    mirrorChip.addEventListener("click", function(){ setMode("mirror"); });
    if(guideChip) guideChip.addEventListener("click", function(){ setMode("guide"); });
    paint();
    // فاز R/S — session persist در tab switch (localStorage؛ فقط preview/متن، بدون secret)
    var ASKLOG_KEY = "octopus.asklog.v1";
    function saveLog(){
      try {
        var rows = [];
        log.querySelectorAll(".askturn").forEach(function(r){
          var q = (r.querySelector(".askq")||{}).textContent || "";
          var a = (r.querySelector(".aska")||{}).textContent || "";
          var m = (r.querySelector(".askmeta")||{}).textContent || "";
          rows.push({q:q, a:a, m:m, bad: (r.querySelector(".aska")||{}).classList.contains("bad")});
        });
        localStorage.setItem(ASKLOG_KEY, JSON.stringify(rows.slice(-24)));
      } catch(e){ /* storage نباشد → بی‌صدا */ }
    }
    function restoreLog(){
      try {
        var rows = JSON.parse(localStorage.getItem(ASKLOG_KEY) || "[]");
        rows.forEach(function(r){
          addTurn(r.q||"", r.a||"", r.m||"", !!r.bad);
        });
      } catch(e){ /* خراب → خالی */ }
    }
    function addTurn(q, a, meta, bad, sourcesHtml){
      var row = document.createElement("div");
      row.className = "askturn";
      row.innerHTML = '<div class="askq">'+esc(q)+'</div>'+
        '<div class="aska'+(bad?" bad":"")+'">'+esc(a)+'</div>'+
        (meta ? '<div class="muted askmeta">'+esc(meta)+'</div>' : '')+
        (sourcesHtml || "");
      log.appendChild(row);
      log.scrollTop = log.scrollHeight;
      saveLog();
      return row;
    }
    function buildSourcesPanel(data){
      if(!data) return "";
      var facts = data.facts || [];
      var lims = data.limitations || [];
      var eq = data.equation_advice || {};
      var uctx = data.unified_context || {};
      var body = "";
      if(facts.length){
        body += facts.map(function(f){
          var p = f.provenance || {};
          return "· "+(f.title||"?")+" ["+(p.source_kind||"?")+"; "+(p.trust||"?")+
            "; conf="+((f.confidence!=null)?Number(f.confidence).toFixed(2):"?")+"]\n"+
            "  path="+(p.path||"?")+" digest="+(p.content_digest||"?");
        }).join("\n");
      }
      if(lims.length){
        body += (body?"\n\n":"")+"محدودیت‌ها:\n"+lims.map(function(x){return "· "+x;}).join("\n");
      }
      // فاز R/Q — معادلات مرتبط (advice-only) — فقط وقتی backend فرستاده
      if(eq && eq.equations_consulted && eq.equations_consulted.length){
        body += (body?"\n\n":"")+"معادلات مرتبط:\n"+
          "· "+(eq.equations_consulted||[]).join(" · ")+
          "  [aggregate="+(eq.aggregate_advice||"?")+"]\n"+
          "  advice_only="+(eq.equation_advice_only===true?"true":"false")+
          " decision_effect="+(eq.decision_effect===true?"true":"false")+
          " apply_effect="+(eq.apply_effect===true?"true":"false");
      }
      // لایهٔ ۵ — نبض مغزها از فایل (file-bridge؛ نه IPC)
      var sc = uctx && uctx.self_context;
      if(sc && (sc.cortex || sc.business_brain)){
        var cx = sc.cortex || {};
        var bb = sc.business_brain || {};
        // 2026-08-12 fix: live قبلاً فقط یعنی «فایل parse شد»، نه تازه بودن —
        // حالا brain_pulse سنِ واقعی (age_s) هم می‌فرستد؛ نشانش می‌دهیم تا
        // live=false کهنه‌بودن را توضیح بدهد نه فقط یک بولیِ خشک.
        body += (body?"\n\n":"")+"مغزها (file-bridge):\n"+
          "· cortex: live="+(cx.live===true?"true":"false")+
          (cx.age_s!=null?" age="+Math.round(cx.age_s)+"s":"")+
          " cycle="+(cx.cycle!=null?cx.cycle:"?")+
          " coherence="+(cx.coherence!=null?cx.coherence:"?")+
          " aligned="+(cx.aligned===true?"true":(cx.aligned===false?"false":"?"))+
          "\n· business_brain: live="+(bb.live===true?"true":"false")+
          (bb.age_s!=null?" age="+Math.round(bb.age_s)+"s":"")+
          " beat="+(bb.beat!=null?bb.beat:"?")+
          " proposals="+(bb.n_proposals!=null?bb.n_proposals:"?")+
          "\n· bridge="+(sc.bridge||"file-read-only")+
          " ipc="+(sc.ipc_to_cortex===true?"true":"false")+
          " heard_chat="+(sc.chat_heard_by_brains===true?"true":"false");
        var titles = bb.proposal_titles || [];
        if(titles.length){
          body += "\n· پیشنهادها:\n"+titles.map(function(t){return "  - "+t;}).join("\n");
        }
        var sk = sc.doctor_self_knowledge || {};
        if(sk && (sk.focus || sk.smallest_fix)){
          body += "\n· doctor.focus="+(sk.focus||"?")+
            "\n· smallest_fix="+(sk.smallest_fix||"?");
        }
      }
      // فاز T — وضعیت سایه (shadow) — همیشه applied=false
      if(uctx && uctx.shadow){
        body += (body?"\n\n":"")+"وضعیت سایه (Shadow):\n"+
          "· records="+(uctx.shadow.shadow_records||0)+
          " applied="+(uctx.shadow.applied===true?"true":"false")+
          " may_authorize="+(uctx.shadow.may_authorize===true?"true":"false");
      }
      // فاز T — پیشنهاد اثر (limited-effect) — فقط proposal
      if(uctx && uctx.effects){
        body += (body?"\n\n":"")+"پیشنهاد اثر:\n"+
          "· policy_gate="+(uctx.effects.policy_gate_status||"?")+
          " proposal_created="+(uctx.effects.proposal_created===true?"true":"false")+
          " applied="+(uctx.effects.applied===true?"true":"false");
      }
      // فاز Q — معماری مرتبط (اگر backend فرستاد)
      if(uctx && uctx.architecture && uctx.architecture.components){
        body += (body?"\n\n":"")+"اجزای معماری:\n"+
          "· "+(uctx.architecture.components||[]).slice(0,6).join("\n· ");
      }
      // Cognitive Runtime — run_id + trace + event timeline
      if(data.run_id){
        body += (body?"\n\n":"")+"Run: "+data.run_id;
        if(data.trace_id) body += " · trace: "+data.trace_id;
        // event timeline: fetch SSE endpoint (events already complete for sync flow)
        // استفاده از fetch نه EventSource — چون events قبلاً نوشته شده‌اند
        try {
          // UI-08 (DISCOVERY-WIRE 2026-08-12): auth از tgHeaders — وگرنه 403 ساکت
          var evHeaders = tgHeaders({});
          var evUrl = "/api/runs/"+data.run_id+"/events?after=0";
          var xhr = new XMLHttpRequest();
          xhr.open("GET", evUrl, false); // sync — در buildSourcesPanel
          for(var hk in evHeaders) xhr.setRequestHeader(hk, evHeaders[hk]);
          xhr.send(null);
          if(xhr.status === 200 && xhr.responseText){
            var evLines = xhr.responseText.split("\n").filter(function(l){
              return l.indexOf("event:") === 0;
            });
            if(evLines.length){
              body += "\n\nرویدادهای run:\n"+evLines.map(function(l){
                return "· "+l.replace("event: ","").trim();
              }).slice(0,8).join("\n");
            }
          }
        } catch(ee){ /* SSE fetch اختیاری — بی‌صدا */ }
      }
      if(!body) return "";
      return '<details class="ask-sources"><summary>📎 Sources / شواهد · معادلات · وضعیت</summary>'+
        '<pre class="muted" style="white-space:pre-wrap;font-size:12px;margin:6px 0 0">'+
        esc(body)+'</pre></details>';
    }
    // 2026-08-12 fix: پیام شکست قبلاً همیشه یک پسوندِ ثابت داشت («دوباره
    // بپرس؛ DeepSeek گاهی ۲۰-۴۰ثانیه») — حتی وقتی دلیل سهمیهٔ تمام‌شده یا
    // halt بود که تا نیمه‌شب/رأی مالک حل نمی‌شود. دوباره‌فرستادن در آن حالت
    // فقط زمانِ کاربر را تلف می‌کند، پس پیام باید فرق کند.
    function _failureSuffix(reason){
      var r = String(reason||"");
      if(/daily-cap|quota|stop-fugu|kill-switch|halt/i.test(r)){
        return " — شکستِ گذرا نیست (سهمیه/توقف)؛ دوباره‌فرستادن الان کمکی نمی‌کند.";
      }
      return " — دوباره بپرس؛ DeepSeek گاهی ۲۰–۴۰ثانیه طول می‌کشد.";
    }
    function ask(){
      var q = (input.value||"").trim();
      if(!q){ toast("سؤال خالی است","warn"); return; }
      go.disabled = true; input.disabled = true; go.setAttribute("data-busy","1");
      var pending = addTurn(q, "در حال فکر کردن…", "");
      pending.querySelector(".aska").classList.add("muted");
      var useCollab = mode === "collab";
      var useMirror = mode === "mirror";
      var useGuide = mode === "guide";
      // 2026-08-12 fix: guide/mirror باید one-shot باشند — چیپ قبلاً بعد از
      // ارسال روشن می‌ماند، پس پیام بعدیِ نامرتبط بی‌صدا به همان مسیر می‌رفت
      // (مثلاً «از خودت بگو» بعد از «به کورتکس» به owner_guidance می‌خورد).
      if(useGuide || useMirror){ mode = prevMode; paint(); }
      var endpoint = useGuide ? "/api/brain-guide"
        : (useCollab ? "/api/collab" : (useMirror ? "/api/mirror" : "/api/ask"));
      var payload = (useCollab || useGuide) ? {text: q} : {question: q};
      // DeepSeek روی همکار اغلب ۱۰–۳۰ث؛ Ask زنجیره هم طولانی‌تر از ۴۵ث است (UI-05).
      var tmo = useGuide ? 20000 : (useCollab ? 90000 : 90000);
      apiPost(endpoint, payload, tmo).then(function(r){
        try { pending.remove(); } catch(e){}
        // UI-07: 403 → toast ببند/باز کن مینی‌اپ
        if(r && (r.http_status === 403 || /owner_auth|403/.test(String(r.reason||"")))){
          toast("احراز رد شد — مینی‌اپ را ببند و از تلگرام دوباره باز کن","warn");
        }
        if(useGuide){
          if(r && r.ok){
            var d = r.directive || {};
            var bits = [];
            if(d.focus) bits.push("focus="+String(d.focus).slice(0,120));
            if(d.think_every_n!=null) bits.push("think_every_n="+d.think_every_n);
            if(d.paused!=null) bits.push("paused="+d.paused);
            addTurn(q,
              "ثبت شد برای cortex (owner_guidance). "+(bits.join(" · ")||"directive ok")+
              "\nمسیر: "+(r.path||"state/cortex/owner-guidance.jsonl")+
              "\n"+ (r.note||"در cycle بعد خوانده می‌شود."),
              "منبع: brain-guide · بدون IPC · بدون اثر بیرونی", false);
          } else {
            addTurn(q, "ثبت نشد ("+((r&&r.error)||(r&&r.reason)||"نامشخص")+")", "", true);
          }
        } else if(useCollab){
          // owner-console.reply.v1 — or feature_disabled / auth errors
          if(r && r.schema === "owner-console.reply.v1"){
            var meta = "منبع: همکار"+(r.model_source?" · "+r.model_source:"")+
              (r.kind ? " · "+r.kind : "")+" · draft · بدون اثر خارجی";
            var src = buildSourcesPanel(r.data);
            addTurn(q, r.text||"", meta, r.kind === "disabled", src);
          } else if(r && r.reason === "feature_disabled"){
            addTurn(q, "همکار خاموش است (OCTOPUS_WIRE_COLLAB=0). روشن‌کردنش فقط با رأی مالک.", "", true);
          } else {
            addTurn(q, "جواب نگرفتم ("+((r&&r.reason)||"نامشخص")+(r&&r.http_status?" · HTTP "+r.http_status:"")+")"+_failureSuffix(r&&r.reason), "", true);
          }
        } else if(r && r.ok){
          var vaultSrc = "";
          if(r.source === "vault" && (r.sources||[]).length){
            vaultSrc = '<details class="ask-sources"><summary>📎 منابع vault ('+r.sources.length+' نوت)</summary>'+
              '<pre class="muted" style="white-space:pre-wrap;font-size:12px;margin:6px 0 0">'+
              esc((r.sources||[]).map(function(s){ return "· "+(typeof s === "string" ? s : (s.path||s.title||JSON.stringify(s))); }).join("\n"))+
              '</pre></details>';
          }
          var meta = r.source === "vault"
            ? "منبع: vault ("+((r.sources||[]).length)+" نوت)"+(r.vault_empty===true?" · vault_empty=true":"")
            : r.source === "mirror"
              ? "منبع: آینه"+(r.recorded_correction?" · تصحیحت ثبت شد":"")
              : r.source === "collab-fallback"
                ? "منبع: همکار (fallback · مغز جواب نداد)"+(r.kind?" · "+r.kind:"")+
                  " · chip=Ask ولی مسیر fallback"
                : "منبع: مغزِ "+(r.model||r.tier||"گران");
          // UI-09: Sources برای collab-fallback هم مثل collab
          var extraSrc = vaultSrc;
          if(r.source === "collab-fallback" && r.data){
            extraSrc = (extraSrc||"") + buildSourcesPanel(r.data);
          }
          if(r.source === "collab-fallback"){
            toast("جواب از همکار آمد (fallback) — chip Ask بود","warn");
          }
          addTurn(q, r.answer||"", meta, false, extraSrc);
        } else {
          addTurn(q, "جواب نگرفتم ("+((r&&r.reason)||"نامشخص")+(r&&r.http_status?" · HTTP "+r.http_status:"")+")"+_failureSuffix(r&&r.reason), "", true);
        }
        input.value = "";
        go.disabled = false; input.disabled = false; go.removeAttribute("data-busy");
        input.focus();
      });
    }
    go.addEventListener("click", ask);
    input.addEventListener("keydown", function(e){
      if(e.key === "Enter"){ e.preventDefault(); ask(); }
    });
  }
  function viewAsk(el){ stack(el||content, [renderAsk]); }

  var renderers = {home:viewHome,approvals:viewApprovals,money:viewMoney,
                   leads:viewLeads,tasks:viewTasks,system:viewSystem,
                   scans:viewScans,
                   notifications:viewNotifications,
                   ask:viewAsk};
  // ⚠️ سکوت را بلند کن. نسخهٔ قبلی `renderers[name]||renderHome` بود، پس یک تبِ
  // بی‌رندرکننده **بی‌صدا** محتوای خانه را نشان می‌داد — کلاسِ باگی که کلِ امروز
  // دنبالش بودیم، این‌بار در UI. حالا تبِ ناشناخته خودش را اعلام می‌کند.
  function render(name){
    _renderSeq++;   // stale-fetch guard: هر رندرِ نو توکنِ قبلی را باطل می‌کند
    clearDecisionTimers();
    hideBottomButton();   // هر تب CTA ِ خودش را ست می‌کند؛ تبِ قبلی پاک شود
    enableClosingGuard(false);   // تب‌های فقط‌خواندنی هشدارِ بستن لازم ندارند
    var fn = renderers[name];
    if(!fn){
      // FIX (deep-scan 2026-08-07): قبلاً `el` تعریف‌نشده بود → ReferenceError.
      // محتوای خطا باید رویِ content (همان DOM که بقیه استفاده می‌کنند) بنویسد.
      content.innerHTML = '<div class="card"><h2>این تب هنوز رندرکننده ندارد</h2>'+
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
