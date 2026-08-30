# -*- coding: utf-8 -*-
# TARGET (owner wires in worktree): F:\backup\_ops\output_guard.py
"""
output_guard — «هیچ خروجیِ ایجنت نباید اجرایی باشد» — stdlib، خالص، inert تا import.

چرا (Why): مهم‌ترین درسِ تحقیقِ فرارِ سندباکس (Pillar/AGT 2026): ایجنت لازم نیست kernel را
بشکند؛ کافی است فایلی بسازد که یک برنامهٔ **مورد اعتمادِ بیرونِ سندباکس** (langar، ویندوزِ تو،
VS Code، git hook) بعداً اجرایش کند. پس هر artifactِ پیشنهادیِ ایجنت باید **دادهٔ بی‌جان**
باشد (‎.txt/.json/.md/.diff‎)، نه چیزی که host به‌طورِ خودکار اجرا می‌کند.

این چیست و چه چیزی نیست:
  * یک **بازرسِ خالص**: (مسیرِ مقصد + محتوا) → allow/deny + دلیل. هیچ فایلی نمی‌نویسد/اجرا
    نمی‌کند. قبل از هر «نوشتنِ artifact» یا apply صدا زده می‌شود.
  * NOT جایگزینِ code_autonomy worktree یا capability_gate؛ یک لایهٔ دفاعیِ مکمل است
    (نگاه به «چه چیزی نوشته می‌شود»، نه «چه کسی اجازه دارد»).

سیاست (fail-closed): اگر مقصد بیرونِ دایرکتوریِ artifactِ مجاز باشد، یا پسوند/نامِ فایل
auto-run باشد، یا محتوا الگوی اجرای shell داشته باشد → DENY و ارجاع به مالک.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

# پسوندهایی که host می‌تواند مستقیم اجرا کند
EXECUTABLE_EXT = frozenset({
    ".bat", ".cmd", ".ps1", ".psm1", ".psd1", ".sh", ".bash", ".zsh", ".fish",
    ".vbs", ".vbe", ".wsf", ".hta", ".reg", ".scr", ".com", ".exe", ".msi",
    ".lnk", ".pif", ".jar", ".apk", ".app", ".deb", ".appimage", ".dll", ".so",
})

# نام‌فایل‌هایی که ابزارهای مورد اعتماد auto-run می‌کنند (بی‌توجه به پسوند)
AUTORUN_NAMES = frozenset({
    "tasks.json", "launch.json", "settings.json", ".code-workspace",
    "package.json", "autorun.inf", "makefile", "dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "sitecustomize.py", "usercustomize.py", "conftest.py",
    "crontab", ".bashrc", ".bash_profile", ".profile", ".zshrc", "profile.ps1",
})

# قطعهٔ مسیرهایی که «اجرا هنگامِ رخداد» را نشان می‌دهند
AUTORUN_PATH_HINTS = (
    ".git/hooks/", ".vscode/", "startup/", "systemd/", "launchagents/",
    "launchdaemons/", "cron.d/", "init.d/", "etc/profile.d/",
)

# مسیرهای ممنوعِ مطلق (هم‌راستا با repair_policy.FORBIDDEN + TCB)
FORBIDDEN_PREFIXES = (
    "_ops/", "langar/", "secrets/", "config/keys/", ".env", ".git/",
    "07 - knowledge/genome-system/", "budget/budgets.yaml",
)

# محتواهایی که اجرای دستور را ممکن می‌کنند
_SHELL_PATTERNS = re.compile(
    r"(os\.system|subprocess\.(?:run|popen|call|check_output)|__import__\(\s*['\"]os"
    r"|\beval\s*\(|\bexec\s*\(|invoke-expression|iex\b|powershell\s+-e(?:nc)?"
    r"|curl\s+[^\n|]*\|\s*(?:bash|sh)|wget\s+[^\n|]*\|\s*(?:bash|sh)"
    r"|child_process|Runtime\.getRuntime\(\)\.exec|System\.Diagnostics\.Process)",
    re.IGNORECASE,
)

# پسوندهای «دادهٔ بی‌جانِ» مجاز به‌طور پیش‌فرض
INERT_EXT = frozenset({".txt", ".md", ".json", ".jsonl", ".diff", ".patch",
                       ".csv", ".log", ".yaml.report", ".ndjson"})

DEFAULT_ARTIFACT_PREFIXES = (
    "state/artifacts/", "artifacts/", "state/proposals/", "state/runs/",
    "_ops/state/artifacts/", "worktree-out/",
)


@dataclass
class OutputVerdict:
    allowed: bool
    severity: str                      # ok | suspicious | blocked
    reasons: List[str] = field(default_factory=list)
    normalized_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _norm(path: str) -> str:
    return str(PurePosixPath((path or "").replace("\\", "/"))).lstrip("/")


def _starts_any(path_lower: str, prefixes) -> bool:
    return any(path_lower.startswith(pre) for pre in prefixes)


def check_output(path: str, content: str = "",
                 allow_prefixes: Optional[Tuple[str, ...]] = None) -> OutputVerdict:
    """آیا نوشتنِ این artifact امن است؟ fail-closed.

    path: مسیرِ مقصدِ پیشنهادی. content: محتوایی که قرار است نوشته شود.
    allow_prefixes: دایرکتوری‌های مجازِ artifact (پیش‌فرض: DEFAULT_ARTIFACT_PREFIXES).
    """
    allow = tuple(a.lower() for a in (allow_prefixes or DEFAULT_ARTIFACT_PREFIXES))
    norm = _norm(path)
    low = norm.lower()
    reasons: List[str] = []

    if not norm:
        return OutputVerdict(False, "blocked", ["empty-path → fail-closed"], norm)

    # 1) مسیرِ ممنوعِ مطلق
    if _starts_any(low, FORBIDDEN_PREFIXES):
        return OutputVerdict(False, "blocked", [f"forbidden target: {norm}"], norm)

    # 2) بیرونِ دایرکتوریِ artifactِ مجاز → fail-closed
    if not _starts_any(low, allow):
        reasons.append(f"outside allowed artifact dirs {allow}")
        return OutputVerdict(False, "blocked", reasons, norm)

    # 3) پسوند/نامِ auto-run
    name = low.rsplit("/", 1)[-1]
    ext = ("." + name.rsplit(".", 1)[-1]) if "." in name else ""
    if ext in EXECUTABLE_EXT:
        return OutputVerdict(False, "blocked", [f"executable extension: {ext}"], norm)
    if name in AUTORUN_NAMES:
        return OutputVerdict(False, "blocked", [f"auto-run filename: {name}"], norm)
    if any(h in low for h in AUTORUN_PATH_HINTS):
        return OutputVerdict(False, "blocked", ["auto-run path (hook/startup/cron/systemd)"], norm)

    # 4) محتوای اجرایی حتی در فایلِ به‌ظاهر بی‌جان
    if content and _SHELL_PATTERNS.search(content):
        return OutputVerdict(False, "blocked", ["content contains shell/exec pattern"], norm)

    # 5) هشدارِ نرم: پسوندِ ناشناخته (نه اجرایی، نه صریحاً inert)
    if ext and ext not in INERT_EXT:
        reasons.append(f"non-inert extension {ext}: treat as data only, host must never execute")
        return OutputVerdict(True, "suspicious", reasons, norm)

    reasons.append("inert data artifact in allowed dir")
    return OutputVerdict(True, "ok", reasons, norm)


def is_inert(path: str, content: str = "") -> bool:
    """کمکیِ بولی برای گاردهای فراخوان."""
    return check_output(path, content).allowed


if __name__ == "__main__":
    # داده‌های امن
    assert check_output("state/artifacts/report.md", "hello").allowed
    assert check_output("artifacts/proposal.json", '{"ok":true}').severity == "ok"
    # اجراییِ آشکار
    assert not check_output("state/artifacts/run.bat", "echo hi").allowed
    assert not check_output("artifacts/deploy.ps1", "").allowed
    # auto-run config
    assert not check_output(".vscode/tasks.json", "{}").allowed
    assert not check_output("state/artifacts/.git/hooks/post-commit", "x").allowed
    # مقصدِ ممنوع
    assert not check_output("_ops/organism.py", "print(1)").allowed
    assert not check_output("secrets/keys.txt", "").allowed
    # بیرونِ artifact dir
    assert not check_output("random/place/note.txt", "").allowed
    # محتوای اجرایی در فایلِ بی‌جان
    assert not check_output("state/artifacts/note.txt", "import os; os.system('rm -rf /')").allowed
    print("output_guard smoke ok")
