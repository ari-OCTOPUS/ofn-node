#!/usr/bin/env python3
"""legs_status.py — خوانندهٔ فقط‌خواندنیِ وضعیتِ بیزنس‌های برد (Orange Pi).

اختاپوسِ ارشد (این ارگانیسم) رییسِ بردِ Orange Pi است، ولی برد مستقل کار
می‌کند. این ماژول «چشمِ رصدِ» ارشد است — نه اقتدارِ فرمان:

  · فقط GET به آدرس‌های *عمومیِ* cloudflared (ziman/lead/studio/panel).
  · پینِ زنده: `/healthz` — فقط ۲۰۰ یعنی listener/تونل جواب داد (نه DB، نه بوت، نه کسب‌وکار).
  · غیر۲۰۰ یا خطای اتصال = همان لگ نرسید/غیرسالم. بدون fallback به `/` یا `/api/health`.
  · بدنهٔ پاسخ هرگز خوانده/ذخیره نمی‌شود — فقط کدِ HTTP + تأخیر (بالا/پایین).
  · هیچ فرمان، هیچ loopback:8796، هیچ دور زدنِ auth، هیچ PII.
  · مرزِ trust حفظ می‌شود: این خواننده هرگز از مرزِ zero-trustِ برد عبور نمی‌کند.
  · قید: برد برای کارکردن به این خواننده نیاز *ندارد* — اگر برد نرسید،
    صادقانه «نمی‌دانم» می‌گوید، نه اینکه چیزی را جعل کند.

stdlib-only. صفر dependency.
"""
from __future__ import annotations

import ipaddress
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# لگ‌های عمومیِ برد → زیردامنه. مرجعِ آدرس‌ها: HANDOFF بردِ 2026-08-05.
_LEGS = ("ziman", "lead", "studio", "panel")
_LABELS = {
    "ziman": "زیمان (گالری)",
    "lead": "لید (نقاشی)",
    "studio": "استودیو (OFN)",
    "panel": "پنل",
}
_DEFAULT_DOMAIN = "master-painting.com"
_HEALTHZ = "/healthz"  # liveness عمومی؛ نه /api/health (تلهٔ ۴۰۱)
_TIMEOUT_S = 3.0
_CACHE_TTL_S = 30.0

_cache: dict = {"at": 0.0, "result": None}

_BLOCKED_HOSTS = frozenset({"localhost", "localhost.localdomain"})


class BlockedUrl(ValueError):
    """URL عمومیِ HTTPS نیست — این لگ را probe نکن."""


def public_https_url_ok(url: str) -> bool:
    """فقط https به host غیرخصوصی. override لوپ‌بک/LAN را رد می‌کند."""
    raw = str(url or "").strip()
    if not raw:
        return False
    try:
        parsed = urlparse(raw)
    except Exception:  # noqa: BLE001
        return False
    if parsed.scheme != "https":
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname
    if not host:
        return False
    h = host.strip().lower().rstrip(".")
    if h in _BLOCKED_HOSTS or h.endswith(".localhost"):
        return False
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return True
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _assert_public_https(url: str) -> None:
    if not public_https_url_ok(url):
        raise BlockedUrl("not-public-https")


class _PublicHttpsRedirectHandler(urllib.request.HTTPRedirectHandler):
    """G1 (2026-08-13): liveness-probe هرگز redirect دنبال نمی‌کند — هر 3xx یعنی
    «۲۰۰ نبود» = نرسید.

    گاردِ public_https_url_ok فقط *رشته* را چک می‌کند و host را resolve نمی‌کند؛
    پس دنبال‌کردنِ یک 3xx ِ بردِ نامعتمد به هاستی که DNS-اش به loopback/LAN ِ خودِ
    ارشد می‌رسد (DNS-rebind) یا literalِ مبهم (مثلِ 0x7f000001) یک SSRFِ blind به
    پورت‌های داخلیِ ارشد بود. یک /healthz ِ سالم ۲۰۰ ِ مستقیم می‌دهد و هرگز به
    redirect نیاز ندارد — پس همه رد می‌شوند و در _probe_one به up=False می‌نشینند.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BlockedUrl(f"redirect-not-followed:{code}")


_OPENER = urllib.request.build_opener(_PublicHttpsRedirectHandler)


def _base_domain() -> str:
    dom = str(os.environ.get("OCTOPUS_BOARD_DOMAIN", "")).strip()
    return dom or _DEFAULT_DOMAIN


def leg_urls() -> dict:
    """leg → URLِ عمومی. هر leg با OCTOPUS_LEG_URL_<NAME> قابلِ override است."""
    dom = _base_domain()
    out: dict = {}
    for leg in _LEGS:
        override = str(os.environ.get(f"OCTOPUS_LEG_URL_{leg.upper()}", "")).strip()
        out[leg] = override or f"https://{leg}.{dom}{_HEALTHZ}"
    return out


def _default_fetch(url: str, timeout: float) -> int:
    """GET می‌زند ولی بدنه را نمی‌خواند — فقط کدِ وضعیت برمی‌گرداند.

    تصمیمِ بالا/پایین با خودِ کد است (فقط ۲۰۰ = رسید). این تابع کد را برمی‌گرداند.
    خطاهای اتصال/timeout/DNS پروپاگیت می‌شوند.
    """
    _assert_public_https(url)
    req = urllib.request.Request(
        url, method="GET",
        headers={"User-Agent": "octopus-legs-reader/0.1 (read-only)"},
    )
    try:
        with _OPENER.open(req, timeout=timeout) as resp:  # noqa: S310
            return int(resp.getcode() or 0)
    except urllib.error.HTTPError as he:
        return int(he.code)  # کد هست؛ up بودن فقط اگر ۲۰۰ باشد


def _probe_one(leg: str, url: str, timeout: float, fetch) -> dict:
    t0 = time.time()
    try:
        _assert_public_https(url)
        code = int(fetch(url, timeout))
        ms = int((time.time() - t0) * 1000)
        ok = code == 200
        rec = {"leg": leg, "url": url, "up": ok, "http": code, "ms": ms}
        if not ok:
            rec["error"] = f"http-{code}"
        return rec
    except Exception as exc:  # noqa: BLE001
        ms = int((time.time() - t0) * 1000)
        return {"leg": leg, "url": url, "up": False,
                "error": type(exc).__name__, "ms": ms}


def snapshot(fetch=None, force: bool = False) -> dict:
    """وضعیتِ همهٔ لگ‌ها — همزمان (thread pool)، کش‌شده با TTLِ کوتاه.

    fetch: تزریق‌پذیر برای تست (پیش‌فرض = GETِ واقعیِ شبکه).
    """
    now = time.time()
    if (not force and _cache["result"] is not None
            and (now - _cache["at"]) < _CACHE_TTL_S):
        return _cache["result"]

    fetch = fetch or _default_fetch
    urls = leg_urls()
    legs: dict = {}
    # همزمان تا بدترین‌حالت ≈ یک timeout باشد نه جمعِ چهارتا.
    with ThreadPoolExecutor(max_workers=len(urls) or 1) as ex:
        futures = {ex.submit(_probe_one, leg, url, _TIMEOUT_S, fetch): leg
                   for leg, url in urls.items()}
        for fut in futures:
            r = fut.result()
            legs[r["leg"]] = r

    up = sum(1 for v in legs.values() if v.get("up"))
    result = {
        "legs": legs,
        "up": up,
        "total": len(legs),
        "domain": _base_domain(),
        "checked_at": now,
        "read_only": True,
        "external_effect": False,
        "pin": "healthz",
        "pin_means": "http-listener-only",
    }
    _cache["at"] = now
    _cache["result"] = result
    return result


def _reset_cache() -> None:
    """فقط برای تست — کش را پاک می‌کند."""
    _cache["at"] = 0.0
    _cache["result"] = None


def format_for_chat(snap: "dict | None" = None) -> str:
    """خروجیِ content-free برای چتِ «پرسش از اختاپوس»."""
    snap = snap or snapshot()
    lines = [
        f"رصدِ listener/تونل برد — {snap['up']}/{snap['total']} پاسخ ۲۰۰ (/healthz):",
    ]
    for leg in _LEGS:
        v = snap["legs"].get(leg)
        name = _LABELS.get(leg, leg)
        if not v:
            lines.append(f"· {name}: —")
        elif v.get("up"):
            lines.append(f"· {name}: رسید (HTTP 200، {v.get('ms')}ms)")
        elif v.get("http"):
            lines.append(f"· {name}: نرسید/غیرسالم (HTTP {v.get('http')})")
        else:
            lines.append(f"· {name}: نرسید ({v.get('error')})")
    lines.append(
        "این پین فقط می‌گوید پروسهٔ HTTP جواب می‌دهد — نه DB، نه بوت، نه کانکتور، نه سلامتِ کسب‌وکار.\n"
        "بدون fallback به / یا /api/health. رصد فقط‌خواندنی؛ برد مستقل است."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    import json as _json
    snap = snapshot(force=True)
    print(_json.dumps(snap, ensure_ascii=False, indent=2))
    print()
    print(format_for_chat(snap))
