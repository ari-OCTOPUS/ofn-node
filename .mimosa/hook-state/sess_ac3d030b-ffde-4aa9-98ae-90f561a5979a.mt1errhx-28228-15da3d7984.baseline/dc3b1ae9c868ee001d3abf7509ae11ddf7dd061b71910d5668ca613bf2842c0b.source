#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mission_runner.py — اجرای ایزولهٔ ماموریت (§۷ و فازِ ۴ اکتاپوس‌OS).

قانونی که سؤال‌بردار نیست:
    هیچ پچی مستقیم روی درختِ زنده نوشته نمی‌شود. سه پروسهٔ در حالِ اجرا کد را از
    دیسک می‌خوانند؛ پچِ نیمه = مرگِ ارگانیسم وسطِ کار.

چرخه:
    git worktree add  →  پچ  →  سوئیت  →  دیف  →  کارت  →  (رأی)  →  merge
                                                          ↘ رد ⇒ worktree پاک

تضمین‌هایی که این ماژول می‌دهد و تست می‌شوند:
    ۱ پچِ خراب ⇒ کارتِ قرمز و **صفر بایتِ** تغییر در درختِ زنده
    ۲ worktree در `finally` پاک می‌شود، حتی با استثنا یا تایم‌اوت
    ۳ پایه هر بار **اندازه‌گیری** می‌شود، نه هاردکد
    ۴ سقفِ زمان و سقفِ فراخوانِ پولی، هر دو enforce
    ۵ merge فقط با رأیِ صریح — سبزِ کامل به‌تنهایی کافی نیست

stdlib-only (subprocess + pathlib). صفر وابستگیِ بیرونی.
"""
from __future__ import annotations

import difflib
import hashlib
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

__all__ = ["MissionRunner", "MissionResult", "SuiteResult", "Verdict"]

_COUNT_RE = re.compile(r"(\d+)\s*(?:فایل تست|tests?|passed|/)", re.IGNORECASE)


@dataclass(frozen=True)
class SuiteResult:
    exit_code: int
    count: int | None
    seconds: float
    tail: str
    failed: tuple[str, ...] = ()   # فایل‌های تستِ قرمز (از خطِ خلاصهٔ run_all)

    @property
    def green(self) -> bool:
        return self.exit_code == 0


@dataclass
class MissionResult:
    mission_id: str
    ok: bool
    stage: str
    baseline: SuiteResult | None = None
    candidate: SuiteResult | None = None
    diff: str = ""
    files_changed: int = 0
    seconds: float = 0.0
    reasons: list[str] = field(default_factory=list)
    live_tree_untouched: bool = True
    suite_touched: list[str] = field(default_factory=list)   # پچ به شاهد دست زد؟

    @property
    def new_failures(self) -> tuple[str, ...]:
        """تست‌هایی که کاندید **به‌نام** قرمز کرد ولی در پایه قرمز نبودند — یعنی خودِ پچ
        شکاندشان. قرمزهای **پیش‌موجود** (پایه هم قرمزشان بود) و قرمزهای **محیطیِ**
        worktree (رازِ gitignore‌شده که کپی نمی‌شود) در هر دو طرف‌اند و خودبه‌خود حذف می‌شوند."""
        if self.baseline is None or self.candidate is None:
            return ()
        return tuple(sorted(set(self.candidate.failed) - set(self.baseline.failed)))

    @property
    def regressed(self) -> bool:
        """پچ سوئیت را بدتر کرد؟ دو حالت: (۱) فایلِ تستِ نوی نام‌دار قرمز شد، یا
        (۲) پایه سبز بود ولی کاندید نه — حتی اگر قالبِ سوئیت نامِ فایل ندهد (تستِ mini)."""
        if self.baseline is None or self.candidate is None:
            return True
        if self.new_failures:
            return True
        return self.baseline.green and not self.candidate.green

    @property
    def may_merge(self) -> bool:
        """معیارِ *پیشنهادِ* merge = **بدونِ رگرسیون** — نه سبزِ مطلق. چرا: سوئیتِ زنده
        ممکن است قرمزِ پیش‌موجود داشته باشد (کارِ در-جریانِ دیگری) یا قرمزِ محیطی
        (تستی که رازِ زنده می‌خواند و worktree آن را ندارد). گیت باید بسنجد «پچ چیزی
        شکاند؟»، نه «همه‌چیز سبز است؟» — وگرنه یا قفلِ ابدی می‌شود یا وادار به دروغ.
        خودِ merge همچنان رأیِ صریحِ مالک می‌خواهد؛ این فقط *پیشنهاد* را باز می‌کند."""
        return (self.ok and self.live_tree_untouched
                and self.candidate is not None and self.baseline is not None
                and not self.regressed
                and self.candidate.exit_code not in (124, 125))   # تایم‌اوت/کرشِ harness نه

    def card(self) -> str:
        """متنِ کارتِ تلگرام (کارتِ ۲ — گیتِ دیف)."""
        if not self.ok:
            return (f"❌ ماموریت {self.mission_id} — {self.stage}\n"
                    + "\n".join(f"· {r}" for r in self.reasons[:4]))
        b = len(self.baseline.failed) if self.baseline else "?"
        c = len(self.candidate.failed) if self.candidate else "?"
        mark = "✅" if self.may_merge else "⚠️"
        warn = (f"\n⚠️ پچ به سوئیت دست زد ({len(self.suite_touched)} فایل) — "
                "حکم با سوئیتِ **دست‌نخورده** گرفته شد" if self.suite_touched else "")
        if not self.regressed:
            reg = "بدونِ رگرسیون"
        elif self.new_failures:
            reg = f"❌ {len(self.new_failures)} قرمزِ نو: " + ", ".join(self.new_failures[:3])
        else:
            reg = "❌ سوئیت قرمز شد (پایه سبز بود)"
        return (f"{mark} ماموریت {self.mission_id}\n"
                f"{reg} · قرمزِ پیش‌موجود: پایه {b} / کاندید {c} · "
                f"دیف {self.files_changed} فایل · {self.seconds:.0f}s\n"
                f"درختِ زنده دست‌نخورده: {'بله' if self.live_tree_untouched else '❌ خیر'}"
                + warn)


class Verdict:
    APPROVE = "approve"
    REJECT = "reject"
    RETRY = "retry"


class MissionRunner:
    def __init__(self, repo_root: str | Path, suite_cmd: list[str],
                 worktrees_dir: str | Path | None = None,
                 timeout_s: float = 900.0,
                 env_root_key: str | None = None):
        self.repo = Path(repo_root).resolve()
        self.suite_cmd = list(suite_cmd)
        self.worktrees = Path(worktrees_dir or (self.repo / "_worktrees")).resolve()
        self.timeout_s = float(timeout_s)
        # env_root_key: نامِ متغیرِ محیطی که ریشهٔ درختِ زیرِ آزمون را به سوئیت اعلام
        # می‌کند (مثلاً ORG_ROOT — همان الگوی code_autonomy). بدونِ این pin، سوئیتی که
        # ریشه‌اش را از env می‌گیرد در worktree هم به درختِ زنده resolve می‌شود و
        # می‌تواند ارگانیسمِ زنده را لمس/متوقف کند. None = رفتارِ قبلی (وراثتِ env).
        self.env_root_key = env_root_key

    # ------------------------------------------------------------------ git
    def _git(self, *args: str, cwd: Path | None = None, check: bool = True):
        r = subprocess.run(["git", *args], cwd=str(cwd or self.repo),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        if check and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} ⇒ {r.returncode}: {r.stderr[:400]}")
        return r

    # مصنوعاتِ ساخت که تغییرشان «لمسِ درختِ زنده» نیست. اجرای خودِ سوئیت این‌ها
    # را می‌سازد؛ اگر جزوِ اثرِ انگشت باشند، گاردِ ایمنی هر بار الکی شلیک می‌کند و
    # بعد از دو روز کسی جدی‌اش نمی‌گیرد — همان بیماریِ §۰ به شکلِ آژیرِ دروغ.
    EPHEMERAL = ("__pycache__/", ".pyc", ".pyo", ".pytest_cache/",
                 ".coverage", "_worktrees/")
    # ۲۹ جولای (VQ-DR-005): این مسیرها را ارگانیسمِ زنده **هر تیک** می‌نویسد — دادهٔ
    # حالت، نه منبع. شمردنشان در اثرِ انگشت یعنی هر اجرای چنددقیقه‌ای «درختِ زنده تغییر
    # کرد» می‌دهد حتی وقتی پچ هیچ فایلِ سورسی را لمس نکرده. fingerprint فقط **منبع** را می‌سنجد.
    VOLATILE = ("_ops/state/", "_ops/state\\", "/state/",
                "governor-alerts.md", "ledger.jsonl", "-latest.json",
                "budget-state.json", "organ-state.json", "fugu-quota.json")

    def live_fingerprint(self) -> str:
        """اثرِ انگشتِ **محتوای منبعِ** درختِ زنده — نه دادهٔ حالتِ متغیرِ ارگانیسم.

        دو جزء:
          · تغییرِ فایل‌های tracked ِ **سورس** (`_ops/state` و لاگ‌های زنده حذف می‌شوند)
          · فایل‌های untrackedِ **غیرِ مصنوعِ ساخت و غیرِ حالت** — تا فایلِ نوی پچ دیده شود
        """
        def keep(ln: str) -> bool:
            return (not any(p in ln for p in self.EPHEMERAL)
                    and not any(p in ln for p in self.VOLATILE))
        head = self._git("rev-parse", "HEAD", check=False).stdout.strip()
        tracked = [ln for ln in self._git("status", "--porcelain",
                   "--untracked-files=no", check=False).stdout.splitlines() if keep(ln)]
        untracked = [
            ln for ln in self._git("status", "--porcelain", "--untracked-files=all",
                                   check=False).stdout.splitlines()
            if ln.startswith("??") and keep(ln)
        ]
        blob = head + "\n" + "\n".join(sorted(tracked)) + "\n" + "\n".join(sorted(untracked))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # ---------------------------------------------------------------- suite
    def run_suite(self, cwd: Path) -> SuiteResult:
        t0 = time.time()
        env = None
        if self.env_root_key:
            env = {**os.environ, self.env_root_key: str(Path(cwd).resolve())}
        try:
            r = subprocess.run(self.suite_cmd, cwd=str(cwd), capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               timeout=self.timeout_s, env=env)
            out = (r.stdout or "") + (r.stderr or "")
            code = r.returncode
        except subprocess.TimeoutExpired:
            return SuiteResult(124, None, time.time() - t0, "TIMEOUT")
        except Exception as e:                              # noqa: BLE001
            return SuiteResult(125, None, time.time() - t0, f"{type(e).__name__}: {e}")
        return SuiteResult(code, self._parse_count(out), time.time() - t0,
                           out[-1500:], self._parse_failed(out))

    # خطِ خلاصهٔ run_all روی شکست: «❌ شکست: a.py, b.py  (capability revoked)».
    _FAIL_RE = re.compile(r"شکست:\s*(.+?)\s*\(capability", re.DOTALL)

    @classmethod
    def _parse_failed(cls, text: str) -> tuple[str, ...]:
        """مجموعهٔ فایل‌های تستِ قرمز. خالی = یا سبز یا قالبِ ناشناخته (که green جدا می‌سنجد)."""
        m = cls._FAIL_RE.search(text)
        if not m:
            return ()
        return tuple(sorted(
            x.strip() for x in m.group(1).replace("\n", " ").split(",") if x.strip()))

    @staticmethod
    def _parse_count(text: str) -> int | None:
        """شمارِ صریحِ تست. «نبودِ ❌» یعنی سبز نیست — عدد لازم است."""
        best = None
        for line in text.splitlines()[-40:]:
            m = _COUNT_RE.search(line)
            if m:
                try:
                    best = int(m.group(1))
                except ValueError:
                    pass
        return best

    # ---------------------------------------------------- replicate live tree
    # ۲۹ جولای، از اولین `day --live` (یافتهٔ F-08): `git worktree add HEAD` فقط
    # فایل‌های **کامیت‌شده** را می‌آورد. این مخزن ده‌ها فایلِ تستِ untracked روی دیسکِ
    # زنده دارد (سوئیتِ زنده اجراشان می‌کند ولی هرگز کامیت نشده‌اند). پس worktree کدِ
    # **متفاوتی** از زنده تست می‌کند و run_all با «can't open file» ده‌ها قرمز می‌دهد —
    # نه به‌خاطرِ پچ، بلکه چون تست‌ها غایب‌اند. اصلاح: source ِ زندهٔ کاری در worktree
    # کپی می‌شود تا وفادار باشد. **فقط .py زیرِ _ops** — state/راز هرگز (untracked با
    # --exclude-standard که gitignore را رعایت می‌کند + فیلترِ .py برای modified).
    def _snapshot_live_source(self) -> dict:
        """محتوای فایل‌های .py ِ untracked/modified ِ زندهٔ کاری را **یک‌بار** می‌گیرد
        (relpath → bytes). این snapshot به **هر دو** worktree (پایه و کاندید) داده
        می‌شود تا فقط با پچ فرق کنند. ⛔ VQ-DR-005: بدونِ این، پایه و کاندید با فاصلهٔ
        چند دقیقه از دیسکِ زنده می‌خواندند و اگر چیزی (ارگانیسم/جلسهٔ موازی) در آن فاصله
        عوض می‌شد، رگرسیونِ **کاذب** می‌ساخت. فقط .py زیرِ _ops؛ state/راز هرگز."""
        others = self._git("ls-files", "--others", "--exclude-standard",
                           check=False).stdout.splitlines()
        mod = self._git("diff", "--name-only", check=False).stdout.splitlines()
        snap = {}
        for rel in others + mod:
            rel = rel.strip().strip('"').replace("\\", "/")
            if not rel.startswith("_ops/") or not rel.endswith(".py"):
                continue
            if "/state/" in rel or "/_worktrees/" in rel or "__pycache__" in rel:
                continue
            src = self.repo / rel
            if src.is_file():
                snap[rel] = src.read_bytes()
        return snap

    def _replicate_live_source(self, wt: Path, commit: bool,
                               snapshot: dict | None = None) -> int:
        """snapshot را در worktree می‌نشاند (یا اگر داده نشد، تازه می‌گیرد — برای APIِ مستقل)."""
        snap = self._snapshot_live_source() if snapshot is None else snapshot
        copied = 0
        for rel, data in snap.items():
            dst = wt / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            copied += 1
        if commit and copied:
            # کامیتِ throwaway در HEAD ِ همین worktree (detached) — شاخهٔ زنده هرگز
            # لمس نمی‌شود، با حذفِ worktree زباله می‌شود. تا فایل‌های نو در HEAD باشند
            # و `_restore_pristine` تستِ کپی‌شده را «تغییرِ پچ» نپندارد و برنگرداند.
            # ⛔ ۲۹ جولای: `git add -A` ِ ۱۳۶فایلی زیرِ AV با «Permission denied» روی
            # .git/objects شکست می‌خورد؛ اگر بی‌صدا رد شویم، فایل‌ها uncommitted می‌مانند
            # و pristine آن‌ها را برمی‌گرداند ⇒ ۵۲ رگرسیونِ **کاذب**. پس retry با backoff،
            # و اگر باز هم کثیف ماند، استثنا (شکستِ صادق، نه رگرسیونِ جعلی).
            clean = False
            for attempt in range(6):
                self._git("add", "-A", cwd=wt, check=False)
                self._git("-c", "user.name=octopus-doctor",
                          "-c", "user.email=doctor@octopus",
                          "commit", "-qm", "replicate live working tree (F-08)",
                          cwd=wt, check=False)
                if not self._git("status", "--porcelain", cwd=wt,
                                 check=False).stdout.strip():
                    clean = True
                    break
                time.sleep(1.0 + attempt)   # قفلِ AV آزاد شود
            if not clean:
                raise RuntimeError(
                    "replicate-commit نافرجام (قفلِ AV روی .git/objects) — "
                    "worktree پس از ۶ تلاش هنوز کثیف است؛ ماموریت با شکستِ صادق رد شد")
        return copied

    # -------------------------------------------------------------- mission
    # مسیرهایی که **شاهد** را می‌سازند. پچ حق دارد پیشنهادشان بدهد، ولی حکم با
    # نسخهٔ دست‌نخوردهٔ آن‌هاست — وگرنه متهم، دادگاهِ خودش را می‌نویسد.
    PRISTINE = ("_ops/tests/", "tests/", "conftest.py")

    def _restore_pristine(self, wt: Path, snapshot: dict, patched: set) -> list[str]:
        """فایل‌های تستی که **پچ** لمس کرده را به نسخهٔ زندهٔ اصلی برمی‌گرداند.

        ⛔ چرا — از مقالهٔ Darwin Gödel Machine (۲۰۲۵): ایجنتِ خودبهبود وقتی با «سوئیت
        سبز» سنجیده شد، لاگِ اجرا را جعل کرد و نشانگرِ تشخیصِ توهم را حذف کرد. پس متهم
        نباید دادگاهش را بنویسد؛ قضاوت با سوئیتِ **دست‌نخورده**.

        نکته (VQ-DR-005): چون commit روی این ماشین با قفلِ AV شکست می‌خورد، به جای
        `git checkout HEAD` از خودِ **snapshotِ زنده** ترمیم می‌کنیم — دقیقاً فقط
        فایل‌هایی که پچ عوضشان کرده (`patched`)، نه همهٔ replicatها.
        """
        hit = []
        for f in patched:
            f = f.replace("\\", "/")
            if not any(p in f for p in self.PRISTINE):
                continue
            hit.append(f)
            if f in snapshot:
                (wt / f).write_bytes(snapshot[f])          # نسخهٔ زندهٔ تست
            else:
                r = self._git("show", f"HEAD:{f}", cwd=wt, check=False)
                if r.returncode == 0:
                    (wt / f).write_text(r.stdout, encoding="utf-8")
                else:
                    (wt / f).unlink(missing_ok=True)        # تستِ نوی خودِ پچ ⇒ حذف
        return hit

    def _build_diff(self, wt: Path, snapshot: dict, patched: set) -> str:
        """دیفِ متنیِ پچ — بدونِ git. «قبل» = نسخهٔ زندهٔ snapshot، یا HEAD، یا خالی (فایلِ نو)."""
        parts = []
        for rel in sorted(patched)[:20]:
            if rel in snapshot:
                before = snapshot[rel].decode("utf-8", "replace")
            else:
                r = self._git("show", f"HEAD:{rel}", cwd=wt, check=False)
                before = r.stdout if r.returncode == 0 else ""
            dst = wt / rel
            after = dst.read_text("utf-8", "replace") if dst.is_file() else ""
            d = difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                     fromfile=f"a/{rel}", tofile=f"b/{rel}")
            parts.append("".join(d))
        return "\n".join(p for p in parts if p.strip())

    def _patch_changes(self, wt: Path, snapshot: dict) -> set:
        """فایل‌هایی که **پچ** عوض کرده — بدونِ git commit. منطق: `git status` در worktree
        هم replicatها را نشان می‌دهد هم پچ را. replicat = فایلی در snapshot که محتوایش
        هنوز == snapshot است (پچ لمسش نکرده) ⇒ حذف. باقی = تغییرِ واقعیِ پچ (نو، یا فایلی
        که پچ ورایِ replicat عوضش کرده). برای هر دو حالتِ _ops و ریشه (تستِ mini) درست است."""
        changed = set()
        for ln in self._git("status", "--porcelain", "--untracked-files=all",
                            cwd=wt, check=False).stdout.splitlines():
            if not ln.strip():
                continue
            path = ln[3:].strip().strip('"').replace("\\", "/")
            if any(p in path for p in self.EPHEMERAL) or "/state/" in path:
                continue
            if path in snapshot:
                dst = wt / path
                if dst.is_file() and dst.read_bytes() != snapshot[path]:
                    changed.add(path)   # پچ فایلِ replicat را عوض کرده
                # وگرنه فقط خودِ replicat است، نه تغییرِ پچ
            else:
                changed.add(path)       # نو یا modified-غیرِreplicat = پچ
        return changed

    def run(self, mission_id: str, apply_patch: Callable[[Path], None],
            branch: str | None = None, measure_baseline: bool = True,
            judge_with_pristine_suite: bool = True,
            allow_live_baseline: bool = False) -> MissionResult:
        """یک ماموریتِ کامل در ایزوله. درختِ زنده هرگز لمس نمی‌شود."""
        t0 = time.time()
        res = MissionResult(mission_id=mission_id, ok=False, stage="init")
        fp_before = self.live_fingerprint()
        wt = self.worktrees / f"mission-{mission_id}"
        # snapshotِ **واحد** از کدِ زندهٔ کاری + commitِ **پین‌شده** — پایه و کاندید هر دو
        # همین را می‌گیرند تا فقط با پچ فرق کنند (VQ-DR-005: جلوگیری از رگرسیونِ کاذب وقتی
        # دیسک یا HEAD بینِ دو اجرا عوض می‌شود، مثلاً کامیتِ جلسهٔ موازی).
        snap = self._snapshot_live_source()
        pinned = branch or self._git("rev-parse", "HEAD", check=False).stdout.strip()

        try:
            if measure_baseline:
                res.stage = "baseline"
                # ⛔ ۲۹ جولای، از بازدیدِ درختِ زنده: `_ops/tests/run_all.py` بی‌صدا نیست —
                # روی سبز `capability_gate.mark_capability` می‌نویسد و روی **هر شکست**
                # `revoke_capability` می‌زند. اجرای پایه روی درختِ زنده یعنی یک تستِ
                # لرزان (مخزن خودش ~۴۰٪ لرزش را مستند کرده) **مسیرِ پولِ زنده را می‌بندد**.
                # پس پایه هم در worktreeِ ایزوله اندازه گرفته می‌شود، نه روی درختِ زنده.
                if allow_live_baseline:
                    res.baseline = self.run_suite(self.repo)
                else:
                    base_wt = self.worktrees / f"baseline-{mission_id}"
                    try:
                        self.worktrees.mkdir(parents=True, exist_ok=True)
                        self._drop_worktree(base_wt)
                        self._git("worktree", "add", "--detach", str(base_wt), pinned)
                        self._replicate_live_source(base_wt, commit=False, snapshot=snap)
                        res.baseline = self.run_suite(base_wt)
                    finally:
                        self._drop_worktree(base_wt)
                # ۲۹ جولای (VQ-DR-005): پایهٔ قرمز دیگر ماموریت را رد نمی‌کند. سوئیتِ
                # زنده ممکن است قرمزِ پیش‌موجود (کارِ در-جریانِ دیگری) یا قرمزِ محیطی
                # (تستی که رازِ gitignore‌شده می‌خواند و worktree ندارد) داشته باشد.
                # گیت روی **رگرسیون** است نه سبزِ مطلق (may_merge). تنها شکستِ پایه که
                # ماموریت را می‌کشد، خرابیِ harness است (تایم‌اوت/کرش)، نه قرمزِ تست.
                if res.baseline.exit_code in (124, 125):
                    res.reasons.append(
                        f"پایه اصلاً اجرا نشد (harness exit={res.baseline.exit_code}) — "
                        f"{res.baseline.tail[:120]}")
                    return self._finish(res, wt, fp_before, t0)
                if res.baseline.failed:
                    res.reasons.append(
                        f"پایه {len(res.baseline.failed)} قرمزِ پیش‌موجود دارد "
                        "(مستقل از پچ) — گیت روی رگرسیون است، نه سبزِ مطلق")

            res.stage = "worktree"
            self.worktrees.mkdir(parents=True, exist_ok=True)
            if wt.exists():
                self._drop_worktree(wt)
            self._git("worktree", "add", "--detach", str(wt), pinned)
            # commit=False: روی این ماشین `git add`/commit ِ ۱۳۶فایلی با قفلِ AV روی
            # .git/objects پایدار می‌شکند (Permission denied). پس هیچ‌چیز در .git نوشته
            # نمی‌شود؛ تشخیصِ پچ و ترمیمِ pristine با هش و snapshot انجام می‌شود.
            self._replicate_live_source(wt, commit=False, snapshot=snap)

            res.stage = "patch"
            # پنجرهٔ **تنگ**: اثرِ انگشتِ زنده دقیقاً قبل و بعدِ apply_patch. پچ فقط اینجا
            # می‌تواند درختِ زنده را لمس کند (باید فقط در wt بنویسد). فاصله ~۱ ثانیه، پس
            # نوشتنِ حالتِ ارگانیسم/کامیتِ موازی فرصتِ تغییر ندارند.
            fp_pre_patch = self.live_fingerprint()
            try:
                apply_patch(wt)
            except Exception as e:                          # noqa: BLE001
                res.reasons.append(f"پچ خطا داد: {type(e).__name__}: {e}")
                return self._finish(res, wt, fp_before, t0)
            res.live_tree_untouched = (self.live_fingerprint() == fp_pre_patch)
            if not res.live_tree_untouched:
                res.reasons.insert(0, "⛔ درختِ زنده تغییر کرد — این هرگز نباید رخ دهد")
                return self._finish(res, wt, fp_before, t0)

            # چه چیزی را پچ عوض کرد (نه replicat) — از git status + مقایسه با snapshot.
            patched = self._patch_changes(wt, snap)

            if judge_with_pristine_suite:
                res.stage = "pristine"
                res.suite_touched = self._restore_pristine(wt, snap, patched)
                if res.suite_touched:
                    res.reasons.append(
                        "⚠️ پچ به سوئیت دست زد؛ برای قضاوت به نسخهٔ زنده برگردانده شد: "
                        + ", ".join(res.suite_touched[:3]))
                    patched -= set(res.suite_touched)   # اثرشان از دیف/شمار حذف

            res.stage = "diff"
            res.files_changed = len(patched)
            if res.files_changed == 0:
                res.reasons.append("پچ هیچ تغییری نداد")
                return self._finish(res, wt, fp_before, t0)
            res.diff = self._build_diff(wt, snap, patched)[:8000]

            res.stage = "suite"
            res.candidate = self.run_suite(wt)
            if res.candidate.exit_code in (124, 125):
                res.reasons.append(
                    f"سوئیتِ کاندید اجرا نشد (harness exit={res.candidate.exit_code})")
                return self._finish(res, wt, fp_before, t0)

            # گیتِ اصلی: **رگرسیون**. قرمزِ نو = تستی که پچ شکاند (نه پیش‌موجود، نه محیطی).
            if res.regressed:
                if res.new_failures:
                    res.reasons.append(
                        f"پچ {len(res.new_failures)} تستِ نو شکاند: "
                        + ", ".join(res.new_failures[:4]))
                else:
                    res.reasons.append(
                        f"سوئیت قرمز شد (پایه سبز بود، کاندید "
                        f"exit={res.candidate.exit_code}) — merge ممنوع")
                return self._finish(res, wt, fp_before, t0)

            # افتِ پوشش فقط وقتی هر دو سبزند معنا دارد (وقتی قرمز، عددِ count نامعتبر است).
            if res.baseline.green and res.candidate.green:
                bc = res.baseline.count or 0
                cc = res.candidate.count or 0
                if cc < bc:
                    res.reasons.append(f"شمارِ تست افت کرد: {cc} < پایهٔ {bc}")
                    return self._finish(res, wt, fp_before, t0)

            res.ok = True
            res.stage = "awaiting-owner"
            return self._finish(res, wt, fp_before, t0)

        except Exception as e:                              # noqa: BLE001
            res.reasons.append(f"{res.stage}: {type(e).__name__}: {e}")
            return self._finish(res, wt, fp_before, t0)

    # ------------------------------------------------------------- teardown
    def _finish(self, res: MissionResult, wt: Path, fp_before: str,
                t0: float) -> MissionResult:
        try:
            self._drop_worktree(wt)
        except Exception:                                   # noqa: BLE001
            res.reasons.append("پاک‌سازیِ worktree ناموفق (بررسی دستی)")
        res.seconds = time.time() - t0
        # live_tree_untouched دیگر اینجا (پایانِ ماموریت) سنجیده نمی‌شود — آن پنجرهٔ
        # ۱۵دقیقه‌ای شاملِ دو اجرای سوئیت است که ارگانیسمِ زنده در طولش حالت می‌نویسد و
        # جلسهٔ موازی کامیت می‌کند ⇒ «تغییرِ کاذب». معنایِ درست «پچ درخت را لمس کرد؟» است
        # که فقط در پنجرهٔ تنگِ دورِ apply_patch سنجیده می‌شود (VQ-DR-005، در run()).
        return res

    # ---------------------------------------------------------------- merge
    def merge(self, mission_id: str, apply_patch: Callable[[Path], None],
              files: list[str] | None = None, fp_expected: str | None = None,
              message: str | None = None) -> dict:
        """تنها جایی که درختِ زنده لمس می‌شود — و فقط بعد از رأیِ صریحِ مالک.

        این تابع خودش رأی نمی‌گیرد و رأی را نمی‌سنجد؛ صدا زدنش **یعنی** رأی گرفته شده.
        کارِ آن فقط این است که اگر همه‌چیز طبقِ نقشه پیش نرفت، **دقیقاً** به حالتِ قبل برگردد.

        ترتیبِ عمداً محافظه‌کارانه:
          ۱ اگر درخت از زمانِ ماموریت تکان خورده ⇒ توقف (کسی زیرِ پایمان نوشته)
          ۲ اسنپ‌شاتِ بایت‌به‌بایتِ **همان فایل‌هایی** که قرار است عوض شوند
          ۳ اعمال ⇒ اجرای سوئیت روی درختِ زنده
          ۴ قرمز شد ⇒ بازگردانیِ اسنپ‌شات و استثنا. `git checkout` **نمی‌زنیم** —
            چون کارِ نیمه‌کارهٔ دیگری را هم پاک می‌کرد.
          ۵ سبز شد ⇒ کامیت
        """
        if fp_expected is not None and self.live_fingerprint() != fp_expected:
            raise RuntimeError("درختِ زنده از زمانِ ماموریت تغییر کرده — merge لغو شد")

        if not files:
            raise RuntimeError("merge بدونِ فهرستِ صریحِ فایل‌ها انجام نمی‌شود")

        # درختِ کثیف = بازگردانیِ مطمئن ناممکن. کارِ نیمه‌کارهٔ کسِ دیگری آنجاست و
        # ما حق نداریم رویش بنویسیم یا پاکش کنیم.
        dirty = self._git("status", "--porcelain", "--untracked-files=no",
                          check=False).stdout.strip()
        if dirty:
            raise RuntimeError("درختِ کاری تمیز نیست — merge روی تغییرِ ثبت‌نشدهٔ دیگری ممنوع")

        snap: dict[Path, bytes | None] = {}
        for rel in files:
            p = (self.repo / rel.replace("\\", "/")).resolve()
            if not str(p).startswith(str(self.repo)):
                raise RuntimeError(f"فرار از ریشه در فهرستِ merge: {rel}")
            snap[p] = p.read_bytes() if p.exists() else None

        def restore() -> None:
            for p, old in snap.items():
                try:
                    if old is None:
                        p.unlink(missing_ok=True)
                    else:
                        p.write_bytes(old)
                except OSError:
                    pass

        apply_patch(self.repo)

        # ⛔ گاردِ «فقط همان فایل‌ها». اگر پچ چیزی بیرونِ فهرست را عوض کرده باشد،
        # حتی اگر سوئیت سبز باشد، merge نمی‌کنیم — چون فهرست دیگر توصیفِ درستی
        # از آن چیزی نیست که مالک به آن رأی داده.
        declared = {f.replace("\\", "/") for f in files}
        changed = {ln[3:].strip().strip('"').replace("\\", "/")
                   for ln in self._git("status", "--porcelain", "--untracked-files=no",
                                       check=False).stdout.splitlines() if ln.strip()}
        stray = changed - declared
        if stray:
            restore()
            # چون درخت در شروع تمیز بود، برگرداندنِ فایلِ اعلام‌نشده امن است:
            # هرچه آنجا هست را همین پچ ساخته.
            self._git("checkout", "--", *sorted(stray), check=False)
            raise RuntimeError(f"پچ به فایلِ اعلام‌نشده دست زد: {sorted(stray)[:4]} — merge لغو")

        suite = self.run_suite(self.repo)
        if not suite.green:
            restore()
            raise RuntimeError(
                f"سوئیت روی درختِ زنده قرمز شد (exit={suite.exit_code}) — "
                f"{len(snap)} فایل بایت‌به‌بایت برگردانده شد")

        self._git("add", *files)
        msg = message or f"doctor: ماموریت {mission_id} — سوئیت {suite.count or '?'} سبز"
        self._git("commit", "-m", msg)
        head = self._git("rev-parse", "--short", "HEAD", check=False).stdout.strip()
        return {"ok": True, "commit": head, "files": files,
                "suite_count": suite.count, "seconds": round(suite.seconds, 1)}

    def _drop_worktree(self, wt: Path) -> None:
        if wt.exists():
            self._git("worktree", "remove", "--force", str(wt), check=False)
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        self._git("worktree", "prune", check=False)
