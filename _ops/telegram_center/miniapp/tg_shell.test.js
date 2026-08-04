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
