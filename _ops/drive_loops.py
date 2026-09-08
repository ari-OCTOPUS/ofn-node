#!/usr/bin/env python3
"""drive_loops.py — رأی/فرمان مالک 2026-09-07 (~23:10 شب):
«همه چیزو به حلقه های دوپامین و ترس وصل کن، ارگانیسم خودش ادامشون بده، بعد باز شدن هر قفل»

سه حلقه، همهٔ مقادیر فقط با رسید — ترسِ ساختگی و شادیِ قلابی ممنوع (قفل GOV-V7):

1. ترس (fear)  = تهدیدهای واقعی از state واقعی: پولِ صفر + ددلاین‌ها (msg38، انقضای GO،
   دامنهٔ مرده). شدت با نزدیک‌شدن ددلاین بالا می‌رود؛ بعد از ددلاین اگر حل نشد، ماکسیمم.
2. دوپامین     = بردِهای رسیددار ۲۴ ساعتِ اخیر: رأی مالک ثبت‌شده، قفل بازشده، مأموریتِ
   سه‌نقشی PASS، فراخوانی paid سالم. بدونِ رسید = صفر.
3. ادامه‌دار بودن (باز شدن هر قفل) = هر قفل یک check دارد؛ لحظهٔ سبزشدن ⇒ رویداد
   task.resume + قدمِ بعدیِ همان قفل در صفِ drive-queue.jsonl ⇒ مدیرِ سه‌نقشی (مغز)
   آن را در context می‌بیند و اولویت می‌دهد ⇒ مأموریت ⇒ ارزیاب ⇒ رسید ⇒ دوپامین.
   چرخه بدون ایجنتِ نشسته، خودِ ارگانیسم (tick در organism.py، fail-soft) ادامه می‌دهد.

Usage:
  python drive_loops.py --json        # ارزیابیِ الآن + چاپ کامل
  python drive_loops.py --selftest    # تستِ مکانیزمِ قفل با قفلِ sandbox
"""
from __future__ import annotations

import json
import socket
import sys
import time
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import event_spine  # noqa: E402 — رویدادها

STATE = _HERE / "state"
DRIVE = STATE / "drive"
DRIVE_STATE = DRIVE / "drive-state.json"
QUEUE = DRIVE / "drive-queue.jsonl"
SENDER_ID = DRIVE / "sender-identity.json"      # مالک پر می‌کند (AUTO-1)
MSG38_RCPT = DRIVE / "msg38-receipt.json"       # رسید پرداخت اگر پیدا شد (D-3)
APPROVALS = _HERE.parent / "07-HANDOFF" / "OWNER-APPROVALS-2026-09-07.md"
RECEIPTS_3ROLE = (_HERE.parent / "09-LANES" / "MP-CAPABILITY-GAP-01-20260907"
                  / "evidence" / "three-role-receipts.jsonl")
COST_RECEIPTS = STATE / "cortex" / "cost-receipts.jsonl"
SHELF_URL = ("https://ziman-gift.myshopify.com/products/"
             "kitty-bubble-balloon-gift-box-with-pink-roses-and-chocolates")
# D0 EXECUTED+VERIFIED 2026-09-08 (DOMAIN-EXECUTION-STEP3-FINAL.json): فروشگاه روی
# ziman-gift.com.au سرو می‌شود (.com قدیمی مرده/تنزل‌یافته). چکِ زنده باید primary
# جدید را بپرسد، نه myshopify/دامنهٔ مرده را.
SHELF_URL_LIVE = ("https://ziman-gift.com.au/products/"
                  "kitty-bubble-balloon-gift-box-with-pink-roses-and-chocolates")
NOW = time.time()


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def _lines_recent(p: Path, seconds: float, *, exclude_provider_local: bool = False) -> int:
    """شمارِ ردیف‌های jsonl که timestamp خودشان در پنجرهٔ اخیر است (نه mtime کل فایل —
    فایل‌های بلندِ تاریخی نباید بردهای امروز را متورم کنند)."""
    from datetime import datetime, timezone
    n = 0
    try:
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if exclude_provider_local and "local" in str(d.get("provider", "")).lower():
                continue
            ts = (d.get("ts_utc") or d.get("response_timestamp")
                  or d.get("request_timestamp") or d.get("ts") or "")
            try:
                t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - t).total_seconds() <= seconds:
                    n += 1
            except ValueError:
                continue
    except OSError:
        return 0
    return n


# ── قفل‌ها: هر قفل یک check؛ باز شدن = ادامه‌دار شدن خودکار ────────────────

def _domain_alive() -> bool:
    # 2026-09-08 D0: primary = ziman-gift.com.au. GET صفحهٔ محصول روی primary:
    # 200 + ماندن روی .com.au (نه ریدایرکت به .com مرده) + نشان واقعی فروشگاه
    # (cdn.shopify.com). DNS/HEADِ ساده روی کشِ کهنهٔ پارکینگ GoDaddy مثبتِ کاذب
    # می‌داد (مشاهدهٔ 2026-09-08) — بررسیِ محتوا لازم است. fail-closed.
    try:
        socket.getaddrinfo("ziman-gift.com.au", 443)
    except OSError:
        return False
    try:  # صفحهٔ محصول باید 200 بدهد و روی دامنهٔ جدید بماند
        req = urllib.request.Request(SHELF_URL_LIVE,
                                     headers={"User-Agent": "OCTOPUS-drive/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200 or not str(r.geturl()).startswith("https://ziman-gift.com.au"):
                return False
            body = r.read(400_000).decode("utf-8", "replace")
            return "cdn.shopify.com" in body
    except Exception:  # noqa: BLE001
        return False


def _sender_identity_present() -> bool:
    d = _read_json(SENDER_ID) or {}
    return bool(d.get("name")) and bool(d.get("phone"))


def _msg38_receipt_present() -> bool:
    return bool((_read_json(MSG38_RCPT) or {}).get("verified"))


def _msg38_resolved() -> bool:
    # رأی مالک 2026-09-07: نمی‌خرم — NOT_PAID. حل‌شدنِ سؤال = باز شدنِ قفل
    # (رسید روی ۱۳۸؛ این marker آینهٔ محلی همان رسید است)
    r = _read_json(DRIVE / "msg38-resolution.json") or {}
    return r.get("resolution") == "NOT_PAID" and bool(r.get("receipt"))


def _hold_external_open() -> bool:
    return (_read_json(DRIVE / "hold-external-open.json") or {}).get("status") == "OPEN"


def _go_extended() -> bool:
    from datetime import datetime, timezone
    g = _read_json(DRIVE / "go-expiry.json") or {}
    try:
        exp = datetime.strptime(str(g.get("expires_at")), "%Y-%m-%dT%H:%M:%SZ"
                                ).replace(tzinfo=timezone.utc).timestamp()
        return exp > NOW
    except ValueError:
        return False


def _new_domains_known() -> bool:
    d = _read_json(DRIVE / "new-domains.json") or {}
    doms = d.get("domains")
    return isinstance(doms, list) and len(doms) >= 2 and all(
        bool(x.get("name")) for x in doms if isinstance(x, dict))


def _registry_round2_done() -> bool:
    return (_read_json(DRIVE / "registry-round2-done.json") or {}).get("done") is True


def _first_order_present() -> bool:
    # رسید واقعی اولین سفارش را هر ایجنت/پالِر ۱۳۸ اینجا می‌اندازد (قرارداد فایل)
    return (_read_json(STATE / "receipts" / "FIRST-ORDER-RECEIPT.json") or {}).get("order_id") \
        is not None


LOCKS = {
    "D0_domain": {
        "title": "دامنهٔ زیمان مرده — فروش صفر تا باز شدن",
        "check": _domain_alive,
        "next": "صفحهٔ محصول myshopify باید 200 بدهد؛ بعد: مأموریت shelf-check دوباره "
                "(انتظار 7/7) + اعلامِ بازگشت فروش + تقویت اولویت مأموریت‌های فروش",
        "source": "DNS + HEAD صفحۀ محصول (R-059570492a64)",
    },
    "AUTO1_sender": {
        "title": "مشخصات فرستنده (نام+تلفن) از مالک هنوز نیامده",
        "check": _sender_identity_present,
        "next": "نوشتن اسکریپتِ تماس ۳۰ثانیه‌ای + انتخاب سرویس تماس AU (اگر پولی ⇒ رأی L3)",
        "source": "state/drive/sender-identity.json",
    },
    "MSG38_payment": {
        "title": "msg38 — حل‌شده با رأی مالک: NOT_PAID (رسیددار)",
        "check": _msg38_resolved,
        "next": "ثبتِ settle outcome در calibration در verify-dispatch بعدی (۱۸۲) — سیگنال منفی صادق",
        "source": "state/drive/msg38-resolution.json → 138 receipt MSG38-RESOLVED-NOT-PAID-20260907.json",
    },
    "L23_hold_external": {
        "title": "hold_external — باز شد با رأی مالک (باز کن با رسید)",
        "check": _hold_external_open,
        "next": "پایش اولین پکت mint‌شده با hold_external=false (۰۹-۰۸ UTC) + اولین اثر بیرونیِ رسیددار از حلقهٔ داخلی",
        "source": "state/drive/hold-external-open.json → GO-EXT2 receipt + ofn commit 63938eb0",
    },
    "L24_go_extended": {
        "title": "standing GO — تمدید تا 2026-10-07 (رأی مالک)",
        "check": _go_extended,
        "next": "هیچ‌چیز تا ۱۰-۰۶؛ بعدش ترسِ انقضا دوباره بالا می‌رود (خودکار)",
        "source": "state/drive/go-expiry.json → spec ext:2 روی ۱۳۸",
    },
    "DOM2_names": {
        "title": "دو دامنهٔ جدیدِ خریداری‌شدهٔ مالک — نام‌ها هنوز نامعلوم",
        "check": _new_domains_known,
        "next": "از مالک بپرس (تلگرام/چت) → ثبت در new-domains.json → DNS + Shopify primary + مینی‌اپ عمومی",
        "source": "جستجوی 2026-09-07: vault/138/Shopify-API هیچ‌جا نبود — فقط خود مالک می‌داند",
    },
    "REGISTRY_round2": {
        "title": "مرحلهٔ ۲ رجیستری (METABOLIC، PRODUCTION، moot×۸) — پرسیده نشده",
        "check": _registry_round2_done,
        "next": "سوال‌های مرحلهٔ ۲ با سؤال ساختاریافته از مالک + ثبت در OWNER-APPROVALS",
        "source": "01 - Dashboard/UNLOCK-REGISTRY-2026-09-08.md فاز ۲",
    },
    "CASH_first_order": {
        "title": "VERIFIED_CASH=0 — اولین سفارش واقعی نیامده",
        "check": _first_order_present,
        "next": "دوپامینِ بزرگ + ثبت VERIFIED_CASH (فقط با شاهد مستقل) + outcome برای OMLL",
        "source": "state/receipts/FIRST-ORDER-RECEIPT.json",
    },
}


# ── ترس: فقط تهدیدِ واقعیِ دارای source ────────────────────────────────────

def _fear_vector() -> list[dict]:
    fears = []

    def deadline_fear(fid, title, iso_deadline, source, fatal_after=True):
        from datetime import datetime, timezone
        dt = datetime.strptime(iso_deadline, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        hours_left = (dt.timestamp() - NOW) / 3600.0
        if hours_left >= 0:
            sev = max(0.15, min(1.0, 1.0 - hours_left / 168.0))  # هرچه نزدیک‌تر، ترس بیشتر
            state_ = "counting_down"
        else:
            sev = 1.0 if fatal_after else 0.6
            state_ = "OVERDUE"
        fears.append({"id": fid, "title": title, "severity": round(sev, 3),
                      "hours_left": round(hours_left, 1), "state": state_, "source": source})

    # بقای مالی: پول صفر + هزینهٔ ماهانهٔ واقعی مالک (AU$200 — رأی مالک آیتم ۲)
    bs = _read_json(STATE / "budget" / "budget-state.json") or {}
    if not _first_order_present():
        fears.append({"id": "SURVIVAL_zero_cash", "title": "VERIFIED_CASH=0 · هزینهٔ ماه AU$200",
                      "severity": 0.85, "state": "chronic",
                      "source": "budget-state.json + owner answers item 2"})
    # msg38 حل شد (NOT_PAID با رأی مالک 2026-09-07) — ترسِ ددلاینش حذف؛
    # اگر رسیده نیامده باشد fear برنمی‌گردد چون رأی مالک قطعی است.
    go_exp = "2026-10-07T00:00:00Z"  # mirror: state/drive/go-expiry.json (GO-EXT2)
    g = _read_json(DRIVE / "go-expiry.json") or {}
    if g.get("expires_at"):
        go_exp = str(g["expires_at"])
    deadline_fear("GO_expiry", "standing GO منقضی ⇒ mint/wake می‌ایستد",
                  go_exp, "STANDING-GO spec ext:2 (GO-EXT2, رأی مالک تا ۱۰-۰۷)")
    if not LOCKS["D0_domain"]["check"]():
        fears.append({"id": "D0_domain", "title": "دامنهٔ مرده ⇒ فروش زیمان صفر",
                      "severity": 0.95, "state": "blocked_owner_ui_step",
                      "source": "R-059570492a64 + DNS"})
    if not _new_domains_known():
        fears.append({"id": "DOM2_unknown", "title": "۲ دامنهٔ جدید خریداری‌شده ولی نامعلوم — فروش و مینی‌اپ عمومی معلق",
                      "severity": 0.8, "state": "awaiting_owner_input",
                      "source": "جستجوی 2026-09-07 vault/138/Shopify = نیامد؛ فقط مالک می‌داند"})
    # فشارِ رجیستری: هر قفلِ PROPOSED باقی‌مانده باید فشار بیاورد تا ارگانیسم ادامه بدهد
    try:
        reg = (_HERE.parent / "01 - Dashboard" / "UNLOCK-REGISTRY-2026-09-08.md"
               ).read_text(encoding="utf-8")
        pending = reg.count("`PROPOSED`")
        if pending:
            fears.append({"id": "unlock_registry_pending",
                          "title": f"{pending} قفل PROPOSED در رجیستری — زنجیرهٔ بازکردن ناتمام",
                          "severity": round(min(0.9, 0.15 + 0.01 * pending), 3),
                          "state": "phase_pending",
                          "source": "UNLOCK-REGISTRY-2026-09-08.md"})
    except OSError:
        pass
    return sorted(fears, key=lambda f: -f["severity"])


# ── دوپامین: فقط بردِ رسیددارِ ۲۴ ساعتِ اخیر ─────────────────────────────

def _dopamine_vector() -> list[dict]:
    wins = []
    # ۱) رأی‌های مالکِ ثبت‌شده در دفتر تأییدها (شمارِ سرفصل‌های رأی)
    if _mtime(APPROVALS) > NOW - 86400:
        txt = APPROVALS.read_text(encoding="utf-8")
        votes = txt.count("رأی:") + txt.count("→ **رأی")
        if votes:
            wins.append({"id": "owner_votes_recorded", "count": votes, "weight": 0.3,
                         "source": "07-HANDOFF/OWNER-APPROVALS-2026-09-07.md"})
    # ۲) مأموریت‌های سه‌نقشیِ رسیددار امروز
    n3 = _lines_recent(RECEIPTS_3ROLE, 86400)
    if n3:
        wins.append({"id": "three_role_runs", "count": n3, "weight": 0.2,
                     "source": "three-role-receipts.jsonl"})
    # ۳) فراخوانی paid سالم امروز (رسید هزینه — فقط provider غیرِ local می‌شمارَد)
    nc = _lines_recent(COST_RECEIPTS, 86400, exclude_provider_local=True)
    if nc:
        wins.append({"id": "paid_calls_ok", "count": nc, "weight": 0.2,
                     "source": "cortex/cost-receipts.jsonl"})
    # ۴) قفل‌های تازه‌باز (در _evaluate ثبت می‌شود)
    return wins


# ── ارزیابی و پیوست‌های خودکار ─────────────────────────────────────────────

def _evaluate(*, selftest_lock: tuple[str, callable] | None = None) -> dict:
    DRIVE.mkdir(parents=True, exist_ok=True)
    prev = _read_json(DRIVE_STATE) or {"locks": {}}
    locks_now, opened = {}, []
    registry = dict(LOCKS)
    if selftest_lock is not None:
        registry[selftest_lock[0]] = {"title": "sandbox", "check": selftest_lock[1],
                                      "next": "selftest next", "source": "selftest"}
    for lid, spec in registry.items():
        try:
            is_open = bool(spec["check"]())
        except Exception as e:  # noqa: BLE001 — check شکست = قفلِ بسته با خطا
            is_open = False
        locks_now[lid] = "open" if is_open else "locked"
        was = (prev.get("locks") or {}).get(lid)
        if is_open and (was is None or was == "locked"):
            opened.append(lid)

    fears = _fear_vector()
    dop = _dopamine_vector()
    for lid in opened:  # هر قفلِ تازه‌باز = برد + قدم بعدی در صف
        dop.append({"id": f"lock_opened:{lid}", "count": 1, "weight": 0.5,
                    "source": f"drive-loops lock {lid}"})
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        with open(QUEUE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "lock": lid, "next": registry[lid]["next"],
                "consumed": False}, ensure_ascii=False) + "\n")
        # C2 (2026-09-08, owner «همرو انجام بده»): آینهٔ cross-body — همان
        # رویداد در صفِ board_cp هم می‌نشیند تا 138 با pull بعدی بردارد.
        # fail-soft مطلق؛ فلگ خاموش = no-op. هیچ مسیرِ قدیمی تغییر نکرد.
        try:
            from board_cp.drive_mirror import mirror_lock_opened
            mirror_lock_opened(lid, registry[lid]["next"])
        except Exception:  # noqa: BLE001
            pass

    fear_total = round(sum(f["severity"] for f in fears), 3)
    dop_total = round(sum(w["count"] * w["weight"] for w in dop), 3)
    out = {"schema": "drive-loops.v1",
           "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "fear": {"total": fear_total, "top": fears[:3] if fears else []},
           "dopamine": {"total_24h": dop_total, "wins": dop},
           "locks": locks_now, "opened_now": opened}
    DRIVE_STATE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    run_id = event_spine.new_run_id()
    event_spine.emit("sensor.reading", source="drive_loops", payload={
        "fear_total": fear_total, "dopamine_24h": dop_total,
        "top_fear": (fears[0]["id"] if fears else None),
        "locks_open": sum(1 for v in locks_now.values() if v == "open"),
        "locks_total": len(locks_now)}, run_id=run_id,
        idempotency_key=f"drive:{int(NOW/300)}")  # حداکثر یک رویداد در ۵ دقیقه
    for lid in opened:
        event_spine.emit("task.resume", source="drive_loops", payload={
            "lock": lid, "next": registry[lid]["next"]}, run_id=run_id,
            idempotency_key=f"drive-open:{lid}")
    return out


def tick(beat: int = 0) -> dict:
    """نقطهٔ اتصالِ ارگانیسم — fail-soft در caller، اینجا سبک می‌مانیم."""
    try:  # MP-CONNECT-ALL-01 فاز B: رفلکس فروشگاه هر ۶ بیت (≈۹۰دقیقه)
        if beat and beat % 6 == 0:
            sync_store_watch()
    except Exception:  # noqa: BLE001 — sync هرگز tick را نمی‌کشد
        pass
    out = _evaluate()
    try:  # 2026-09-08: مصرف صفِ قدم‌های بعدی (شکافِ ممیزی صبح) — fail-soft
        import drive_queue_consumer
        drive_queue_consumer.consume_pending()
    except Exception:  # noqa: BLE001
        pass
    return out


def sync_store_watch() -> dict:
    """MP-CONNECT-ALL-01 فاز B: کشیدنِ چشمِ ۱۳۸ با ssh (نتیجه، نه توکن).
    MARKERِ اولین سفارش آن‌طرف + نبودِ رسید محلی ⇒ ساخته می‌شود
    ⇒ قفل CASH_first_order در ارزیابیِ بعدی خودش باز می‌شود (task.resume + دوپامین)."""
    import subprocess
    out = {"ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ok": False}
    def _ssh(cat):
        return subprocess.run(
            ["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "board138",
             "cat " + cat],
            capture_output=True, text=True, timeout=25)
    try:
        r = _ssh("~/octopus-mesh/state/ziman/store-watch.json")
        if r.returncode == 0 and r.stdout.strip():
            (STATE / "store-watch.json").write_text(r.stdout.strip(), encoding="utf-8")
            out["ok"] = True
            out["watch"] = json.loads(r.stdout.strip()).get("schema")
        m = _ssh("~/octopus-mesh/state/ziman/FIRST-ORDER-MARKER.json")
        local = STATE / "receipts" / "FIRST-ORDER-RECEIPT.json"
        if m.returncode == 0 and m.stdout.strip() and not local.exists():
            d = json.loads(m.stdout.strip())
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps({
                "order_id": d.get("order_id"), "total": d.get("total"),
                "financial_status": d.get("financial_status"),
                "created_at": d.get("created_at"),
                "witness": "board138 store_watch FIRST-ORDER-MARKER (قرارداد MP-CONNECT-ALL-01)",
                "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                ensure_ascii=False, indent=1), encoding="utf-8")
            out["first_order_receipt_created"] = True
    except Exception as e:  # noqa: BLE001
        out["err"] = f"{type(e).__name__}: {e}"[:120]
    try:
        DRIVE.mkdir(parents=True, exist_ok=True)
        with open(DRIVE / "store-sync.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return out


def context_for_director() -> str:
    """یک خطِ فشرده برای اینکه مدیرِ سه‌نقشی (مغز) درایوها را «حس» کند."""
    st = _read_json(DRIVE_STATE) or {}
    f = (st.get("fear") or {})
    d = (st.get("dopamine") or {})
    top = (f.get("top") or [{}])[0].get("id", "none")
    queued = 0
    try:
        queued = sum(1 for ln in open(QUEUE, encoding="utf-8")
                     if ln.strip() and not json.loads(ln).get("consumed"))
    except OSError:
        pass
    return (f"DRIVE: fear={f.get('total', 0)} (top: {top}) · "
            f"dopamine_24h={d.get('total_24h', 0)} · "
            f"queued_next_steps={queued} — revenue-blocking fears must raise mission priority")


def _selftest() -> bool:
    sandbox_file = DRIVE / "selftest-lock.flag"
    sandbox_file.parent.mkdir(parents=True, exist_ok=True)
    r1 = _evaluate(selftest_lock=("SBX_test", lambda: sandbox_file.exists()))
    ok1 = r1["locks"].get("SBX_test") == "locked"
    sandbox_file.write_text("open", encoding="utf-8")
    r2 = _evaluate(selftest_lock=("SBX_test", lambda: sandbox_file.exists()))
    ok2 = "SBX_test" in r2["opened_now"] and r2["locks"]["SBX_test"] == "open"
    q_last = ""
    try:
        q_last = open(QUEUE, encoding="utf-8").read().splitlines()[-1]
    except (OSError, IndexError):
        pass
    ok3 = "SBX_test" in q_last
    sandbox_file.unlink(missing_ok=True)
    _evaluate()  # پاک‌سازی state از قفل sandbox
    print(f"selftest: locked_ok={ok1} open_detected={ok2} queued={ok3}")
    return ok1 and ok2 and ok3


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(0 if _selftest() else 1)
    r = _evaluate()
    print(json.dumps(r, ensure_ascii=False, indent=1 if not a.json else None))
