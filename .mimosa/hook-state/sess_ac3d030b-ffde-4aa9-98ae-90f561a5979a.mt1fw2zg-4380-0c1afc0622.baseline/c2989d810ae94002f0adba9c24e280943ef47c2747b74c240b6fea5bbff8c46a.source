#!/usr/bin/env python3
"""config.py — تنظیماتِ runtimeِ Project-F OS.

همه‌ی پیکربندی از env می‌آید (طبقِ قراردادِ پروژه: هیچ dotenv، هیچ config-file با
secret). هر مقدار یک fallbackِ امنِ $0/آفلاین دارد تا pf_os در shadow-mode هم کار کند.

قراردادِ flag (هم‌الگوی _ops/wiring.py::flag): env == "1" یعنی روشن؛ هر چیزِ دیگر
(حتی "true"/"yes"/"on") یعنی خاموش. یک‌شکل بودن با ارگانیسم مهم است.

$0 آفلاین، stdlib-only، صفر dependency بیرونی.
"""
from __future__ import annotations

import os


def flag(name: str) -> bool:
    """env-flag با پیش‌فرضِ خاموش (هم‌الگوی _ops/wiring.py:30).

    فقط "1" یعنی True؛ هر چیزِ دیگر False. این قراردادِ سراسریِ اختاپوس است
    (flag-gated wiring) و pf_os هم همین‌طور تا toggle یک‌دست باشد.
    """
    return os.environ.get(name, "0") == "1"


# ─── مسیرها (resolved once at import) ─────────────────────────────────────────
PF_ROOT = os.environ.get("PF_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""ریشه‌ی Project-F (پوشه‌ی 03 - Projects/اونلی فنز)."""


def _resolve_vault() -> str:
    """ریشه‌ی vault اختاپوس را به‌صورتِ ویندوز-امن resolve کن.

    2026-07-25 fix: قبلاً یک‌خطی بود و در Git-Bash/دورزدنِ drive، مسیرِ drive-relative
    مثل 'F:backup' (بدونِ بک‌اسلش) → dirname دو بار → 'F:' → makedirs یک دایرکتوریِ
    literal به‌نامِ 'F:backup' در کنارِ پروژه می‌ساخت (باگِ path-escaping؛ دو دایرکتوریِ
    خالیِ زائد ساخته شده بودند). این نگاشت drive-relative را تشخیص می‌دهد و آن را
    به fallbackِ واقعی (دو سطح بالاتر از PF_ROOT) رد می‌کند. fail-safe."""
    env_vault = os.environ.get("OCTOPUS_VAULT", "").strip()
    if env_vault:
        # drive-relative مثلِ 'F:backup' یا 'C:foo' = ناقص (وجودِ colon بدونِ بک‌اسلش
        # بعدش). در ویندوز این یعنی مسیرِ نسبی روی آن drive، نه absolute. رد کن.
        if len(env_vault) >= 2 and env_vault[1] == ":" and \
                (len(env_vault) == 2 or env_vault[2] not in ("\\", "/")):
            pass   # drive-relative → به fallback بیفت
        elif os.path.isdir(env_vault):
            return env_vault
    return os.path.dirname(os.path.dirname(PF_ROOT))


VAULT = _resolve_vault()
"""ریشه‌ی vault اختاپوس (F:\\backup) — drive-relative‌ها رد می‌شوند (fail-safe)."""

OPS_STATE = os.path.join(VAULT, "_ops", "state")
"""مسیرِ state ارگانیسم مرکزی (برای saba-bridge.jsonl و غیره)."""

PF_STATE = os.path.join(PF_ROOT, "pf_os_state")
"""مسیرِ state محلیِ pf_os (در پروژه؛ هرگز در _ops)."""

# ─── cortex central LLM router ───────────────────────────────────────────────
CORTEX_URL = os.environ.get("OCTOPUS_CORTEX_URL") or "http://127.0.0.1:8772"
"""آدرسِ cortex مرکزی. pf_os برای هر LLM call به اینجا POST /ask می‌زند."""

CORTEX_TIMEOUT = float(os.environ.get("PF_CORTEX_TIMEOUT", "8.0"))
"""مهلتِ HTTP برای cortex (ثانیه). بعد از آن fallback به heuristic."""

# ─── HTTP API (فاز ۴) ─────────────────────────────────────────────────────────
API_PORT = int(os.environ.get("PF_OS_PORT", "8780"))
"""پورتِ REST API. single-instance lock روی همین پورت (الگوی organism.py)."""

API_TOKEN = os.environ.get("PF_OS_API_TOKEN", "")
"""توکنِ HTTP Basic برای API. خالی = فقط localhost بدون auth (shadow-mode)."""

# ─── حلقه‌ی tick (فاز ۳) ──────────────────────────────────────────────────────
TICK_SECONDS = float(os.environ.get("PF_OS_TICK_SECONDS", "300"))
"""دوره‌ی حلقه‌ی tick (ثانیه). پیش‌فرض ۵ دقیقه (هم‌الگوی organism TICK_SECONDS=300)."""

# ─── flags (همگی default-OFF — flag-gated wiring) ────────────────────────────
WIRE_LOOP = "OCTOPUS_WIRE_PROJECTF_LOOP"
"""حلقه‌ی tick مستقلِ pf_os را روشن می‌کند."""

WIRE_API = "OCTOPUS_WIRE_PROJECTF_API"
"""REST API را روشن می‌کند."""

WIRE_BRIDGE = "OCTOPUS_WIRE_SABA_BRIDGE"
"""نوشتنِ events به saba-bridge.jsonl را روشن می‌کند."""

WIRE_CORTEX = "OCTOPUS_WIRE_PROJECTF_CORTEX"
"""فراخوانیِ واقعیِ cortex را روشن می‌کند. خاموش = همیشه heuristic fallback."""

WIRE_EVAL = "OCTOPUS_WIRE_PROJECTF_EVAL"
"""حلقهٔ eval→learn (bandit + ضدگودهارت، shadow/propose-only) را در tick روشن می‌کند."""

# ─── organ (در budgets.yaml — PROJECT_F از قبل ثبت شده) ─────────────────────
ORGAN = "PROJECT_F"
"""نامِ ارگانِ بودجه در budgets.yaml. PROJECT_F از قبل با floor:3 ثبت شده.
(توجه: بلوکِ allocation مالِ لِینِ قلب است — این فقط نام است، نه ویرایش.)"""

# ─── helpers ─────────────────────────────────────────────────────────────────
def ensure_pf_state() -> str:
    """ساختِ PF_STATE اگر نیست. idempotent."""
    if not os.path.isdir(PF_STATE):
        try:
            os.makedirs(PF_STATE, exist_ok=True)
        except OSError:
            pass
    return PF_STATE
