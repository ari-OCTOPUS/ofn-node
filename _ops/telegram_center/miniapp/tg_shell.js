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

    if (caps.events) {
      var sub = function (name, fn) {
        try { tg.onEvent(name, fn); wired.push(name); } catch (e) {}
      };
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
    capabilities: capabilities,
    initShell: initShell,
    toggleFullscreen: toggleFullscreen,
    addToHomeScreen: addToHomeScreen
  };
}));
