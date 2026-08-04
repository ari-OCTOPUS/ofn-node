/* tg_shell.js — پوستهٔ مینی‌اپ برای Mini Apps 2.0 (۲۰۲۶).
 *
 * چرا (فاز ۳، ۲۰۲۶-۰۸-۰۴)
 * ────────────────────────
 * کلِ یکپارچگیِ تلگرامِ این اپ تا امروز یک خط بود:
 *
 *     if (tg) { tg.expand(); tg.setHeaderColor("#0f1117"); }
 *
 * یعنی روی گوشی محتوا **زیرِ نُچ** می‌رفت (هیچ safe-area ای اعمال نمی‌شد)،
 * تمام‌صفحه نبود، آیکونِ صفحهٔ اصلی نداشت، و وقتی اپ به پس‌زمینه می‌رفت
 * همچنان poll می‌کرد. اندازه‌گیری: در ۸۸ ساعت **یک** نشستِ احرازشده.
 *
 * ⚠️ قاعدهٔ حاکم: هر API ِ ۲۰۲۶ باید **شناسایی** شود نه فرض. کلاینت‌های قدیمی
 * و حالتِ dev (بدونِ تلگرام) هر دو باید سالم بمانند — یک `TypeError` این‌جا
 * یعنی صفحهٔ سفید، و صفحهٔ سفید بدترین شکلِ «دیده نمی‌شود» است.
 *
 * تزریق‌پذیر عمداً: `initShell(tg, hooks)` هیچ‌چیزِ سراسری نمی‌خواند، پس در
 * node با یک WebApp ِ ساختگی تست می‌شود — نه با assert ِ متنی روی سورس.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) { module.exports = api; }
  root.OctopusShell = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function _num(v) {
    var n = Number(v);
    return (isFinite(n) && n >= 0) ? n : 0;
  }

  /* ─── safe-area ────────────────────────────────────────────────────────
   * بدونِ این، روی هر گوشیِ نُچ‌دار سرِ کارت زیرِ دوربین می‌رود. دو مجموعه
   * جداست و هر دو لازم: `safeAreaInset` مالِ دستگاه است و
   * `contentSafeAreaInset` مالِ کرومِ خودِ تلگرام (هدر/دکمه‌ها).
   */
  function insetVars(tg) {
    var out = {};
    var dev = (tg && tg.safeAreaInset) || {};
    var con = (tg && tg.contentSafeAreaInset) || {};
    ["top", "bottom", "left", "right"].forEach(function (side) {
      out["--tg-safe-" + side] = _num(dev[side]) + "px";
      out["--tg-content-safe-" + side] = _num(con[side]) + "px";
    });
    return out;
  }

  function applyInsets(tg, setVar) {
    var vars = insetVars(tg);
    Object.keys(vars).forEach(function (k) { setVar(k, vars[k]); });
    return vars;
  }

  /* ─── تمِ تلگرام ───────────────────────────────────────────────────────
   * تا امروز رنگ‌ها هاردکد بودند (`#0f1117`)، پس اگر تلگرامِ مالک لایت باشد
   * اپ مثلِ یک وصلهٔ تیره وسطش می‌نشیند.
   *
   * ⚠️ ناوردیِ باربر: **کلیدِ غایب هرگز نوشته نمی‌شود.** اگر `themeParams`
   * نباشد یا ناقص باشد، پالتِ فعلی بایت‌به‌بایت سرِ جایش می‌ماند. نوشتنِ
   * مقدارِ خالی یعنی متنِ سفید روی زمینهٔ سفید — یعنی صفحهٔ عملاً نامرئی،
   * که بدترین شکلِ «دیده نمی‌شود» است.
   */
  // ⚠️ نام‌ها باید با همان متغیرهایی بخوانند که CSS **واقعاً می‌خواند**.
  // نسخهٔ قبلی به `--card` و `--text` می‌نوشت در حالی که استایل `--surface`
  // و `--ink` را می‌خواند ⇒ رنگ‌های تم داخلِ متغیرهای مرده می‌رفتند و هیچ
  // اثری نداشتند. نوشتنی که خواننده ندارد، با ننوشتن یکی است.
  /* ⚠️⚠️ نگاشتِ تم عمداً **خالی** است. ۲۰۲۶-۰۸-۰۴.
   *
   * این خالی‌بودن، خودِ رفعِ باگ است — نه یک ساده‌سازی.
   *
   * تاریخچه: قبلاً این نگاشت `bg_color→--bg`، `secondary_bg_color→--surface`،
   * `section_bg_color→--surface-2`، `text_color→--ink`، `hint_color→--muted`
   * داشت. `applyTheme` هرکدام را با `setVar` می‌نوشت و `setVar` در app.js
   * `documentElement.style.setProperty` است — یعنی **استایلِ inline**، که در
   * cascade از `:root{}` بالاتر است. پس پالتِ تیرهٔ CSS بی‌صدا بازنویسی می‌شد
   * با هر رنگی که تلگرام گزارش می‌کرد.
   *
   * نتیجه: مالک سه بار گفت «هنوز سفید است» و من سه بار `scheme()` را دارک
   * کردم — که فقط `data-theme` را ست می‌کند و `color-scheme` را، و **هرگز**
   * نمی‌تواند با یک متغیرِ inline بجنگد. سه دورِ کامل روی معلولِ اشتباه.
   *
   * رأیِ مالک: «دارک می‌خواهم · نمی‌خواهم تغییرپذیر باشد». پس تنها طراحیِ
   * درست این است که تم **هیچ** رنگی ندهد. تیرگی هویتِ لوگوست، نه سلیقهٔ
   * لحظه‌ایِ کلاینت. تابع می‌ماند (نه حذف) تا این درز نام‌دار و آزمون‌پذیر
   * بماند و کسی فردا دوباره «کلیدِ کوچکی» به آن اضافه نکند.
   */
  var THEME_MAP = {};

  function _isColor(v) {
    return typeof v === "string" && /^#[0-9a-fA-F]{3,8}$/.test(v.trim());
  }

  function themeVars(tg) {
    var tp = (tg && tg.themeParams) || {};
    var out = {};
    Object.keys(THEME_MAP).forEach(function (k) {
      if (_isColor(tp[k])) { out[THEME_MAP[k]] = tp[k].trim(); }
    });
    return out;   // امروز همیشه {} — و تستی هست که این را قفل می‌کند
  }

  /* ⚠️ در مینی‌اپِ تلگرام، `prefers-color-scheme` **معتبر نیست** — وب‌ویو
   * اغلب «روشن» گزارش می‌دهد حتی وقتی تلگرام دارک است. سیگنالِ معتبر
   * `tg.colorScheme` است. مالک دارک داشت و اپ روشن رندر می‌شد، چون فقط
   * مدیا-کوئری خوانده می‌شد. پیش‌فرض تیره است (هویتِ لوگو). */
  function scheme(tg) {
    // ⚠️ رأیِ صریحِ مالک (۲۰۲۶-۰۸-۰۴): «رنگ کلی دارک باشه». پس تمِ روشنِ
    // تلگرام هم اپ را روشن نمی‌کند — تیرگی بخشی از هویتِ لوگوست (اختاپوسِ
    // کروم روی فضای عمیق)، نه سلیقهٔ لحظه‌ای. قواعدِ خوانایی سرِ جایشان‌اند
    // چون پالتِ تیره خودش کنتراستِ کافی دارد.
    // برگشت: همین تابع را به خواندنِ tg.colorScheme برگردان.
    return "dark";
  }

  function applyScheme(tg, setTheme) {
    var s = scheme(tg);
    if (typeof setTheme === "function") { try { setTheme(s); } catch (e) {} }
    return s;
  }

  function applyTheme(tg, setVar) {
    var vars = themeVars(tg);
    Object.keys(vars).forEach(function (k) { setVar(k, vars[k]); });
    return vars;
  }

  /* ─── شناساییِ قابلیت ──────────────────────────────────────────────────
   * هرگز «نسخه» را نمی‌خوانیم؛ خودِ تابع را می‌سنجیم. نسخه‌سنجی روی
   * کلاینت‌های میانی دروغ می‌گوید، وجودِ تابع نه.
   */
  function capabilities(tg) {
    var has = function (n) { return !!(tg && typeof tg[n] === "function"); };
    return {
      present: !!tg,
      fullscreen: has("requestFullscreen") && has("exitFullscreen"),
      homeScreen: has("addToHomeScreen"),
      events: has("onEvent"),
      insets: !!(tg && (tg.safeAreaInset || tg.contentSafeAreaInset)),
      expand: has("expand"),
      theme: !!(tg && tg.themeParams)
    };
  }

  /* ─── راه‌اندازی ───────────────────────────────────────────────────────
   * hooks: { setVar(name, value), onActive(bool), onFullscreen(bool) }
   * خروجی: گزارشِ آنچه واقعاً وصل شد — تا «سیم‌کشی شد» یک ادعا نباشد.
   */
  function initShell(tg, hooks) {
    hooks = hooks || {};
    var setVar = hooks.setVar || function () {};
    var onActive = hooks.onActive || function () {};
    var onFullscreen = hooks.onFullscreen || function () {};
    var caps = capabilities(tg);
    var wired = [];

    if (!caps.present) {
      // حالتِ dev — بدونِ تلگرام. هیچ استثنایی، صفحه باید کار کند.
      applyInsets(null, setVar);
      // عمداً applyTheme صدا زده نمی‌شود: بی‌تلگرام هیچ رنگی نباید عوض شود.
      return { caps: caps, wired: wired, mode: "dev" };
    }

    // هر فراخوان جدا try می‌شود: یک متدِ نبودهٔ کلاینتِ قدیمی نباید بقیه را
    // با خودش ببرد. (یک try ِ بزرگ = اولین خطا همه‌چیز را خاموش می‌کند.)
    ["ready", "expand"].forEach(function (m) {
      if (typeof tg[m] === "function") {
        try { tg[m](); wired.push(m); } catch (e) { /* بی‌صدا، عمدی */ }
      }
    });

    applyInsets(tg, setVar);
    wired.push("insets");
    applyTheme(tg, setVar);
    applyScheme(tg, hooks.setTheme);
    wired.push("theme");

    if (caps.events) {
      var sub = function (name, fn) {
        try { tg.onEvent(name, fn); wired.push(name); } catch (e) {}
      };
      sub("themeChanged", function () {
        applyTheme(tg, setVar); applyScheme(tg, hooks.setTheme);
      });
      sub("safeAreaChanged", function () { applyInsets(tg, setVar); });
      sub("contentSafeAreaChanged", function () { applyInsets(tg, setVar); });
      sub("fullscreenChanged", function () { onFullscreen(!!tg.isFullscreen); });
      // ⚠️ ارزشِ عملیاتی: وقتی اپ در پس‌زمینه است، poll کردن هم باتری را
      // می‌خورد هم سهمیهٔ API را — بی‌آنکه کسی نتیجه را ببیند.
      sub("activated", function () { onActive(true); });
      sub("deactivated", function () { onActive(false); });
    }

    // وضعِ اولیه: `isActive` ممکن است تعریف نشده باشد ⇒ فرضِ «فعال»
    onActive(tg.isActive === undefined ? true : !!tg.isActive);
    return { caps: caps, wired: wired, mode: "telegram" };
  }

  function toggleFullscreen(tg) {
    var caps = capabilities(tg);
    if (!caps.fullscreen) { return "unsupported"; }
    try {
      if (tg.isFullscreen) { tg.exitFullscreen(); return "exited"; }
      tg.requestFullscreen(); return "requested";
    } catch (e) { return "failed"; }
  }

  function addToHomeScreen(tg) {
    if (!capabilities(tg).homeScreen) { return "unsupported"; }
    try { tg.addToHomeScreen(); return "requested"; }
    catch (e) { return "failed"; }
  }

  return {
    insetVars: insetVars,
    applyInsets: applyInsets,
    themeVars: themeVars,
    applyTheme: applyTheme,
    scheme: scheme,
    applyScheme: applyScheme,
    capabilities: capabilities,
    initShell: initShell,
    toggleFullscreen: toggleFullscreen,
    addToHomeScreen: addToHomeScreen
  };
}));
