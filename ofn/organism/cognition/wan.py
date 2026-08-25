from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import ssl
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote, urlparse

from ofn.organism.cognition.policy import wan_enabled
from ofn.organism.persistence.db import DB_LOCK


MAX_BYTES = 24 * 1024
TIMEOUT_S = 12
USER_AGENT = "board-life-001/0.7.0 (owner-granted public HTTPS)"
WEATHER_URL = "https://wttr.in/{city}?format=3"
BTC_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
NEWS_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"
CITY_OK = re.compile(r"^[A-Za-z][A-Za-z0-9 \-]{0,40}$")
HTTPS_URL = re.compile(r"https://[^\s<>\"']+")
COORD_BITS = re.compile(r"-?\d{1,3}\.\d{3,}")

GEOIP_HOSTS = {
    "ipinfo.io",
    "ip-api.com",
    "ipapi.co",
    "freegeoip.app",
    "geolocation-db.com",
    "ipgeolocation.io",
    "ipdata.co",
    "ifconfig.me",
    "icanhazip.com",
    "ident.me",
    "checkip.amazonaws.com",
    "api.ipify.org",
}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def wan_status() -> dict[str, Any]:
    return {
        "enabled": wan_enabled(),
        "mode": "PUBLIC_HTTPS" if wan_enabled() else "OFF",
        "https_only": True,
        "geoip": "FORBIDDEN",
        "actuators": "FORBIDDEN",
        "claim_level": "WAN_FETCHED",
        "sources": ["wttr.in", "api.coingecko.com", "feeds.bbci.co.uk", "user_https"],
    }


def wan_kind(text: str) -> str:
    normalised = " ".join((text or "").casefold().split())
    if HTTPS_URL.search(text or ""):
        return "url"
    if re.search(r"(هوا|weather|باران|forecast)", normalised):
        return "weather"
    if re.search(r"(bitcoin|btc)", normalised):
        return "btc"
    if re.search(r"(قیمت دلار|تومان|ریال)", normalised):
        return "fiat"
    if re.search(r"(خبر|news)", normalised):
        return "news"
    return "world"


def extract_https_url(text: str) -> str | None:
    match = HTTPS_URL.search(text or "")
    if not match:
        return None
    return match.group(0).rstrip(").,;")


def weather_city(text: str, snapshot: dict[str, Any] | None = None) -> str:
    if re.search(r"(سیدنی|sydney)", text or "", re.IGNORECASE):
        return "Sydney"
    season = (snapshot or {}).get("season") or {}
    city = str(season.get("city") or "Sydney")
    if CITY_OK.match(city):
        return city
    return "Sydney"


def _ip_public(raw: str) -> bool:
    try:
        addr = ipaddress.ip_address(raw)
    except ValueError:
        return False
    if (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    ):
        return False
    if addr in ipaddress.ip_network("100.64.0.0/10"):
        return False
    return True


def classify_url(url: str) -> tuple[bool, str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False, "https_only", ""
    if parsed.username or parsed.password:
        return False, "userinfo_forbidden", ""
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        return False, "missing_host", ""
    if host in GEOIP_HOSTS or host.endswith(".local"):
        return False, "geoip_or_local_host", host
    if parsed.port not in {None, 443}:
        return False, "port_denied", host
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False, "dns_fail", host
    ips = [item[4][0] for item in infos if item and item[4]]
    if not ips:
        return False, "dns_fail", host
    for ip in ips:
        if not _ip_public(ip):
            return False, "private_or_local_ip", host
    return True, "ok", host


def _strip_coords(text: str) -> str:
    return COORD_BITS.sub("[coord_stripped]", text)


def https_get(url: str) -> dict[str, Any]:
    allowed, reason, host = classify_url(url)
    if not allowed:
        return {
            "status": "DENIED",
            "reason": reason,
            "host": host,
            "url": url,
            "excerpt": None,
        }
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain, application/json, application/xml, text/xml, */*",
        },
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirectHandler(),
    )
    t0 = time.monotonic()
    try:
        with opener.open(request, timeout=TIMEOUT_S) as response:
            raw = response.read(MAX_BYTES + 1)
            status = response.status
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_BYTES)
        status = exc.code
        final_url = url
    except Exception as exc:
        return {
            "status": "DEGRADED",
            "reason": type(exc).__name__,
            "host": host,
            "url": url,
            "excerpt": None,
        }
    if final_url != url:
        ok, redirect_reason, _ = classify_url(final_url)
        if not ok:
            return {
                "status": "DENIED",
                "reason": f"redirect_{redirect_reason}",
                "host": host,
                "url": url,
                "excerpt": None,
            }
    if len(raw) > MAX_BYTES:
        raw = raw[:MAX_BYTES]
    excerpt = _strip_coords(raw.decode("utf-8", "replace")).strip()
    excerpt = re.sub(r"\s+", " ", excerpt)[:800]
    return {
        "status": "OK" if status == 200 and excerpt else "DEGRADED",
        "reason": None if excerpt else "empty_body",
        "host": host,
        "url": url,
        "http_status": status,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "response_hash": hashlib.sha256(raw or b"").hexdigest(),
        "excerpt": excerpt or None,
        "claim_level": "WAN_FETCHED",
    }


def persist_fetch(
    con,
    *,
    url: str,
    host: str,
    kind: str,
    status: str,
    excerpt: str,
    response_hash: str,
) -> None:
    fetch_id = hashlib.sha256(f"{time.time_ns()}:{url}".encode()).hexdigest()[:32]
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO wan_fetches(
                fetch_id, created_at, url, host, kind, status, claim_level,
                excerpt, response_hash
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                fetch_id,
                time.time(),
                url,
                host,
                kind,
                status,
                "WAN_FETCHED",
                excerpt[:800],
                response_hash,
            ),
        )


def list_fetches(con, limit: int = 8) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT fetch_id, created_at, url, host, kind, status, claim_level, excerpt
            FROM wan_fetches
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "fetch_id": row[0],
            "created_at": row[1],
            "url": row[2],
            "host": row[3],
            "kind": row[4],
            "status": row[5],
            "claim_level": row[6],
            "excerpt": row[7],
        }
        for row in rows
    ]


def _store(con, result: dict[str, Any], kind: str) -> None:
    if con is None or not result.get("url"):
        return
    persist_fetch(
        con,
        url=str(result.get("url")),
        host=str(result.get("host") or ""),
        kind=kind,
        status=str(result.get("status") or "DEGRADED"),
        excerpt=str(result.get("excerpt") or result.get("reason") or ""),
        response_hash=str(result.get("response_hash") or ""),
    )


def fetch_weather(city: str, con=None) -> dict[str, Any]:
    if not CITY_OK.match(city):
        city = "Sydney"
    url = WEATHER_URL.format(city=quote(city))
    result = https_get(url)
    result["kind"] = "weather"
    result["city"] = city
    _store(con, result, "weather")
    return result


def fetch_bitcoin(con=None) -> dict[str, Any]:
    result = https_get(BTC_URL)
    result["kind"] = "btc"
    _store(con, result, "btc")
    return result


def fetch_news(con=None) -> dict[str, Any]:
    result = https_get(NEWS_URL)
    result["kind"] = "news"
    if result.get("excerpt"):
        titles = re.findall(r"<title>([^<]+)</title>", result["excerpt"], re.I)
        cleaned = [re.sub(r"\s+", " ", item).strip() for item in titles]
        cleaned = [item for item in cleaned if item and item.lower() != "bbc news"][:4]
        if cleaned:
            result["excerpt"] = " | ".join(cleaned)
    _store(con, result, "news")
    return result


def fetch_user_url(url: str, con=None) -> dict[str, Any]:
    result = https_get(url)
    result["kind"] = "url"
    _store(con, result, "url")
    return result


def format_wan_answer(
    kind: str,
    result: dict[str, Any] | None = None,
    *,
    city: str | None = None,
) -> str:
    if kind == "fiat":
        return (
            "[WAN] منبع زندهٔ نرخ ارز محلی از اینترنت ندارم. "
            "اختراع هم نمی‌کنم. این حسگر برد نیست."
        )
    if not result:
        return "[WAN] خواندن اینترنت نشد. حسگر برد نیست و عدد اختراع نمی‌کنم."
    if result.get("status") != "OK" or not result.get("excerpt"):
        return (
            f"[WAN] خواندن {result.get('host') or 'منبع'} نشد "
            f"({result.get('reason') or result.get('status')}). "
            "عدد زنده اختراع نمی‌کنم. حسگر برد نیست."
        )
    host = result.get("host") or ""
    excerpt = result.get("excerpt")
    if kind == "weather":
        return (
            f"[WAN_FETCHED] از wttr.in برای {city or result.get('city')}: {excerpt} "
            "این دمای SoC برد نیست. GPS هم نیست."
        )
    if kind == "btc":
        return (
            f"[WAN_FETCHED] از {host}: {excerpt} "
            "این حسگر برد نیست و نرخ ارز محلی نیست."
        )
    if kind == "news":
        return (
            f"[WAN_FETCHED] عنوان‌های BBC World RSS: {excerpt} "
            "این حسگر برد نیست."
        )
    return (
        f"[WAN_FETCHED] از {host}: {excerpt[:500]} "
        "این حسگر برد نیست. geoip و GPS نیست."
    )


def answer_wan(con, text: str, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    if not wan_enabled():
        return {
            "status": "DISABLED",
            "kind": "off",
            "answer": (
                "این را از اینترنت نمی‌گیرم. روی برد اندازه‌گیری نشده. "
                "geoip و هواشناسی و قیمت بیرونی خاموش‌اند."
            ),
        }
    kind = wan_kind(text)
    if kind == "fiat":
        return {"status": "NO_SOURCE", "kind": kind, "answer": format_wan_answer(kind)}
    if kind == "weather":
        city = weather_city(text, snapshot)
        result = fetch_weather(city, con)
        return {
            "status": result.get("status"),
            "kind": kind,
            "answer": format_wan_answer(kind, result, city=city),
            "host": result.get("host"),
        }
    if kind == "btc":
        result = fetch_bitcoin(con)
        return {
            "status": result.get("status"),
            "kind": kind,
            "answer": format_wan_answer(kind, result),
            "host": result.get("host"),
        }
    if kind == "news":
        result = fetch_news(con)
        return {
            "status": result.get("status"),
            "kind": kind,
            "answer": format_wan_answer(kind, result),
            "host": result.get("host"),
        }
    if kind == "url":
        url = extract_https_url(text) or ""
        result = fetch_user_url(url, con)
        return {
            "status": result.get("status"),
            "kind": kind,
            "answer": format_wan_answer(kind, result),
            "host": result.get("host"),
        }
    from ofn.organism.cognition.teacher import complete_deep

    prompt = (
        "سؤال عمومی جهان. اگر واقعیت زندهٔ هوا/قیمت نداری بگو نمی‌دانم. "
        "مختصات برد را نساز.\n"
        f"{text}"
    )
    model = complete_deep(prompt, mode="wan")
    if model.get("status") == "OK" and model.get("answer"):
        return {
            "status": "OK",
            "kind": "world",
            "answer": (
                "[WAN_MODEL] " + model["answer"]
                + " این دانش مدل است نه حسگر برد."
            ),
            "host": "api.deepseek.com",
        }
    return {
        "status": model.get("status") or "DEGRADED",
        "kind": "world",
        "answer": "[WAN] مدل بیرونی جواب نداد. حسگر برد نیست.",
    }
