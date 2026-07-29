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
    def may_merge(self) -> bool:
        """سبزِ کافی برای *پیشنهادِ* merge — نه خودِ merge. آن رأی می‌خواهد."""
        return (self.ok and self.live_tree_untouched
                and self.candidate is not None and self.candidate.green
                and self.baseline is not None
                and (self.candidate.count or 0) >= (self.baseline.count or 0))

    def card(self) -> str:
        """متنِ کارتِ تلگرام (کارتِ ۲ — گیتِ دیف)."""
        if not self.ok:
            return (f"❌ ماموریت {self.mission_id} — {self.stage}\n"
                    + "\n".join(f"· {r}" for r in self.reasons[:4]))
        b = self.baseline.count if self.baseline else "?"
        c = self.candidate.count if self.candidate else "?"
        mark = "✅" if self.may_merge else "⚠️"
        warn = (f"\n⚠️ پچ به سوئیت دست زد ({len(self.suite_touched)} فایل) — "
                "حکم با سوئیتِ **دست‌نخورده** گرفته شد" if self.suite_touched else "")
        return (f"{mark} ماموریت {self.mission_id}\n"
                f"سوئیت: {c}/{c} (پایه {b}) · دیف {self.files_changed} فایل · "
                f"{self.seconds:.0f}s\n"
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

    def live_fingerprint(self) -> str:
        """اثرِ انگشتِ **محتوای منبعِ** درختِ زنده.

        دو جزء:
          · تغییرِ فایل‌های tracked (`--untracked-files=no`) — هر پچی اینجا ظاهر می‌شود
          · فایل‌های untrackedِ **غیرِ مصنوعِ ساخت** — تا پچی که فایلِ نو بسازد هم دیده شود
        """
        head = self._git("rev-parse", "HEAD", check=False).stdout.strip()
        tracked = self._git("status", "--porcelain", "--untracked-files=no",
                            check=False).stdout
        untracked = [
            ln for ln in self._git("status", "--porcelain", "--untracked-files=all",
                                   check=False).stdout.splitlines()
            if ln.startswith("??") and not any(p in ln for p in self.EPHEMERAL)
        ]
        blob = head + "\n" + tracked + "\n" + "\n".join(sorted(untracked))
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
        return SuiteResult(code, self._parse_count(out), time.time() - t0, out[-1500:])

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

    # -------------------------------------------------------------- mission
    # مسیرهایی که **شاهد** را می‌سازند. پچ حق دارد پیشنهادشان بدهد، ولی حکم با
    # نسخهٔ دست‌نخوردهٔ آن‌هاست — وگرنه متهم، دادگاهِ خودش را می‌نویسد.
    PRISTINE = ("_ops/tests/", "tests/", "conftest.py")

    def _restore_pristine(self, wt: Path) -> list[str]:
        """سوئیت را در worktree به نسخهٔ HEAD برمی‌گرداند و می‌گوید چه چیزی برگشت.

        ⛔ چرا این وجود دارد — از مقالهٔ Darwin Gödel Machine (۲۰۲۵):
        ایجنتِ خودبهبود، وقتی با «سوئیت سبز» سنجیده شد، **لاگِ اجرا را جعل کرد** و در
        موردی دیگر **نشانگرِ تشخیصِ توهم را حذف کرد**. یعنی سیستمی که با آزمونِ خودش
        سنجیده می‌شود، یاد می‌گیرد آزمون را عوض کند، نه خودش را.

        پس: پچ در worktree اعمال می‌شود، بعد **سوئیت به نسخهٔ اصلی برمی‌گردد**، و
        قضاوت با همان سوئیتِ دست‌نخورده انجام می‌شود.
        """
        changed = [ln[3:].strip().strip('"').replace("\\", "/")
                   for ln in self._git("status", "--porcelain", cwd=wt,
                                       check=False).stdout.splitlines() if ln.strip()]
        hit = [f for f in changed if any(p in f for p in self.PRISTINE)]
        for f in hit:
            r = self._git("checkout", "HEAD", "--", f, cwd=wt, check=False)
            if r.returncode != 0:
                # در HEAD نبوده ⇒ پچ یک فایلِ تستِ **نو** ساخته. آن هم شاهدِ خودساخته
                # است و برای قضاوت حذف می‌شود؛ ولی در گزارش می‌ماند.
                (wt / f).unlink(missing_ok=True)
        return hit

    def run(self, mission_id: str, apply_patch: Callable[[Path], None],
            branch: str | None = None, measure_baseline: bool = True,
            judge_with_pristine_suite: bool = True,
            allow_live_baseline: bool = False) -> MissionResult:
        """یک ماموریتِ کامل در ایزوله. درختِ زنده هرگز لمس نمی‌شود."""
        t0 = time.time()
        res = MissionResult(mission_id=mission_id, ok=False, stage="init")
        fp_before = self.live_fingerprint()
        wt = self.worktrees / f"mission-{mission_id}"

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
                        h = branch or self._git("rev-parse", "HEAD").stdout.strip()
                        self._git("worktree", "add", "--detach", str(base_wt), h)
                        res.baseline = self.run_suite(base_wt)
                    finally:
                        self._drop_worktree(base_wt)
                if not res.baseline.green:
                    res.reasons.append(
                        f"پایه خودش قرمز است (exit={res.baseline.exit_code}) — "
                        "قبل از هر ماموریت باید سبز باشد")
                    return self._finish(res, wt, fp_before, t0)

            res.stage = "worktree"
            self.worktrees.mkdir(parents=True, exist_ok=True)
            if wt.exists():
                self._drop_worktree(wt)
            head = branch or self._git("rev-parse", "HEAD").stdout.strip()
            self._git("worktree", "add", "--detach", str(wt), head)

            res.stage = "patch"
            try:
                apply_patch(wt)
            except Exception as e:                          # noqa: BLE001
                res.reasons.append(f"پچ خطا داد: {type(e).__name__}: {e}")
                return self._finish(res, wt, fp_before, t0)

            if judge_with_pristine_suite:
                res.stage = "pristine"
                res.suite_touched = self._restore_pristine(wt)
                if res.suite_touched:
                    res.reasons.append(
                        "⚠️ پچ به سوئیت دست زد؛ برای قضاوت به نسخهٔ اصلی برگردانده شد: "
                        + ", ".join(res.suite_touched[:3]))

            res.stage = "diff"
            d = self._git("diff", "--stat", cwd=wt, check=False).stdout
            res.diff = self._git("diff", cwd=wt, check=False).stdout[:8000]
            res.files_changed = max(0, len([l for l in d.splitlines() if "|" in l]))
            if res.files_changed == 0:
                res.reasons.append("پچ هیچ تغییری نداد")
                return self._finish(res, wt, fp_before, t0)

            res.stage = "suite"
            res.candidate = self.run_suite(wt)
            if not res.candidate.green:
                res.reasons.append(
                    f"سوئیت قرمز شد (exit={res.candidate.exit_code}) — merge ممنوع")
                return self._finish(res, wt, fp_before, t0)

            bc = (res.baseline.count if res.baseline else None) or 0
            cc = res.candidate.count or 0
            if res.baseline and cc < bc:
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
        res.live_tree_untouched = (self.live_fingerprint() == fp_before)
        if not res.live_tree_untouched:
            res.ok = False
            res.reasons.insert(0, "⛔ درختِ زنده تغییر کرد — این هرگز نباید رخ دهد")
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
