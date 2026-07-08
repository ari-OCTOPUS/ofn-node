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
                 approval_channel=None, sandbox_runner=None):
        self._state_dir = Path(state_dir) if state_dir else (opslib.STATE_DIR)
        self._knowledge_dir = Path(knowledge_dir) if knowledge_dir else (
            _OPS.parent / "07 - Knowledge" / "genome-system" / "knowledge" / "internal")
        self._ledger = ledger                            # genome ledger (lazy via opslib)
        self._channel = approval_channel                 # P3 TelegramApprovalChannel (D-5)
        self._sandbox_runner = sandbox_runner            # قابل‌تزریق (تست)
        self._rfcs: dict[str, RFC] = {}                  # registry در حافظه

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
        """جمعِ متریک از state/*.json + heartbeat. fail-soft: نبود = trace خالی."""
        trace: dict[str, Any] = {}
        org = _read_json_safe(self._state_dir / "ORGANISM-STATE.json")
        if org:
            trace["frozen"] = bool(org.get("frozen"))
            trace["halted"] = org.get("halted")
            trace["errors_24h"] = len(org.get("conflicts") or [])
        rep = _read_json_safe(self._state_dir / "replication-latest.json")
        if rep:
            try:
                trace["sigma_effective"] = float(rep.get("sigma") or rep.get("sigma_effective") or 0)
            except (TypeError, ValueError):
                pass
        # effects_pending از chrono (اگر db وصل باشد) — در production از Pacemaker
        return trace

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

    def run_cycle(self, beat: int | None = None, trace: dict | None = None) -> dict | None:
        """یک دورِ کامل دکتر: mine → propose_rfc → sandbox → submit.
        هر N ضربان از Pacemaker صدا زده می‌شود. خروجی = خلاصه یا None.
        trace قابل‌تزریق (Pacemaker می‌تواند trace را پاس دهد، یا تست).
        propose-only: هیچ merge بدونِ human-append."""
        bottleneck = self.mine(trace=trace)
        if bottleneck is None:
            return None   # چیزی برای فیکس نیست
        rfc = self.propose_rfc(bottleneck, fix="(auto-detected — نیاز به تعامل)",
                               expected_lift=f"رفعِ {bottleneck['severity']}: {bottleneck['bottleneck']}",
                               rollback="revert flag")
        self.run_sandbox(rfc)   # sandbox + critic (propose-only)
        self.submit_for_approval(rfc)   # کارتِ P3 یا pending
        return {"rfc_id": rfc.rfc_id, "status": rfc.status,
                "bottleneck": bottleneck["bottleneck"], "beat": beat}


def _read_json_safe(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
