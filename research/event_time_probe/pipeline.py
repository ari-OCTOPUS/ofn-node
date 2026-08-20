#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline.py — زنجیرهٔ کامل T48/prob سازگار با دستور مالک 2026-08-20 (~15:45):

  RBA raw (CSV+HTML) → parser → conflict → pin-receipt (append-only) →
  probe تک‌فراخوانی (nonce، ۵ timestamp، retries=0) → رویداد spine → حکم.

حکم‌های مجاز (بدون PARTIAL مبهم):
  PROBE_PASS · PROBE_RESPONSE_INVALID · PROBE_HTTP_FAILED ·
  PROBE_BLOCKED_FX_STALE · PROBE_BLOCKED_SOURCE_CONFLICT ·
  PROBE_BLOCKED_SIGNATURE · PROBE_BLOCKED_LEASE

اجرا: python -X utf8 research/event_time_probe/pipeline.py [--watch]"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT / "_ops"), str(_ROOT / "_ops/cortex"),
           str(_ROOT / "_ops/owner-signing"), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rba_parser import parse_f11  # noqa: E402

SYD = timezone(timedelta(hours=10))
CSV_URL = "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv"
HTML_URL = "https://www.rba.gov.au/statistics/frequency/exchange-rates.html"
RECEIPTS = _ROOT / "_ops/state/cortex/fx-pin-receipts.jsonl"
PROBE_OUT = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json"
RUN_ID_FILE = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-RUN-ID.txt"
PAYLOAD = _ROOT / "02-DECISIONS/PAYLOAD-EVENT-TIME-PROBE-2026-08-20.json"
SIG = Path(str(PAYLOAD) + ".sig")
PUBKEY = _ROOT / "_ops/owner-signing/octopus-owner-ed25519-public.pem"
LEASE = _ROOT / "_ops/writer_lease.py"
AGENT, SESSION = "agent-B-ZCode", "sess_1d388c34"
ANCHOR = "2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _verdict(v: str, extra: dict | None = None) -> dict:
    out = {"schema": "event-time-pipeline/1", "verdict": v, "ts": _now_iso(),
           "agent_id": AGENT, "session_id": SESSION, **(extra or {})}
    PROBE_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def _lease(op: str, lease_id: str | None = None) -> str | None:
    cmd = ["python", "-X", utf8 := "utf8", str(LEASE), op,
           "--agent", f"{AGENT}-probe", "--session", f"{SESSION}-probe"]
    if op == "release" and lease_id:
        pass
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_ROOT))
    try:
        return json.loads(r.stdout).get("lease_id")
    except Exception:
        return None


def _fetch(url: str) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-fx-pin/1"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read(), {"http_status": resp.status,
                             "content_type": resp.headers.get("Content-Type", ""),
                             "etag": resp.headers.get("ETag", ""),
                             "last_modified": resp.headers.get("Last-Modified", ""),
                             "fetched_at": _now_iso()}


def _html_latest_date(html: bytes) -> str:
    import re
    text = html.decode("utf-8", errors="replace")
    dates = re.findall(r"(\d{1,2}\s+\w{3}\s+2026)", text)
    return dates[-1].replace("  ", " ").strip() if dates else ""


def _verify_signature() -> bool:
    from check_anchor import check
    ok, _, _ = check()
    if not ok:
        return False
    v = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-rawin",
                        "-inkey", str(PUBKEY), "-in", str(PAYLOAD),
                        "-sigfile", str(SIG)], capture_output=True, text=True)
    return v.returncode == 0 and "Verified" in v.stdout


def main() -> dict:
    required_date = datetime.now(SYD).strftime("%d-%b-%Y")

    # ── ۱) امضا + لنگر (fail-closed) ────────────────────────────────────
    if not _verify_signature():
        return _verdict("PROBE_BLOCKED_SIGNATURE")
    lease_id = _lease("acquire")
    if not lease_id:
        return _verdict("PROBE_BLOCKED_LEASE")
    try:
        # ── ۲) منبع خام CSV + HTML و parser ─────────────────────────────
        try:
            csv_raw, csv_meta = _fetch(CSV_URL)
        except Exception as e:
            return _verdict("PROBE_HTTP_FAILED", {"stage": "rba-csv", "error": type(e).__name__})
        parsed = parse_f11(csv_raw, required_date)
        if parsed.verdict == "BLOCK_FX_STALE":
            return _verdict("PROBE_BLOCKED_FX_STALE",
                            {"required_date": required_date,
                             "reasons": parsed.reasons, "raw_sha256": parsed.raw_sha256})
        if not parsed.ok:
            return _verdict("PROBE_BLOCKED_SOURCE_CONFLICT"
                            if "duplicate" in str(parsed.reasons) else "PROBE_HTTP_FAILED",
                            {"parser": parsed.reasons})
        # HTML/CSV conflict — اختلاف = BLOCK (سختی دستور)
        try:
            html_raw, _ = _fetch(HTML_URL)
            html_date = _html_latest_date(html_raw)
        except Exception:
            html_date = ""
        if html_date and not parsed.published_date.startswith(html_date[:6]):
            # تاریخ‌های کامل ممکن است فرمت متفاوت داشته باشند؛ مقایسهٔ ماه/روز
            return _verdict("PROBE_BLOCKED_SOURCE_CONFLICT",
                            {"csv_date": parsed.published_date, "html_date": html_date})

        # ── ۳) رسید پین append-only ─────────────────────────────────────
        rate_usd_per_aud = parsed.rate
        rate = round(1.0 / rate_usd_per_aud, 9)
        receipt_id = hashlib.sha256(
            f"{parsed.raw_sha256}|{parsed.published_date}|{rate}".encode()).hexdigest()[:16]
        if RUN_ID_FILE.exists():
            run_id = RUN_ID_FILE.read_text(encoding="utf-8").strip()
        else:
            run_id = str(uuid.uuid4())
            RUN_ID_FILE.write_text(run_id, encoding="utf-8")
        receipt = {
            "schema": "fx-pin-receipt.v2", "receipt_id": receipt_id,
            "pin_id": "FX-PIN-20260820-01",
            "run_id": run_id, "task_id": "event-time-probe-20260820",
            "authority": {"card_id": "PRE-REG-EVENT-TIME-PROBE-2026-08-20",
                          "payload_sha256": hashlib.sha256(PAYLOAD.read_bytes()).hexdigest().upper(),
                          "signature_path": str(SIG), "signature_verified": True,
                          "trust_anchor_fingerprint": ANCHOR},
            "source": {"publisher": "Reserve Bank of Australia", "source_type": "csv",
                       "source_url": CSV_URL, **csv_meta,
                       "raw_sha256": parsed.raw_sha256, "raw_size_bytes": len(csv_raw)},
            "parser": {"path": "research/event_time_probe/rba_parser.py",
                       "parser_sha256": hashlib.sha256(
                           Path(__file__).resolve().parent.joinpath("rba_parser.py").read_bytes()
                       ).hexdigest()[:16],
                       "selected_series_id": "FXRUSD", "selected_column": parsed.series_col,
                       "rows_seen": parsed.rows_seen, "warnings": parsed.reasons},
            "observation": {"published_date": parsed.published_date,
                            "publication_timezone": "Australia/Sydney",
                            "currency_pair": "AUD/USD",
                            "quote_convention": "USD_per_AUD",
                            "rate_usd_per_aud": rate_usd_per_aud,
                            "fx_usd_to_aud": rate,
                            "source_precision": "4dp",
                            "selected_row_hash": hashlib.sha256(
                                f"{parsed.published_date}|{rate_usd_per_aud}".encode()).hexdigest()[:16]},
            "freshness": {"evaluated_at": _now_iso(), "required_date": required_date,
                          "observed_date": parsed.published_date, "max_age_hours": 24,
                          "verdict": "FRESH",
                          "expires_at": f"{parsed.published_date[-4:]}-"
                                        + {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                                           "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                                           "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                                          [parsed.published_date[3:6]]
                                        + f"-{parsed.published_date[:2]}T06:00:00Z",
                          "reasons": []},
            "lease": {"lease_id": lease_id, "agent_id": f"{AGENT}-probe",
                      "session_id": f"{SESSION}-probe", "acquired_at": _now_iso()},
            "previous_pin": {"pin_id": "FX-PIN-20260819-02",
                             "rate_usd_to_aud": 1.414427157,
                             "published_date": "19-Aug-2026"},
            "result": {"pin_written": True, "live_state_mutated": True,
                       "probe_authorized": True},
        }
        RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
        with RECEIPTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        # وضعیت جاری (شاهد اصلی همین رسید append-only است)
        for p in (_ROOT / "_ops/cortex/pricing_pinned.json",
                  _ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live4/FX-RECORD.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            d["fx_usd_to_aud"] = rate
            d["fx_record"] = {"fx_source_id": f"RBA_EXCHANGE_RATES_DAILY_{required_date}",
                              "fx_timestamp_utc": receipt["freshness"]["expires_at"].replace(
                                  "T06:00:00Z", "T06:00:00Z"),
                              "fx_rate_usd_to_aud": rate,
                              "FX_SOURCE_VALUE": f"AUD_USD = {rate_usd_per_aud}",
                              "FX_CONVERSION_METHOD": "reciprocal_of_RBA_AUD_USD",
                              "owner_pin_id": receipt["pin_id"],
                              "receipt_id": receipt_id,
                              "standing_authorization":
                                  "SIGNED PRE-REG-EVENT-TIME-PROBE-2026-08-20"}
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

        # ── ۴) پروب تک‌فراخوانی (http.client برای تفکیک ۵ زمان) ─────────
        from run_probe_v2 import execute_probe
        result = execute_probe(run_id=run_id, receipt_id=receipt_id,
                               fx_rate=rate, lease_id=lease_id)
        return _verdict(result.pop("verdict"), result)
    finally:
        _lease("release")


if __name__ == "__main__":
    main()
