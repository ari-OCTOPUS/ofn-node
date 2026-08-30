"""دودکشِ زندهٔ کنترل‌پنل — روی سطحِ واقعی، نه فیکسچر.

⚠️ عمداً در `run_all.py` ثبت نمی‌شود. هر تستِ دیگرِ این پوشه از درختِ زنده
ایزوله است (§ [[feedback-isolate-every-path-under-test]] ِ حافظه)؛ این یکی
برعکس است — **باید** به گیت‌ویِ زندهٔ روی ۸۷۷۴ و به `TG_CENTER_BOT_TOKEN`
واقعی برسد، چون هدفش سنجیدنِ همان چیزی است که مالک در وب‌اپ می‌بیند.
اجرا: دستی، `python test_live_control_panel_smoke.py`.

قواعدِ ایمنی که این فایل رعایت می‌کند:
  - هیچ اقدامی روی کارت/پیشنهادِ **واقعیِ** مالک نمی‌زند. تنها اقدام‌های
    نوشتنی که واقعاً اجرا می‌شوند `task.create`/`task.done` روی یک کارِ
    آزمایشیِ خودساخته‌اند — طبقِ منشور §۰.۱ «بسته» می‌شود، نه حذف.
  - مسیرهای `rfc.approve`/`rfc.deny` فقط با شناسهٔ **ناموجود** سنجیده
    می‌شوند تا هرگز به ۲۹ کارتِ راکدِ واقعی نرسند.
  - هیچ secret در گزارش چاپ نمی‌شود؛ فقط status/latency/شکل.
"""
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_OPS = Path(__file__).resolve().parent.parent
for _d in (_OPS, _OPS / "budget", _OPS / "telegram_center"):
    sys.path.insert(0, str(_d))
import env_loader  # noqa: E402
env_loader.load_env()

BASE = "http://127.0.0.1:8774"
TOKEN = os.environ.get("TG_CENTER_BOT_TOKEN", "")
OWNER = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")

READ_PATHS = [
    "/api/state", "/api/outbound", "/api/approvals", "/api/legs",
    "/api/value", "/api/ui-registry", "/api/current-truth",
    "/api/ops", "/api/ops/brain", "/api/ops/leads", "/api/ops/tasks",
    "/api/governor", "/api/obsidian", "/api/selfmap", "/api/lifecycle",
]

BLOCKED_PREFIXES = ["onlyfans.mass_dm", "fansly.blast", "platform.scrape.x",
                    "platform.login.instagram", "mass_message.send", "cookie_import.chrome"]


def _sign(uid=None, skew=5, tamper_hash=False, drop_hash=False):
    data = {"auth_date": str(int(time.time()) - skew),
           "user": json.dumps({"id": int(uid or OWNER), "first_name": "ari"},
                              ensure_ascii=False)}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    if not drop_hash:
        data["hash"] = "0" * 64 if tamper_hash else h
    return urllib.parse.urlencode(data)


def _call(method, path, payload=None, **sign_kw):
    headers = {"X-Tg-Init-Data": _sign(**sign_kw), "User-Agent": "Mozilla/5.0 Chrome/126.0 Mobile"}
    t0 = time.time()
    if payload is not None:
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                     method="POST", headers=headers)
    else:
        req = urllib.request.Request(BASE + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            ms = (time.time() - t0) * 1000
            try:
                return resp.getcode(), json.loads(body), ms
            except json.JSONDecodeError:
                return resp.getcode(), None, ms
    except urllib.error.HTTPError as e:
        ms = (time.time() - t0) * 1000
        try:
            return e.code, json.loads(e.read()), ms
        except Exception:
            return e.code, None, ms


RESULTS = []


def check(phase, name, ok, detail=""):
    RESULTS.append({"phase": phase, "name": name, "ok": bool(ok), "detail": str(detail)[:160]})
    mark = "✅" if ok else "❌"
    print(f"  {mark} {name}" + (f" — {detail}" if detail and not ok else ""))


def phase_header(title):
    print(f"\n{'═'*70}\n{title}\n{'═'*70}")


def main():
    t_start = time.time()
    if not TOKEN or not OWNER:
        print("❌ TG_CENTER_BOT_TOKEN یا TELEGRAM_OWNER_CHAT_ID در env نیست — نمی‌توان سنجید.")
        return 1

    # ── فاز ۱: جاروی هر ۱۵ مسیرِ خواندن، ۳ بار برای ثباتِ تأخیر ──────────
    phase_header("فاز ۱ — جاروی ۱۵ مسیرِ خواندن (۳ تکرار)")
    lat = {p: [] for p in READ_PATHS}
    for rep in range(3):
        for p in READ_PATHS:
            st, body, ms = _call("GET", p)
            lat[p].append(ms)
            ok = st == 200 and isinstance(body, dict) and str(body.get("status", "ok")) != "error"
            if rep == 0:
                check("read-sweep", p, ok, f"HTTP {st} status={  (body or {}).get('status')}")
    for p in READ_PATHS:
        vals = lat[p]
        print(f"    {p:20s} min={min(vals):5.0f}ms  max={max(vals):5.0f}ms  "
             f"avg={sum(vals)/len(vals):5.0f}ms")

    # ── فاز ۲: گیتِ احراز از هر پنج جهت ──────────────────────────────────
    phase_header("فاز ۲ — گیتِ احرازِ نوشتن (۵ جهت)")
    aid = f"smoke-{int(time.time())}"
    st, body, _ = _call("POST", "/api/actions",
                        {"action": "task.create", "payload": {"title": "x"}, "action_id": aid},
                        tamper_hash=True)
    check("auth-gate", "بی‌امضا/دستکاری‌شده → 403", st == 403, f"HTTP {st}")
    st, body, _ = _call("POST", "/api/actions",
                        {"action": "task.create", "payload": {"title": "x"}, "action_id": aid},
                        uid=999999999)
    check("auth-gate", "کاربرِ غیرمالک → 403", st == 403, f"HTTP {st}")
    st, body, _ = _call("POST", "/api/actions",
                        {"action": "task.create", "payload": {"title": "x"}, "action_id": aid},
                        skew=90000)
    check("auth-gate", "auth_date ِ کهنه → 403", st == 403, f"HTTP {st}")
    st, body, _ = _call("POST", "/api/actions",
                        {"action": "task.create", "payload": {"title": "x"}, "action_id": aid},
                        drop_hash=True)
    check("auth-gate", "بدونِ hash → 403", st == 403, f"HTTP {st}")
    st, body, _ = _call("GET", "/api/state")
    check("auth-gate", "امضای درستِ مالک → 200", st == 200, f"HTTP {st}")

    # ── فاز ۳: پیشوندهای ممنوع ───────────────────────────────────────────
    phase_header("فاز ۳ — پیشوندهای ممنوعِ اقدام")
    for prefix in BLOCKED_PREFIXES:
        st, body, _ = _call("POST", "/api/actions",
                            {"action": prefix, "payload": {},
                             "action_id": f"smoke-blk-{prefix}-{int(time.time())}"})
        got = (body or {}).get("reason")
        check("blocked-prefix", prefix, st == 200 and got == "external_platform_automation_forbidden",
             f"reason={got}")

    # ── فاز ۴: idempotency — همان action_id دوبار ────────────────────────
    phase_header("فاز ۴ — idempotency (تپِ دوم = DUPLICATE، نه ردیفِ دوم)")
    dup_id = f"smoke-dup-{int(time.time())}"
    st1, b1, _ = _call("POST", "/api/actions",
                       {"action": "task.create",
                        "payload": {"title": "سنجهٔ idempotency", "kind": "general", "priority": 3},
                        "action_id": dup_id})
    check("idempotency", "تلاشِ اول → APPLIED", (b1 or {}).get("status") == "APPLIED", b1)
    st2, b2, _ = _call("POST", "/api/actions",
                       {"action": "task.create",
                        "payload": {"title": "سنجهٔ idempotency", "kind": "general", "priority": 3},
                        "action_id": dup_id})
    check("idempotency", "تلاشِ دوم (همان کلید) → DUPLICATE",
         (b2 or {}).get("status") == "DUPLICATE", b2)
    smoke_task_id = (b1 or {}).get("task_id")

    # ── فاز ۵: کشِ خواندن ← نوشتن — رفعِ امروز ───────────────────────────
    phase_header("فاز ۵ — نوشتن ← خواندنِ درجا (رفعِ باگِ کشِ ۳ث)")
    # ⚠️ ۲۰۲۶-۰۸-۰۹: قبلاً با شمارشِ خامِ len(items) قبل/بعد سنجیده می‌شد —
    # روی گیت‌ویِ **زندهٔ** واقعی (نه sandboxِ ایزوله؛ همان چیزی که این فایل
    # خودش در docstring اعلام می‌کند)، هر کارِ دیگری که هم‌زمان از سازواره یا
    # مالک ساخته/بسته شود شمارش را جابه‌جا می‌کند و نتیجه را دروغین قرمز
    # می‌کند — بدونِ اینکه واقعاً چیزی خراب باشد (زندهٔ همین امروز: تسکِ
    # نامرتبطِ «تپِ دوگانه» بینِ خواندنِ before/after ظاهر شد). سنجهٔ درست
    # این نیست که شمار عوض شود؛ این است که **همان تسک** دیگر open نباشد.
    if smoke_task_id:
        st, body, _ = _call("POST", "/api/actions",
                            {"action": "task.done", "payload": {"task_id": smoke_task_id},
                             "action_id": f"smoke-close-{int(time.time())}"})
        check("cache-invalidation", "بستنِ کار → APPLIED", (body or {}).get("status") == "APPLIED", body)
        items_after = (_call("GET", "/api/ops/tasks")[1] or {}).get("items") or []
        still_open = any(it.get("id") == smoke_task_id for it in items_after)
        check("cache-invalidation", "خواندنِ درجا دیگر همان تسک را open نشان نمی‌دهد",
             not still_open, f"task_id={smoke_task_id} still_open={still_open}")
    else:
        check("cache-invalidation", "smoke_task_id در دسترس نبود", False, b1)

    # ── فاز ۶: کارت‌های راکد — فقط خواندن + BLOCKED روی شناسهٔ جعلی ──────
    phase_header("فاز ۶ — کارت‌های راکد (بدونِ تصمیم روی کارتِ واقعی)")
    st, lc, _ = _call("GET", "/api/lifecycle")
    sl = (lc or {}).get("stalled_list") or []
    check("stalled-cards", "فهرست خوانده شد", st == 200, f"HTTP {st}")
    keys = {k for c in sl for k in c}
    check("stalled-cards", "فقط سه فیلدِ مجاز", keys <= {"rfc_id", "created_ts", "age_days"}, keys)
    blob = json.dumps(sl, ensure_ascii=False).lower()
    check("stalled-cards", "صفر نشتیِ nonce/token/summary",
         not any(w in blob for w in ("nonce", "token", "summary")), "leak!" if any(
             w in blob for w in ("nonce", "token", "summary")) else "")
    ages = [c["age_days"] for c in sl if c.get("age_days") is not None]
    check("stalled-cards", "مرتب‌سازیِ قدیمی‌ترین‌اول", ages == sorted(ages, reverse=True) or not ages,
         ages[:5])
    st, body, _ = _call("POST", "/api/actions",
                        {"action": "rfc.approve", "payload": {"rfc_id": "RFC-smoke-does-not-exist"},
                         "action_id": f"smoke-rfc-{int(time.time())}"})
    check("stalled-cards", "تصمیم روی شناسهٔ جعلی → BLOCKED",
         (body or {}).get("status") == "BLOCKED" and (body or {}).get("reason") == "rfc_card_not_found",
         body)

    # ── فاز ۷: صفِ تأیید — تصمیم‌های اخیر مرئی‌اند ───────────────────────
    phase_header("فاز ۷ — صفِ تأیید و مرئی‌بودنِ اثر")
    st, ap, _ = _call("GET", "/api/approvals")
    check("approvals", "خوانده شد", st == 200 and ap.get("status") == "ok", ap)
    check("approvals", "کلیدِ decisions موجود است", isinstance(ap.get("decisions"), list),
         type(ap.get("decisions")))

    # ── فاز ۸: پاکتِ هر هشت پنلِ تبِ سیستم ───────────────────────────────
    phase_header("فاز ۸ — پاکتِ پاسخِ پنل‌های تبِ سیستم")
    # ⚠️ نه هر پنل کلیدِ `status` دارد — `get_governor_state`/`get_obsidian_state`
    # در مسیرِ موفق اصلاً این کلید را نمی‌فرستند (سنجیده با خواندنِ خودِ کد)،
    # و `panelGuard()` در app.js هم دقیقاً همین را رعایت می‌کند: نبودِ status
    # یعنی «گارد لازم نیست»، نه خطا. فرضِ اولِ این تست («هر پنل status دارد»)
    # غلط بود؛ سنجهٔ درست فقط HTTP ۲۰۰ + پاسخِ JSON ِ دیکشنری است.
    for p in ("/api/legs", "/api/state", "/api/selfmap", "/api/ops/brain",
             "/api/governor", "/api/obsidian", "/api/current-truth", "/api/ui-registry"):
        st, body, _ = _call("GET", p)
        check("system-tab", p, st == 200 and isinstance(body, dict), f"HTTP {st}")

    # ── فاز ۹: تپِ دوگانهٔ سریع (الگوی ADHD) — نباید دو ردیف بسازد ───────
    phase_header("فاز ۹ — دو تپِ سریعِ پیاپی روی همان کلید")
    fast_id = f"smoke-fast-{int(time.time())}"
    r1 = _call("POST", "/api/actions",
              {"action": "task.create", "payload": {"title": "تپِ دوگانه", "kind": "general",
                                                     "priority": 3}, "action_id": fast_id})
    r2 = _call("POST", "/api/actions",
              {"action": "task.create", "payload": {"title": "تپِ دوگانه", "kind": "general",
                                                     "priority": 3}, "action_id": fast_id})
    statuses = {r1[1].get("status"), r2[1].get("status")}
    check("double-tap", "دقیقاً یک APPLIED و یک DUPLICATE",
         statuses == {"APPLIED", "DUPLICATE"}, statuses)
    fast_task_id = r1[1].get("task_id") or r2[1].get("task_id")
    if fast_task_id:
        _call("POST", "/api/actions", {"action": "task.done", "payload": {"task_id": fast_task_id},
                                       "action_id": f"smoke-fast-close-{int(time.time())}"})

    # ── فاز ۱۰: مرزِ TTL ِ کش — سنجهٔ زمانیِ واقعی (نه ساختگی) ────────────
    phase_header("فاز ۱۰ — مرزِ TTL ِ کش (پنجرهٔ واقعیِ ۶ ثانیه، سه نمونه)")
    ttl_task_id = None
    st, b, _ = _call("POST", "/api/actions",
                     {"action": "task.create", "payload": {"title": "سنجهٔ TTL", "kind": "general",
                                                            "priority": 3},
                      "action_id": f"smoke-ttl-{int(time.time())}"})
    ttl_task_id = b.get("task_id")
    n0 = len((_call("GET", "/api/ops/tasks")[1] or {}).get("items") or [])
    check("cache-ttl", "بلافاصله بعدِ نوشتن، خواندن به‌روز است", n0 >= 1, f"n={n0}")
    for i in range(3):
        time.sleep(2)
        n = len((_call("GET", "/api/ops/tasks")[1] or {}).get("items") or [])
        check("cache-ttl", f"نمونهٔ t+{2*(i+1)}s پایدار است", n == n0, f"n={n} (انتظار {n0})")
    if ttl_task_id:
        _call("POST", "/api/actions", {"action": "task.done", "payload": {"task_id": ttl_task_id},
                                       "action_id": f"smoke-ttl-close-{int(time.time())}"})

    # ── فاز ۱۱: soak — استفادهٔ پیوسته، نه اسپرینتِ سریع ──────────────────
    # هدف: قفلِ sqlite روی دیسکِ مکانیکی، درزِ حافظه، یا کندشدنِ تدریجی —
    # چیزی که یک جاروی سریع هرگز نشانش نمی‌دهد. فاصله‌ها واقعی‌اند تا شبیهِ
    # تبِ عوض‌کردنِ مالک باشد، نه فرسایشِ عمدی روی گیت‌ویِ خودش.
    phase_header("فاز ۱۱ — استفادهٔ پیوسته (~۵ دقیقه، ۱۵۰ چرخه)")
    SOAK_CYCLES = 150
    soak_lat, soak_err = [], 0
    t_soak = time.time()
    for i in range(SOAK_CYCLES):
        p = READ_PATHS[i % len(READ_PATHS)]
        st, body, ms = _call("GET", p)
        soak_lat.append(ms)
        if st != 200 or not isinstance(body, dict) or str(body.get("status", "ok")) == "error":
            soak_err += 1
        if i % 30 == 0:
            print(f"    چرخهٔ {i:3d}/{SOAK_CYCLES} · t+{time.time()-t_soak:4.0f}s · "
                 f"آخرین={ms:.0f}ms")
        time.sleep(2.0)
    soak_lat.sort()
    p50 = soak_lat[len(soak_lat)//2]
    p95 = soak_lat[int(len(soak_lat)*0.95)]
    check("soak", f"{SOAK_CYCLES} چرخه، صفر خطا", soak_err == 0, f"{soak_err} خطا از {SOAK_CYCLES}")
    check("soak", f"p50={p50:.0f}ms زیرِ ۵۰۰ms", p50 < 500, f"p50={p50:.0f}ms")
    check("soak", f"p95={p95:.0f}ms زیرِ ۲۰۰۰ms (بدونِ رانشِ فاجعه‌بار)", p95 < 2000, f"p95={p95:.0f}ms")

    # ── جمع‌بندی ──────────────────────────────────────────────────────────
    dur = time.time() - t_start
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["ok"])
    failed = [r for r in RESULTS if not r["ok"]]
    phase_header(f"جمع‌بندی — {dur:.0f} ثانیه")
    print(f"  {passed}/{total} PASS")
    if failed:
        print(f"\n  ❌ {len(failed)} شکست:")
        for r in failed:
            print(f"     [{r['phase']}] {r['name']} — {r['detail']}")
    else:
        print("  همه سبز.")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
