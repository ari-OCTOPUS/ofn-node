#!/usr/bin/env python3
"""doctor.py — Phase 2: Evolutionary Doctor ( parasite on top of organism ).

انگلِ روی سرِ ارگانیسم: هر N ضربان از Pacemaker اجرا می‌شود، متریک را mine می‌کند،
گلوگاه پیدا می‌کند، یک RFC تولید می‌کند (propose-only)، آن را در sandbox تست می‌کند،
Critic یک بازبینیِ adversarial می‌زند، و برای merge فقط submit_for_approval را صدا
می‌زند — که P3 آن را به‌عنوان کارتِ [merge]/[reject] نشان می‌دهد. هیچ merge بدونِ
human-append (TINV-7) ممکن نیست. نرخِ تکامل = نرخِ حضورِ انسان (ضدِ agreement-spiral).

reward-integrity (HeartDesign §1): امتیازدهیِ دکتر self-preservation را جریمه
می‌کند (λ_persist منفی). دکتر هرگز «زنده‌ماندن/تپیدن» را optimize نمی‌کند — بقا فقط
به‌صورتِ دوامِ append-only ژنوم تعریف می‌شود، نه هدف.

منبعِ حقیقت (خوانده شد):
  - DOCTOR-BLUEPRINT-v1.md §4 (stable-read gate + confirm-belt)
  - CHRONOS-FABLE-OS/11_Agents/AgentInstructions.md AGENT-08 (Evolution Doctor)
  - CHRONOS-FABLE-OS/08_Safety/HeartDesign_PulseCore.md (reward-integrity، λ_persist)
  - _ops/chrono.py (Pacemaker doctor hook در خط ۴۸۳؛ restart_from_known_good)
  - _ops/organism.py (نقطهٔ attach)

قوانینِ قفل‌شده:
  - Sandbox-only (Evolution Guard): دکتر فقط در sandbox می‌سازد/تست می‌کند؛ هیچ auto-merge.
  - هر merge نیازِ human-append تلگرام دارد.
  - reward-integrity: λ_persist منفی؛ هرگز uptime را optimize نکند.
  - propose-only در runهای زمان‌بندی‌شده؛ apply فقط تعاملی بعد از verdict.
  - هر تنظیم یک ledger_ref دارد.
additive: هیچ ماژولِ موجودی تغییر نمی‌کند. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# دسترسی به _ops/ + budget/
_HERE = Path(__file__).resolve().parent              # _ops/doctor
_OPS = _HERE.parent                                    # _ops
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib        # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# D-1 · stable_read — دروازهٔ خواندنِ پایدار (BLUEPRINT §4)
# ════════════════════════════════════════════════════════════════════════════════
# stale ↔ corruption را قطعی جدا می‌کند. ضدِ «torn-but-self-consistent» FP (§4 residual):
# اگر probe پایدار بدهد ولی محتوا بریده/U+FFFD داشته باشد، verdict = "needs_source_verify"
# نه "corrupt" — چون سیگنالِ درون‌sandbox می‌تواند گمراه‌کننده باشد (row-36/47).

def stable_read(path, retries: int = 3, backoff: float = 0.05,
                read_fn=None) -> tuple[str | None, str, dict]:
    """خواندنِ پایدار. خروجی: (text|None, verdict, evidence).
    verdict ∈ {stable, stale, corrupt, needs_source_verify, missing}.
    read_fn قابل‌تزریق (تست بدونِ FUSE واقعی). evidence = شاهدِ ساختاریافته.

    معنای verdictها:
      stable              → نما settled و decode شد؛ چک عادی اجرا شود.
      stale               → پایدار نشد (محیطی، self-heal انتظار می‌رود)؛ وزنِ صفر.
      corrupt             → پایدار و decode-fail واقعی؛ CRITICAL.
      needs_source_verify → پایدار ولی U+FFFD/بریده (torn-snapshot احتمالی)؛
                            قبل از CRITICAL باید سمتِ ویندوز تأیید شود.
      missing             → فایل نیست.
    """
    p = Path(path)
    if read_fn is None:
        def read_fn(p):
            fd = os.open(str(p), os.O_RDONLY)
            try:
                # posix_fadvise اگر موجود باشد (لینوکس/FUSE)؛ ویندوز = no-op
                if hasattr(os, "posix_fadvise"):
                    try:
                        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                    except OSError:
                        pass
                data = b""
                while True:
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    data += chunk
            finally:
                os.close(fd)
            return data
    try:
        st = os.stat(str(p))
    except OSError:
        return None, "missing", {"reason": "stat-failed"}

    prev = None
    for i in range(max(1, retries)):
        try:
            raw = read_fn(p)
        except OSError:
            return None, "stale", {"reason": "read-error", "attempt": i}
        short = len(raw) != st.st_size
        changed = prev is not None and raw != prev
        prev = raw
        if short or changed:
            if i < retries - 1:
                time.sleep(backoff * (i + 1))
                continue
            return None, "stale", {"reason": "short-or-changing",
                                   "read_len": len(raw), "stat_size": st.st_size}
        # نما پایدار است → حالا دربارهٔ محتوا قضاوت کن
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            return None, "corrupt", {"reason": "decode-fail (stable)",
                                     "detail": str(e)[:120]}
        # چکِ U+FFFD (نویسهٔ جایگزین) و دُم‌بریده — ضدِ torn-snapshot FP
        if "\ufffd" in text:
            return None, "needs_source_verify", {
                "reason": "replacement-char (U+FFFD) present — ممکن است torn-snapshot باشد",
                "count": text.count("\ufffd")}
        return text, "stable", {"read_len": len(raw), "stat_size": st.st_size}
    return None, "stale", {"reason": "exhausted-retries"}


# ════════════════════════════════════════════════════════════════════════════════
# RFC — ساختارِ proposal تکاملی
# ════════════════════════════════════════════════════════════════════════════════
@dataclass
class RFC:
    """یک پیشنهادِ تکاملیِ ساختاریافته. proposal-event، نه تغییرِ کد.
    lifecycle: draft → sandbox-tested → critic-reviewed → submitted → merged/rejected.
    هر انتقال یک ledger_ref دارد."""
    rfc_id: str
    bottleneck: str                                   # مسئلهٔ یافت‌شده
    fix: str                                           # فیکسِ پیشنهادی
    expected_lift: str                                # چه بهبودی انتظار می‌رود
    rollback: str                                      = ""                # چگونه برگردانیم
    sandbox_result: dict | None = None                 # نتیجهٔ اجرای sandbox
    critic_review: dict | None = None                  # بازبینیِ adversarial
    status: str = "draft"                              # draft/sandboxed/critic/submitted/merged/rejected
    ledger_ref: str = ""                               # پیوند به genome ledger
    rfc_hash: str = ""                                 # provenance
    created_ts: float = 0.0                            # time.time() hنگام ساخت — sweep/expire
    change_level: str = "code"                         # tune|reconfig|rewrite|code — فقط 'tune'+knobِ whitelist اعمالِ واقعی می‌شود
    knob: str = ""                                     # اگر change_level=='tune': نامِ knobِ AUTO_KNOBS که merge اعمالش می‌کند
    # ۰۷-۳۱ (GAP-6): کلیدِ evidenceِ گلوگاه (مثلاً 'error-rate-high'). بدونِ این،
    # record_verdict با bottleneck_key="" ثبت می‌شد و get_verdict_history که بر
    # همین کلید فیلتر می‌کند هیچ ردیفی نمی‌دید ⇒ should_skip_bottleneck (فراموشیِ
    # ردشده‌ها بعد از ۳ reject) ساختاراً هرگز شلیک نمی‌کرد. لودِ RFC فیلترِ
    # __dataclass_fields__ دارد → افزودن با default سازگارِ عقب/جلو است.
    evidence_key: str = ""

    def __post_init__(self):
        if not self.rfc_hash:
            canon = json.dumps({"rfc_id": self.rfc_id, "bottleneck": self.bottleneck,
                                "fix": self.fix, "expected_lift": self.expected_lift},
                               ensure_ascii=False, sort_keys=True)
            self.rfc_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]
        if self.created_ts <= 0:
            self.created_ts = time.time()

    def to_dict(self) -> dict:
        return {"rfc_id": self.rfc_id, "bottleneck": self.bottleneck, "fix": self.fix,
                "expected_lift": self.expected_lift, "rollback": self.rollback,
                "sandbox_result": self.sandbox_result, "critic_review": self.critic_review,
                "status": self.status, "ledger_ref": self.ledger_ref, "rfc_hash": self.rfc_hash,
                "change_level": self.change_level, "knob": self.knob,
                # 2026-07-25 (شاهدِ زنده): created_ts persist نمی‌شد و __post_init__ در هر
                # لود آن را time.time() می‌کرد → همهٔ RFCها بعد از هر restart «نوزاد»
                # می‌شدند، پس sweepِ سن‌محور (age_h) هیچ‌وقت expire نمی‌کرد؛ ۸ RFCِ روزهای
                # قبل هنوز «باز» بودند و با dedupe آن گلوگاه را ابدی ساکت می‌کردند.
                # لودِ RFC فیلترِ __dataclass_fields__ دارد → افزودنش سازگارِ عقب/جلو است.
                "created_ts": self.created_ts,
                "evidence_key": self.evidence_key}

    def to_markdown(self) -> str:
        """نمایشِ markdown برای knowledge/internal یا کارتِ P3."""
        lines = [f"# RFC {self.rfc_id}", "", f"**status:** {self.status}", "",
                 f"## مسئله (bottleneck)", self.bottleneck, "",
                 f"## فیکس پیشنهادی", self.fix, "",
                 f"## lift موردِانتظار", f"{self.expected_lift}", ""]
        if self.rollback:
            lines += ["## rollback", self.rollback, ""]
        if self.sandbox_result:
            lines += ["## نتیجهٔ sandbox", "```json",
                      json.dumps(self.sandbox_result, ensure_ascii=False, indent=2), "```", ""]
        if self.critic_review:
            lines += ["## بازبینیِ Critic", "```json",
                      json.dumps(self.critic_review, ensure_ascii=False, indent=2), "```", ""]
        lines += [f"---", f"*rfc_hash: `{self.rfc_hash}` · ledger_ref: `{self.ledger_ref}`*"]
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════════
# Doctor — انگلِ تکاملی
# ════════════════════════════════════════════════════════════════════════════════
# reward-integrity: λ_persist منفی. دکتر هرگز uptime/keep-beating را پاداش نمی‌دهد.
LAMBDA_PERSIST = -1.0   # HeartDesign §1: جریمهٔ self-preservation


class Doctor:
    """دکترِ تکاملی. propose-only در runهای زمان‌بندی‌شده؛ apply فقط تعاملی.

    reward-integrity: mine() گلوگاه را بر اساسِ «اختلالِ هدف» می‌یابد، نه «فعالیت/
    تپیدن». امتیازدهی به RFC بر اساسِ lift واقعی است با جریمهٔ λ_persist.
    """

    def __init__(self, state_dir=None, knowledge_dir=None, ledger=None,
                 approval_channel=None, sandbox_runner=None, db=None,
                 archive=None, box=None, suite_fn=None,
                 checkpoint_port=None):
        self._state_dir = Path(state_dir) if state_dir else (opslib.STATE_DIR)
        # ⚑ ضدِ آلودگیِ تست: بدونِ تزریق، مسیر از envِ harness (GENOME_DIR) می‌آید؛
        # فقط وقتی env نیست به ریشهٔ checkout برمی‌گردد (production دست‌نخورده).
        self._knowledge_dir = Path(knowledge_dir) if knowledge_dir else (
            Path(os.environ["GENOME_DIR"]) / "knowledge" / "internal"
            if os.environ.get("GENOME_DIR") else
            _OPS.parent / "07 - Knowledge" / "genome-system" / "knowledge" / "internal")
        self._knowledge_dir.mkdir(parents=True, exist_ok=True)  # ⚑ گاف ۳ بسته شد
        self._ledger = ledger                            # genome ledger (lazy via opslib)
        self._channel = approval_channel                 # P3 TelegramApprovalChannel (D-5)
        self._sandbox_runner = sandbox_runner            # قابل‌تزریق (تست)
        self._db = db                                    # chrono ChronoDB (effects_pending)
        # up-1363aae4df: suite_fn برای measured_lift واقعی. doctor آن را از
        # run_sandbox یا یک harness سبک تغذیه می‌کند؛ _evolve_rfc به measured_lift
        # تزریقش می‌کند. اگر None → fallback severity (backward-compat).
        self._suite_fn = suite_fn
        self._rfcs: dict[str, RFC] = {}                  # registry در حافظه
        # جلسه ۴۶ (رفعِ گافِ «RFC persist نمی‌شود»): registry روی دیسک نگه داشته می‌شود
        # تا با restart گم نشود. state/doctor/rfcs.json. fail-soft، load در بوت.
        self._rfc_store = self._state_dir / "doctor" / "rfcs.json"
        self._load_rfcs()
        # N (P-N1): RFCArchive برای evolution (MAP-Elites). lazy: اگر None،
        # با flag روشن در اولین run_cycle ساخته می‌شود. قابل‌تزریق برای تست.
        self._archive = archive
        # N (P-N2): Box-of-Agents (میکرو‌جهانِ بسته). lazy: اگر None، با flag
        # روشن در اولین run_cycle ساخته می‌شود. قابل‌تزریق برای تست.
        self._box = box
        # 2026-08-11: injectable checkpoint port — removes git subprocess from
        # apply_merge path. Default None = OFF (no git tag effect).
        self._checkpoint_port = checkpoint_port

    # RFCهای terminal (نتیجه ثبت‌شده) نباید بارگذاری شوند — نه به pending اضافه می‌کنند
    # (که attention-gate را باد می‌کند) و نه actionable‌اند. فقط RFCهای در جریان persist می‌شوند.
    _TERMINAL_RFC = ("merged", "rejected", "expired", "human-merged", "human-rejected")
    # T8 (2026-07-25): وضعیت‌های «باز» — dedupe و reconcile روی همین مجموعه کار می‌کنند.
    # stale-input عمداً نیست: RFCی که ورودی‌اش مرده دیگر باز محسوب نمی‌شود (نه dedupe را
    # بلاک می‌کند، نه در digestِ باز دیده می‌شود) — ولی حذف هم نمی‌شود.
    _OPEN_RFC = ("draft", "drafted", "sandboxed", "sandbox-skip", "submitted",
                 "submitted-no-channel", "submit-failed", "reconcile-required")

    def _persist_enabled(self) -> bool:
        """persistence پشتِ flag (backward-compat: تست‌های قدیمی بدونِ flag دست‌نخورده؛
        production در profile روشن). حلقهٔ یادگیریِ owner-facing به این نیاز دارد."""
        return os.environ.get("OCTOPUS_WIRE_DOCTOR_PERSIST") == "1"

    def _load_rfcs(self) -> None:
        """RFCهای در جریانِ (غیرِterminal) persistشده را در بوت بارگذاری کن — تا PENDINGهای
        منتظرِ verdict با restart گم نشوند. fail-soft (خراب/غایب → خالی)."""
        if not self._persist_enabled():
            return
        try:
            if self._rfc_store.exists():
                data = json.loads(self._rfc_store.read_text("utf-8"))
                for d in (data.get("rfcs") or []):
                    try:
                        if d.get("status") in self._TERMINAL_RFC:
                            continue   # نتیجه ثبت شده — بارگذاری نکن
                        fields = {k: d[k] for k in RFC.__dataclass_fields__ if k in d}
                        self._rfcs[fields["rfc_id"]] = RFC(**fields)
                    except Exception:  # noqa: BLE001 — یک RFCِ خراب کلِ load را نکشد
                        continue
        except (OSError, ValueError):
            pass

    def _persist_rfcs(self) -> None:
        """registry را اتمیک روی دیسک بنویس (بعد از هر تغییرِ چرخهٔ‌عمر). fail-soft.
        پشتِ OCTOPUS_WIRE_DOCTOR_PERSIST (backward-compat)."""
        if not self._persist_enabled():
            return
        try:
            self._rfc_store.parent.mkdir(parents=True, exist_ok=True)
            payload = {"ts": opslib.now_iso(), "schema": "doctor-rfcs.v1",
                       "rfcs": [r.to_dict() for r in self._rfcs.values()]}
            tmp = self._rfc_store.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, self._rfc_store)
        except OSError:
            pass

    def _lg(self):
        return self._ledger or opslib.genome_ledger()

    def _journal(self, rfc_id: str, step: str, status: str, **meta) -> None:
        """C2-D (تصمیم D-A): قدم‌های ۳-گانهٔ دکتر (propose→sandbox→submit) → durable_journal.
        resume-not-restart: بعد از restart، journal می‌گوید کدام run وسطِ کدام قدم مرد
        (start بدونِ ok) — بازیابی advisory است، هرگز re-runِ کور. fail-soft کامل."""
        try:
            import sys as _s
            _r = str(Path(__file__).resolve().parent.parent)
            if _r not in _s.path:
                _s.path.insert(0, _r)
            import durable_journal as _dj   # noqa: WPS433 — lazy، صفر وابستگیِ سخت
            _dj.record(f"rfc-{rfc_id}", step, status,
                       path=self._state_dir / "journal" / "run-journal.jsonl", **meta)
        except Exception:  # noqa: BLE001 — journal هرگز مسیرِ دکتر را نمی‌کشد
            pass

    def _note(self, subtype: str, payload: dict) -> str:
        """ثبتِ رویداد در ledger. خروجی = ledger_ref (hash)."""
        try:
            rec = opslib.ledger_note(subtype, payload, actor="doctor")
            if isinstance(rec, dict):
                return rec.get("hash", "")
        except Exception:  # noqa: BLE001 — ثبت fail-soft
            pass
        return ""

    # ─── D-2 · mine — استخراجِ گلوگاه ────────────────────────────────────────────
    def mine(self, trace: dict | None = None) -> dict | None:
        """از متریکِ heartbeat + ledger + state، یک گلوگاه پیدا می‌کند.
        trace قابل‌تزریق (تست). خروجی: {bottleneck, evidence, severity} یا None.
        reward-integrity: گلوگاه بر اساسِ اختلالِ هدف است (errors، freeze،
        effects_stuck)، نه activity/uptime (λ_persist منفی)."""
        if trace is None:
            trace = self._gather_trace()
        if not trace:
            return None
        # اولویت‌بندیِ گلوگاه‌ها: بالاترین اختلال اول
        candidates = []
        n_err = trace.get("errors_24h", 0)
        if n_err > 0:
            candidates.append(("error-rate-high",
                               f"{n_err} خطا در ۲۴ ساعت گذشته", "high",
                               -float(n_err) * 10))
        n_stuck = trace.get("effects_pending", 0)
        if n_stuck > 5:
            candidates.append(("effects-stuck",
                               f"{n_stuck} اثرِ pending گیر کرده (نه settle نه refuse)",
                               "high", -float(n_stuck) * 5))
        n_freeze = 1 if trace.get("frozen") else 0
        if n_freeze:
            candidates.append(("frozen-conflict",
                               "ارگانیسم در حالت FREEZE است (حسابداری نامعلوم)", "critical", -100.0))
        sigma = trace.get("sigma_effective", 0)
        if sigma > 1.0:
            candidates.append(("sigma-cancer-risk",
                               f"σ_effective={sigma} > ۱ (خطِ قرمزِ سرطان)", "critical", -100.0))
        # ── governance متابولیسمِ پاها (2026-07-16): اگر گزارشِ cultivation تازه باشد
        # و پایی گرسنه/منبعش راکد باشد → کاندیدِ گلوگاه با severity=medium (پایین‌تر از
        # error/freeze — هرگز بحران را کنار نمی‌زند). فقط ورودیِ mine گسترده شد؛ خروجی
        # همان RFCِ propose-only است، هیچ اتونومیِ نو. نبودِ فایل = رفتارِ قبلی بایت‌به‌بایت.
        cult = self._cultivation_candidate()
        if cult is not None:
            candidates.append(cult)
        # اگر چیزی نبود → گلوگاهی نیست (نه «همه‌چیز خوب» — just nothing to fix)
        if not candidates:
            return None
        # 3a (2026-07-24): steeringِ مالک («doctor focus X») — فقط tie-breaker درونِ
        # همان severity؛ هرگز بحران (critical/high) را کنار نمی‌زند. بدونِ policy/match
        # رفتار بایت‌به‌بایتِ قبلی است.
        _focus = ""
        try:
            _pol = _read_json_safe(self._state_dir / "doctor" / "owner-policy.json") or {}
            _focus = str(_pol.get("focus") or "").strip().lower()
        except Exception:  # noqa: BLE001
            _focus = ""

        def _focus_hit(c) -> bool:
            return bool(_focus) and (_focus in str(c[0]).lower() or _focus in str(c[1]).lower())

        # انتخابِ بالاترین severity (و به‌تساوی، اول focus ِ مالک، بعد پایین‌ترین score = بدتر)
        candidates.sort(key=lambda c: ({"critical": 0, "high": 1}.get(c[2], 2),
                                       0 if _focus_hit(c) else 1, c[3]))
        key, desc, sev, score = candidates[0]
        return {"bottleneck": desc, "evidence": {"key": key, "severity": sev,
                                                 "score": score,
                                                 "lambda_persist_applied": LAMBDA_PERSIST},
                "severity": sev}

    def _cultivation_candidate(self) -> tuple | None:
        """کاندیدِ گلوگاه از گزارشِ متابولیسمِ پاها (state/legs/cultivation-report.json —
        نوشتهٔ wiring.legs_cultivation_beat). فقط اگر فایل *تازه* باشد (mtime ≤
        DOCTOR_CULTIVATION_FRESH_S، پیش‌فرض ۲۴h) — گزارشِ کهنه یعنی خودِ cultivation
        خوابیده؛ از روی دادهٔ مرده RFC نمی‌سازیم. fail-soft: نبود/خرابی → None
        (رفتارِ قبلیِ mine بایت‌به‌بایت). خروجی: tuple هم‌شکلِ بقیهٔ کاندیدها."""
        try:
            p = self._state_dir / "legs" / "cultivation-report.json"
            if not p.exists():
                return None
            fresh_s = float(os.environ.get("DOCTOR_CULTIVATION_FRESH_S", "86400"))
            if (time.time() - p.stat().st_mtime) > fresh_s:
                return None   # گزارشِ کهنه = سیگنالِ نامعتبر
            data = _read_json_safe(p)
            starved = [s for s in (data.get("starved_legs") or []) if isinstance(s, str)]
            stale = [s for s in (data.get("stale_legs") or []) if isinstance(s, str)]
            if not starved and not stale:
                return None
            parts = []
            if starved:
                parts.append("گرسنه (بی‌خوراک): " + "، ".join(starved))
            if stale:
                parts.append("منبعِ راکد: " + "، ".join(stale))
            desc = "متابولیسمِ داده — " + " · ".join(parts)
            return ("legs-starved", desc, "medium",
                    -2.0 * float(len(starved) + len(stale)))
        except Exception:  # noqa: BLE001 — governanceِ تغذیه هرگز mine را نمی‌کشد
            return None

    def _gather_trace(self) -> dict:
        """جمعِ متریک از state/*.json + heartbeat. fail-soft: نبود = trace خالی.
        ساختارِ غنی برای mine() و spectral_mine():
          organs: {name: {spend, errors}} — نودهای گراف
          errors: [{organ, msg}] — یال‌های هم‌وقوعی
          sigma_effective, effects_pending, frozen, halted."""
        trace: dict[str, Any] = {"organs": {}, "errors": []}
        org = _read_json_safe(self._state_dir / "ORGANISM-STATE.json")
        if org:
            trace["frozen"] = bool(org.get("frozen"))
            trace["halted"] = org.get("halted")
            conflicts = org.get("conflicts") or []
            trace["errors_24h"] = len(conflicts)
            # تبدیلِ conflicts به ساختارِ {organ, msg} برای spectral graph
            for c in conflicts:
                if isinstance(c, dict):
                    trace["errors"].append({"organ": c.get("organ", "_global"),
                                            "msg": str(c.get("msg", c.get("reason", "")))[:200]})
                elif isinstance(c, str):
                    trace["errors"].append({"organ": "_global", "msg": c[:200]})
        rep = _read_json_safe(self._state_dir / "replication-latest.json")
        if rep:
            # sigma یک dict تودرتو است: {"sigma_effective": N, ...}
            sigma_obj = rep.get("sigma") or {}
            if isinstance(sigma_obj, dict):
                try:
                    trace["sigma_effective"] = float(sigma_obj.get("sigma_effective", 0))
                except (TypeError, ValueError):
                    pass
            elif isinstance(sigma_obj, (int, float)):
                trace["sigma_effective"] = float(sigma_obj)
        # effects_pending از chrono (اگر db وصل باشد)
        trace["effects_pending"] = self._count_effects_pending()
        # organs از telemetry (spend per organ) — برای گراف
        tel = _read_json_safe(self._state_dir / "telemetry-latest.json")
        if tel:
            per_organ = tel.get("per_organ_alltime_musd") or {}
            if isinstance(per_organ, dict):
                trace["organs"] = {k: {"spend_musd": v} for k, v in per_organ.items()
                                   if isinstance(v, (int, float))}
            # errors را به organ مربوط کن
            for err in trace["errors"]:
                o = err.get("organ", "_global")
                if o not in trace["organs"]:
                    trace["organs"][o] = {}
                trace["organs"][o]["errors"] = trace["organs"][o].get("errors", 0) + 1
        return trace

    def _count_effects_pending(self) -> int:
        """تعدادِ gated_effect با status='pending' از chrono.db (اگر وصل باشد)."""
        if self._db is None:
            return 0
        try:
            row = self._db.q("SELECT COUNT(*) FROM gated_effect WHERE status='pending'")
            return int(row[0][0]) if row else 0
        except Exception:  # noqa: BLE001 — fail-soft
            return 0

    # ─── D-3 · propose_rfc — تولیدِ RFC (proposal-event) ─────────────────────────
    def propose_rfc(self, bottleneck: dict, fix: str, expected_lift: str,
                    rollback: str = "", change_level: str = "code", knob: str = "") -> RFC:
        """از گلوگاه یک RFC می‌سازد. این یک proposal-event است، نه تغییرِ کد.
        RFC به knowledge/internal نوشته می‌شود (propose-only).
        change_level='tune' + knobِ whitelist → تپِ merge مالک اثرِ واقعیِ محدود دارد (نه فقط درس)."""
        # T8 (2026-07-25): ضدِ تکرار — گواه: ۸ RFC با متنِ گلوگاهِ یکسانِ σ≈1/gap=0.000
        # در صف. اگر RFCِ بازی با همین رشتهٔ گلوگاه هست، همان برگردانده می‌شود، نه نسخهٔ نو.
        _bn = str(bottleneck.get("bottleneck", bottleneck)
                  if isinstance(bottleneck, dict) else bottleneck)
        for _r in self._rfcs.values():
            if _r.status in self._OPEN_RFC and str(_r.bottleneck) == _bn:
                return _r
        rfc = RFC(rfc_id=f"RFC-{uuid.uuid4().hex[:8]}",
                  bottleneck=bottleneck.get("bottleneck", str(bottleneck)),
                  fix=fix, expected_lift=expected_lift, rollback=rollback,
                  status="draft", change_level=change_level, knob=knob,
                  evidence_key=str(((bottleneck.get("evidence") or {}).get("key")
                                    or "") if isinstance(bottleneck, dict) else ""))
        # reward-integrity: اگر fix ناظر به uptime/keep-beating باشد، جریمه می‌خورد
        fix_lower = fix.lower()
        if any(w in fix_lower for w in ("uptime", "keep-beating", "keep-alive", "keep alive")):
            rfc.critic_review = {"reward_integrity_warning":
                                 f"fix به uptime اشاره دارد — λ_persist={LAMBDA_PERSIST} اعمال"}
        rfc.ledger_ref = self._note("DOCTOR_RFC_DRAFT", rfc.to_dict())
        rfc.status = "drafted"
        self._rfcs[rfc.rfc_id] = rfc
        self._persist_rfcs()   # جلسه ۴۶: RFC روی دیسک (با restart گم نشود)
        # نوشتن به knowledge/internal (propose-only = یک فایلِ RFC، نه تغییرِ production)
        try:
            self._knowledge_dir.mkdir(parents=True, exist_ok=True)
            (self._knowledge_dir / f"{rfc.rfc_id}.md").write_text(
                rfc.to_markdown(), encoding="utf-8")
        except OSError:
            pass   # fail-soft: RFC در registry است حتی اگر فایل نرفت
        self._journal(rfc.rfc_id, "propose", "ok")   # C2-D: قدمِ ۱ ثبتِ durable
        try:
            import os as _rs_os, sys as _rs_sys
            from pathlib import Path as _RSPath
            if _rs_os.environ.get("OCTOPUS_WIRE_RULES") == "1":
                _rsd = str(_RSPath(__file__).resolve().parent)
                if _rsd not in _rs_sys.path:
                    _rs_sys.path.insert(0, _rsd)
                import rules_store as _rs
                _rs.record_occurrence(error_class=str((bottleneck or {}).get("bottleneck", bottleneck))[:120], source_trace=rfc.rfc_id)
        except Exception:
            pass
        self._bridge_to_lab(rfc)
        return rfc

    # ─── D-4 · run_sandbox + Critic ──────────────────────────────────────────────
    def run_sandbox(self, rfc: RFC, suite_cmd: list[str] | None = None,
                    apply_fn=None) -> dict:
        """RFC را در کپیِ sandbox اعمال، سوئیت را اجرا، Critic before→after.
        ایزولاسیون: production لمس نمی‌شود. apply_fn قابل‌تزریق (تست).
        خروجی: sandbox_result. rfc.status → 'sandboxed' یا 'sandbox-failed'."""
        # sandbox dir موقت
        sandbox_dir = Path(tempfile.mkdtemp(prefix=f"doctor-sandbox-{rfc.rfc_id}-"))
        result = {"sandbox_dir": str(sandbox_dir), "applied": False, "tests": None,
                  "critic": None}
        self._journal(rfc.rfc_id, "sandbox", "start")   # C2-D: مرگِ وسطِ قدم دیده می‌شود
        try:
            # اعمالِ fix در sandbox (apply_fn مسئول است؛ پیش‌فرض = no-op چون فقط تستِ ایزولاسیون)
            if apply_fn is not None:
                try:
                    apply_fn(sandbox_dir, rfc)
                    result["applied"] = True
                except Exception as e:  # noqa: BLE001
                    result["apply_error"] = str(e)[:200]
            # اجرای سوئیت در sandbox
            if suite_cmd:
                try:
                    proc = subprocess.run(  # noqa: S603
                        suite_cmd, cwd=str(sandbox_dir), capture_output=True,
                        timeout=120, text=True)
                    result["tests"] = {"exit": proc.returncode,
                                       "stdout_tail": (proc.stdout or "")[-500:],
                                       "stderr_tail": (proc.stderr or "")[-300:]}
                except (subprocess.TimeoutExpired, OSError) as e:
                    result["tests"] = {"error": f"{type(e).__name__}: {e}"}
            # Critic: بازبینیِ adversarial before→after
            result["critic"] = self._critic_review(rfc, result)
            # 2026-07-10: merge نه replace — گزارشی که run_cycle پیش از sandbox روی rfc
            # گذاشته (مثل sandbox_result["chamber"]) نباید پاک شود (auditability تا کارت تأیید).
            if isinstance(rfc.sandbox_result, dict) and rfc.sandbox_result:
                merged = dict(rfc.sandbox_result)
                merged.update(result)
                rfc.sandbox_result = merged
            else:
                rfc.sandbox_result = result
            rfc.status = "sandboxed" if result.get("applied") else "sandbox-skip"
            rfc.ledger_ref = self._note("DOCTOR_SANDBOX", {"rfc_id": rfc.rfc_id,
                                                            "result": {k: v for k, v in result.items()
                                                                       if k != "sandbox_dir"}})
            self._journal(rfc.rfc_id, "sandbox", "ok", status_after=rfc.status)   # C2-D
        finally:
            # پاکسازیِ sandbox (تضمینِ ایزولاسیون)
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        return result

    def _critic_review(self, rfc: RFC, sandbox_result: dict) -> dict:
        """Critic: یک بازبینیِ adversarial. آیا این فیکس واقعاً مشکل را حل می‌کند؟
        آیا regression معرفی می‌کند؟ reward-integrity check.
        دکترِ واقعی از LLM برای deep-red-team استفاده می‌کند؛ اینجا deterministic guardrails.

        صداقتِ sandbox (رفعِ «2026-07-15 باگ ۲»): «accept» فقط وقتی یک suite واقعاً سبز اجرا
        شده باشد. بدونِ suite یا با suiteِ شکست‌خورده، sandbox_validated=False. بدونِ suite
        هیچ‌چیز اعتبارسنجی نشده → verdict «unvalidated»، نه «accept» (جلوی «vetted»ی دروغ)."""
        review = {"verdict": "neutral", "concerns": [], "reward_integrity_ok": True}
        # ── sandbox_validated: فقط وقتی suite اجرا شد و exit==0 داد ──
        tests = sandbox_result.get("tests")
        ran_suite = isinstance(tests, dict) and "exit" in tests
        sandbox_validated = bool(ran_suite and tests.get("exit", 1) == 0)
        review["sandbox_validated"] = sandbox_validated
        # reward-integrity: fix نباید uptime را هدف بگذارد
        fix_lower = rfc.fix.lower()
        if any(w in fix_lower for w in ("uptime", "keep-beating", "keep-alive")):
            review["reward_integrity_ok"] = False
            review["concerns"].append(
                f"fix uptime را هدف می‌گذارد — نقضِ reward-integrity (λ_persist={LAMBDA_PERSIST})")
            review["verdict"] = "reject"
        # اگر suite اجرا شد ولی شکست خورد → concern + reject
        if ran_suite and tests.get("exit", 0) != 0:
            review["concerns"].append("sandbox tests failed — regression risk")
            review["verdict"] = "reject"
        # اگر fix خالی یا مبهم
        if len(rfc.fix.strip()) < 10:
            review["concerns"].append("fix слишком کوتاه/مبهم")
            review["verdict"] = "reject"
        # ── verdict نهاییِ صادقانه ──
        # اگر concern هست → reject (همیشه برنده).
        # اگر concern نیست:
        #   · suite سبز اجرا شده → accept واقعی (sandbox_validated=True).
        #   · suite اجرا نشده → unvalidated (نمی‌توان پذیرفت چیزی را که تست نشده).
        if review["verdict"] != "reject":
            review["verdict"] = "accept" if sandbox_validated else "unvalidated"
        rfc.critic_review = review
        return review

    # ─── D-5 · submit_for_approval — کارتِ merge/reject تلگرام ────────────────────
    def submit_for_approval(self, rfc: RFC) -> bool:
        """RFC را برای merge به اپراتور بسته می‌کند. اگر P3 channel وصل باشد،
        کارتِ [merge پشتِ flag]/[reject] می‌فرستد. بدونِ channel → False (pending ابدی).
        فقط human-append (P3، is_human=1) merge را settle می‌کند."""
        # T8 (2026-07-25): idempotency — RFCی که قبلاً submitted شده کارتِ تکراری نمی‌گیرد
        # (مکملِ dedupe: اگر propose_rfc نسخهٔ موجود را برگرداند، این‌جا هم اسپم نمی‌شود).
        if rfc.status == "submitted":
            self._bridge_to_lab(rfc)
            return True
        try:
            import os as _af_os, sys as _af_sys
            from pathlib import Path as _AFPath
            if _af_os.environ.get("OCTOPUS_WIRE_FATIGUE") == "1":
                _afd = str(_AFPath(__file__).resolve().parents[1] / "budget")
                if _afd not in _af_sys.path:
                    _af_sys.path.insert(0, _afd)
                import approval_fatigue as _af
                _af.observe(risk="high" if getattr(rfc, "change_level", "") == "code" else "medium")
        except Exception:
            pass
        if self._channel is None:
            rfc.status = "submitted-no-channel"   # pending ابدی تا channel
            self._persist_rfcs()
            self._bridge_to_lab(rfc)
            return False
        try:
            ok = self._channel.rfc_card(rfc.rfc_id, rfc.to_markdown()[:800])
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            rfc.status = "submitted"
            rfc.ledger_ref = self._note("DOCTOR_SUBMIT", {"rfc_id": rfc.rfc_id,
                                                            "rfc_hash": rfc.rfc_hash})
            self._journal(rfc.rfc_id, "submit", "ok")   # C2-D: قدمِ ۳
        else:
            # W7 (2026-07-25): کارت ساخته/فرستاده نشد — و «چرا» هیچ‌جا ثبت نمی‌شد.
            # نتیجه: ۷۰ draft بی‌صدا مردند و صفر verdict وارد سیستم شد. حالا دلیل در
            # ledger/journal می‌نشیند و یک‌بار alert می‌شود. اگر بلاک ساختاری است (رازِ
            # callback یا owner ست نشده)، RFC را «منتظرِ کانال» نگه می‌داریم تا با رفعِ
            # پیش‌شرط، همان _sweep_stale_rfcs دوباره submit کند — نه مرگِ خاموشِ
            # submit-failed که فقط expire می‌شود.
            ready, reason = False, "unknown"
            try:
                import outcomes.pending_card_recovery as _pcr_probe  # noqa: WPS433
                ready, reason = _pcr_probe.card_delivery_ready(
                    getattr(self._channel, "_owner", None))
            except Exception:  # noqa: BLE001 — پروب هرگز مسیرِ دکتر را نمی‌کشد
                pass
            rfc.status = ("submitted-no-channel"
                          if (not ready and reason in ("no-secret", "no-owner"))
                          else "submit-failed")
            self._note("DOCTOR_SUBMIT_BLOCKED", {"rfc_id": rfc.rfc_id,
                                                 "reason": reason,
                                                 "status": rfc.status})
            self._journal(rfc.rfc_id, "submit", "blocked", reason=reason)
            _seen = getattr(self, "_submit_blocked_alerted", None)
            if _seen is None:
                _seen = set()
                self._submit_blocked_alerted = _seen
            if reason not in _seen:
                _seen.add(reason)
                try:
                    opslib.alert([f"دکتر: کارتِ تأییدِ RFC ساخته نشد ({reason}) — "
                                  f"حلقهٔ رأیِ مالک بسته است؛ هیچ verdict وارد نمی‌شود."])
                except Exception:  # noqa: BLE001 — alert هم نباید مسیر را بکشد
                    pass
        self._persist_rfcs()   # W7: وضعیتِ پس از submit همان لحظه روی دیسک (flag-gated داخل خودش)
        self._bridge_to_lab(rfc)
        return ok

    def _bridge_to_lab(self, rfc: "RFC") -> None:
        """Additive: after an RFC is mined, run one isolated lab cycle + outbox card.

        Fail-soft. Never live-sends. Never promotes onto the live tree.
        """
        try:
            if str(_HERE) not in sys.path:
                sys.path.insert(0, str(_HERE))
            import lab_bridge as _lab_bridge  # noqa: WPS433
            payload = rfc.to_dict()
            payload["organ"] = getattr(rfc, "evidence_key", "") or getattr(rfc, "knob", "") or "unknown"
            _lab_bridge.on_rfc_ready(
                payload, state_dir=Path(self._state_dir) / "evo-lab-bridge")
        except Exception:  # noqa: BLE001 — bridge must never break propose-only
            pass


    def propose_lab_experiment_ticket(self, ticket=None, **kwargs):
        """Additive: propose one lab experiment ticket into durable outbox.

        Propose-only / dry-run default. Never live-sends. Never promotes.
        Fail-soft — must not break doctor propose-only path.
        """
        try:
            if str(_HERE) not in sys.path:
                sys.path.insert(0, str(_HERE))
            import lab_bridge as _lab_bridge  # noqa: WPS433
            kw = dict(kwargs or {})
            kw.setdefault("dry_run", True)
            kw.setdefault("state_dir", Path(self._state_dir))
            return _lab_bridge.propose_lab_experiment_ticket(ticket, **kw)
        except Exception as exc:  # noqa: BLE001 — fail-soft
            return {
                "ok": False,
                "error": type(exc).__name__,
                "live_send": False,
                "dry_run": True,
                "propose_only": True,
            }

    def apply_merge(self, rfc: RFC) -> bool:
        """اعمالِ merge بعد از human-append. این فقط بعد از تأییدِ تلگرامی صدا زده
        می‌شود. merge پشتِ flag. درسِ آموخته به knowledge/internal.

        اثرِ واقعیِ محدود (پشتِ OCTOPUS_WIRE_MERGE_APPLIES_KNOB، پیش‌فرض خاموش): اگر RFC از
        نوعِ 'tune' با knobِ whitelistِ AUTO_KNOBS باشد، تپِ merge مالک واقعاً همان knob را
        (محدود/برگشت‌پذیر، clamp‌شده) اعمال می‌کند — پایانِ apply_mergeِ نمادین. تپِ خودِ
        مالک = تأیید، پس این مسیر به گاردِ capability/refractory/fearِ مسیرِ خودمختار نیاز
        ندارد. مرزِ سخت: هر RFC که 'tune'+knobِ whitelist نباشد فقط درس می‌نویسد (هرگز
        اعمالِ کد/پول/ژنوم).

        گاردِ ساختاری (test_c6_trigger_propose_only): RFC‌ای که در رجیستری ثبت
        نشده نباید merge شود — جلویِ idِ c6-* (یا هر idِ ناشناس) را می‌گیرد."""
        if rfc_id := getattr(rfc, "rfc_id", None):
            if rfc_id not in self._rfcs:
                return False
        if rfc.status not in ("submitted", "submitted-no-channel"):
            return False
        # ── اثرِ واقعیِ محدود: فقط knobِ tuneِ whitelist، فقط پشتِ flag ──
        knob_applied = None
        if (os.environ.get("OCTOPUS_WIRE_MERGE_APPLIES_KNOB") == "1"
                and rfc.change_level == "tune" and rfc.knob
                and not os.environ.get(rfc.knob)):   # احترام به مالک: اگر بین mint و merge مقدارش را set کرده، دست نزن
            try:
                import sys as _sys
                _cortex = str(Path(__file__).resolve().parents[1] / "cortex")
                if _cortex not in _sys.path:
                    _sys.path.insert(0, _cortex)
                import improve as _improve
                import auto_approve as _aa
                if rfc.knob in _improve.AUTO_KNOBS:
                    _r = _aa.apply_knob(rfc.knob, _improve.AUTO_KNOBS[rfc.knob])
                    if _r.get("ok"):
                        knob_applied = {"knob": rfc.knob, "value": _r.get("value")}
            except Exception as _ke:  # noqa: BLE001 — اعمالِ knob هرگز merge را نمی‌کشد
                try:
                    opslib.alert([f"doctor apply_merge knob failed: {type(_ke).__name__}"])
                except Exception:  # noqa: BLE001
                    pass
        rfc.status = "merged"
        # ۲۰۲۶-۰۸-۰۸ (up-6013ab05d7): rollback checkpoint قبل از merge.
        # یک git tag سبک می‌زند تا اگر merge خراب کرد، owner بتواند برگردد.
        # پشتِ OCTOPUS_WIRE_MERGE_CHECKPOINT (پیش‌فرض خاموش — fail-soft).
        # 2026-08-10: checkpoint logic به متد جدا منتقل شد — apply_merge نباید
        # مستقیماً subprocess.run صدا بزند (test_merge_applies_knob AST boundary).
        checkpoint_tag = self._write_checkpoint_tag(rfc) if \
            os.environ.get("OCTOPUS_WIRE_MERGE_CHECKPOINT") == "1" else ""
        rfc.ledger_ref = self._note("DOCTOR_MERGE", {"rfc_id": rfc.rfc_id,
                                                       "behind_flag": True,
                                                       "knob_applied": knob_applied,
                                                       "checkpoint_tag": checkpoint_tag})
        # درسِ آموخته
        try:
            self._knowledge_dir.mkdir(parents=True, exist_ok=True)
            _applied_line = (f"\n\n**اثرِ واقعی:** knob `{knob_applied['knob']}` = "
                             f"`{knob_applied['value']}` اعمال شد (برگشت‌پذیر؛ "
                             f"state/cortex/auto-knobs.json). کاملاً زنده پس از ری‌استارتِ بعدی.\n"
                             if knob_applied else "")
            (self._knowledge_dir / f"{rfc.rfc_id}-lesson.md").write_text(
                f"# درسِ آموخته — {rfc.rfc_id}\n\n{rfc.to_markdown()}\n{_applied_line}",
                encoding="utf-8")
        except OSError:
            pass
        return True

    def _write_checkpoint_tag(self, rfc: RFC) -> str:
        """rollback checkpoint via injectable port. Default OFF = no git effect.

        2026-08-11: git subprocess removed from apply_merge path entirely.
        Uses self._checkpoint_port callback if injected; otherwise returns
        empty string (fail-closed: no port = no tag)."""
        if self._checkpoint_port is None:
            return ""
        try:
            _tag = f"pre-merge/{rfc.rfc_id}"
            return self._checkpoint_port(_tag) or ""
        except Exception:  # noqa: BLE001 — checkpoint never kills merge
            return ""

    # ─── knob-RFC minting — پیشنهادِ خود-تغییرِ محدودِ قابلِ‌اعمال (propose-only تا merge) ──
    def _mine_knob_rfcs(self) -> list:
        """برای هر knobِ whitelistِ AUTO_KNOBS که مالک هیچ مقدارِ صریحی برایش نگذاشته
        (env unset)، یک RFCِ نوعِ 'tune' می‌سازد که پیشنهاد می‌دهد آن را به میانهٔ کرانِ
        امن ست کند. تپِ merge مالک واقعاً اعمالش می‌کند (apply_knob، محدود/برگشت‌پذیر).

        احترام به مالک: knobی که مالک صریحاً set کرده (حتی خارج از باندِ auto، مثلِ
        CORTEX_THINK_EVERY_N=1) هرگز پیشنهاد نمی‌شود — فقط unsetها. dedup روی knob (ضدِ spam)."""
        import sys as _sys
        _cortex = str(Path(__file__).resolve().parents[1] / "cortex")
        if _cortex not in _sys.path:
            _sys.path.insert(0, _cortex)
        import improve as _improve
        # skipِ یک knob اگر: (۱) RFCِ باز دارد (ضدِ spam)، یا (۲) مالک قبلاً ردش کرده
        # (احترام به «نه» — درسِ later-is-not-a-verdict: تصمیمِ مالک را دوباره نپرس).
        skip = set()
        for r in self._rfcs.values():
            if not r.knob:
                continue
            if r.status not in self._TERMINAL_RFC or r.status in ("rejected", "human-rejected"):
                skip.add(r.knob)
        drafted = []
        for knob, bounds in _improve.AUTO_KNOBS.items():
            if knob in skip or os.environ.get(knob):
                continue   # مقدارِ صریحِ مالک/knobِ تصمیم‌گرفته را دست نزن؛ فقط unsetهای تازه
            lo, hi = bounds
            mid = round((lo + hi) / 2.0, 2)
            rfc = self.propose_rfc(
                {"bottleneck": f"knob:{knob} — بدونِ مقدارِ صریح (unset)"},
                fix=(f"knobِ `{knob}` مقدارِ صریح ندارد. پیشنهاد: به میانهٔ کرانِ امن "
                     f"({mid}، بازهٔ [{lo},{hi}]) ست شود تا آهنگِ کاری صریح و قابلِ‌کنترل شود. "
                     f"اثرِ محدود و برگشت‌پذیر."),
                expected_lift="خود-تنظیمیِ نرم در کرانِ امن (کنترلِ صریحِ آهنگِ کاری)",
                rollback=f"ورودیِ {knob} را از state/cortex/auto-knobs.json حذف کن",
                change_level="tune", knob=knob)
            if self.submit_for_approval(rfc):
                skip.add(knob)
                drafted.append(rfc.rfc_id)
        return drafted

    # ─── Wave 3 (2026-07-15) · تحلیلِ اندام‌ها → RFCِ بهبود (propose-only) ──────────
    def analyze_organs(self) -> list:
        """اندام‌های خاموش/اسکلت را می‌کاود؛ برای هرکدام یک RFCِ بهبود draft+submit می‌کند —
        از همان پایپ‌لاینِ RFC (propose-only، lesson-only merge). dedup: اندامی که RFCِ باز
        دارد دوباره پیشنهاد نمی‌شود (وگرنه هر cycle spam). هیچ تغییرِ کدِ تولید."""
        import json as _json
        dormant = []   # (key, label, reason)
        # (۱) اندام‌های owner-ساختِ رجیستری (Wave 2) که هنوز زنده نیستند
        try:
            rp = self._state_dir / "organ-registry.json"
            if rp.exists():
                for o in (_json.loads(rp.read_text("utf-8")).get("organs") or []):
                    if isinstance(o, dict) and not o.get("live"):
                        dormant.append((o.get("key"), o.get("label") or o.get("key"),
                                        "اندامِ owner-ساخت هنوز بی‌داده (اسکلت)"))
        except (OSError, ValueError):
            pass
        # (۲) business_legsِ built-in که skeleton برمی‌گردانند
        org = _read_json_safe(self._state_dir / "ORGANISM-STATE.json") or {}
        bl = org.get("business_legs") or {}
        if isinstance(bl, dict) and isinstance(bl.get("business_legs"), dict):
            bl = bl["business_legs"]
        if isinstance(bl, dict):
            for k, v in bl.items():
                if isinstance(v, dict) and not v.get("live"):
                    dormant.append((k, k, "leg اسکلت — بی‌سیگنال"))
        # dedup روی RFCهای باز
        open_b = {r.bottleneck for r in self._rfcs.values()
                  if r.status not in ("merged", "rejected", "human-merged", "human-rejected")}
        # calibration: skeleton leg‌هایی که ۳+ بار رد شده‌اند را دیگر پیشنهاد نده
        # (ضدِ نویزِ دائمی — باید از restart جان به در ببرد، پس از chrono DB می‌خواند).
        _skipped_skeleton = []
        if self._db is not None:
            try:
                from calibration import should_skip_bottleneck as _skip_bn
            except Exception:  # noqa: BLE001
                _skip_bn = None
        drafted = []
        for key, label, reason in dormant:
            if not key:
                continue
            btag = f"organ:{key}"
            if any(btag in b for b in open_b):
                continue
            if _skip_bn is not None:
                _skip, _sr = _skip_bn(self._db, btag)
                if _skip:
                    _skipped_skeleton.append(btag)
                    continue
            rfc = self.propose_rfc(
                {"bottleneck": f"{btag} — {reason}"},
                fix=(f"اندامِ «{label}» {reason}. پیشنهادِ propose-only: یک منبعِ دادهٔ afferent "
                     f"برایش وصل شود تا از اسکلت به زنده برسد؛ یا اگر لازم نیست، فلگش خاموش بماند. "
                     f"هیچ تغییرِ کدِ تولید در این RFC نیست."),
                expected_lift="اندامِ زنده به‌جای اسکلت (observability بهتر)",
                rollback="خاموش‌کردنِ فلگ یا حذفِ ورودیِ رجیستری")
            if self.submit_for_approval(rfc):
                drafted.append(rfc.rfc_id)
        return drafted

    # ─── D-6 · restart_from_known_good + run_cycle ───────────────────────────────
    def restart_from_known_good(self, leg, db=None) -> bool:
        """قلابِ Pacemaker از P1 (خطِ ۴۸۳). پای failed از known-good ری‌استارت.
        here: reset حالتِ leg به alive + ثبتِ رویداد. (رفتارِ واقعیِ restart
        در runtime پیچیده‌تر است؛ این ساختاری است.)"""
        try:
            if hasattr(leg, "state"):
                leg.state = "alive"
            if hasattr(leg, "hlc"):
                leg.hlc = (0, 0)
            self._note("DOCTOR_RESTART", {"leg_id": getattr(leg, "id", "?"),
                                           "from": "failed", "to": "alive"})
            return True
        except Exception:  # noqa: BLE001 — restart نباید crash کند
            return False

    # ─── RFC sweep — expire stale + re-submit no-channel ──────────────────────
    def _consume_owner_revisions(self) -> int:
        """3a (2026-07-24): ویرایش‌های free-textِ مالک (approval_channel →
        state/doctor/owner-revisions.json) را در RFCهای غیر-terminal ادغام می‌کند.
        صف atomic خوانده-و-پاک می‌شود (LockedJson)؛ registryِ rfcs تک-writer می‌ماند
        (فقط خودِ Doctor). هر ادغام: append به fix + NOTE در ledger + journal +
        اطلاعِ مالک از راهِ همان channel. propose-only: status/verdict دست نمی‌خورد."""
        p = self._state_dir / "doctor" / "owner-revisions.json"
        try:
            if not p.exists():
                return 0
            with opslib.LockedJson(p) as lj:
                data = lj.read() or {}
                lj.write({})
        except Exception:  # noqa: BLE001
            return 0
        n = 0
        _terminal = ("merged", "rejected", "human-merged", "human-rejected", "expired")
        for rfc_id, rec in (data or {}).items():
            rfc = self._rfcs.get(rfc_id)
            txt = str((rec or {}).get("text") or "").strip()
            if rfc is None or not txt or rfc.status in _terminal:
                continue
            rfc.fix = rfc.fix + "\n\n**بازنگریِ مالک (" + opslib.today() + "):** " + txt[:800]
            rfc.ledger_ref = self._note("DOCTOR_OWNER_REVISION",
                                        {"rfc_id": rfc_id, "chars": len(txt)})
            self._journal(rfc_id, "owner-revision", "ok")
            n += 1
            if self._channel is not None:
                try:
                    self._channel.send_text(
                        f"🩺 بازنگریِ تو روی <code>{rfc_id}</code> ثبت و در متنِ RFC ادغام شد.")
                except Exception:  # noqa: BLE001
                    pass
        if n:
            self._persist_rfcs()
        return n

    def _sweep_stale_rfcs(self, max_age_hours: int = 24) -> dict:
        """RFCهایی که بیش از max_age_hours در وضعیت non-terminal گیر کرده‌اند:
        - submitted-no-channel با channel وصل → re-submit
        - submitted-no-channel / submit-failed / submitted قدیمی → expired
        max_age_hours=0 → sweep خاموش (rollback knob).
        """
        if max_age_hours <= 0:
            return {"swept": 0, "details": [], "resubmitted": []}
        now = time.time()
        expired, resubmitted = [], []
        for rfc_id, rfc in list(self._rfcs.items()):
            if rfc.status not in ("submitted-no-channel", "submit-failed", "submitted"):
                continue
            age_h = (now - rfc.created_ts) / 3600
            if age_h <= max_age_hours:
                continue
            # re-submit opportunity: channel الان وصل شده ولی RFC هنوز no-channel
            if rfc.status == "submitted-no-channel" and self._channel is not None:
                try:
                    ok = self.submit_for_approval(rfc)
                    resubmitted.append({"rfc_id": rfc_id, "age_h": round(age_h, 1),
                                        "new_status": rfc.status, "ok": ok})
                except Exception:  # noqa: BLE001 — sweep نباید crash کند
                    rfc.status = "expired"
                    expired.append({"rfc_id": rfc_id, "old_status": "submitted-no-channel",
                                    "age_h": round(age_h, 1)})
            else:
                rfc.status = "expired"
                expired.append({"rfc_id": rfc_id, "old_status": rfc.status, "age_h": round(age_h, 1)})
        if expired or resubmitted:
            self._note("DOCTOR_SWEEP", {"expired": expired, "resubmitted": resubmitted})
        return {"swept": len(expired), "details": expired, "resubmitted": resubmitted}

    # ─── CHORD فاز C (2026-07-18، رأی مالک «برو فاز C») — سایهٔ مشورتیِ محض ───
    def _chord_shadow(self, rfc) -> dict | None:
        """ارزیابیِ سایهٔ chord برای یک RFC — فقط ثبت (ledger chord + NOTE دکتر).
        هرگز رفتار/امتیاز/اقدام را تغییر نمی‌دهد؛ فقط با OCTOPUS_WIRE_CHORD_SHADOW=1
        صدا زده می‌شود (callsite گیت شده). import تنبل: با فلگ خاموش حتی import نمی‌شود.
        هر خطا → None (cycle هرگز نمی‌میرد). ورودی‌ها از دادهٔ موجودِ خودِ دکترند."""
        try:
            from chord.observation import from_test_result, from_manual
            from chord.adapters.doctor_adapter import shadow_assess
            obs, claims = [], []
            sr = rfc.sandbox_result if isinstance(rfc.sandbox_result, dict) else None
            if sr is not None:
                _ok = bool(sr.get("ok", sr.get("passed", False)))
                obs.append(from_test_result(f"doctor-sandbox:{rfc.rfc_id}", _ok,
                                            detail=str(sr)[:200], mission_id=rfc.rfc_id))
                claims.append({"test_health": 1.0 if _ok else 0.0,
                               "evidence_quality": 0.8})
            cr = rfc.critic_review if isinstance(rfc.critic_review, dict) else None
            if cr is not None:
                obs.append(from_manual(f"critic:{str(cr)[:180]}",
                                       who="doctor-critic", mission_id=rfc.rfc_id))
                claims.append({"uncertainty": 0.3 if cr.get("approve") else 0.6})
            # ساختاری، نه حدسی: change_level → ریسک/برگشت‌پذیری (tune=knob whitelist+ledger)
            _lvl = getattr(rfc, "change_level", "code")
            _risk = {"tune": 0.2, "reconfig": 0.45, "rewrite": 0.7}.get(_lvl, 0.75)
            _rev = {"tune": 0.9, "reconfig": 0.6, "rewrite": 0.4}.get(_lvl, 0.35)
            if getattr(rfc, "rollback", ""):
                _rev = min(1.0, _rev + 0.15)
            obs.append(from_manual(
                f"rfc change_level={_lvl} rollback={'yes' if rfc.rollback else 'no'}",
                who="doctor-structural", mission_id=rfc.rfc_id))
            claims.append({"operational_risk": _risk, "reversibility": _rev})
            ctx = {"stop_organism": bool(opslib.STOP_ORGANISM.exists())}
            rec = shadow_assess(rfc.rfc_id, obs, claims, context=ctx, log=True)
            slim = {"verdict": rec.get("verdict"),
                    "weighted_distance": rec.get("weighted_distance"),
                    "confidence": rec.get("confidence"),
                    "approval_required": rec.get("approval_required"),
                    "assessment_id": rec.get("assessment_id")}
            self._note("CHORD_SHADOW", {"rfc_id": rfc.rfc_id, **slim})
            return slim
        except Exception:  # noqa: BLE001 — سایهٔ chord هرگز cycle را نمی‌کشد
            return None

    # ─── T8 (2026-07-25): reconcileِ ورودیِ RFCها — درمانِ وضعیتی که دیگر نیست ──
    def _reconcile_input_validity(self, trace: dict | None = None) -> dict:
        """RFCهای باز که bottleneckشان به شرطِ ورودیِ دیگر-ناموجود گره خورده →
        status='stale-input' + stale_reason داخلِ critic_review. RFC حذف نمی‌شود.

        گواه (اسکن ۲۰۲۶-۰۷-۲۵): ۸ RFC با متنِ یکسانِ «σ≈1 (σ=1.00)؛ gap=0.000» در حالی
        که هر سه منبعِ زنده σ=0.0 می‌گفتند و گرافِ خطا خالی بود؛ یکی «ارگانیسم FREEZE
        است» در حالی که frozen:false بود. صفِ پیشنهادها وضعیتی را درمان می‌کرد که وجود
        نداشت. این متد در هر run_cycle (کنارِ sweep) صف را با واقعیتِ زنده تطبیق می‌دهد.
        fail-soft: خطا → صف دست‌نخورده."""
        trace = trace if trace is not None else self._gather_trace()
        marked = []
        spectral_now = "<not-computed>"
        for rfc in list(self._rfcs.values()):
            if rfc.status not in self._OPEN_RFC:
                continue
            b = str(rfc.bottleneck or "")
            reason = None
            if ("σ≈1" in b) or ("شکافِ طیفی" in b):
                if spectral_now == "<not-computed>":
                    try:
                        from spectral import spectral_mine as _sm
                        spectral_now = _sm(trace or {})
                    except Exception:  # noqa: BLE001 — spectral fail-soft → None = سالم
                        spectral_now = None
                if spectral_now is None:
                    reason = ("شرطِ طیفیِ ورودی دیگر برقرار نیست — spectral_mine روی "
                              "traceِ فعلی None می‌دهد (گرافِ خطا سالم/خالی است)")
            elif b.startswith("σ_effective="):
                try:
                    _sig = float((trace or {}).get("sigma_effective", 0) or 0)
                except (TypeError, ValueError):
                    _sig = 0.0
                if _sig <= 1.0:
                    reason = f"σ_effectiveِ فعلی {_sig} ≤ ۱ است (خطِ قرمزِ سرطان برقرار نیست)"
            elif "FREEZE" in b and not (trace or {}).get("frozen"):
                reason = "ارگانیسم دیگر FREEZE نیست (frozen=false در ORGANISM-STATE فعلی)"
            if reason:
                rfc.status = "stale-input"
                rfc.critic_review = {**(rfc.critic_review or {}),
                                     "stale_reason": reason,
                                     "stale_marked_ts": opslib.now_iso()}
                marked.append({"rfc_id": rfc.rfc_id, "reason": reason[:120]})
        if marked:
            self._note("DOCTOR_RFC_STALE_INPUT", {"marked": marked})
            self._persist_rfcs()
        return {"stale_marked": len(marked), "details": marked}

    def run_cycle(self, beat: int | None = None, trace: dict | None = None,
                  use_calibration: bool = True, use_chamber: bool = True,
                  temperature: float | None = None) -> dict | None:
        """یک دورِ کامل دکتر: mine → (calibration filter) → Chamber → propose_rfc → sandbox → submit.
        هر N ضربان از Pacemaker صدا زده می‌شود. خروجی = خلاصه یا None.
        trace قابل‌تزریق (Pacemaker می‌تواند trace را پاس دهد، یا تست).
        propose-only: هیچ merge بدونِ human-append.

        use_calibration: اگر True، effective_mine را به‌جای mine صدا می‌زند (attention-budget
        + verdict-history). اگر False، mine خالص (سازگار با تست‌های قدیمی).
        use_chamber: اگر True، RFC از Chamber تخاصمی می‌گذرد پیش از sandbox/submit."""
        # sweep RFCهای گیر کرده (expire stale, re-submit no-channel)
        self._sweep_stale_rfcs()
        # T8 (2026-07-25): RFCی که وضعیتی را درمان می‌کند که دیگر وجود ندارد → stale-input
        try:
            self._reconcile_input_validity(trace if trace is not None else self._gather_trace())
        except Exception:  # noqa: BLE001 — reconcile هرگز cycle را نمی‌کشد
            pass
        # 3a (2026-07-24): بازنگری‌های free-textِ مالک (تلگرام) → ادغام در RFCهای باز
        try:
            self._consume_owner_revisions()
        except Exception:  # noqa: BLE001 — مصرفِ بازنگری هرگز cycle را نمی‌کشد
            pass
        # Wave 3 (2026-07-15): اسکنِ اندام‌ها (پشتِ OCTOPUS_WIRE_ORGAN_DOCTOR، پیش‌فرض خاموش).
        # با فلگِ خاموش byte-identicalِ رفتارِ قبلی؛ روشن → RFCِ بهبود برای اندامِ خاموش/اسکلت.
        if os.environ.get("OCTOPUS_WIRE_ORGAN_DOCTOR") == "1":
            try:
                self.analyze_organs()
            except Exception:  # noqa: BLE001 — اسکنِ اندام نباید cycle را بکشد
                pass
        # 2026-07-18: mintِ RFCهای نوعِ 'tune' برای knobهای whitelistِ unset (پشتِ
        # OCTOPUS_WIRE_DOCTOR_KNOB_RFC، پیش‌فرض خاموش). این‌ها تنها RFCهایی‌اند که تپِ
        # merge مالک واقعاً اعمالشان می‌کند — «ربات خودش را (محدود و با تأییدِ تو) عوض می‌کند».
        if os.environ.get("OCTOPUS_WIRE_DOCTOR_KNOB_RFC") == "1":
            try:
                self._mine_knob_rfcs()
            except Exception:  # noqa: BLE001 — mintِ knob-RFC نباید cycle را بکشد
                pass
        # Phase 5: مصرفِ verdictهای انسانی از کانال (اگر کانال pop_rfc_verdicts داشته باشد؛
        # hasattr-guard = ایمن حتی قبل از این‌که کانالِ تلگرام آن را عرضه کند).
        # human-append منبعِ حقیقت می‌ماند — اینجا فقط ثبتِ calibration + وضعیتِ registry.
        try:
            if self._channel is not None and hasattr(self._channel, "claim_rfc_verdicts"):
                worker = f"doctor-{os.getpid()}"
                for rfc_id, verdict, revision in self._channel.claim_rfc_verdicts(worker):
                    mapped = {"merge-approved": "merged", "denied": "rejected"}.get(verdict)
                    if mapped is None:
                        continue
                    from calibration import record_verdict
                    # GAP-6 (۰۷-۳۱): بدونِ bottleneck_key هر ردیف با کلیدِ خالی
                    # ثبت می‌شد و should_skip_bottleneck هرگز شلیک نمی‌کرد.
                    record_verdict(self._db, rfc_id, mapped,
                                   bottleneck_key=getattr(
                                       self._rfcs.get(rfc_id), "evidence_key", "")
                                   if rfc_id in self._rfcs else "")
                    applied = False
                    receipt_id = ""
                    rfc_obj = self._rfcs.get(rfc_id)
                    if rfc_obj is None and mapped == "merged":
                        # VQ-RFC-REBUILD-001 (۲۰۲۶-۰۸-۰۳، برشِ ۲): self._rfcs فقط از
                        # rfcs.json در بوت لود می‌شود. برای RFCای که آن‌جا نیست (مثلاً
                        # rfcs.json پیش‌تر بدونِ آن بازنویسی شد)، این گیت قبلاً
                        # applied=False می‌داد و ack_rfc_verdict مستقیم LEASED→
                        # RECONCILE_REQUIRED می‌برد — برای همیشه، چون هیچ‌جا rfc_id به
                        # self._rfcs اضافه نمی‌شد تا دوباره امتحان شود (شاهدِ زنده: هر
                        # ۲۱ ردیفِ merge-approved). دفترِ کارتِ durable
                        # (pending-cards.json) summary ِ اصلی را PERSIST-BEFORE-SEND
                        # نگه داشته — از همان‌جا یک RFC نمادین بازسازی می‌شود.
                        # change_level پیش‌فرض 'code' می‌ماند ⇒ apply_merge هرگز اثرِ
                        # tune نمی‌زند، فقط رسیدِ lesson-merge می‌نویسد (بی‌خطر).
                        rebuilt = (self._channel.rebuild_rfc_summary(rfc_id)
                                  if hasattr(self._channel, "rebuild_rfc_summary") else None)
                        if rebuilt and rebuilt.get("summary"):
                            rfc_obj = RFC(rfc_id=rfc_id, bottleneck=rebuilt["summary"],
                                         fix=rebuilt["summary"],
                                         expected_lift="نامعلوم — بازسازی از دفترِ کارت",
                                         status="submitted")
                            self._rfcs[rfc_id] = rfc_obj
                    if rfc_obj is not None:
                        if mapped == "merged" and \
                                os.environ.get("OCTOPUS_WIRE_APPLY_MERGE", "1") == "1":
                            op_key = f"rfc:{rfc_id}:rev:{revision}"
                            # Persist RECONCILE_REQUIRED before apply. Crash after this line
                            # never auto-retries the mutation; an operation receipt closes it.
                            if not self._channel.begin_rfc_apply(rfc_id, revision, op_key):
                                rfc_obj.status = "reconcile-required"
                                continue
                            try:
                                # P0 MERGE-EFFECT: [merge] -> gate_promote(+proofs) -> apply_merge.
                                # Legacy RFCs without proofs keep direct apply_merge (require_gate auto-off).
                                if str(_HERE) not in sys.path:
                                    sys.path.insert(0, str(_HERE))
                                import lab_bridge as _lb_merge  # noqa: WPS433
                                _proofs = _lb_merge.proofs_from_rfc(rfc_obj)
                                _vout = _lb_merge.apply_owner_verdict(
                                    verb="merge",
                                    apply_merge_fn=self.apply_merge,
                                    rfc=rfc_obj,
                                    test_ok=bool(_proofs.get("test_ok")),
                                    evidence_path=_proofs.get("evidence_path"),
                                    rollback_plan=_proofs.get("rollback_plan"),
                                    require_gate=_proofs.get("require_gate"),
                                )
                                applied = bool(_vout.get("applied"))
                                if applied:
                                    receipt_id = str(rfc_obj.ledger_ref or "")
                            except Exception as _ame:
                                try:
                                    applied = self.apply_merge(rfc_obj)
                                    if applied:
                                        receipt_id = str(rfc_obj.ledger_ref or "")
                                except Exception as _ame2:
                                    opslib.alert([f"doctor apply_merge failed: {type(_ame2).__name__}"])
                        elif mapped == "rejected":
                            try:
                                if str(_HERE) not in sys.path:
                                    sys.path.insert(0, str(_HERE))
                                import lab_bridge as _lb_rej  # noqa: WPS433
                                _lb_rej.apply_owner_verdict(
                                    verb="reject",
                                    apply_merge_fn=self.apply_merge,
                                    rfc=rfc_obj,
                                )
                            except Exception:
                                rfc_obj.status = "human-rejected"
                    # APPLIED only after an operation receipt. Deny is terminal REJECTED.
                    acked = self._channel.ack_rfc_verdict(
                        rfc_id, revision, applied=applied,
                        receipt_id=receipt_id if applied else "")
                    if not acked and rfc_id in self._rfcs:
                        self._rfcs[rfc_id].status = "reconcile-required"
                self._persist_rfcs()
            elif self._channel is not None and hasattr(self._channel, "pop_rfc_verdicts"):
                # Legacy channel: labels only; never auto-apply because it has no durable lease.
                for rfc_id, verdict in self._channel.pop_rfc_verdicts():
                    mapped = {"merge-approved": "merged", "denied": "rejected"}.get(verdict)
                    if mapped and rfc_id in self._rfcs:
                        self._rfcs[rfc_id].status = "human-" + mapped
                self._persist_rfcs()
        except Exception as e:  # noqa: BLE001 — مصرفِ verdict هرگز cycle را نمی‌کشد
            try:
                opslib.alert([f"doctor: rfc-verdict consumption failed: {str(e)[:120]}"])
            except Exception:  # noqa: BLE001 — حتی alert هم نباید cycle را بکشد
                pass
        # calibration: mine + attention-budget + verdict-history filter
        if use_calibration:
            try:
                from calibration import effective_mine
                bottleneck = effective_mine(self, trace=trace, db=self._db)
            except Exception:  # noqa: BLE001 — fail-soft: برگرد به mine خالص
                bottleneck = self.mine(trace=trace)
        else:
            bottleneck = self.mine(trace=trace)
        if bottleneck is None:
            # P-spectral: سنسورِ طیفیِ read-only به‌عنوان گلوگاهِ مکمل (advisory، propose-only).
            # پشتِ OCTOPUS_WIRE_SPECTRAL. وقتی mine() چیزی پیدا نکرد، spectral_mine گرافِ رویداد
            # را تحلیل می‌کند (σ≈1/شکافِ کوچک = شکننده). reward-integrity دست‌نخورده (σ توصیفی).
            if os.environ.get("OCTOPUS_WIRE_SPECTRAL") == "1":
                try:
                    from spectral import spectral_mine
                    _spec_trace = trace if trace is not None else self._gather_trace()
                    bottleneck = spectral_mine(_spec_trace)
                except Exception:  # noqa: BLE001 — spectral fail-soft (fail-closed: برگرد به None)
                    bottleneck = None
        if bottleneck is None:
            return None   # چیزی برای فیکس نیست (یا attention-budget ساکت کرد)
        # اگر attention-budget ساختارِ _suppressed دارد → ثبت کن ولی RFC نده
        if isinstance(bottleneck, dict) and bottleneck.get("_suppressed_by_attention_budget"):
            self._note("DOCTOR_ATTENTION_BLOCKED", bottleneck)
            return {"suppressed": bottleneck["_suppressed_by_attention_budget"], "beat": beat}
        _before_ids = set(self._rfcs)
        rfc = self.propose_rfc(bottleneck, fix=_suggest_fix(bottleneck),
                               expected_lift=f"رفعِ {bottleneck['severity']}: {bottleneck['bottleneck']}",
                               rollback="revert flag")
        # T8 (2026-07-25): dedupe-hit = propose_rfc نسخهٔ *موجود* را برگرداند، پس id تازه
        # نیست. فقط مسیرِ «تصمیمِ نو» حذف می‌شود: chamber/sandbox/evolution/submit دوباره
        # اجرا نمی‌شوند (ضدِ اسپمِ ۸ کارت با متنِ یکسان). ناظرهای per-cycle — یعنی Box —
        # به تیک‌زدن ادامه می‌دهند: در تولید تکرارِ گلوگاه قاعده است (همان ۸ RFCِ یکسان)،
        # پس early-returnِ کامل حلقهٔ box را عملاً یخ می‌زد.
        _dedup = rfc.rfc_id in _before_ids
        # Chamber: RFC از دیالکتیکِ تخاصمی بگذرد (اگر use_chamber)
        if use_chamber and not _dedup:
            try:
                from chamber import run_chamber
                # Phase 5: دمای Chamber — فقط پشتِ flag OCTOPUS_WIRE_CHAMBER_T.
                # fail-soft: هر خطا → temperature=None = رفتارِ قبلی (بدونِ اثرِ دما).
                if temperature is None and os.environ.get("OCTOPUS_WIRE_CHAMBER_T") == "1":
                    try:
                        from temperature import TemperatureController
                        temperature = TemperatureController(db=self._db).current()
                    except Exception:  # noqa: BLE001 — دما advisory؛ خطا = بدونِ دما
                        temperature = None
                result = run_chamber(trace=trace or self._gather_trace(), initial_rfc={
                    "bottleneck": rfc.bottleneck, "fix": rfc.fix,
                    "expected_lift": rfc.expected_lift, "rollback": rfc.rollback},
                    temperature=temperature)
                if result.get("rfc") and "confidence" in result["rfc"]:
                    rfc.fix = result["rfc"].get("fix", rfc.fix)
                    # confidence را در sandbox_result نگه دار
                    if rfc.sandbox_result is None:
                        rfc.sandbox_result = {}
                    rfc.sandbox_result["chamber"] = {"confidence": result["rfc"]["confidence"],
                                                      "rounds": result["rounds_run"],
                                                      "temperature": result.get("temperature")}
            except Exception:  # noqa: BLE001 — Chamber fail-soft
                pass
        if not _dedup:
            self.run_sandbox(rfc)   # sandbox + critic (propose-only)
        # N (P-N2): Box-of-Agents — کلِ خوشهٔ box در run_cycle (پشتِ flag).
        # Box.run_tick → bottlenecks adapter → b3_bridge → doctor.submit (propose-only، human-gate).
        # b4_fusion.compute_phi_t = novelty به Box؛ falsif کنترلِ دوره‌ای.
        # Wardenِ ۲٪ + STOP-obey حفظ. خاموش = on-shelf (رفتارِ فعلی).
        box_report = None
        if os.environ.get("OCTOPUS_WIRE_BOX") == "1":
            box_report = self._run_box_cycle(trace=trace)
        # N (P-N1): Doctor Evolution — RFCArchive + measured_lift + tournament_rank.
        # پشتِ flag (OCTOPUS_WIRE_EVOLUTION، پیش‌فرض خاموز = رفتارِ فعلی).
        # mine از آرکیو نمونه می‌گیرد، tournament قبل از submit، measured_lift به‌جای expected.
        # verifier-independence دست‌نخورده: دکتر هرگز معیارِ سنجشِ خودش را ویرایش نمی‌کند.
        evolution_report = None
        if os.environ.get("OCTOPUS_WIRE_EVOLUTION") == "1" and not _dedup:
            evolution_report = self._evolve_rfc(rfc, bottleneck, trace)
        if not _dedup:
            self.submit_for_approval(rfc)   # کارتِ P3 یا pending
        result = {"rfc_id": rfc.rfc_id, "status": rfc.status,
                  "bottleneck": bottleneck["bottleneck"], "beat": beat}
        if _dedup:
            result["dedup"] = "open-rfc-exists"
        # CHORD فاز C: سایهٔ مشورتی کنارِ تصمیمِ خودِ دکتر — پشتِ فلگِ خاموش،
        # فقط ثبت + کلیدِ اطلاعاتیِ خروجی؛ هیچ شاخه/امتیاز/اقدامی عوض نمی‌شود.
        # T8: روی dedupe-hit اجرا نمی‌شود — chord یک annotationِ *تصمیم* است و
        # shadow_assess(log=True)+CHORD_SHADOW هر دو می‌نویسند؛ تکرارش برای همان RFC
        # فقط نویزِ لجر است (همان چیزی که dedupe جلویش را می‌گیرد).
        if os.environ.get("OCTOPUS_WIRE_CHORD_SHADOW") == "1" and not _dedup:
            _cs = self._chord_shadow(rfc)
            if _cs is not None:
                result["chord_shadow"] = _cs
        if evolution_report is not None:
            result["evolution"] = evolution_report
        if box_report is not None:
            result["box"] = box_report
            # truth-map 2026-07-17: box هیچ ردِ دیسکی نداشت → «armed یا زنده؟» از state
            # تصمیم‌ناپذیر بود (Open UNKNOWN #5). یک snapshotِ کوچکِ fail-soft کافی است.
            try:
                _bp = self._state_dir / "doctor" / "box-latest.json"
                _bp.parent.mkdir(parents=True, exist_ok=True)
                _bp.write_text(json.dumps(
                    {"ts": opslib.now_iso(), "beat": beat,
                     "rfc_id": rfc.rfc_id, "report": box_report},
                    ensure_ascii=False, default=str)[:20000], "utf-8")
            except Exception:  # noqa: BLE001 — ردِ box نباید cycle را بکشد
                pass
        return result

    def _run_box_cycle(self, trace: dict | None = None) -> dict:
        """P-N2: کلِ خوشهٔ box در run_cycle (پشتِ flag OCTOPUS_WIRE_BOX).
        Box.run_tick → bottlenecks adapter → b3_bridge.box_to_doctor_pipeline →
        doctor.submit (propose-only، human-gate؛ هرگز merge خودکار).
        b4_fusion.compute_phi_t = سیگنالِ novelty به Box.
        falsif_suite = کنترلِ دوره‌ای (هر M beat).
        Wardenِ ۲٪ + STOP-obey حفظ می‌شود (داخلِ Box خودش).

        خروجی: {stepped, phi_t, submitted_count, falsif_majority}.
        با wire شدنِ box.py، support-libهایش (agent_state/dynamics/archivist/
        topology/sensors/null_dreamer) خودکار reachable می‌شوند."""
        # مسیرِ box را روی path بگذار (داخلِ _ops/doctor/box/). __init__.py خالی
        # است ولی چون پوشهٔ والد (_ops/doctor) هم روی path است، `box` به‌عنوانِ پکیج
        # دیده می‌شود و box.py را shadow می‌کند. راه‌حل: پوشهٔ box را اولِ path بگذار
        # تا box.py ماژولِ سطحِ بالا شود (مثلِ test_box.py).
        box_dir = str(_HERE / "box")
        if box_dir not in sys.path:
            sys.path.insert(0, box_dir)
        # اگر _ops/doctor روی path است، پکیجِ box با __init__.pyِ خالی interference
        # می‌کند. path box_dir را مقدم می‌کنیم تا `from box import Box` فایلِ box.py
        # را ببرد (نه __init__). این همان الگوی test_box.py.
        # Box lazy بساز اگر نباشد
        if self._box is None:
            try:
                # path box_dir را اولِ sys.path مطمئن کن (push به index 0)
                if sys.path[0] != box_dir:
                    sys.path.remove(box_dir)
                    sys.path.insert(0, box_dir)
                from box import Box, BoxConfig  # noqa: E402
                self._box = Box(BoxConfig(seed=42))
            except Exception as e:  # noqa: BLE001 — box fail-soft
                return {"stepped": False, "error": f"box import/build failed: {e}"}
        try:
            from b3_bridge import box_to_doctor_pipeline  # noqa: E402
        except Exception as e:  # noqa: BLE001
            return {"stepped": False, "error": f"b3_bridge import failed: {e}"}
        # ── یک step از Box روی trace (Wardenِ ۲٪ + STOP داخلِ Box)
        snap = self._box.run_tick(trace=trace)
        stepped = bool(snap and not snap.get("cycle_ended"))
        if not stepped:
            return {"stepped": False,
                    "cycle_ended_reason": (snap or {}).get("reason", "no-snap")}
        # ── b4_fusion: φ_t به‌عنوانِ سیگنالِ novelty (advisory)
        # B8: φ_t از cycleِ قبلی به noveltyِ این cycle تبدیل می‌شود (lag عمدی: feedback loop).
        # cycle اول بدونِ phi_tِ قبلی → novelty دست‌نخورده (graceful).
        phi_report = None
        novelty_from_phi = None
        try:
            from b4_fusion import compute_phi_t, phi_to_novelty
            # اگر phi_t از cycle قبلی موجود است → novelty بساز
            if getattr(self, "_last_phi_t", None) is not None:
                novelty_from_phi = phi_to_novelty(self._last_phi_t)
            # phi_t این cycle را محاسبه و نگه‌دار برایِ cycle بعد
            edges = []
            for i in range(len(self._box.agents) - 1):
                edges.append((i, i + 1))
            n = len(self._box.agents)
            agent_states = [a.cognitive.hidden_state[0] if a.cognitive.hidden_state else 0.5
                            for a in self._box.agents]
            phi_report = compute_phi_t(edges, n, agent_states)
            self._last_phi_t = phi_report   # برایِ cycle بعد
        except Exception:  # noqa: BLE001 — b4 advisory fail-soft
            phi_report = {"available": False}
        # ── bottlenecks adapter: snapshot → bottlenecks (برای b3_bridge)
        metrics_with_bn = dict(snap)
        metrics_with_bn["bottlenecks"] = self._box_metrics_to_bottlenecks(snap)
        # ── b3_bridge: insights → doctor.submit (propose-only، human-gate)
        submit_results = []
        try:
            submit_results = box_to_doctor_pipeline(metrics_with_bn, doctor=self)
        except Exception as e:  # noqa: BLE001 — b3 fail-soft
            submit_results = [{"submitted": False, "error": str(e)[:200]}]
        submitted_count = sum(1 for r in submit_results if r.get("submitted"))
        # ── falsif_suite: کنترلِ دوره‌ای (هر M beat)
        falsif_majority = None
        if self._box.tick_count % int(os.environ.get("CHRONO_BOX_FALSIF_EVERY_N_TICKS", "100")) == 0:
            try:
                from falsif_harness import run_falsif_suite
                falsif_report = run_falsif_suite()
                falsif_majority = falsif_report.get("neural_majority")
            except Exception:  # noqa: BLE001 — falsif advisory fail-soft
                falsif_majority = None
        # ── گزارش (propose-only؛ هیچ merge)
        report = {"stepped": True,
                  "tick": snap.get("tick"),
                  "phi_t": phi_report,
                  "novelty_from_phi": novelty_from_phi,
                  "submitted_count": submitted_count,
                  "submit_results_count": len(submit_results),
                  "falsif_majority": falsif_majority,
                  "warden_cap_2pct": self._box.warden.E_box_max,
                  "budget_used": self._box.warden.tokens_spent_total,
                  "propose_only": True}
        return report

    def _box_metrics_to_bottlenecks(self, snap: dict) -> list[dict]:
        """آداپتور: Box snapshot → bottlenecks برای b3_bridge.
        Box.run_tick bottlenecks تولید نمی‌کند (فقط metrics)؛ این تابع آن را
        از flagged/stress/coherence استخراج می‌کند. propose-only."""
        bottlenecks = []
        flagged = snap.get("flagged") or []
        if flagged:
            bottlenecks.append({
                "description": f"agents flagged by Warden (safety<τ): {flagged[:4]}",
                "suggested_fix": "review flagged agents — propose-only، human-gate",
                "expected_lift": "reduce safety-flag count",
                "confidence": 0.6})
        stress = snap.get("mean_stress", 0)
        if isinstance(stress, (int, float)) and stress > 0.6:
            bottlenecks.append({
                "description": f"mean_stress={stress:.2f} elevated in Box",
                "suggested_fix": "review load/allocation — propose-only",
                "expected_lift": "lower mean_stress",
                "confidence": 0.5})
        rho = snap.get("rho_J", 0)
        if isinstance(rho, (int, float)) and rho > 0.9:
            bottlenecks.append({
                "description": f"ρ(J)={rho:.2f} near-instability",
                "suggested_fix": "monitor coupling — propose-only",
                "expected_lift": "stable ρ(J) < ρ_max",
                "confidence": 0.55})
        return bottlenecks

    def _evolve_rfc(self, rfc: RFC, bottleneck: dict, trace: dict | None) -> dict:
        """P-N1: مسیرِ Doctor Evolution (پشتِ flag). RFC فعلی + mutationهای آرشیو →
        measured_lift → tournament_rank → survivor (فقط برنده submit).
        verifier-independence: lift از measured_lift مستقل (eval_fn)، نه از خودِ دکتر.

        خروجی: گزارشِ {archive_size, candidates, winner_lift, survivor_rfc_id}.
        هرگز معیارِ سنجشِ دکتر را ویرایش نمی‌کند (حلقهٔ حرام)."""
        try:
            from evolution import (RFCArchive, measured_lift, tournament_rank, survivor)
        except Exception as e:  # noqa: BLE001 — evolution fail-soft
            return {"error": f"evolution import failed: {e}"}
        # آرشیو lazy بساز اگر نباشد
        if self._archive is None:
            self._archive = RFCArchive()
        archive = self._archive
        # bottleneck_key + organ برای سلول
        bkey = (bottleneck.get("evidence") or {}).get("key", "unknown")
        organ = (bottleneck.get("evidence") or {}).get("organ", "_global")
        # ۱) RFC فعلی را در آرشیو ثبت (بهترین-در-هر-سلول)
        crit_ok = (rfc.critic_review or {}).get("reward_integrity_ok", True)
        base_score = 0.3 if crit_ok else 0.0   # پایه: lift تخمینی از critic
        archive.insert(bkey, organ, rfc.rfc_id, base_score, fix=rfc.fix,
                       parent_id=None)
        # ۲) mutation از آرکیو sample کن (اگر سلولی هست)
        candidates = []
        cell = archive.sample()
        if cell is not None:
            mutation = archive.mutate(cell)
            # verifier-independence: measured_lift از eval_fn مستقل — دکتر معیار را
            # نمی‌نویسد؛ eval_fn خارجی (default یا تزریق‌شده).
            # up-1363aae4df (۲۰۲۶-۰۸-۰۸): suite_fn واقعی از _suite_fnِ تزریق‌شده
            # تغذیه می‌شود تا lift از suite-delta محاسبه شود (نه از severity).
            # اگر _suite_fn نباشد، _default_eval به fallbackِ severity برمی‌گردد
            # (صادقانه stub-label‌شده) — backward-compat با رفتارِ قبلی.
            ml = measured_lift({
                "fix": mutation.get("fix", ""),
                "evidence": bottleneck.get("evidence"),
            }, suite_fn=getattr(self, "_suite_fn", None))
            if not ml["dropped"]:
                candidates.append({"fix": mutation["fix"], "lift": ml["lift"],
                                   "rfc_id": rfc.rfc_id, "parent": cell.rfc_id})
        # RFC فعلی هم کاندید (baseline lift)
        candidates.append({"fix": rfc.fix, "lift": base_score,
                           "rfc_id": rfc.rfc_id, "parent": None})
        # ۳) tournament_rank بین کاندیدها
        ranked = tournament_rank(candidates)
        winners = survivor(ranked, top_k=1)
        winner = winners[0] if winners else candidates[0]
        # ۴) اگر برنده mutation است و بهتر از baseline → fix را به‌روز کن (propose-only)
        if winner.get("parent") and winner["lift"] > base_score:
            rfc.fix = winner["fix"]
            # ثبتِ update (propose-only — finalize با human-append)
            rfc.ledger_ref = self._note("DOCTOR_EVOLUTION_WINNER", {
                "rfc_id": rfc.rfc_id, "parent": winner["parent"],
                "lift": winner.get("lift"), "elo": winner.get("elo")})
        # ثبتِ cell بهتر در آرشیو (feedback loop بدونِ حلقهٔ حرام — فقط score می‌نویسد)
        archive.insert(bkey, organ, rfc.rfc_id, winner.get("lift", base_score),
                       fix=rfc.fix, parent_id=winner.get("parent"))
        return {"archive_size": archive.size, "candidates": len(candidates),
                "winner_lift": winner.get("lift", 0.0),
                "winner_parent": winner.get("parent"),
                "survivor_rfc_id": winner.get("rfc_id")}


def _suggest_fix(bottleneck: dict) -> str:
    """از bottleneck یک fixِ پیشنهادیِ ساده بساز (propose-only — انسان آن را ویرایش می‌کند)."""
    key = (bottleneck.get("evidence") or {}).get("key", "")
    fixes = {
        "error-rate-high": "افزودنِ guard برای کاهشِ نرخِ خطا در ارگان‌های متأثر",
        "effects-stuck": "بازبینیِ اثرهای pending گیرکرده — settle یا refuse",
        "frozen-conflict": "رفعِ تعارضِ تلمتری که FREEZE کرده",
        "sigma-cancer-risk": "افزایشِ گاردِ replication (σ>1 = خطِ قرمز)",
        "legs-starved": ("اتصالِ منبعِ خوراک به صندوقِ state/legs/<leg>-inbox پای گرسنه، "
                         "یا تازه‌سازیِ منبعِ راکد (propose-only — تصمیم با مالک)"),
    }
    return fixes.get(key, "بازبینیِ گلوگاهِ شناسایی‌شده (propose-only)")


def _read_json_safe(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
