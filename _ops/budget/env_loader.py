#!/usr/bin/env python3
"""env_loader.py — بارگذاریِ .env از root (هرگز log/commit، هرگز secret را چاپ نکن).

قراردادِ سخت:
  - فقط فایلِ `.env` در rootِ vault (F:\\backup\\.env) را می‌خواند.
  - هرگز مقدارِ کلید را log/echo/print نمی‌کند — فقط نام را.
  - .env در .gitignore است (خطِ *.env) — هرگز commit نمی‌شود.
  - idempotent: اگر کلید از قبل در os.environ بود، overwrite نمی‌کند.
  - fail-soft: نبودِ .env → no-op (تست‌ها با stub کار می‌کنند).

نام‌های کلید (طبق budgets.yaml):
  GLM_API_KEY, GLM_BASE_URL      — provider: glm (api.z.ai / Z.ai)
  FUGU_API_KEY                    — provider: sakana (fugu)
  DEEPSEEK_API_KEY                — provider: deepseek (موجود، econ)
"""
from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/budget
_VAULT_ROOT = _HERE.parent.parent                 # F:\backup
_ENV_PATH = _VAULT_ROOT / ".env"

# کلیدهایی که ممکن است در .env باشند (برای گزارشِ امنِ "set/not-set")
_KNOWN_KEYS = ("GLM_API_KEY", "GLM_BASE_URL", "FUGU_API_KEY",
               "DEEPSEEK_API_KEY", "ZAI_API_KEY", "ANTHROPIC_API_KEY")

_LOADED = False   # فقط یک‌بار load کن


def load_env(path=None) -> dict:
    """فایلِ .env را بخوان و در os.environ بریز (idempotent، overwrite نمی‌کند).
    خروجی: {key: "set" | "skip"} برای کلیدهای شناخته (هرگز مقدار را برنمی‌گرداند).
    fail-soft: نبودِ فایل → {} و no-op."""
    global _LOADED
    p = Path(path) if path else _ENV_PATH
    report = {}
    if not p.exists():
        return report
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if not key:
                continue
            # idempotent: اگر از قبل در os.environ بود، overwrite نکن
            if key not in os.environ:
                os.environ[key] = val
    except OSError:
        return report
    _LOADED = True
    # گزارشِ امن (فقط set/skip، هرگز مقدار)
    for k in _KNOWN_KEYS:
        if k in os.environ:
            report[k] = "set"
    return report


def env_status() -> dict:
    """گزارشِ امنِ وضعیتِ کلیدها (فقط set/not-set، هرگز مقدار)."""
    load_env()   # مطمئن شو .env خوانده شد
    return {k: ("set" if k in os.environ else "not-set") for k in _KNOWN_KEYS}


if __name__ == "__main__":
    st = env_status()
    # فقط نام و set/not-set چاپ کن — هرگز مقدار
    for k, v in st.items():
        print(f"{k}: {v}")
