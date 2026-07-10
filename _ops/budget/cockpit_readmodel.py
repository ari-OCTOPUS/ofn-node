#!/usr/bin/env python3
"""cockpit_readmodel.py — read-modelِ فقط‌خواندنیِ کابینِ تلگرام (Cockpit v2).

قراردادِ سخت (INV-7 مگاپرامپت TELEGRAM-BRAIN-COCKPIT-v2-FULL-BODY):
  - هرگز `import organism` نمی‌کند؛ هیچ subsystem cycle را اجرا نمی‌کند.
  - فقط می‌خواند: `_ops/state/*.json`، فایل‌های مشتقِ neural، و `chrono.db`
    (اتصالِ read-only با URI `mode=ro&immutable=1` و timeout=1 — هرگز pacemaker را بلاک نمی‌کند).
  - stdlib-only: json / os / pathlib / sqlite3 / datetime / re.
  - fail-soft مطلق: نبود/خرابیِ هر فایل → {} یا None؛ هیچ استثنایی به caller نمی‌رسد.
  - هرگز فایل‌های secret (OWNER-PROFILE*, *.env, wallet, seed, key) را نمی‌خواند —
    فقط فایل‌های نام‌بردهٔ صریح در همین ماژول.

مصرف‌کننده: TelegramApprovalChannel (کارت‌های تب‌های ۱..۸). قابل‌تزریق برای تست
(state_dir/ops_dir tmp).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ── flagهای wiring (آینهٔ dashboard/server.py:WIRE_FLAGS — sync دستی، ۱۹ عدد) ──
# chamber_t عمداً غایب است: RED — خارج از profile، فقط verdict صریحِ مالک (P5).
WIRE_FLAG_NAMES = [
    "OCTOPUS_WIRE_DOCTOR", "OCTOPUS_WIRE_NEURAL", "OCTOPUS_WIRE_UNIFIED",
    "OCTOPUS_WIRE_LEAD", "OCTOPUS_WIRE_LEAD_TICK", "OCTOPUS_WIRE_SCHOOL",
    "OCTOPUS_WIRE_CONSOLIDATION", "OCTOPUS_WIRE_EVOLUTION", "OCTOPUS_WIRE_BOX",
    "OCTOPUS_WIRE_IDEAS", "OCTOPUS_WIRE_SPECTRAL", "OCTOPUS_WIRE_BARBELL",
    "OCTOPUS_WIRE_DEBATE", "OCTOPUS_WIRE_SCHEDULER", "OCTOPUS_WIRE_RECONCILE",
    "OCTOPUS_WIRE_FITNESS", "OCTOPUS_WIRE_EPISTEMICS", "OCTOPUS_WIRE_SELFHEAL",
    "OCTOPUS_WIRE_BIO",
]
PAPER_FULL_FLAGS = {
    "OCTOPUS_WIRE_DOCTOR", "OCTOPUS_WIRE_NEURAL", "OCTOPUS_WIRE_UNIFIED",
    "OCTOPUS_WIRE_LEAD", "OCTOPUS_WIRE_SCHOOL", "OCTOPUS_WIRE_CONSOLIDATION",
    "OCTOPUS_WIRE_EVOLUTION", "OCTOPUS_WIRE_BOX", "OCTOPUS_WIRE_LEAD_TICK",
    "OCTOPUS_WIRE_IDEAS", "OCTOPUS_WIRE_SPECTRAL",
}
# cadenceها (آینهٔ dashboard/server.py:CADENCE_FLAGS — نامِ env → پیش‌فرض)
CADENCE_DEFAULTS = {
    "CHRONO_DOCTOR_EVERY_N_BEATS": "1440",
    "CHRONO_CONSOLIDATION_EVERY_N_BEATS": "720",
    "CHRONO_AFFERENT_EVERY_N_BEATS": "1440",
    "CHRONO_EPISTEMICS_EVERY_N_BEATS": "720",
    "CHRONO_IDEAS_EVERY_N_BEATS": "1440",
}


def _read_json(p: Path):
    """خواندنِ امن JSON؛ نبود/خرابی → {}."""
    try:
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _tail_lines(p: Path, n: int) -> list[str]:
    try:
        if not p.exists():
            return []
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return []


def _age_minutes(ts_iso: str) -> float | None:
    """سنِ یک timestamp ایزو به دقیقه؛ خرابی → None."""
    if not ts_iso:
        return None
    try:
        t = str(ts_iso).replace("Z", "+00:00")[:19]
        dt = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
        # ارگانیسم timestampها را naive-local می‌نویسد (opslib.now_iso)؛ پس با
        # datetime.now() ِ naive-local مقایسه می‌کنیم، نه UTC (وگرنه offsetِ منطقهٔ
        # زمانی سنِ منفی می‌سازد — سیدنی UTC+10).
        return (datetime.now() - dt).total_seconds() / 60.0
    except (ValueError, TypeError):
        return None


class CockpitReadModel:
    """خوانندهٔ واحدِ همهٔ منابعِ read کابین. هر متد fail-soft است."""

    def __init__(self, state_dir=None, ops_dir=None):
        here = Path(__file__).resolve().parent            # _ops/budget
        self.ops = Path(ops_dir) if ops_dir else here.parent   # _ops
        self.state = Path(state_dir) if state_dir else (self.ops / "state")

    # ── خواننده‌های سادهٔ state/*.json ────────────────────────────────────────
    def read_state(self) -> dict:
        return _read_json(self.state / "ORGANISM-STATE.json")

    def read_sigma(self) -> dict:
        return _read_json(self.state / "replication-latest.json")

    def read_telemetry(self) -> dict:
        return _read_json(self.state / "telemetry-latest.json")

    def read_fitness(self) -> dict:
        return _read_json(self.state / "fitness-latest.json")

    def read_school(self) -> dict:
        return _read_json(self.state / "school-awareness.json")

    def read_latent(self) -> dict:
        return _read_json(self.state / "latent-vectors.json")

    def read_bcm(self) -> dict:
        return _read_json(self.state / "bcm-weights.json")

    def read_sparse(self) -> dict:
        return _read_json(self.state / "sparse-predictor.json")

    def read_idea(self) -> dict:
        return _read_json(self.state / "idea-graph-latest.json")

    def read_chamber_t(self) -> dict:
        return _read_json(self.state / "chamber-temperature.json")

    def read_fisher(self) -> dict:
        return _read_json(self.state / "fisher-latest.json")

    def read_epi(self) -> dict:
        return _read_json(self.state / "epi-latest.json")

    def read_box(self) -> dict:
        return _read_json(self.state / "doctor_box.json")

    def read_phase(self) -> dict:
        return _read_json(self.state / "phase-gate-state.json")

    def read_channels(self) -> dict:
        return _read_json(self.state / "channel-status.json")

    def read_lab(self) -> dict:
        return _read_json(self.state / "lab_state.json")

    def read_bundle(self) -> dict:
        return _read_json(self.state / "export" / "octopus-status-bundle.json")

    def read_consolidation(self) -> dict:
        return _read_json(self.ops / "neural" / "consolidation.json")

    def read_hebbian(self) -> dict:
        return _read_json(self.ops / "neural" / "hebbian.json")

    def read_heart(self) -> dict:
        """HH-P7: قلبِ ترکیبی — سایه/سیگنال‌ها/setpoint/قفل‌ها. توجه: زیرشاخه‌های
        state/pulse و state/sim (نه ریشهٔ state — یافتهٔ ریویو). فقط‌خواندنی؛
        دلایلِ production_wire از فایلِ سایه می‌آیند (INV-7: هیچ importِ heart)."""
        return {
            "shadow": _read_json(self.state / "pulse" / "heart-shadow-latest.json"),
            "signals": _read_json(self.state / "pulse" / "heart-signals-latest.json"),
            "setpoint": _read_json(self.state / "pulse" / "heart-setpoint-latest.json"),
            "lock": _read_json(self.state / "sim" / "PULSE-EQUATIONS-LOCKED.json"),
            "sim": _read_json(self.state / "sim" / "HEART-SIM-REPORT.json"),
        }

    def read_requests(self, n: int = 10) -> list[dict]:
        """صفِ out-of-bandِ کابین (درخواست‌های act که organism مصرف می‌کند)."""
        out = []
        for ln in _tail_lines(self.state / "cockpit-requests.jsonl", n):
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out

    # ── flagهای مؤثر (آینهٔ dashboard: OCTOPUS-flags.cmd > env > profile) ─────
    def read_flag_overrides(self) -> dict[str, str]:
        out: dict[str, str] = {}
        p = self.ops / "OCTOPUS-flags.cmd"
        try:
            if not p.exists():
                return out
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.lower().startswith("rem") or line.startswith("#"):
                    continue
                if line.lower().startswith("set "):
                    line = line[4:]
                if "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
        except OSError:
            pass
        return out

    def read_capabilities(self) -> dict:
        """وضعیتِ مؤثرِ ۱۹ flag + پروفایل (بدون importِ dashboard).
        اولویت: OCTOPUS-flags.cmd > os.environ > profile-default (paper-full)."""
        ov = self.read_flag_overrides()
        profile = ov.get("OCTOPUS_PROFILE") or os.environ.get("OCTOPUS_PROFILE", "paper-full")
        flags: dict[str, bool] = {}
        for name in WIRE_FLAG_NAMES:
            if name in ov:
                flags[name] = ov[name] == "1"
            elif name in os.environ:
                flags[name] = os.environ[name] == "1"
            else:
                flags[name] = profile in ("paper-full", "live") and name in PAPER_FULL_FLAGS
        cadences = {n: (ov.get(n) or os.environ.get(n, d))
                    for n, d in CADENCE_DEFAULTS.items()}   # C15
        return {"profile": profile, "flags": flags, "cadences": cadences,
                "overrides": sorted(ov)}

    # ── chrono.db — فقط‌خواندنی، هرگز بلاک نمی‌کند (INV-7) ────────────────────
    def read_chrono_ro(self) -> dict:
        """خلاصهٔ chrono.db با اتصالِ `file:...?mode=ro&immutable=1`, timeout=1.
        هر OperationalError (busy/locked/نبود) → {} — نه crash نه block."""
        db = self.state / "chrono.db"
        if not db.exists():
            return {}
        uri = f"file:{db.resolve().as_posix()}?mode=ro&immutable=1"
        con = None
        try:
            con = sqlite3.connect(uri, uri=True, timeout=1)
            out: dict = {}
            tables = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if "gated_effect" in tables:
                out["effects_by_status"] = dict(con.execute(
                    "SELECT status, COUNT(*) FROM gated_effect GROUP BY status"))
            if "beat" in tables:
                row = con.execute("SELECT COUNT(*), MAX(ts_ms) FROM beat").fetchone()
                out["beats"] = {"count": row[0], "last_ms": row[1]}
            if "human_judgment" in tables:
                out["human_judgments"] = con.execute(
                    "SELECT COUNT(*) FROM human_judgment").fetchone()[0]
            out["tables"] = sorted(tables)
            return out
        except (sqlite3.OperationalError, sqlite3.DatabaseError, OSError):
            return {}
        finally:
            try:
                if con is not None:
                    con.close()
            except Exception:  # noqa: BLE001
                pass

    # ── tailهای متنی (مصرف‌کننده باید redact کند — INV-12) ────────────────────
    def tail_governor_alerts(self, n: int = 30) -> list[str]:
        return _tail_lines(self.ops / "governor" / "governor-alerts.md", n)

    def tail_structured_log(self, n: int = 20) -> list[str]:
        """tailِ فایلِ JSONLِ FileEmitter (octopus_logger). فقط مسیرهای شناخته."""
        for cand in (self.state / "octopus-log.jsonl",
                     self.ops / "logs" / "octopus.jsonl"):
            lines = _tail_lines(cand, n)
            if lines:
                return lines
        return []

    # ── ارزیابِ ۲۴ قاعدهٔ سلامت (R1..R24 — پیوستِ مگاپرامپت / pptx مالک) ─────
    def rules(self) -> list[dict]:
        """۲۴ قاعده، هرکدام {id, label, status, evidence}. status ∈ 🟢🟡🔴ℹ️.
        منبعِ اول bundle؛ جای خالی از فایل‌های زنده. fail-soft: بی‌داده → ℹ️."""
        b = self.read_bundle()
        org = (b.get("organism_state") or {}) or self.read_state()
        rep = (b.get("replication") or {}) or self.read_sigma()
        fit = (b.get("fitness") or {}) or self.read_fitness()
        out: list[dict] = []

        def rule(rid, label, status, evidence):
            out.append({"id": rid, "label": label, "status": status,
                        "evidence": str(evidence)[:120]})

        # R1 تازگی داده
        age = _age_minutes(str(org.get("ts", "")))
        rule("R1", "تازگی داده",
             "🟢" if age is not None and age < 30 else ("🟡" if age is not None else "ℹ️"),
             f"آخرین tick: {age:.0f} دقیقه پیش" if age is not None else "بی‌داده")
        # R2..R4 کلیدهای خاموشی
        rule("R2", "halted", "🟢" if not org.get("halted") else "🔴",
             f"halted={org.get('halted')}")
        rule("R3", "FREEZE (I3)", "🟢" if not org.get("frozen") else "🔴",
             f"frozen={org.get('frozen')}")
        rule("R4", "STOP-ORGANISM", "🟢" if not org.get("stop_organism") else "🔴",
             f"stop={org.get('stop_organism')}")
        # R5 سایهٔ $0 تا گیتِ زنده
        month_usd = ((org.get("month") or {}).get("usd") or 0)
        lg = (rep.get("live_gate") or {})
        rule("R5", "سایهٔ $0 تا گیتِ زنده",
             "🟢" if not lg.get("open", False) and month_usd == 0 else "🟡",
             f"ماه US${month_usd} · live_gate={'باز' if lg.get('open') else 'قفل'}")
        # R6/R7
        rule("R6", "suspect-zero", "🟢" if not org.get("suspect_zero_total") else "🔴",
             f"{org.get('suspect_zero_total', 0)} مورد")
        rule("R7", "conflicts", "🟢" if not (org.get("conflicts") or []) else "🔴",
             f"{len(org.get('conflicts') or [])} تعارض")
        # R8 germline
        lagh = org.get("germline_lag_h")
        rule("R8", "بک‌اپ germline (off-box)",
             "🟢" if isinstance(lagh, (int, float)) and lagh < 2 else (
                 "🟡" if isinstance(lagh, (int, float)) and lagh < 26 else "🔴"),
             f"{lagh} ساعت از آخرین بک‌اپ")
        # R9 σ ضدسرطان
        sig = (rep.get("sigma") or {})
        se = sig.get("sigma_effective", 0)
        rule("R9", "σ ضدسرطان (I8)", "🟢" if isinstance(se, (int, float)) and se < 1.0 else "🔴",
             f"σ={se} · zone={sig.get('zone', '?')}")
        # R10 fitness shadow
        rule("R10", "fitness authoritative",
             "🟢" if not fit.get("authoritative", False) else "🟡",
             f"authoritative={fit.get('authoritative')} · تجربه {fit.get('experience_span_days', 0)} روز (سایه تا ۲۸ روز درست است)")
        # R11 تطبیق outbox/db
        rule("R11", "تطبیق outbox/db",
             "🟢" if not (fit.get("integrity_alerts") or []) else "🔴",
             f"{len(fit.get('integrity_alerts') or [])} هشدار یکپارچگی")
        # R12/R13 فازها + پیش‌ثبت
        pm = b.get("phase_metrics") or []
        phase = self.read_phase()
        rule("R12", "رأی فازهای P0–P6",
             "🟢" if phase or pm else "ℹ️",
             f"phase-state={'هست' if phase else 'نیست'} · metrics×{len(pm)}")
        prereg = [m for m in pm if isinstance(m, dict)
                  and m.get("registered_before_implementation")]
        rule("R13", "پیش‌ثبت متریک‌ها", "🟢" if prereg else "ℹ️",
             f"{len(prereg)} فاز پیش‌ثبت‌شده")
        # R14 زنجیرهٔ ژنوم
        gen = b.get("genome_ledger") or {}
        v = str(gen.get("verify", gen.get("verify_scars", "")))
        rule("R14", "زنجیرهٔ ژنوم (verify-scars)",
             "🟢" if ("ok" in v.lower() or gen.get("records")) else "ℹ️",
             f"records={gen.get('records', '?')} · {v[:60]}")
        # R15/R16 chrono
        ch = self.read_chrono_ro()
        rule("R15", "pacemaker persist (chrono)",
             "🟢" if ch else "🟡",
             "chrono.db خوانا" if ch else "chrono.db نیست/قفل")
        pend = (ch.get("effects_by_status") or {}).get("pending", 0)
        rule("R16", "اثرهای معلق", "🟢" if not pend else "🟡", f"{pend} pending")
        # R17/R18 مدرسه + تحکیم
        school = (b.get("school_awareness") or {}) or self.read_school()
        mean = school.get("mean", (school.get("awareness") and
                                   sum(school["awareness"].values()) / max(len(school["awareness"]), 1)))
        rule("R17", "مدرسه", "🟢" if mean else "🟡", f"میانگین آگاهی={mean}")
        cons = self.read_consolidation()
        n_cycles = len(cons.get("cycles", cons) if isinstance(cons, dict) else [])
        rule("R18", "consolidation تازه", "🟢" if cons else "🟡",
             f"{n_cycles} رکورد تحکیم")
        # R19 BCM
        bcm = self.read_bcm()
        rule("R19", "اشباع BCM", "🟢" if bcm else "ℹ️",
             f"keys={len(bcm.get('weights', bcm)) if bcm else 0}" if bcm else "BCM هنوز نچرخیده")
        # R20 chamber-T (RED)
        cht = self.read_chamber_t()
        caps = self.read_capabilities()["flags"]
        rule("R20", "chamber-T (RED)",
             "🟢" if not cht and not os.environ.get("OCTOPUS_WIRE_CHAMBER_T") else "🔴",
             "RED خاموش — طبق طراحی" if not cht else "فایلِ دما هست!")
        # R21 Fisher advisory
        fish = self.read_fisher()
        rule("R21", "Fisher advisory-only",
             "🟢" if fish else ("🟡" if not caps.get("OCTOPUS_WIRE_FITNESS") else "ℹ️"),
             f"cond={fish.get('fisher_condition_number', '—')}" if fish else "flag خاموش/بی‌فایل")
        # R22 ارگان‌ها
        tel = (b.get("telemetry") or {}) or self.read_telemetry()
        organs = tel.get("per_organ_alltime_musd") or {}
        rule("R22", "ارگان PAINTING",
             "🟢" if any("paint" in str(k).lower() for k in organs) else "🟡",
             f"{len(organs)} ارگان ثبت‌شده")
        # R23 هشدارهای ۲۴h
        tail = self.tail_governor_alerts(60)
        warns = sum(1 for ln in tail if "⚠" in ln)
        crits = sum(1 for ln in tail if "CRIT" in ln or "🔴" in ln)
        rule("R23", "هشدارهای اخیر",
             "🔴" if crits else ("🟡" if warns else "🟢"),
             f"{warns} هشدار ⚠ · {crits} بحرانی در tail")
        # R24 گیت‌های wiring
        wiring = org.get("wiring") or {}
        n_on = sum(1 for v in wiring.values() if v is True)
        rule("R24", "گیت‌های wiring",
             "🟢" if wiring else "ℹ️",
             f"{n_on} گیت روشن" if wiring else "wiring در state نیست")
        return out


# ── redaction (INV-12) — الگوهای secret، هم‌راستا با export_status._SECRET_PATTERNS ──
# «سختِ» بی‌ابهام (توکن/کلید/PEM): match → کلِ بدنه جایگزین می‌شود (whole-body).
HARD_SECRET_PATTERNS = [
    re.compile(r"\d{8,12}:AA[A-Za-z0-9_-]{30,}"),   # توکن بات تلگرام
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),            # کلیدهای sk-*
    re.compile(r"-----BEGIN [A-Z ]*KEY"),            # PEM
]
# hex ۶۴رقمی مبهم است (seed/private-key ولی هم‌شکلِ hashِ ledger/effect) — C7:
# فقط همان توکن جایگزین می‌شود، نه کلِ کارت (وگرنه هر کارتِ حاویِ hash نابود می‌شد).
HEX64_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")
HEX64_MASK = "‹hex64:حذف‌شده›"
REDACTED_BODY = "⚠️ محتوا به‌دلیلِ الگوی حساس حذف شد"
# سازگاریِ عقب‌رو: مجموعهٔ کامل (بعضی مصرف‌کننده‌ها SECRET_PATTERNS را می‌خوانند).
SECRET_PATTERNS = HARD_SECRET_PATTERNS + [HEX64_PATTERN]


def contains_secret(text: str) -> bool:
    """فقط secretِ «سخت» (whole-body). hex64 اینجا نمی‌شمارد (per-match در redact)."""
    t = str(text or "")
    return any(p.search(t) for p in HARD_SECRET_PATTERNS)


def redact(text: str) -> str:
    """پاسِ خروجیِ INV-12: secretِ سخت → کلِ بدنه REDACTED_BODY؛ hex64 → ماسکِ per-match."""
    t = str(text or "")
    if any(p.search(t) for p in HARD_SECRET_PATTERNS):
        return REDACTED_BODY
    return HEX64_PATTERN.sub(HEX64_MASK, t)
