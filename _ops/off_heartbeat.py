#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""off_heartbeat.py — R9 «هیچی خاموش نیست»: heartbeat ماژول‌های خفته.

فاز ۳ دستورالعملِ ۲۰۲۶-۰۸-۱۶ (Owner: Armin): هر ماژولِ خاموش هر **۱۰ beat** یک
رویداد `module.heartbeat` با `status=OFF` در `state/events.jsonl` می‌فرستد — با
trace_id/correlation_id/idempotency_key (R8). ماژولی که وصل شد (فلگش روشن است)
خودکار از فهرستِ خاموش‌ها حذف می‌شود — spine که wired شد دیگر OFF نمی‌زند.

وضعیتِ هر ماژول از **فلگِ زندهٔ همان پروسه** خوانده می‌شود (env)، نه از حافظه:
  spine        ← OCTOPUS_WIRE_SPINE          (الان: ON در تولید — spine.db زنده)
  intel_spine  ← OCTOPUS_INTERACTION_LOG     (ON در env)
  synapse      ← SYNAPSE_ENABLED             (خاموش)
  chord        ← OCTOPUS_WIRE_CHORD          (خاموش — خوانندهٔ فلگ با فاز ۸d می‌آید)
  action_bridge← OCTOPUS_WIRE_ACTION_BRIDGE **و** OCTOPUS_ACTION_BRIDGE_RUNTIME
                (فلگِ اول در env روشن است ولی runtime caller وجود ندارد → تا فاز ۸e
                 که caller وصل شود، OFF می‌زند — همان حقیقتِ AGENT-INVENTORY §۲)

addon-only · fail-soft (هر استثنا = no-op) · تک‌نویسنده: فقط organism loop صدایش می‌زند.
"""
from __future__ import annotations

import os

EVERY_N = 10   # هر ۱۰ beat یک‌بار (D6/roadmap: «هر ۱۰ beat heartbeat OFF»)

# نامِ ماژول → (فلگِ اصلی، فلگِ دومِ اختیاری) — هر دو باید روشن باشند تا «زنده» باشد.
_MODULE_FLAGS = {
    "spine": ("OCTOPUS_WIRE_SPINE", None),
    "intel_spine": ("OCTOPUS_INTERACTION_LOG", None),
    "synapse": ("SYNAPSE_ENABLED", None),
    "chord": ("OCTOPUS_WIRE_CHORD", None),
    "action_bridge": ("OCTOPUS_WIRE_ACTION_BRIDGE", "OCTOPUS_ACTION_BRIDGE_RUNTIME"),
}

_TRUTHY = ("1", "true", "yes", "on")


def _on(env, flag: str) -> bool:
    return str(env.get(flag, "")).strip().lower() in _TRUTHY


def module_live(name: str, env=None) -> bool:
    """آیا این ماژول در این پروسه زنده/وصل است؟ ماژولِ ناشناخته → True
    (دعوا با ماژول‌هایِ خارج از مأموریتِ این فایل نیستیم)."""
    env = os.environ if env is None else env
    flags = _MODULE_FLAGS.get(name)
    if flags is None:
        return True
    main, second = flags
    return _on(env, main) and (second is None or _on(env, second))


def dormant_modules(env=None) -> list:
    """ماژول‌هایی که الان خاموش‌اند و باید OFF بزنند."""
    return [m for m in _MODULE_FLAGS if not module_live(m, env)]


def emit_off_heartbeat(beat: int, *, env=None, events_mod=None) -> list:
    """اگر beat مضربِ ۱۰ بود، برای هر ماژولِ خاموش یک module.heartbeat با status=OFF
    بفرست. خروجی: فهرستِ رویدادهای emit شده (خالی = این beat نوبت نبود / همه زنده).
    هرگز raise نمی‌کند — بخشی از تیکِ ارگانیسم است."""
    try:
        beat = int(beat or 0)
        if beat <= 0 or beat % EVERY_N != 0:
            return []
        if events_mod is None:
            import events as events_mod  # noqa: WPS433 — lazy، همان پروسه
        out = []
        for m in dormant_modules(env):
            ev = events_mod.emit(
                "module.heartbeat", m, status="OFF",
                summary=f"dormant module heartbeat (every {EVERY_N} beats, R9)",
                next_action="wiring this module removes it from OFF list",
                trace_id=f"hb-off-{m}-{beat}",
                correlation_id=f"hb-off-{m}-{beat}",
                idempotency_key=f"module.heartbeat|{m}|{beat}",
                approval_state="none")
            out.append(ev)
        return out
    except Exception:  # noqa: BLE001 — R9 هرگز تیک را نمی‌کشد
        return []


def tick(beat: int, env=None) -> list:
    """نقطهٔ ورودِ organism loop — همان emit_off_heartbeat با پوششِ fail-softِ مضاعف."""
    return emit_off_heartbeat(beat, env=env)


if __name__ == "__main__":
    import json
    beat = int(os.environ.get("BEAT", "0") or 0)
    print(json.dumps({"beat": beat, "dormant": dormant_modules(),
                      "emitted": tick(beat)}, ensure_ascii=False, indent=1))
