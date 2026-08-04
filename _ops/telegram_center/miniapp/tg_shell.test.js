/* tg_shell.test.js — تستِ **واقعیِ** جاوااسکریپت، نه assert ِ متنی روی سورس.
 *
 * چرا با node و نه با regex: گاردی که فقط دنبالِ رشته در فایل بگردد، از هر
 * جهشِ معنایی رد می‌شود — «تابع صدا زده شد» با «تابع درست کار کرد» یکی نیست.
 * این‌جا یک `WebApp` ِ ساختگی می‌سازیم و **رفتار** را می‌سنجیم.
 *
 * اجرا:  node _ops/telegram_center/miniapp/tg_shell.test.js
 */
"use strict";
const S = require("./tg_shell.js");

let passed = 0;
const failures = [];

function t(name, fn) {
  try { fn(); passed++; console.log("  OK  " + name); }
  catch (e) { failures.push(name); console.log("  FAIL " + name + ": " + e.message); }
}
function eq(a, b, msg) {
  const A = JSON.stringify(a), B = JSON.stringify(b);
  if (A !== B) { throw new Error((msg || "") + " — گرفتم " + A + " انتظار " + B); }
}
function ok(v, msg) { if (!v) { throw new Error(msg || "false بود"); } }

/* یک WebApp ِ ساختگیِ قابل‌تنظیم. عمداً می‌شود قابلیت‌ها را **برداشت**، تا
 * کلاینتِ قدیمی شبیه‌سازی شود. */
function fakeTg(opts) {
  opts = opts || {};
  const calls = [];
  const handlers = {};
  const tg = {
    _calls: calls, _handlers: handlers,
    isFullscreen: !!opts.isFullscreen,
    ready() { calls.push("ready"); },
    expand() { calls.push("expand"); }
  };
  if (opts.isActive !== undefined) { tg.isActive = opts.isActive; }
  if (opts.insets !== false) {
    tg.safeAreaInset = opts.safeAreaInset || { top: 44, bottom: 34, left: 0, right: 0 };
    tg.contentSafeAreaInset = opts.contentSafeAreaInset || { top: 56, bottom: 0, left: 0, right: 0 };
  }
  if (opts.events !== false) {
    tg.onEvent = function (n, fn) { (handlers[n] = handlers[n] || []).push(fn); calls.push("onEvent:" + n); };
  }
  if (opts.fullscreen !== false) {
    tg.requestFullscreen = function () { calls.push("requestFullscreen"); tg.isFullscreen = true; };
    tg.exitFullscreen = function () { calls.push("exitFullscreen"); tg.isFullscreen = false; };
  }
  if (opts.homeScreen !== false) {
    tg.addToHomeScreen = function () { calls.push("addToHomeScreen"); };
  }
  return tg;
}
function fire(tg, name) { (tg._handlers[name] || []).forEach(f => f()); }

/* ── ۱. هرگز نشکن ────────────────────────────────────────────────────── */
t("بدونِ تلگرام (حالتِ dev) استثنا نمی‌دهد", () => {
  const vars = {};
  const r = S.initShell(null, { setVar: (k, v) => { vars[k] = v; } });
  eq(r.mode, "dev");
  eq(vars["--tg-safe-top"], "0px", "‏inset پیش‌فرض صفر نشد");
});

t("کلاینتِ قدیمی (فقط ready/expand) استثنا نمی‌دهد", () => {
  const old = { ready() {}, expand() {} };
  const r = S.initShell(old, {});
  eq(r.caps.fullscreen, false);
  eq(r.caps.homeScreen, false);
  eq(r.caps.events, false);
  ok(r.wired.indexOf("insets") >= 0, "‏inset روی کلاینتِ قدیمی هم باید اعمال شود");
});

t("یک متدِ ترکنده بقیه را با خود نمی‌برد", () => {
  // ⚠️ اگر همه در یک try باشند، اولین خطا کلِ راه‌اندازی را خاموش می‌کند.
  const tg = fakeTg();
  tg.ready = function () { throw new Error("boom"); };
  const r = S.initShell(tg, {});
  ok(r.wired.indexOf("expand") >= 0, "‏expand بعد از ترکیدنِ ready اجرا نشد");
  ok(r.wired.indexOf("insets") >= 0, "‏insets بعد از ترکیدنِ ready اعمال نشد");
});

/* ── ۲. safe-area، همان چیزی که محتوا را از زیرِ نُچ درمی‌آورد ─────────── */
t("هر دو مجموعهٔ inset به CSS می‌روند", () => {
  const v = S.insetVars(fakeTg());
  eq(v["--tg-safe-top"], "44px");
  eq(v["--tg-safe-bottom"], "34px");
  eq(v["--tg-content-safe-top"], "56px", "‏inset ِ کرومِ تلگرام جدا لازم است");
});

t("مقدارِ نامعتبر به صفر می‌افتد نه به NaN", () => {
  // "NaNpx" در CSS یعنی کلِ قاعده دور ریخته می‌شود — یعنی دوباره زیرِ نُچ.
  const v = S.insetVars(fakeTg({ safeAreaInset: { top: "خراب", bottom: -5 } }));
  eq(v["--tg-safe-top"], "0px");
  eq(v["--tg-safe-bottom"], "0px");
});

t("رویدادِ safeAreaChanged دوباره اعمال می‌کند", () => {
  const tg = fakeTg();
  const vars = {};
  S.initShell(tg, { setVar: (k, v) => { vars[k] = v; } });
  eq(vars["--tg-safe-top"], "44px");
  tg.safeAreaInset = { top: 99, bottom: 0, left: 0, right: 0 };
  fire(tg, "safeAreaChanged");
  eq(vars["--tg-safe-top"], "99px", "چرخشِ گوشی inset را به‌روز نکرد");
});

/* ── ۲.۵ تمِ تلگرام ──────────────────────────────────────────────────── */
t("رنگ‌های تم به متغیرهای CSS نگاشت می‌شوند", () => {
  const tg = fakeTg();
  tg.themeParams = { bg_color: "#ffffff", text_color: "#000000",
                     hint_color: "#707579", secondary_bg_color: "#f4f4f5" };
  const v = S.themeVars(tg);
  eq(v["--bg"], "#ffffff");
  eq(v["--ink"], "#000000");
  eq(v["--muted"], "#707579");
  eq(v["--surface"], "#f4f4f5");
});

t("کلیدِ غایب هرگز نوشته نمی‌شود (پالتِ فعلی می‌ماند)", () => {
  // ⚠️ ناوردیِ باربر: نوشتنِ مقدارِ خالی = متنِ سفید روی زمینهٔ سفید =
  // صفحهٔ عملاً نامرئی. بدترین شکلِ «دیده نمی‌شود».
  const tg = fakeTg();
  tg.themeParams = { bg_color: "#ffffff" };
  const v = S.themeVars(tg);
  eq(Object.keys(v), ["--bg"], "کلیدهای غایب هم نوشته شدند");
  ok(!("--ink" in v) && !("--muted" in v));
});

t("مقدارِ نامعتبر رد می‌شود، نه اینکه داخلِ CSS برود", () => {
  const tg = fakeTg();
  tg.themeParams = { bg_color: "خراب", text_color: "", hint_color: null,
                     secondary_bg_color: "#f4f4f5" };
  const v = S.themeVars(tg);
  eq(Object.keys(v), ["--surface"], "مقدارِ بی‌اعتبار وارد شد");
});

t("رنگِ برند از تم اثر نمی‌گیرد", () => {
  // ⚠️ فیروزه‌ای/بنفشِ لوگو هویت است، نه سلیقهٔ تم. اگر تلگرام بتواند
  // عوضشان کند، اپ دیگر شبیهِ اختاپوس نیست. تم فقط زمینه/متن را می‌گیرد.
  const tg = fakeTg();
  tg.themeParams = { link_color: "#ff0000", accent_text_color: "#00ff00",
                     button_color: "#0000ff", bg_color: "#101010" };
  const v = S.themeVars(tg);
  ok(!("--accent" in v), "تم رنگِ برند را دزدید");
  ok(!("--accent-2" in v), "تم رنگِ دومِ برند را دزدید");
  eq(v["--bg"], "#101010", "زمینه باید همچنان از تم بیاید");
});

t("بدونِ تلگرام هیچ رنگی عوض نمی‌شود", () => {
  const written = {};
  S.initShell(null, { setVar: (k, val) => { written[k] = val; } });
  const colorKeys = Object.keys(written).filter(k => !k.startsWith("--tg-"));
  eq(colorKeys, [], "حالتِ dev رنگ نوشت");
});

t("رویدادِ themeChanged دوباره اعمال می‌کند", () => {
  const tg = fakeTg();
  tg.themeParams = { bg_color: "#000000" };
  const written = {};
  S.initShell(tg, { setVar: (k, val) => { written[k] = val; } });
  eq(written["--bg"], "#000000");
  tg.themeParams = { bg_color: "#ffffff" };
  fire(tg, "themeChanged");
  eq(written["--bg"], "#ffffff", "سوییچِ لایت/دارک اعمال نشد");
});

t("‏colorScheme ِ تلگرام بر مدیا-کوئری غلبه می‌کند", () => {
  // ⚠️ باگی که مالک دید: تلگرامش دارک بود و اپ روشن رندر شد. در وب‌ویوِ
  // مینی‌اپ، prefers-color-scheme اغلب «روشن» گزارش می‌دهد. سیگنالِ معتبر
  // tg.colorScheme است.
  // رأیِ صریحِ مالک: همیشه تیره — حتی وقتی تلگرام روشن است. تیرگی هویتِ
  // لوگوست نه سلیقهٔ لحظه‌ای.
  const tg = fakeTg(); tg.colorScheme = "dark";
  let theme = null;
  S.initShell(tg, { setTheme: (t) => { theme = t; } });
  eq(theme, "dark");
  const tg2 = fakeTg(); tg2.colorScheme = "light";
  S.initShell(tg2, { setTheme: (t) => { theme = t; } });
  eq(theme, "dark", "تمِ روشنِ تلگرام نباید اپ را روشن کند");
});

t("‏colorScheme ِ نامعلوم به تیره می‌افتد، نه روشن", () => {
  // پیش‌فرض باید هویتِ لوگو باشد. روشنِ ناخواسته یعنی اپ شسته و بی‌شکل.
  const tg = fakeTg(); delete tg.colorScheme;
  eq(S.scheme(tg), "dark");
  eq(S.scheme(null), "dark");
  tg.colorScheme = "zzz"; eq(S.scheme(tg), "dark");
});

t("نگاشتِ تم به همان متغیرهایی می‌نویسد که CSS می‌خواند", () => {
  // ⚠️ باگِ واقعی: به --card و --text می‌نوشت ولی CSS ِ نو --surface و
  // --ink می‌خواند. نوشتنی که خواننده ندارد، با ننوشتن یکی است.
  const fs = require("fs");
  const css = fs.readFileSync(__dirname + "/style.css", "utf8");
  const tg = fakeTg();
  tg.themeParams = { bg_color:"#111", secondary_bg_color:"#222",
                     section_bg_color:"#333", text_color:"#eee", hint_color:"#999" };
  const v = S.themeVars(tg);
  Object.keys(v).forEach((k) => {
    ok(css.indexOf("var(" + k + ")") >= 0, "‏CSS هرگز " + k + " را نمی‌خواند");
  });
  ok(Object.keys(v).length >= 5, "نگاشت خیلی کم شد");
});

/* ── ۳. فعال/غیرفعال — ارزشِ عملیاتی ─────────────────────────────────── */
t("‏deactivated باعثِ توقف و activated باعثِ ادامه می‌شود", () => {
  const tg = fakeTg({ isActive: true });
  const seen = [];
  S.initShell(tg, { onActive: (b) => seen.push(b) });
  eq(seen, [true], "وضعِ اولیه گزارش نشد");
  fire(tg, "deactivated"); eq(seen, [true, false]);
  fire(tg, "activated");   eq(seen, [true, false, true]);
});

t("‏isActive ِ تعریف‌نشده «فعال» فرض می‌شود نه «خاموش»", () => {
  // وگرنه روی کلاینتی که این فیلد را ندارد، اپ هرگز poll نمی‌کند و
  // داشبورد برای همیشه خالی می‌ماند — یک سکوتِ تازه.
  const tg = fakeTg();
  delete tg.isActive;
  const seen = [];
  S.initShell(tg, { onActive: (b) => seen.push(b) });
  eq(seen, [true]);
});

/* ── ۴. تمام‌صفحه و صفحهٔ اصلی ────────────────────────────────────────── */
t("تمام‌صفحه: درخواست، خروج، و «پشتیبانی‌نشده»", () => {
  const tg = fakeTg();
  eq(S.toggleFullscreen(tg), "requested");
  eq(S.toggleFullscreen(tg), "exited", "بارِ دوم باید خارج شود");
  eq(S.toggleFullscreen(fakeTg({ fullscreen: false })), "unsupported");
  eq(S.toggleFullscreen(null), "unsupported");
});

t("افزودن به صفحهٔ اصلی روی کلاینتِ بی‌پشتیبانی نمی‌ترکد", () => {
  eq(S.addToHomeScreen(fakeTg()), "requested");
  eq(S.addToHomeScreen(fakeTg({ homeScreen: false })), "unsupported");
  eq(S.addToHomeScreen(null), "unsupported");
});

t("‏fullscreenChanged وضع را به UI می‌دهد", () => {
  const tg = fakeTg();
  const seen = [];
  S.initShell(tg, { onFullscreen: (b) => seen.push(b) });
  tg.isFullscreen = true;
  fire(tg, "fullscreenChanged");
  eq(seen, [true]);
});

/* ── ۵. شناسایی، نه فرض ──────────────────────────────────────────────── */
t("قابلیت‌ها از وجودِ **تابع** استنتاج می‌شوند نه از نسخه", () => {
  const src = require("fs").readFileSync(__dirname + "/tg_shell.js", "utf8");
  ok(!/\bversion\b\s*[<>=]/.test(src),
     "نسخه‌سنجی پیدا شد — روی کلاینت‌های میانی دروغ می‌گوید");
  const caps = S.capabilities(fakeTg({ fullscreen: false }));
  eq(caps.fullscreen, false);
  eq(caps.homeScreen, true);
});

t("گزارشِ سیم‌کشی واقعی است نه ادعا", () => {
  const r = S.initShell(fakeTg(), {});
  ["ready", "expand", "insets", "safeAreaChanged", "activated", "deactivated"]
    .forEach(n => ok(r.wired.indexOf(n) >= 0, "وصل نشد: " + n));
});

const total = passed + failures.length;
console.log("\ntg_shell.test: " + passed + "/" + total);
process.exit(failures.length ? 1 : 0);
