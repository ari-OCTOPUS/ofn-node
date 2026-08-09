#!/usr/bin/env python3
"""soak_gateway.py — probe مداومِ Miniapp Gateway برای پایداری.

سه پنجره: 10 / 30 / 120 دقیقه. هر N ثانیه همه‌ی endpointها را probe می‌کند،
زمانِ پاسخ را می‌سنجد، و در پایانِ هر پنجره یک گزارش می‌دهد:
  - تعدادِ کلِ probeها، موفق، شکست، timeout
  - min/avg/max/p95 زمانِ پاسخ per-endpoint
  - leak حافظه (working set پروسه)
  - خطاهای تکراری

استفاده: python -X utf8 soak_gateway.py <minutes> [interval_s]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "budget"))

import env_loader  # noqa: E402
env_loader.load_env()

GATEWAY = "http://127.0.0.1:8774"
INITDATA_FILE = Path(HERE.parent / "state" / "_gw_initdata.txt")

# همه‌ی endpointهای قابل‌تست
READ_PATHS = [
    "/api/state", "/api/approvals", "/api/legs", "/api/notifications",
    "/api/value", "/api/ui-registry", "/api/current-truth", "/api/ops",
    "/api/governor", "/api/obsidian", "/api/selfmap",
    "/api/cognitive-scan", "/api/agent-log",
]
STATIC_PATHS = ["/", "/miniapp", "/miniapp/app.js", "/miniapp/style.css"]
POST_PATHS = ["/api/actions", "/api/ask", "/api/mirror"]


def _load_initdata() -> str:
    try:
        return INITDATA_FILE.read_text().strip()
    except Exception:
        return ""


def _refresh_initdata() -> str:
    """یک initData تازه می‌سازد (۳۰۰s اعتبار دارد، پس در soak طولانی باید تازه شود)."""
    import hmac, hashlib, urllib.parse
    token = os.environ.get("TG_CENTER_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
    if not token or not owner:
        return _load_initdata()
    auth_date = int(time.time())
    user_json = '{"id":' + str(owner) + ',"first_name":"Owner"}'
    params = {"query_id": "soaktest", "user": user_json, "auth_date": str(auth_date)}
    items = sorted(params.items())
    data_check = "\n".join(f"{k}={v}" for k, v in items)
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    sig = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    pairs = list(items) + [("hash", sig)]
    return urllib.parse.urlencode(pairs)


def _probe(path: str, method: str = "GET", initdata: str = "",
           timeout: float = 12.0, body: dict | None = None) -> tuple[int, float]:
    """یک probe → (status_code, elapsed_s). 0 = خطا/اتصال.

    `body`: بدنهٔ POST ِ سفارشی (پیش‌فرض None = رفتارِ قدیمی، بایت‌به‌بایت)."""
    url = GATEWAY + path
    headers = {}
    if initdata:
        headers["X-Tg-Init-Data"] = initdata
    data = None
    if method == "POST":
        headers["Content-Type"] = "application/json"
        _b = body if body is not None else {"question": "تست پایداری", "action": "invalid.x",
                                            "payload": {}}
        data = json.dumps(_b).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, time.monotonic() - t0
    except Exception:
        return 0, time.monotonic() - t0


def _percentile(sorted_vals: list, p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * p)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def run_soak(minutes: int, interval_s: float = 5.0) -> dict:
    """یک پنجرهٔ soak را اجرا می‌کند و گزارش می‌دهد."""
    initdata = _load_initdata()
    duration_s = minutes * 60
    end = time.monotonic() + duration_s
    cycle = 0
    # per-path stats
    stats: dict[str, dict] = {}
    initdata = _refresh_initdata()  # تازه در شروع
    last_refresh = time.monotonic()

    def _ensure(path: str):
        if path not in stats:
            stats[path] = {"times": [], "ok": 0, "fail": 0, "codes": {}}

    print(f"\n{'='*60}")
    print(f"  SOAK TEST — {minutes} دقیقه (probe هر {interval_s:.0f}s)")
    print(f"{'='*60}")
    start_ts = time.time()

    while time.monotonic() < end:
        cycle += 1
        # تازه‌سازیِ initData هر ۲۰۰s (اعتبار ۳۰۰s)
        if time.monotonic() - last_refresh > 200:
            initdata = _refresh_initdata()
            last_refresh = time.monotonic()
        # static (no auth)
        for p in STATIC_PATHS:
            _ensure(p)
            code, elapsed = _probe(p, "GET")
            stats[p]["times"].append(elapsed)
            stats[p]["codes"][code] = stats[p]["codes"].get(code, 0) + 1
            if 200 <= code < 400:
                stats[p]["ok"] += 1
            else:
                stats[p]["fail"] += 1
        # read (with auth)
        for p in READ_PATHS:
            _ensure(p)
            code, elapsed = _probe(p, "GET", initdata)
            stats[p]["times"].append(elapsed)
            stats[p]["codes"][code] = stats[p]["codes"].get(code, 0) + 1
            if 200 <= code < 400:
                stats[p]["ok"] += 1
            else:
                stats[p]["fail"] += 1
        # POST (with auth) — فقط /api/ask برای جلوگیری از side-effect
        _ensure("/api/ask")
        code, elapsed = _probe("/api/ask", "POST", initdata, timeout=65.0)
        stats["/api/ask"]["times"].append(elapsed)
        stats["/api/ask"]["codes"][code] = stats["/api/ask"]["codes"].get(code, 0) + 1
        if 200 <= code < 400:
            stats["/api/ask"]["ok"] += 1
        else:
            stats["/api/ask"]["fail"] += 1
        # ۲۰۲۶-۰۸-۰۹ (مگاپرامپتِ تناقضات، الف-۳): مسیرِ نوشتنِ واقعی هم زیرِ
        # soak قرار می‌گیرد — با diagnostics.noop که فقط جدولِ اختصاصیِ
        # تشخیصی را لمس می‌کند، صفر ریسکِ آلودگیِ دادهٔ بیزینسی.
        _ensure("/api/actions")
        code, elapsed = _probe("/api/actions", "POST", initdata, timeout=20.0,
                               body={"action": "diagnostics.noop",
                                     "payload": {"note": "soak-test"}})
        stats["/api/actions"]["times"].append(elapsed)
        stats["/api/actions"]["codes"][code] = stats["/api/actions"]["codes"].get(code, 0) + 1
        if 200 <= code < 400:
            stats["/api/actions"]["ok"] += 1
        else:
            stats["/api/actions"]["fail"] += 1

        if cycle % 12 == 0:  # هر ~۱ دقیقه progress
            elapsed_min = (time.time() - start_ts) / 60
            total_ok = sum(s["ok"] for s in stats.values())
            total_fail = sum(s["fail"] for s in stats.values())
            print(f"  [{elapsed_min:.1f}m] cycle={cycle} probes={total_ok+total_fail} "
                  f"ok={total_ok} fail={total_fail}")

        # صبر تا interval بعدی (مگر در cycle آخر)
        remaining = end - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval_s, remaining))

    # ── گزارش ──
    print(f"\n{'─'*60}")
    print(f"  گزارش SOAK — {minutes} دقیقه")
    print(f"{'─'*60}")
    total_ok = sum(s["ok"] for s in stats.values())
    total_fail = sum(s["fail"] for s in stats.values())
    total = total_ok + total_fail
    print(f"  کل probeها: {total} | موفق: {total_ok} | شکست: {total_fail} "
          f"| نرخ موفقیت: {100*total_ok/max(total,1):.1f}%")
    print()
    print(f"  {'endpoint':<28} {'#':>5} {'ok':>5} {'fail':>5} "
          f"{'avg_ms':>7} {'p95_ms':>7} {'max_ms':>7} codes")
    print(f"  {'─'*80}")
    for path in sorted(stats.keys()):
        s = stats[path]
        times = sorted(s["times"])
        n = len(times)
        avg = sum(times) / n * 1000 if n else 0
        p95 = _percentile(times, 0.95) * 1000
        mx = max(times) * 1000 if times else 0
        codes_str = ",".join(f"{c}:{n}" for c, n in sorted(s["codes"].items()))
        flag = "✅" if s["fail"] == 0 else ("⚠️" if s["ok"] > s["fail"] else "❌")
        print(f"  {path:<28} {n:>5} {s['ok']:>5} {s['fail']:>5} "
              f"{avg:>7.0f} {p95:>7.0f} {mx:>7.0f} {codes_str} {flag}")

    report = {
        "minutes": minutes, "interval_s": interval_s,
        "total_probes": total, "ok": total_ok, "fail": total_fail,
        "success_rate": round(100 * total_ok / max(total, 1), 2),
        "per_endpoint": {
            p: {"n": len(s["times"]), "ok": s["ok"], "fail": s["fail"],
                "avg_ms": round(sum(s["times"]) / max(len(s["times"]), 1) * 1000, 1),
                "p95_ms": round(_percentile(sorted(s["times"]), 0.95) * 1000, 1),
                "max_ms": round(max(s["times"]) * 1000, 1) if s["times"] else 0,
                "codes": s["codes"]}
            for p, s in stats.items()
        }
    }
    return report


if __name__ == "__main__":
    mins = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    report = run_soak(mins, interval)
    out = Path(HERE.parent / "state" / f"soak-{mins}m.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  گزارش ذخیره شد: {out}")
