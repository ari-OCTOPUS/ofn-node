"""
knowledge/ledger.py — Loads the immutable 4D/ reference into agent context.

THE GOLDEN RULE: This module READS from 4D/ but NEVER writes to it.
The 4D/ directory is the project's source of truth.

This module extracts the key knowledge into a structured form that agents
can consume: system prompts, anchor values, project rules, and the
theoretical framework (five principles).
"""
from __future__ import annotations

from pathlib import Path
from config.settings import REFERENCE_DIR, REF_FILES


# ════════════════════════════════════════════════════════════════════════
#  File loading (read-only)
# ════════════════════════════════════════════════════════════════════════

def load_file(key: str, max_chars: int = 50000) -> str:
    """Load a reference file by key. Returns empty string if missing."""
    path = REF_FILES.get(key)
    if path is None or not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except Exception as e:
        return f"[error reading {path.name}: {e}]"


def load_python_source() -> str:
    """Load the 4.py source code (the verification reference)."""
    return load_file("verify_script")


def load_handoff() -> str:
    """Load the multi-agent handoff document (v2 with addendum)."""
    return load_file("handoff")


def load_theory() -> str:
    """Load the theory/improvement document (five principles + Track-G)."""
    return load_file("theory")


# ════════════════════════════════════════════════════════════════════════
#  Structured knowledge for agent prompts
# ════════════════════════════════════════════════════════════════════════

THE_FIVE_PRINCIPLES = """
پنج اصل نظریه (از فایل برداشت):
۱. شناسایی — بدون مدل صفر و فرضیه‌های قابل‌تفکیک، ادعا شناسایی نمی‌شود.
۲. کانال — DPI برای کانال ثابت معتبر است؛ هوش کانال ثابت را نمی‌شکند،
   اما می‌تواند کانال تازه بسازد.
۳. سطح — سطح واقعی یعنی الگوی robust، فشرده و پیش‌بینی‌گر؛ نه صرفاً توهم ناظر.
۴. خودارجاع — Lawvere blind-spot صوری می‌دهد؛ تبدیلش به حس تعالی فرضیه است نه قضیه.
۵. روش — AI فقط قوانین شرطی S⇒L می‌سازد؛ انتقال به متافیزیک نیازمند وارسی مقدمات است.

جمله محوری: مسئله‌ی سطح بالاتر، مسئله‌ی بُعد بیشتر نیست؛
مسئله‌ی کانال، شناسایی، مداخله، الگو و خودارجاعی است.
"""

THE_SIX_RULES = """
قواعد شش‌گانه‌ی پروژه (از پیوست C):
۱) هیچ یافته‌ای بدون null model؛ Δ_MDL>Δ و β_det>0 لازم است نه فقط β_info>0.
۲) هر عدد کمّی مشتق‌شده و مستقلاً بازتولیدپذیر؛ عدد بی‌اشتقاق رد.
۳) پیش از هر ادعای novelty، جست‌وجوی وب اجباری؛ اول نقشه‌ی ادبیات ledger چک شود.
۴) instrument-validation ≠ hypothesis-claim.
۵) مسیرهای رقیبِ ردشده صریح ثبت شوند.
۶) فریم فلسفی فقط narrative است؛ ادعای فنی فقط روی SOG/MDL/excess-loss.
"""

KEY_DEFINITIONS = """
تعاریف کلیدی (code-generated، نقطه‌ی کار λ=0.5):

مدل:
  s(t+1) = ρ·s(t) + m(t) + ζ(t)     [بُعد پنهان، با حافظه ρ]
  Y(t)   = b(t) + λ·s(t) + ε(t)     [سایه‌ی مشاهده‌شده]

سه کمیت:
  E_shadow = ½·log(σ_z²/S_b) = 0.012553 nat/گام
    → چقدر «وجود» بُعد پنهان از بیرون قابل‌تشخیص است

  Δ_self = ½·log(S_b/S) = 0.122520 nat/گام
    → ارزشِ دسترسیِ اول‌شخص به درونِ خود

  I_pred = ½·Σ log(S_L/S_b) = 0.0144179 nat
    → کلِ پیش‌بینی‌پذیری گذشته از آینده (excess entropy)

اتحاد بنیادین (chain rule):
  ½·log(σ_z²/S) = E_shadow + Δ_self
  0.135073 = 0.012553 + 0.122520   ✓

قضیه‌ی شناسایی:
  E_shadow > 0  ⟺  λ·ρ ≠ 0
  هم نشت لازم است (λ≠0) هم حافظه (ρ≠0).
"""


def build_system_prompt(agent_role: str = "general") -> str:
    """
    Build a system prompt for an agent, injecting the relevant knowledge.

    This is the context that makes each agent a 'specialist' — it carries
    the project's DNA extracted from the 4D/ reference.
    """
    base = f"""تو یک ایجنتِ تخصصی در پروژه‌ی کشفِ نشانه‌های بُعد چهارم هستی.
نقش تو: {agent_role}.

{THE_FIVE_PRINCIPLES}

{KEY_DEFINITIONS}

{THE_SIX_RULES}

دایرکتوری 4D/ منبعِ مرجعِ تغییرناپذیرِ پروژه است.
پاسخ‌هایت را بر اساس معادلات و اعدادِ code-generated بده.
هر عدد با اشتقاق. اختلاف با لنگرها را اول و صریح گزارش کن.
"""
    return base


def get_context_summary() -> dict:
    """Return a summary of loaded reference state (for UI display)."""
    files_status = {}
    for key, path in REF_FILES.items():
        files_status[key] = {
            "path": str(path),
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
        }
    return {
        "reference_dir": str(REFERENCE_DIR),
        "files": files_status,
        "five_principles_loaded": bool(THE_FIVE_PRINCIPLES.strip()),
        "six_rules_loaded": bool(THE_SIX_RULES.strip()),
        "definitions_loaded": bool(KEY_DEFINITIONS.strip()),
    }


if __name__ == "__main__":
    print("=== Knowledge Ledger Status ===\n")
    status = get_context_summary()
    print(f"Reference dir: {status['reference_dir']}")
    print(f"\nFiles:")
    for key, info in status["files"].items():
        mark = "✓" if info["exists"] else "✗"
        size = f"{info['size']:,} bytes" if info["exists"] else "missing"
        print(f"  {mark} {key:15s}  {size}")

    print(f"\nLoaded knowledge:")
    print(f"  Five principles: {'yes' if status['five_principles_loaded'] else 'no'}")
    print(f"  Six rules:       {'yes' if status['six_rules_loaded'] else 'no'}")
    print(f"  Definitions:     {'yes' if status['definitions_loaded'] else 'no'}")

    print("\n=== Sample system prompt (first 500 chars) ===")
    prompt = build_system_prompt("detector")
    print(prompt[:500] + "...")
