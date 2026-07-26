#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_probes.py — C2 · رجیستریِ سنجه‌های read-only برای تولیدکنندهٔ صادقِ فرضیهٔ C6.

قیدِ صداقت: هر سنجه فقط count می‌زند؛ هیچ نتیجهٔ صنعتی/بهبودِ ساختگی تولید نمی‌کند.
خروجیِ نامشخص/کرش → count=-1 (هیچ فرضیه‌ای ساخته نشود). صفر شبکه/پول/اثرِ بیرونی؛
stdlib-only؛ fail-soft؛ هر wrapper خواندنی که را override می‌کند در finally برمی‌گردد.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from pathlib import Path

OPS = Path(__file__).resolve().parent
ROMAJAN_FLAG = "OCTOPUS_WIRE_ROMAJAN_PROBES"


def _sys(p: Path) -> None:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


_sys(OPS / "budget")
import opslib  # noqa: E402


def _load_self_audit_module():
    for p in (OPS / "cortex",):
        _sys(p)
    return importlib.import_module("self_audit")


def _probe_self_audit_redundant_reads() -> dict:
    mod = _load_self_audit_module()
    orig_read, orig_grep = mod._read, mod._grep
    calls = {"_read": 0, "_grep": 0}
    try:
        def counting_read(p):
            calls["_read"] += 1
            return orig_read(p)

        def counting_grep(p, needle):
            calls["_grep"] += 1
            return orig_grep(p, needle)

        mod._read = counting_read
        mod._grep = counting_grep
        # ۲۰۲۶-۰۷-۲۶: `mod.main()` وجود ندارد و AttributeError می‌داد → این پروب
        # از وقتی self_audit تغییر نام داد **بی‌صدا کور** بود و count=-1 می‌داد،
        # و produce() آن را «نقصی نیست» می‌خواند. نقطهٔ ورودِ واقعی run_audit است.
        # write=False حیاتی است: پروب باید read-only بماند و ماتریس را ننویسد.
        mod.run_audit(write=False)
        return {"count": calls["_read"], "unit": "read",
                "detail": (f"self_audit.run_audit(write=False) full-matrix "
                           f"reads={calls['_read']} grep={calls['_grep']}")}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "read",
                "detail": f"probe-failed:{type(e).__name__}"}
    finally:
        mod._read, mod._grep = orig_read, orig_grep


def _probe_rfc_duplicate_surplus() -> dict:
    """RFCهای هم‌بطن — چند نسخهٔ تکراری از یک گلوگاه در صف نشسته‌اند؟

    ۲۰۲۶-۰۷-۲۶: این پروب به `state/c6/rfcs/c6-*.json` نگاه می‌کرد، مسیری که هرگز
    ساخته نشد. یعنی همیشه `count=-1` می‌داد و produce() آن را «نقصی نیست»
    می‌خواند — کوریِ دائمی که شبیهِ سلامت بود. انبارِ واقعی `state/doctor/rfcs.json`
    است با اسکیمای `{ts, schema, rfcs: [...]}` و کلیدهای rfc_id/rfc_hash/status.
    """
    try:
        rp = opslib.STATE_DIR / "doctor" / "rfcs.json"
        if not rp.exists():
            return {"count": -1, "unit": "rfc",
                    "detail": f"rfcs.json غایب ({rp.name}) — قضاوت غیرممکن"}
        try:
            doc = json.loads(rp.read_text("utf-8"))
        except (OSError, ValueError) as e:
            return {"count": -1, "unit": "rfc", "detail": f"rfcs.json ناخوانا:{type(e).__name__}"}
        items = doc.get("rfcs") if isinstance(doc, dict) else doc
        if not isinstance(items, list) or not items:
            return {"count": -1, "unit": "rfc", "detail": "صفِ RFC خالی — قضاوت غیرممکن"}
        # امضای هم‌بطن‌بودن: hash صریح، وگرنه متنِ گلوگاه
        keys = []
        for it in items:
            if not isinstance(it, dict):
                continue
            sig = str(it.get("rfc_hash") or it.get("bottleneck") or "").strip().lower()
            if sig:
                keys.append(sig)
        if not keys:
            return {"count": -1, "unit": "rfc",
                    "detail": "هیچ ردیفی امضای قابلِ‌مقایسه ندارد — قضاوت غیرممکن"}
        from collections import Counter
        counts = Counter(keys)
        max_n = max(counts.values())
        surplus = sum(n - 1 for n in counts.values())
        return {"count": max_n, "unit": "rfc",
                "detail": (f"max_duplicate={max_n} surplus={surplus} rfcs={len(items)} "
                           f"comparable={len(keys)}")}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "rfc",
                "detail": f"probe-failed:{type(e).__name__}"}


def _probe_thesis_delta_self_sign() -> dict:
    """ردیفِ `delta-self` دفترِ تز: آیا Δ_self هنوز منفی است؟

    ادعا: مدلی با دسترسی به وضعیتِ درونیِ خود، آیندهٔ خود را بهتر از نسخهٔ کور
    پیش‌بینی می‌کند (Δ>0). اندازه‌گیریِ زنده تا امروز منفی است.
    count = تعدادِ نمونهٔ اخیر با Δ<=0. count==0 با nِ کافی ⇒ ادعا حرکت کرده.
    """
    try:
        vals: list[float] = []
        # استریمِ اختصاصیِ مسیرِ رویا (heart/shadow._append_thesis_measurement).
        # `pulse/heart-params-shadow.jsonl` عمداً چک نمی‌شود: شمایش فقط ۶ کلیدِ
        # باروگیرنده است و Δ در آن نیست — خواندنش nِ دروغین می‌ساخت.
        stream = opslib.STATE_DIR / "thesis" / "measurements.jsonl"
        if stream.exists():
            try:
                lines = stream.read_text("utf-8").splitlines()[-500:]
            except OSError:
                lines = []
            for ln in lines:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                v = d.get("delta_self_live") if isinstance(d, dict) else None
                if isinstance(v, (int, float)):
                    vals.append(float(v))
        if len(vals) < 2:
            latest = opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json"
            try:
                d = json.loads(latest.read_text("utf-8"))
                v = (d.get("telemetry") or {}).get("delta_self_live")
                if isinstance(v, (int, float)):
                    vals.append(float(v))
            except (OSError, ValueError, AttributeError):
                pass
        durable = len(vals)
        if durable < 2:
            # صداقت دربارهٔ نبودِ تاریخ: یک عکسِ لحظه‌ای «روند» نیست. count=-1 یعنی
            # قضاوت غیرممکن — نه صفرِ قلابی، نه n=1ِ گمراه‌کننده.
            snap = None
            try:
                d = json.loads((opslib.STATE_DIR / "pulse"
                                / "heart-shadow-latest.json").read_text("utf-8"))
                v = (d.get("telemetry") or {}).get("delta_self_live")
                snap = float(v) if isinstance(v, (int, float)) else None
            except (OSError, ValueError, AttributeError, TypeError):
                pass
            return {"count": -1, "unit": "sample",
                    "detail": (f"no-durable-history (durable_rows={durable}) — روند "
                               f"غیرقابل‌آزمون تا OCTOPUS_THESIS_MEASURE=1 روشن شود. "
                               f"عکسِ لحظه‌ای: {snap}")}
        neg = sum(1 for v in vals if v <= 0.0)
        mean = sum(vals) / len(vals)
        first_half = vals[:len(vals) // 2]
        second_half = vals[len(vals) // 2:]
        trend = (sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half))
        return {"count": neg, "unit": "sample",
                "detail": (f"n={len(vals)} negative={neg} mean={mean:.6f} "
                           f"latest={vals[-1]:.6f} trend={trend:+.6f} "
                           f"(Δ<=0 ⇒ دسترسیِ درونی بدتر از کوری؛ trend>0 ⇒ به سمتِ مثبت)")}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "sample", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_thesis_phi_saturation() -> dict:
    """ردیفِ `phi-liveness` دفترِ تز: آیا phi هنوز به سقفِ محاسباتیِ خودش می‌چسبد؟

    اشباع = اندازه‌گیری نیست. count = تعدادِ لِگی که phi>=phi_dead دارد.
    count==0 ⇒ آرتیفکت دیگر بازتولید نمی‌شود (فیکس گرفته).
    """
    try:
        p = opslib.STATE_DIR / "ORGANISM-STATE.json"
        d = json.loads(p.read_text("utf-8"))
        diag = ((d.get("chrono") or {}).get("legs_diag") or {})
        if not isinstance(diag, dict) or not diag:
            return {"count": -1, "unit": "leg",
                    "detail": "chrono.legs_diag غایب — قضاوت غیرممکن"}
        sat, mx, parts, honest = 0, 0.0, [], 0
        for leg, v in diag.items():
            if not isinstance(v, dict):
                continue
            phi = v.get("phi")
            dead = v.get("phi_dead")
            if not isinstance(phi, (int, float)) or not isinstance(dead, (int, float)):
                continue
            mx = max(mx, float(phi))
            if bool(v.get("honest_tolerance")):
                honest += 1
            if float(phi) >= float(dead):
                sat += 1
            parts.append(f"{leg}:phi={float(phi):.2f}/dead={float(dead):.1f}"
                         f",n={v.get('ack_samples')},{v.get('state')}")
        if not parts:
            return {"count": -1, "unit": "leg",
                    "detail": "هیچ لِگی phi/phi_dead عددی ندارد — قضاوت غیرممکن"}
        return {"count": sat, "unit": "leg",
                "detail": (f"legs={len(parts)} saturated={sat} max_phi={mx:.2f} "
                           f"honest_tolerance={honest}/{len(parts)} | " + " ".join(parts))}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "leg", "detail": f"probe-failed:{type(e).__name__}"}


PROBES = {
    # ── مسیرِ رویا: پروب‌های ردیف‌های دفترِ تز (رأیِ مالک 2026-07-25) ─────────
    # این‌ها فقط دادهٔ زندهٔ **موجود** را می‌شمارند؛ هیچ آزمایشِ نو، هیچ شبکه، هیچ پول.
    # مصرف‌کننده: thesis_queue → hypothesis-queue → همان ضربانِ خودکارِ C6.
    "thesis_delta_self_sign": {
        "measure": _probe_thesis_delta_self_sign,
        "subject": "Δ_self: آیا دسترسی به وضعیتِ درونی، پیش‌بینیِ خود را بهتر می‌کند؟",
        "question": "آیا Δ_self در استریمِ زنده هنوز منفی است (دسترسیِ درونی بدتر از کوری)؟",
        "floor": 1,
    },
    "thesis_phi_saturation": {
        "measure": _probe_thesis_phi_saturation,
        "subject": "phi-accrual: آیا عددِ phi اندازه‌گیری است یا اشباعِ سقفِ محاسباتی؟",
        "question": "آیا هنوز لِگی هست که phi>=phi_dead بگیرد (اشباع، نه اندازه‌گیری)؟",
        "floor": 1,
    },
    "self_audit_redundant_reads": {
        "measure": _probe_self_audit_redundant_reads,
        "subject": "reduce per-sweep redundant reads in self_audit.main()",
        "question": "آیا هر sweep کاملِ self_audit واقعاً خواندنی‌های زیادی می‌کند؟",
        "floor": 10,
    },
    "rfc_duplicate_surplus": {
        "measure": _probe_rfc_duplicate_surplus,
        "subject": "deduplicate identical RFC hypotheses in state/c6/rfcs",
        "question": "آیا فرضیه‌های یکسانِ C6 به‌طور تکراری RFC می‌شوند؟",
        "floor": 1,
        "hypothesis": (
            "the C6 RFC registry holds duplicate identical hypotheses; a bottleneck-identity "
            "dedup guard before writing would cut surplus files without losing distinct claims."
        ),
        "expected_artifact": "counted surplus/max-duplicate RFC hypotheses",
        "falsification": ["max duplicate hypothesis count <= floor"],
        "fix_hint": "hash bottleneck text before writing a new c6-*.json RFC",
        "unit": "rfc",
    },
}


def _romajan_root() -> Path:
    return Path(os.environ.get("ROMAJAN_LAB_PATH", r"F:\romajan"))


def romajan_seen_path() -> Path:
    return opslib.STATE_DIR / "c6" / "romajan-seen.json"


def load_romajan_seen() -> set:
    """ids already ingested into C6 (append-only set on disk)."""
    p = romajan_seen_path()
    if not p.exists():
        return set()
    try:
        raw = json.loads(p.read_text("utf-8"))
        if isinstance(raw, list):
            return {str(x) for x in raw}
        if isinstance(raw, dict):
            return {str(x) for x in (raw.get("ids") or [])}
    except (OSError, ValueError):
        return set()
    return set()


def mark_romajan_seen(ids) -> dict:
    """Append claim ids to seen-set. Never deletes. Fail-soft.

    Called after a romajan_* hypothesis is DONE (any terminal verdict) so the
    same claim is never re-proposed. Does NOT mean the claim became FACT.
    """
    try:
        incoming = [str(x).strip() for x in (ids or []) if str(x).strip()]
        if not incoming:
            return {"ok": True, "added": 0}
        seen = load_romajan_seen()
        before = len(seen)
        for i in incoming:
            seen.add(i)
        p = romajan_seen_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {"ids": sorted(seen), "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(p)
        return {"ok": True, "added": len(seen) - before, "total": len(seen)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"{type(e).__name__}: {e}"}


def _probe_romajan_new_claims() -> dict:
    """ادعاهای verified/executed در romajan که هنوز در seen-setِ C6 نیستند.

    فقط‌خواندنی، $0، بدون شبکه. نبودِ مسیر/ledger → count=-1 (نمی‌دانم).
    پشتِ OCTOPUS_WIRE_ROMAJAN_PROBES؛ وگرنه count=-1 تا producer فرضیه نسازد.
    """
    if str(os.environ.get(ROMAJAN_FLAG, "")).strip().lower() not in ("1", "true", "yes", "on"):
        return {"count": -1, "unit": "claim",
                "detail": "romajan-probes-flag-off"}
    try:
        root = _romajan_root()
        ledgers = [
            root / "propagation" / "claims_ledger.json",
            root / "propagation-lab" / "data" / "claims_ledger.json",
        ]
        seen = load_romajan_seen()
        new_ids = []
        scanned = 0
        for lp in ledgers:
            if not lp.exists():
                continue
            try:
                data = json.loads(lp.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            claims = data if isinstance(data, list) else (
                data.get("claims") if isinstance(data, dict) else [])
            if not isinstance(claims, list):
                continue
            for c in claims:
                if not isinstance(c, dict):
                    continue
                cid = str(c.get("id") or c.get("claim_id") or "").strip()
                status = str(c.get("status") or "").strip().lower()
                if not cid:
                    continue
                scanned += 1
                if status in ("verified", "executed", "fact") and cid not in seen:
                    new_ids.append(cid)
        if scanned == 0:
            return {"count": -1, "unit": "claim",
                    "detail": f"no-claims-readable under {root}"}
        return {"count": len(new_ids), "unit": "claim",
                "detail": f"new={len(new_ids)} scanned={scanned} seen={len(seen)} root={root}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "claim",
                "detail": f"probe-failed:{type(e).__name__}"}


def _probe_romajan_engine_idle() -> dict:
    """چند روز از آخرین mtimeِ claims_ledger گذشته؟ floor=7 → بیش از یک هفته خاموش.

    count = روزهای سپری‌شده از آخرین تغییر. فقط metadataی فایل، بدون اجرای موتور.
    """
    if str(os.environ.get(ROMAJAN_FLAG, "")).strip().lower() not in ("1", "true", "yes", "on"):
        return {"count": -1, "unit": "day", "detail": "romajan-probes-flag-off"}
    try:
        root = _romajan_root()
        candidates = [
            root / "propagation" / "claims_ledger.json",
            root / "propagation-lab" / "data" / "claims_ledger.json",
            root / "propagation" / "engine_a.py",
            root / "00-INDEX.md",
        ]
        mtimes = []
        for p in candidates:
            try:
                if p.exists():
                    mtimes.append(p.stat().st_mtime)
            except OSError:
                continue
        if not mtimes:
            return {"count": -1, "unit": "day",
                    "detail": f"romajan-path-missing:{root}"}
        age_days = (time.time() - max(mtimes)) / 86400.0
        return {"count": int(age_days), "unit": "day",
                "detail": f"age_days={age_days:.2f} newest_mtime={max(mtimes):.0f}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "day",
                "detail": f"probe-failed:{type(e).__name__}"}


# ─── پروب‌های ۲۰۲۶-۰۷-۲۶ ─────────────────────────────────────────────────────
# هر شش‌تا از یک نقصِ **مشاهده‌شدهٔ همان روز** ساخته شده‌اند، نه از حدس. اگر یک
# کلاسِ نقص یک‌بار توانست یک شبانه‌روز پنهان بماند، پروبش باید بماند حتی وقتی
# صفر است — پروب سالم که صفر می‌دهد شهادت است؛ پروبی که نیست، کوری است.

def _probe_c6_undelivered_cards() -> dict:
    """آزمایشی که تمام شد، حکم گرفت، و کارتش هرگز به مالک نرسید.

    ۲۰۲۶-۰۷-۲۵: `seed-state-read-cache-bench` دقیقاً همین بود و یک شبانه‌روز
    نامرئی ماند چون فراخوانِ تحویل زیرِ early-returnِ «فرضیهٔ pending نیست» بود.
    """
    try:
        q = opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"
        if not q.exists():
            return {"count": -1, "unit": "card", "detail": "صفِ C6 غایب — قضاوت غیرممکن"}
        owed = total = 0
        for ln in q.read_text("utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            total += 1
            if str(d.get("status") or "") == "DONE" and not d.get("card_delivered"):
                owed += 1
        return {"count": owed, "unit": "card",
                "detail": f"undelivered={owed} of done/total rows={total}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "card", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_tg_oversized_callback() -> dict:
    """کارتی که شناسه‌اش از سقفِ ۶۴ بایتِ callback_data تلگرام رد می‌شود.

    ۲۰۲۶-۰۷-۲۶: شناسهٔ ۴۰ کاراکتری → ۷۵ بایت → تلگرام کلِ پیام را ۴۰۰ می‌کرد،
    `send_text` استثنا را می‌بلعید و False می‌داد. کارت بی‌هیچ ردی گم می‌شد.
    """
    try:
        _sys(OPS / "budget")
        import approval_channel as _ac  # noqa: WPS433
        p = opslib.STATE_DIR / "pulse" / "pending-cards.json"
        if not p.exists():
            return {"count": -1, "unit": "card", "detail": "pending-cards.json غایب"}
        doc = json.loads(p.read_text("utf-8"))
        if not isinstance(doc, dict) or not doc:
            return {"count": -1, "unit": "card", "detail": "هیچ کارتِ ثبت‌شده‌ای نیست"}
        bad = [str(v.get("rfc_id") or "") for v in doc.values()
               if isinstance(v, dict) and v.get("kind") == "rfc"
               and not _ac.callback_fits(str(v.get("rfc_id") or ""))]
        return {"count": len(bad), "unit": "card",
                "detail": f"oversized={len(bad)} of rfc_cards; cap={_ac.CALLBACK_DATA_MAX}B"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "card", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_tg_stale_delivery() -> dict:
    """کارتی که رکوردش می‌گوید PENDING و ساعت‌هاست همان‌جا مانده.

    PENDING یعنی `send_text` شکست خورد. اگر ساعت‌ها بماند، یعنی کسی retry نمی‌کند
    و مالک منتظرِ چیزی است که هرگز نمی‌آید — بدونِ اینکه جایی خطایی ثبت شده باشد.
    """
    try:
        p = opslib.STATE_DIR / "pulse" / "pending-cards.json"
        if not p.exists():
            return {"count": -1, "unit": "card", "detail": "pending-cards.json غایب"}
        doc = json.loads(p.read_text("utf-8"))
        if not isinstance(doc, dict) or not doc:
            return {"count": -1, "unit": "card", "detail": "هیچ کارتِ ثبت‌شده‌ای نیست"}
        min_age_s = 6 * 3600.0
        now = time.time()
        stale = 0
        for v in doc.values():
            if not isinstance(v, dict) or str(v.get("delivery") or "") != "PENDING":
                continue
            # زمانِ مرجع: expires_at منهای TTL، وگرنه mtimeِ خودِ فایل
            born = v.get("created_at") or v.get("recorded_at")
            try:
                born = float(born) if born is not None else (float(v.get("expires_at", 0)) - 86400.0)
            except (TypeError, ValueError):
                born = 0.0
            if born and (now - born) > min_age_s:
                stale += 1
        return {"count": stale, "unit": "card",
                "detail": f"pending_older_than_6h={stale} of records={len(doc)}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "card", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_flags_armed_not_loaded() -> dict:
    """فلگی که در flags.cmd مسلح است ولی پروسهٔ زنده هرگز نخوانده‌اش.

    بیماریِ تکرارشوندهٔ این مخزن: flags.cmd سرِ بوت `source` می‌شود، پس هر ویرایشِ
    بعد از بوت **هیچ اثری ندارد** — درحالی‌که فایل می‌گوید «روشن». ۲۰۲۶-۰۷-۲۶ سه
    بار پشتِ‌سرِ هم همین اتفاق افتاد. count = دقیقه‌های فاصلهٔ نوشتن از بوت.
    """
    try:
        f = OPS / "OCTOPUS-flags.cmd"
        s = opslib.STATE_DIR / "ORGANISM-STATE.code"
        if not f.exists() or not s.exists():
            return {"count": -1, "unit": "minute", "detail": "flags.cmd یا ORGANISM-STATE غایب"}
        booted = json.loads(s.read_text("utf-8")).get("booted")
        if not booted:
            return {"count": -1, "unit": "minute", "detail": "زمانِ بوت ثبت نشده"}
        bt = time.mktime(time.strptime(str(booted)[:19], "%Y-%m-%dT%H:%M:%S"))
        lag_min = (f.stat().st_mtime - bt) / 60.0
        if lag_min <= 0:
            return {"count": 0, "unit": "minute",
                    "detail": f"flags.cmd قدیمی‌تر از بوت — بارگذاری شده (lag={lag_min:.1f}m)"}
        return {"count": int(lag_min), "unit": "minute",
                "detail": f"flags.cmd {lag_min:.1f} دقیقه بعد از بوت نوشته شد — بارگذاری نشده"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "minute", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_cmd_lone_lf() -> dict:
    """فایلِ .cmd/.bat که خط‌پایانِ CRLFش به LF تبدیل شده.

    ابزارِ ویرایشِ ایجنت‌ها این کار را می‌کند و cmd.exe فایلِ LF-only را روی
    ساختارهای بلوکی (if/for/goto/label) بد پارس می‌کند. ۲۰۲۶-۰۷-۲۶ خودِ
    OCTOPUS-flags.cmd با ۴۴۲ خطِ LF پیدا شد — آن‌بار بی‌ضرر، ولی تلهٔ خفته.
    """
    try:
        bad = []
        for p in list(OPS.glob("*.cmd")) + list(OPS.glob("*.bat")) \
                + list(OPS.glob("*/*.cmd")) + list(OPS.glob("*/*.bat")):
            try:
                d = p.read_bytes()
            except OSError:
                continue
            lone = d.count(b"\n") - d.count(b"\r\n")
            if lone > 0:
                bad.append(f"{p.name}:{lone}")
        return {"count": len(bad), "unit": "file",
                "detail": ("lone-LF files: " + ", ".join(bad[:6])) if bad else "همه CRLF"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "file", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_discovery_seen_lag() -> dict:
    """چند روز است که کشف‌ها نوشته می‌شوند ولی نشانگرِ «دیده‌شد» تکان نخورده؟

    ۲۰۲۶-۰۷-۲۶ اندازه‌گیری شد: discoveries.jsonl همان روز نوشته شده بود و
    discoveries-seen.json از ۲۰۲۶-۰۷-۱۹ — هفت روز فاصله.
    """
    try:
        a = opslib.STATE_DIR / "discoveries.jsonl"
        b = opslib.STATE_DIR / "discoveries-seen.json"
        if not a.exists():
            return {"count": -1, "unit": "day", "detail": "discoveries.jsonl غایب"}
        if not b.exists():
            return {"count": -1, "unit": "day", "detail": "نشانگرِ seen هرگز ساخته نشده"}
        lag_days = (a.stat().st_mtime - b.stat().st_mtime) / 86400.0
        return {"count": max(0, int(lag_days)), "unit": "day",
                "detail": f"discoveries newer than seen-marker by {lag_days:.2f}d"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "day", "detail": f"probe-failed:{type(e).__name__}"}


# enrich base probes with full contract fields (producer + research_contract)
for _k, _s in list(PROBES.items()):
    _s.setdefault("hypothesis", _s.get("question", "defect exists"))
    _s.setdefault("expected_artifact", f"measured count for {_k}")
    _s.setdefault("falsification", [f"measured count <= floor ({_s.get('floor', 0)})"])
    _s.setdefault("fix_hint", "see probe subject")
    _s.setdefault("unit", "ops")

PROBES["c6_undelivered_cards"] = {
    "measure": _probe_c6_undelivered_cards, "floor": 0, "unit": "card",
    "subject": "state/c6/hypothesis-queue.jsonl → owner card delivery",
    "question": "آیا آزمایشی تمام شده که حکمش هرگز به مالک نرسیده؟",
    "hypothesis": ("finished C6 rows carry card_delivered=false, so a real verdict "
                   "never reached the owner and no error was recorded anywhere."),
    "expected_artifact": "count of DONE rows with card_delivered false",
    "falsification": ["undelivered == 0 (every finished experiment was reported)"],
    "fix_hint": "c6_trigger.redeliver_undelivered_cards above the early return",
}
PROBES["tg_oversized_callback"] = {
    "measure": _probe_tg_oversized_callback, "floor": 0, "unit": "card",
    "subject": "state/pulse/pending-cards.json → Telegram 64B callback cap",
    "question": "آیا کارتی ثبت شده که شناسه‌اش از سقفِ ۶۴ بایت رد می‌شود؟",
    "hypothesis": ("a recorded card's rfc_id makes callback_data exceed 64 bytes; "
                   "Telegram 400s the whole message and the card vanishes silently."),
    "expected_artifact": "count of rfc cards whose callback_data would exceed the cap",
    "falsification": ["oversized == 0 (every recorded card is sendable)"],
    "fix_hint": "shorten the id via a stable digest; approval_channel.callback_fits guards it",
}
PROBES["tg_stale_delivery"] = {
    "measure": _probe_tg_stale_delivery, "floor": 0, "unit": "card",
    "subject": "state/pulse/pending-cards.json → delivery=PENDING backlog",
    "question": "آیا کارتی ساعت‌هاست PENDING مانده و کسی retry نمی‌کند؟",
    "hypothesis": ("cards sit at delivery=PENDING for hours because send failed and "
                   "nothing retries; the owner waits for something that never arrives."),
    "expected_artifact": "count of PENDING delivery records older than 6h",
    "falsification": ["stale == 0 (no delivery has been stuck for hours)"],
    "fix_hint": "a retry pass over PENDING records, or surface them on the cockpit",
}
PROBES["flags_armed_not_loaded"] = {
    "measure": _probe_flags_armed_not_loaded, "floor": 0, "unit": "minute",
    "subject": "OCTOPUS-flags.cmd mtime vs ORGANISM-STATE booted",
    "question": "آیا فلگی مسلح شده که پروسهٔ زنده هرگز نخوانده؟",
    "hypothesis": ("flags.cmd was written after the organism booted, so every flag "
                   "edited since is armed on disk and absent from the running process."),
    "expected_artifact": "minutes between organism boot and the last flags.cmd write",
    "falsification": ["flags.cmd is older than the boot timestamp (already loaded)"],
    "fix_hint": "restart the affected process; flags.cmd is sourced only at boot",
}
PROBES["cmd_lone_lf"] = {
    "measure": _probe_cmd_lone_lf, "floor": 0, "unit": "file",
    "subject": "_ops/*.cmd and *.bat line endings",
    "question": "آیا فایلِ .cmd ای هست که خط‌پایانش به LF خراب شده؟",
    "hypothesis": ("a .cmd/.bat file lost its CRLF endings to an editing tool; cmd.exe "
                   "mis-parses LF-only batch files that contain block constructs."),
    "expected_artifact": "count of .cmd/.bat files containing lone LF bytes",
    "falsification": ["every batch file is pure CRLF"],
    "fix_hint": "byte-level restore: read bytes, normalise to CRLF, verify lone-LF == 0",
}
PROBES["discovery_seen_lag"] = {
    "measure": _probe_discovery_seen_lag, "floor": 2, "unit": "day",
    "subject": "state/discoveries.jsonl vs discoveries-seen.json",
    "question": "آیا کشف‌ها نوشته می‌شوند ولی نشانگرِ «دیده‌شد» جا مانده؟",
    "hypothesis": ("discoveries keep being appended while the seen-marker has not moved "
                   "for days, so the consumer that should read them is not running."),
    "expected_artifact": "integer days the seen-marker lags the discoveries file",
    "falsification": ["lag <= 2 days (the consumer is keeping up)"],
    "fix_hint": "find the consumer that should advance discoveries-seen.json",
}

# romajan probes — registered always; measure() self-gates on ROMAJAN_FLAG
PROBES["romajan_new_claims"] = {
    "measure": _probe_romajan_new_claims,
    "floor": 0,
    "unit": "claim",
    "subject": "F:/romajan claims ledgers → C6 hypothesis feed",
    "question": "آیا romajan ادعای verified/executed جدیدی دارد که C6 هنوز ندیده؟",
    "hypothesis": (
        "romajan claims_ledger holds verified/executed claims not yet translated into "
        "C6 hypothesis-queue rows; wiring them yields falsifiable math hypotheses."
    ),
    "expected_artifact": "count of unseen verified/executed romajan claims",
    "falsification": ["unseen verified claims == 0 (all already ingested or none exist)"],
    "fix_hint": (
        "for each new claim id, append a mechanism_count/romajan_claim row and "
        "add id to state/c6/romajan-seen.json (append-only)"
    ),
}
PROBES["romajan_engine_idle"] = {
    "measure": _probe_romajan_engine_idle,
    "floor": 7,
    "unit": "day",
    "subject": "F:/romajan engine freshness",
    "question": "آیا آزمایشگاهِ romajan بیش از ۷ روز است لمس نشده؟",
    "hypothesis": (
        "romajan lab artifacts are stale (>7d); a scheduled read-only refresh or owner "
        "nudge would restore the math hypothesis pipeline."
    ),
    "expected_artifact": "integer days since newest romajan artifact mtime",
    "falsification": ["age_days <= 7"],
    "fix_hint": "owner runs engine_a/evalharness or touches ledger; no auto-exec from C6",
}
