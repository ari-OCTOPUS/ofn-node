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

    def __post_init__(self):
        if not self.rfc_hash:
            canon = json.dumps({"rfc_id": self.rfc_id, "bottleneck": self.bottleneck,
                                "fix": self.fix, "expected_lift": self.expected_lift},
                               ensure_ascii=False, sort_keys=True)
            self.rfc_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]

    def to_dict(self) -> dict:
        return {"rfc_id": self.rfc_id, "bottleneck": self.bottleneck, "fix": self.fix,
                "expected_lift": self.expected_lift, "rollback": self.rollback,
                "sandbox_result": self.sandbox_result, "critic_review": self.critic_review,
                "status": self.status, "ledger_ref": self.ledger_ref, "rfc_hash": self.rfc_hash}

    def to_markdown(self) -> str:
        """نمایشِ markdown برای knowledge/internal یا کارتِ P3."""
        lines = [f"# RFC {self.rfc_id}", "", f"**status:** {self.status}", "",
                 f"## مسئله (bottleneck)", self.bottleneck, "",
                 f"## فیکس پیشنهادی", self.fix, "",
                 f"## lift موردِانتظار", self.expected_lift, ""]
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
                 archive=None):
        self._state_dir = Path(state_dir) if state_dir else (opslib.STATE_DIR)
        self._knowledge_dir = Path(knowledge_dir) if knowledge_dir else (
            _OPS.parent / "07 - Knowledge" / "genome-system" / "knowledge" / "internal")
        self._knowledge_dir.mkdir(parents=True, exist_ok=True)  # ⚑ گاف ۳ بسته شد
        self._ledger = ledger                            # genome ledger (lazy via opslib)
        self._channel = approval_channel                 # P3 TelegramApprovalChannel (D-5)
        self._sandbox_runner = sandbox_runner            # قابل‌تزریق (تست)
        self._db = db                                    # chrono ChronoDB (effects_pending)
        self._rfcs: dict[str, RFC] = {}                  # registry در حافظه
        # N (P-N1): RFCArchive برای evolution (MAP-Elites). lazy: اگر None،
        # با flag روشن در اولین run_cycle ساخته می‌شود. قابل‌تزریق برای تست.
        self._archive = archive

    def _lg(self):
        return self._ledger or opslib.genome_ledger()

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
        # اگر چیزی نبود → گلوگاهی نیست (نه «همه‌چیز خوب» — just nothing to fix)
        if not candidates:
            return None
        # انتخابِ بالاترین severity (و به‌تساوی، پایین‌ترین score = بدتر)
        candidates.sort(key=lambda c: ({"critical": 0, "high": 1}.get(c[2], 2), c[3]))
        key, desc, sev, score = candidates[0]
        return {"bottleneck": desc, "evidence": {"key": key, "severity": sev,
                                                 "score": score,
                                                 "lambda_persist_applied": LAMBDA_PERSIST},
                "severity": sev}

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
                    rollback: str = "") -> RFC:
        """از گلوگاه یک RFC می‌سازد. این یک proposal-event است، نه تغییرِ کد.
        RFC به knowledge/internal نوشته می‌شود (propose-only)."""
        rfc = RFC(rfc_id=f"RFC-{uuid.uuid4().hex[:8]}",
                  bottleneck=bottleneck.get("bottleneck", str(bottleneck)),
                  fix=fix, expected_lift=expected_lift, rollback=rollback,
                  status="draft")
        # reward-integrity: اگر fix ناظر به uptime/keep-beating باشد، جریمه می‌خورد
        fix_lower = fix.lower()
        if any(w in fix_lower for w in ("uptime", "keep-beating", "keep-alive", "keep alive")):
            rfc.critic_review = {"reward_integrity_warning":
                                 f"fix به uptime اشاره دارد — λ_persist={LAMBDA_PERSIST} اعمال"}
        rfc.ledger_ref = self._note("DOCTOR_RFC_DRAFT", rfc.to_dict())
        rfc.status = "drafted"
        self._rfcs[rfc.rfc_id] = rfc
        # نوشتن به knowledge/internal (propose-only = یک فایلِ RFC، نه تغییرِ production)
        try:
            self._knowledge_dir.mkdir(parents=True, exist_ok=True)
            (self._knowledge_dir / f"{rfc.rfc_id}.md").write_text(
                rfc.to_markdown(), encoding="utf-8")
        except OSError:
            pass   # fail-soft: RFC در registry است حتی اگر فایل نرفت
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
            rfc.sandbox_result = result
            rfc.status = "sandboxed" if result.get("applied") else "sandbox-skip"
            rfc.ledger_ref = self._note("DOCTOR_SANDBOX", {"rfc_id": rfc.rfc_id,
                                                            "result": {k: v for k, v in result.items()
                                                                       if k != "sandbox_dir"}})
        finally:
            # پاکسازیِ sandbox (تضمینِ ایزولاسیون)
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        return result

    def _critic_review(self, rfc: RFC, sandbox_result: dict) -> dict:
        """Critic: یک بازبینیِ adversarial. آیا این فیکس واقعاً مشکل را حل می‌کند؟
        آیا regression معرفی می‌کند؟ reward-integrity check.
        دکترِ واقعی از LLM برای deep-red-team استفاده می‌کند؛ اینجا deterministic guardrails."""
        review = {"verdict": "neutral", "concerns": [], "reward_integrity_ok": True}
        # reward-integrity: fix نباید uptime را هدف بگذارد
        fix_lower = rfc.fix.lower()
        if any(w in fix_lower for w in ("uptime", "keep-beating", "keep-alive")):
            review["reward_integrity_ok"] = False
            review["concerns"].append(
                f"fix uptime را هدف می‌گذارد — نقضِ reward-integrity (λ_persist={LAMBDA_PERSIST})")
            review["verdict"] = "reject"
        # اگر تست‌ها شکست خوردند → concern
        tests = sandbox_result.get("tests")
        if tests and tests.get("exit", 0) != 0:
            review["concerns"].append("sandbox tests failed — regression risk")
            review["verdict"] = "reject" if review["verdict"] != "reject" else "reject"
        # اگر fix خالی یا مبهم
        if len(rfc.fix.strip()) < 10:
            review["concerns"].append("fix слишком کوتاه/مبهم")
            review["verdict"] = "reject"
        # اگر no concern و tests سبز → accept
        if not review["concerns"]:
            review["verdict"] = "accept"
        rfc.critic_review = review
        return review

    # ─── D-5 · submit_for_approval — کارتِ merge/reject تلگرام ────────────────────
    def submit_for_approval(self, rfc: RFC) -> bool:
        """RFC را برای merge به اپراتور بسته می‌کند. اگر P3 channel وصل باشد،
        کارتِ [merge پشتِ flag]/[reject] می‌فرستد. بدونِ channel → False (pending ابدی).
        فقط human-append (P3، is_human=1) merge را settle می‌کند."""
        if self._channel is None:
            rfc.status = "submitted-no-channel"   # pending ابدی تا channel
            return False
        try:
            ok = self._channel.rfc_card(rfc.rfc_id, rfc.to_markdown()[:800])
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            rfc.status = "submitted"
            rfc.ledger_ref = self._note("DOCTOR_SUBMIT", {"rfc_id": rfc.rfc_id,
                                                            "rfc_hash": rfc.rfc_hash})
        else:
            rfc.status = "submit-failed"
        return ok

    def apply_merge(self, rfc: RFC) -> bool:
        """اعمالِ merge بعد از human-append. این فقط بعد از تأییدِ تلگرامی صدا زده
        می‌شود. merge پشتِ flag. درسِ آموخته به knowledge/internal."""
        if rfc.status not in ("submitted", "submitted-no-channel"):
            return False
        rfc.status = "merged"
        rfc.ledger_ref = self._note("DOCTOR_MERGE", {"rfc_id": rfc.rfc_id,
                                                       "behind_flag": True})
        # درسِ آموخته
        try:
            self._knowledge_dir.mkdir(parents=True, exist_ok=True)
            (self._knowledge_dir / f"{rfc.rfc_id}-lesson.md").write_text(
                f"# درسِ آموخته — {rfc.rfc_id}\n\n{rfc.to_markdown()}\n",
                encoding="utf-8")
        except OSError:
            pass
        return True

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

    def run_cycle(self, beat: int | None = None, trace: dict | None = None,
                  use_calibration: bool = True, use_chamber: bool = True) -> dict | None:
        """یک دورِ کامل دکتر: mine → (calibration filter) → Chamber → propose_rfc → sandbox → submit.
        هر N ضربان از Pacemaker صدا زده می‌شود. خروجی = خلاصه یا None.
        trace قابل‌تزریق (Pacemaker می‌تواند trace را پاس دهد، یا تست).
        propose-only: هیچ merge بدونِ human-append.

        use_calibration: اگر True، effective_mine را به‌جای mine صدا می‌زند (attention-budget
        + verdict-history). اگر False، mine خالص (سازگار با تست‌های قدیمی).
        use_chamber: اگر True، RFC از Chamber تخاصمی می‌گذرد پیش از sandbox/submit."""
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
            return None   # چیزی برای فیکس نیست (یا attention-budget ساکت کرد)
        # اگر attention-budget ساختارِ _suppressed دارد → ثبت کن ولی RFC نده
        if isinstance(bottleneck, dict) and bottleneck.get("_suppressed_by_attention_budget"):
            self._note("DOCTOR_ATTENTION_BLOCKED", bottleneck)
            return {"suppressed": bottleneck["_suppressed_by_attention_budget"], "beat": beat}
        rfc = self.propose_rfc(bottleneck, fix=_suggest_fix(bottleneck),
                               expected_lift=f"رفعِ {bottleneck['severity']}: {bottleneck['bottleneck']}",
                               rollback="revert flag")
        # Chamber: RFC از دیالکتیکِ تخاصمی بگذرد (اگر use_chamber)
        if use_chamber:
            try:
                from chamber import run_chamber
                result = run_chamber(trace=trace or {}, initial_rfc={
                    "bottleneck": rfc.bottleneck, "fix": rfc.fix,
                    "expected_lift": rfc.expected_lift, "rollback": rfc.rollback})
                if result.get("rfc") and "confidence" in result["rfc"]:
                    rfc.fix = result["rfc"].get("fix", rfc.fix)
                    # confidence را در sandbox_result نگه دار
                    if rfc.sandbox_result is None:
                        rfc.sandbox_result = {}
                    rfc.sandbox_result["chamber"] = {"confidence": result["rfc"]["confidence"],
                                                      "rounds": result["rounds_run"]}
            except Exception:  # noqa: BLE001 — Chamber fail-soft
                pass
        self.run_sandbox(rfc)   # sandbox + critic (propose-only)
        # N (P-N1): Doctor Evolution — RFCArchive + measured_lift + tournament_rank.
        # پشتِ flag (OCTOPUS_WIRE_EVOLUTION، پیش‌فرض خاموز = رفتارِ فعلی).
        # mine از آرشیو نمونه می‌گیرد، tournament قبل از submit، measured_lift به‌جای expected.
        # verifier-independence دست‌نخورده: دکتر هرگز معیارِ سنجشِ خودش را ویرایش نمی‌کند.
        evolution_report = None
        if os.environ.get("OCTOPUS_WIRE_EVOLUTION") == "1":
            evolution_report = self._evolve_rfc(rfc, bottleneck, trace)
        self.submit_for_approval(rfc)   # کارتِ P3 یا pending
        result = {"rfc_id": rfc.rfc_id, "status": rfc.status,
                  "bottleneck": bottleneck["bottleneck"], "beat": beat}
        if evolution_report is not None:
            result["evolution"] = evolution_report
        return result

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
        # ۲) mutation از آرشیو sample کن (اگر سلولی هست)
        candidates = []
        cell = archive.sample()
        if cell is not None:
            mutation = archive.mutate(cell)
            # verifier-independence: measured_lift از eval_fn مستقل — دکتر معیار را
            # نمی‌نویسد؛ eval_fn خارجی (default یا تزریق‌شده).
            ml = measured_lift({
                "fix": mutation.get("fix", ""),
                "evidence": bottleneck.get("evidence"),
            })
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
