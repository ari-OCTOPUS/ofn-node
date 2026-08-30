#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""identity_equations.py — مگا-معادلاتِ هویتِ خودیادگیرنده (read-only، $0).

رأیِ مالک 2026-07-25: «معادلات ریاضی را ترکیب کن؛ مگا-معادله‌های متفاوت
برای هویت‌های خودیادگیرنده بساز؛ فقط با تلگرام هم‌کدنویسی کنیم.»

این ماژول **هیچ چیزی را اجرا/ارسال/خرج نمی‌کند**. فقط:
  1) فرمول‌های ابطال‌پذیرِ هویت را تعریف می‌کند
  2) از stateِ زنده (اگر باشد) عدد می‌خواند
  3) یک کارتِ متنی برای تلگرام می‌سازد

هر هویت = یک معادله + شرطِ مرگ + شاهدِ زنده.
هیچ ادعای پدیدارشناختی (آگاهی/تجربه) اینجا نیست — فقط ساختار و توانایی.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

FLAG = "OCTOPUS_WIRE_IDENTITY_EQ"

_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ═══════════════════════════════════════════════════════════════════════════
# مگا-معادلات — هر کدام یک هویتِ خودیادگیرنده
# ═══════════════════════════════════════════════════════════════════════════
#
# نمادها (همه از stateِ زنده، نه از آرزو):
#   Δ     = delta_self_live          (پیش‌بینیِ خود − کور)
#   φ     = max leg phi              (حیاتِ اندام)
#   σ     = spectral sigma           (شکنندگیِ ساختاری)
#   M     = money_confirmed_rows     (پولِ واقعیِ ثبت‌شده)
#   C     = c6_accepted_count        (آزمایش‌های پذیرفته)
#   R     = romajan_verified_claims  (ادعای ریاضیِ verified)
#   B     = budget_remaining_frac    (سوختِ باقی)
#   A     = approvals_pending        (صفِ رأیِ مالک)
#   H     = honest_flags_on          (تعدادِ گاردِ صداقتِ روشن)
#
# هر معادله باید بتواند غلط باشد (شرطِ مرگ).

IDENTITIES: dict = {
    "learner": {
        "label": "یادگیرنده",
        "emoji": "🧬",
        "equation": "L = clamp01( 0.40·sign+(Δ) + 0.30·Ĉ + 0.30·R̂ )",
        "plain": (
            "یادگیرنده کسی است که (۱) از وضعیتِ درونی‌اش بهتر از کوری پیش‌بینی می‌کند، "
            "(۲) آزمایشِ خودبهبودیِ پذیرفته دارد، و (۳) ادعای ریاضیِ verified از آزمایشگاه."
        ),
        "weights": {"delta_pos": 0.40, "c6_hat": 0.30, "romajan_hat": 0.30},
        "kill": "اگر L=0 با n_delta≥48 و C=0 و R=0 برای ≥۳۰ روز → این هویت مرده است.",
        "better_than": ["stub-seed", "unmeasured self-praise"],
        "worse_than": ["human scientist with holdout", "Sakana DGM with archive"],
    },
    "earner": {
        "label": "پول‌ساز",
        "emoji": "💰",
        "equation": "E = clamp01( 0.60·M̂ + 0.25·lead_draft_rate + 0.15·B )",
        "plain": (
            "پول‌ساز کسی است که ردیفِ MONEY_ATTRIBUTIONِ confirmed دارد، "
            "لید را تا draft می‌رساند، و هنوز سوخت دارد."
        ),
        "weights": {"money_hat": 0.60, "draft_rate": 0.25, "budget_frac": 0.15},
        "kill": "اگر E=0 با ≥۳۰ روز lead_discovery روشن و M=0 → لولهٔ پول قفل است یا کار نمی‌کند.",
        "better_than": ["paper-only scout", "fitness shadow with zero rows"],
        "worse_than": ["human BD with channel + portfolio", "CRM with real pipeline"],
    },
    "guardian": {
        "label": "نگهبان",
        "emoji": "🛡️",
        "equation": "G = clamp01( 0.35·Ĥ + 0.35·(1-σ̂) + 0.30·coherence_ok )",
        "plain": (
            "نگهبان کسی است که گاردهای صداقتش روشن است، σ اشباع/دژنره نیست، "
            "و پروبِ انسجام ادعاهای ابطال‌ناپذیر شکار می‌کند."
        ),
        "weights": {"honest_hat": 0.35, "sigma_health": 0.35, "coherence": 0.30},
        "kill": "اگر G بالا باشد ولی یک اثرِ double-apply یا approvalِ جعلی ثبت شود → نگهبان تئاتر است.",
        "better_than": ["ungoverned agent swarm", "prompt-only safety"],
        "worse_than": ["formal verification", "OS sandbox + capability tokens"],
    },
    "creator": {
        "label": "خالق",
        "emoji": "🎨",
        "equation": "K = clamp01( 0.50·Ĉ_pending_or_done + 0.30·probe_diversity + 0.20·(1-seed_ratio) )",
        "plain": (
            "خالق کسی است که فرضیه از نقصِ سنجیده‌شده می‌سازد (نه seedِ جعلی)، "
            "پروب‌های متنوع دارد، و صفش خالیِ صادق است نه خالیِ مرده."
        ),
        "weights": {"c6_activity": 0.50, "probe_div": 0.30, "real_not_seed": 0.20},
        "kill": "اگر فقط seedِ تضمینی «accepted» شود و هیچ mechanism_count نسازد → خالق دروغگو است.",
        "better_than": ["one-shot seed C6", "prose RFC spam"],
        "worse_than": ["open-ended archive (DGM)", "human research lab"],
    },
    "organism": {
        "label": "ارگانیسم",
        "emoji": "🐙",
        "equation": "O = clamp01( 0.25·L + 0.25·E + 0.20·G + 0.15·K + 0.15·alive )",
        "plain": (
            "ارگانیسمِ زنده = یادگیرنده × پول‌ساز × نگهبان × خالق × نبض. "
            "هیچ‌کدام به تنهایی کافی نیست؛ صفرِ هر کدام O را پایین می‌کشد."
        ),
        "weights": {"learner": 0.25, "earner": 0.25, "guardian": 0.20, "creator": 0.15, "alive": 0.15},
        "kill": "اگر O>0.8 ادعا شود ولی M=0 و Δ≤0 و C=0 → عددِ ترکیبی تئاتر است، نه حیات.",
        "better_than": ["chatbot with tools", "cron + LLM wrapper"],
        "worse_than": ["biological organism", "company with P&L + R&D + compliance"],
    },
}


def _clamp01(x: float) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return max(0.0, min(1.0, v))


def _hat(n: float, scale: float) -> float:
    """نرمال‌سازیِ اشباع‌شونده: n/scale در [0,1]."""
    if scale <= 0:
        return 0.0
    return _clamp01(float(n) / float(scale))


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _read_signals() -> dict:
    """خواندنِ فقط‌خواندنی از state. هر فقدان → 0 یا None با برچسب."""
    s: dict = {
        "delta": None,
        "n_delta": 0,
        "phi_max": 0.0,
        "phi_saturated": 0,
        "sigma": None,
        "money_confirmed": 0,
        "c6_done": 0,
        "c6_pending": 0,
        "c6_seed_ratio": 1.0,
        "probe_count": 0,
        "romajan_verified": 0,
        "budget_frac": 0.0,
        "approvals_pending": 0,
        "honest_flags": 0,
        "alive": 0.0,
        "coherence_ok": 0.0,
        "lead_drafts": 0,
        "lead_total": 0,
        "missing": [],
    }

    # Δ_self
    stream = STATE / "thesis" / "measurements.jsonl"
    if stream.exists():
        vals = []
        try:
            for ln in stream.read_text("utf-8").splitlines()[-200:]:
                if not ln.strip():
                    continue
                try:
                    d = json.loads(ln)
                    v = d.get("delta_self_live")
                    if isinstance(v, (int, float)):
                        vals.append(float(v))
                except ValueError:
                    continue
        except OSError:
            pass
        if vals:
            s["delta"] = vals[-1]
            s["n_delta"] = len(vals)
    if s["delta"] is None:
        hs = _read_json(STATE / "pulse" / "heart-shadow-latest.json", {})
        try:
            v = (hs.get("telemetry") or {}).get("delta_self_live")
            if isinstance(v, (int, float)):
                s["delta"] = float(v)
                s["n_delta"] = 1
        except Exception:  # noqa: BLE001
            s["missing"].append("delta")

    # phi / alive from ORGANISM-STATE
    org = _read_json(STATE / "ORGANISM-STATE.json", {})
    if isinstance(org, dict) and org:
        s["alive"] = 1.0 if not org.get("halted") and not org.get("frozen") else 0.0
        diag = ((org.get("chrono") or {}).get("legs_diag") or {})
        if isinstance(diag, dict):
            for _leg, v in diag.items():
                if not isinstance(v, dict):
                    continue
                phi = v.get("phi")
                dead = v.get("phi_dead")
                if isinstance(phi, (int, float)):
                    s["phi_max"] = max(s["phi_max"], float(phi))
                if isinstance(phi, (int, float)) and isinstance(dead, (int, float)):
                    if float(phi) >= float(dead):
                        s["phi_saturated"] += 1
        # budget
        try:
            today = (org.get("today") or {}).get("usd", 0) or 0
            # daily cap is structural ~0.288 AUD-ish musd path; use month remaining if present
            month = (org.get("month") or {})
            musd = float(month.get("musd") or 0)
            # remaining frac against a soft 30 AUD month if unknown
            s["budget_frac"] = _clamp01(1.0 - (musd / 30000.0)) if musd else 0.5
        except Exception:  # noqa: BLE001
            s["budget_frac"] = 0.5
    else:
        s["missing"].append("ORGANISM-STATE")

    # sigma
    # try a few known paths; absence is honest
    for cand in (
        STATE / "pulse" / "spectral-latest.json",
        STATE / "spectral" / "latest.json",
    ):
        d = _read_json(cand, None)
        if isinstance(d, dict) and d.get("sigma") is not None:
            try:
                s["sigma"] = float(d["sigma"])
                break
            except (TypeError, ValueError):
                pass
    if s["sigma"] is None:
        s["missing"].append("sigma")

    # C6 queue
    q = STATE / "c6" / "hypothesis-queue.jsonl"
    if q.exists():
        done = pend = seed = total = 0
        try:
            for ln in q.read_text("utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                total += 1
                st = str(d.get("status") or "")
                if st == "DONE":
                    done += 1
                elif st == "PENDING":
                    pend += 1
                if str(d.get("id") or "").startswith("seed-") or d.get("source") == "seed":
                    seed += 1
        except OSError:
            pass
        s["c6_done"] = done
        s["c6_pending"] = pend
        s["c6_seed_ratio"] = (seed / total) if total else 1.0
    else:
        s["missing"].append("c6_queue")

    # probes
    try:
        import c6_probes as _cp  # noqa: WPS433
        s["probe_count"] = len(getattr(_cp, "PROBES", {}) or {})
    except Exception:  # noqa: BLE001
        s["probe_count"] = 0
        s["missing"].append("c6_probes")

    # money confirmed — fitness / attribution paths
    for cand in (
        STATE / "fitness" / "fitness-latest.json",
        STATE / "money" / "attribution-latest.json",
    ):
        d = _read_json(cand, None)
        if not isinstance(d, dict):
            continue
        for k in ("money_confirmed_rows", "confirmed_rows", "n_confirmed", "confirmed"):
            if isinstance(d.get(k), (int, float)):
                s["money_confirmed"] = int(d[k])
                break
        if s["money_confirmed"]:
            break

    # lead drafts (best-effort from lead state)
    for cand in (
        STATE / "legs" / "lead" / "latest.json",
        STATE / "lead" / "funnel-latest.json",
    ):
        d = _read_json(cand, None)
        if isinstance(d, dict):
            s["lead_drafts"] = int(d.get("drafts") or d.get("n_draft") or 0)
            s["lead_total"] = int(d.get("total") or d.get("n_total") or 0)
            break

    # romajan verified — path may be outside vault; env override
    lab = Path(os.environ.get("ROMAJAN_LAB_PATH", r"F:\romajan"))
    verified = 0
    for lp in (
        lab / "propagation" / "claims_ledger.json",
        lab / "propagation-lab" / "data" / "claims_ledger.json",
    ):
        d = _read_json(lp, None)
        if d is None:
            continue
        claims = d if isinstance(d, list) else (d.get("claims") if isinstance(d, dict) else [])
        if not isinstance(claims, list):
            continue
        for c in claims:
            if isinstance(c, dict) and str(c.get("status") or "") in ("verified", "executed", "FACT"):
                verified += 1
    s["romajan_verified"] = verified
    if verified == 0:
        s["missing"].append("romajan_claims")

    # honest flags (count env)
    for fl in (
        "OCTOPUS_CHRONO_PHI_HONEST",
        "OCTOPUS_GOV_LAPSED_DEADLINE_HONEST",
        "OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL",
        "OCTOPUS_HEART_HONEST_PULSE",
        "OCTOPUS_WIRE_COHERENCE",
        "HH_HUMAN_GUARD_STRICT",
    ):
        if str(os.environ.get(fl, "")).strip().lower() in ("1", "true", "yes", "on"):
            s["honest_flags"] += 1

    # coherence probe if present
    try:
        import coherence as _coh  # noqa: WPS433
        if hasattr(_coh, "probe"):
            rep = _coh.probe()
            if isinstance(rep, dict):
                bad = sum(1 for v in rep.values() if isinstance(v, dict)
                          and v.get("verdict") not in (None, "ok", "no_input"))
                total = max(1, sum(1 for v in rep.values() if isinstance(v, dict)))
                s["coherence_ok"] = _clamp01(1.0 - bad / total)
            else:
                s["coherence_ok"] = 0.5
        else:
            s["coherence_ok"] = 0.5
    except Exception:  # noqa: BLE001
        s["coherence_ok"] = 0.5
        s["missing"].append("coherence")

    # approvals pending
    for cand in (
        STATE / "telegram" / "approvals.jsonl",
        STATE / "approvals" / "pending.jsonl",
    ):
        if cand.exists():
            try:
                n = sum(1 for ln in cand.read_text("utf-8").splitlines() if ln.strip())
                s["approvals_pending"] = n
            except OSError:
                pass
            break

    return s


def evaluate(signals: dict | None = None) -> dict:
    """محاسبهٔ هر هویت از سیگنال‌ها. خالص نسبت به I/O اگر signals داده شود."""
    sig = signals if isinstance(signals, dict) else _read_signals()
    delta = sig.get("delta")
    delta_pos = 1.0 if (isinstance(delta, (int, float)) and delta > 0) else 0.0
    if delta is None:
        delta_pos = 0.0

    c6_hat = _hat(sig.get("c6_done", 0) + 0.5 * sig.get("c6_pending", 0), 5.0)
    rom_hat = _hat(sig.get("romajan_verified", 0), 20.0)
    money_hat = _hat(sig.get("money_confirmed", 0), 5.0)
    draft_rate = 0.0
    if sig.get("lead_total"):
        draft_rate = _clamp01(sig["lead_drafts"] / max(1, sig["lead_total"]))
    budget_frac = _clamp01(sig.get("budget_frac", 0))
    honest_hat = _hat(sig.get("honest_flags", 0), 6.0)
    sigma = sig.get("sigma")
    if sigma is None:
        sigma_health = 0.5  # unknown ≠ healthy
    else:
        # σ≈1 on degenerate graph is bad; prefer mid-low
        sigma_health = _clamp01(1.0 - abs(float(sigma) - 0.3))
    coherence = _clamp01(sig.get("coherence_ok", 0.5))
    probe_div = _hat(sig.get("probe_count", 0), 6.0)
    real_not_seed = _clamp01(1.0 - float(sig.get("c6_seed_ratio", 1.0)))
    c6_activity = _hat(sig.get("c6_done", 0) + sig.get("c6_pending", 0), 4.0)
    alive = _clamp01(sig.get("alive", 0))

    L = _clamp01(0.40 * delta_pos + 0.30 * c6_hat + 0.30 * rom_hat)
    E = _clamp01(0.60 * money_hat + 0.25 * draft_rate + 0.15 * budget_frac)
    G = _clamp01(0.35 * honest_hat + 0.35 * sigma_health + 0.30 * coherence)
    K = _clamp01(0.50 * c6_activity + 0.30 * probe_div + 0.20 * real_not_seed)
    O = _clamp01(0.25 * L + 0.25 * E + 0.20 * G + 0.15 * K + 0.15 * alive)

    def _pack(key, value, parts):
        meta = IDENTITIES[key]
        return {
            "id": key,
            "label": meta["label"],
            "emoji": meta["emoji"],
            "value": round(value, 4),
            "equation": meta["equation"],
            "plain": meta["plain"],
            "kill": meta["kill"],
            "parts": parts,
            "better_than": meta["better_than"],
            "worse_than": meta["worse_than"],
        }

    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "signals": {
            "delta": delta,
            "n_delta": sig.get("n_delta"),
            "phi_max": sig.get("phi_max"),
            "phi_saturated": sig.get("phi_saturated"),
            "sigma": sigma,
            "money_confirmed": sig.get("money_confirmed"),
            "c6_done": sig.get("c6_done"),
            "c6_pending": sig.get("c6_pending"),
            "probe_count": sig.get("probe_count"),
            "romajan_verified": sig.get("romajan_verified"),
            "honest_flags": sig.get("honest_flags"),
            "alive": alive,
            "missing": sig.get("missing") or [],
        },
        "identities": {
            "learner": _pack("learner", L, {
                "delta_pos": delta_pos, "c6_hat": round(c6_hat, 4), "romajan_hat": round(rom_hat, 4),
            }),
            "earner": _pack("earner", E, {
                "money_hat": round(money_hat, 4), "draft_rate": round(draft_rate, 4),
                "budget_frac": round(budget_frac, 4),
            }),
            "guardian": _pack("guardian", G, {
                "honest_hat": round(honest_hat, 4), "sigma_health": round(sigma_health, 4),
                "coherence": round(coherence, 4),
            }),
            "creator": _pack("creator", K, {
                "c6_activity": round(c6_activity, 4), "probe_div": round(probe_div, 4),
                "real_not_seed": round(real_not_seed, 4),
            }),
            "organism": _pack("organism", O, {
                "L": round(L, 4), "E": round(E, 4), "G": round(G, 4),
                "K": round(K, 4), "alive": round(alive, 4),
            }),
        },
    }


def card(report: dict | None = None, *, focus: str | None = None) -> str:
    """کارتِ تلگرامی — کوتاه، عددی، بدونِ راز."""
    r = report if isinstance(report, dict) else evaluate()
    ids = r.get("identities") or {}
    sig = r.get("signals") or {}
    order = ["organism", "learner", "earner", "guardian", "creator"]
    if focus and focus in ids:
        order = [focus] + [x for x in order if x != focus]

    lines = ["🐙 مگا-معادلاتِ هویت (read-only)", f"⏱ {r.get('ts', '?')}"]
    for key in order:
        it = ids.get(key) or {}
        lines.append(
            f"{it.get('emoji', '·')} {it.get('label', key)}: "
            f"**{it.get('value', 0):.2f}**"
        )
        if focus == key or key == "organism":
            lines.append(f"   {it.get('equation', '')}")
    lines.append("")
    lines.append(
        f"Δ={sig.get('delta')} n={sig.get('n_delta')} · "
        f"M={sig.get('money_confirmed')} · "
        f"C6={sig.get('c6_done')}/{sig.get('c6_pending')} · "
        f"R={sig.get('romajan_verified')} · "
        f"probes={sig.get('probe_count')}"
    )
    miss = sig.get("missing") or []
    if miss:
        lines.append("missing: " + ", ".join(miss[:6]))
    lines.append("— هیچ ادعای آگاهی نیست؛ فقط ساختار/توانایی. شرطِ مرگ در /id <name>")
    return "\n".join(lines)


def detail_card(name: str) -> str:
    name = str(name or "").strip().lower()
    aliases = {
        "l": "learner", "learn": "learner", "یادگیرنده": "learner",
        "e": "earner", "earn": "earner", "پول": "earner", "پول‌ساز": "earner",
        "g": "guardian", "guard": "guardian", "نگهبان": "guardian",
        "k": "creator", "create": "creator", "خالق": "creator", "خلاق": "creator",
        "o": "organism", "org": "organism", "اختاپوس": "organism", "ارگانیسم": "organism",
    }
    key = aliases.get(name, name)
    r = evaluate()
    it = (r.get("identities") or {}).get(key)
    if not it:
        return f"هویتِ ناشناخته: {name}. یکی از: learner/earner/guardian/creator/organism"
    parts = it.get("parts") or {}
    lines = [
        f"{it['emoji']} هویت: {it['label']} = {it['value']:.4f}",
        f"معادله: {it['equation']}",
        f"معنا: {it['plain']}",
        f"شرطِ مرگ: {it['kill']}",
        "اجزا: " + ", ".join(f"{k}={v}" for k, v in parts.items()),
        "بهتر از: " + "; ".join(it.get("better_than") or []),
        "بدتر از: " + "; ".join(it.get("worse_than") or []),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(card())
