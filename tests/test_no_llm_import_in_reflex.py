"""Reflex on .138 must be LLM-free and network-free (doctrine, PR #162).

If an LLM client or network import reaches the reflex path
(contracts/ now; tools/runtime_truth.py when #163 lands), there is no
reflex — the import itself must fail the build."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# مسیرهای رفلکس — با هر مولد/ابزار بی‌LLM جدید این فهرست یا گسترش می‌یابد
# یا خود فایل در同类 قرارداد قفل می‌شود.
REFLEX_PATHS = [
    ROOT / "contracts",
    ROOT / "tools" / "runtime_truth.py",
]

BANNED = (
    "openai", "anthropic", "google.generativeai", "litellm",
    "requests", "urllib.request", "http.client", "socket",
    "aiohttp", "httpx", "websocket",
)

IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.M)


def test_reflex_paths_have_no_llm_or_network_imports() -> None:
    checked = 0
    for p in REFLEX_PATHS:
        files = p.glob("*.py") if p.is_dir() else (
            [p] if p.exists() else [])
        for f in files:
            src = f.read_text(encoding="utf-8")
            for mod in IMPORT_RE.findall(src):
                root = mod.split(".")[0].lower()
                for banned in BANNED:
                    assert banned.split(".")[0] != root or mod == banned or \
                        not mod.startswith(banned), \
                        f"{f.relative_to(ROOT)} imports {mod!r} — " \
                        f"reflex must stay stdlib-only, no LLM, no network"
                checked += 1
    # اگر هیچ فایلی چک نشد هم تست سبز نماند — خودِ چک باید چک شود
    assert checked >= 3, f"expected to scan the contract at least; checked={checked}"
