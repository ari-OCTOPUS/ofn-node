#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""retrieval_router — حافظه در نقطهٔ تصمیم، با یک قاعدهٔ سخت: فقط narrowing.

شکافی که می‌بندد (ممیزی ۰۷-۳۱): زنجیرهٔ goal→action هنگام تصمیم **هیچ**
خواندنی از MemoryStore نداشت — حافظه پرشونده بود ولی مصرف‌نشونده (همان الگویی
که W2 برای لِین لید بست: «cited but not consumed»).

قواعد:
  · حافظه هرگز مجوز نیست: این router نمی‌تواند عملی را باز کند، فقط می‌تواند
    ببندد (veto) یا شواهد ضمیمه کند. جهتش همیشه fail-closed است.
  · veto فقط از namespace ِ `owner_fact` می‌آید (mkey = ``veto:<goal_key>``) —
    ردیفی که خودِ MemoryGate با گاردِ owner_only پذیرفته؛ یعنی این «اختیارِ
    حافظه» نیست، دستورِ ثبت‌شدهٔ مالک است که relay می‌شود.
  · فقط ADMITTED دیده می‌شود (قاعدهٔ خودِ store)؛ citation به شکلِ
    `as_memories_used` (hash/ref، بدون متنِ خام).
  · انتخابِ حالت: exact (veto) → episodic (تجربهٔ همین هدف) → procedural.
    نتیجهٔ خالی = هیچ context ِ اضافه‌ای؛ «retrieval که کمکی نمی‌کند اصلاً
    اضافه نمی‌شود».

فلگ: `OCTOPUS_WIRE_MEMORY_DECISION` — از ۲۰۲۶-۰۷-۳۱ مسلح است
(`OCTOPUS-flags.cmd:852`؛ رأیِ مالک، بستهٔ TG-UI ۴-موجی «anti-amnesia»).
این کامنت تا ۲۰۲۶-۰۸-۰۶ کهنه مانده و «غایب/معلق» ادعا می‌کرد؛ زنده تأیید شد:
`route()` امروز واقعاً اجرا شده و citation در `state/test_cycle/missions.jsonl`
ثبت کرده (`goal_action_bridge.py` را ببین). فلگ خاموش همچنان = صفر خواندنِ DB.

$0 · stdlib · فقط‌خواندنی روی memory.db · صفر شبکه/نوشتن.
"""
from __future__ import annotations

import os

FLAG = "OCTOPUS_WIRE_MEMORY_DECISION"   # از ۰۷-۳۱ مسلح (OCTOPUS-flags.cmd:852)
SCHEMA = "memory-retrieval.v1"


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def route(*, goal_key: str, method_index=None, store=None, k: int = 3,
          now=None) -> dict:
    """{schema, mode, memories_used, veto, veto_ref, reasons}.

    `store` تزریق‌پذیر برای تست؛ اگر خودمان ساختیم خودمان می‌بندیم (قفلِ
    sqlite روی ویندوز). فلگ خاموش یا goal_key خالی = هیچ تماسی با DB."""
    out = {"schema": SCHEMA, "mode": "none", "memories_used": [],
           "veto": False, "veto_ref": None, "reasons": []}
    if not flag_on():
        out["mode"] = "off"
        return out
    gk = str(goal_key or "").strip()
    if not gk:
        out["reasons"].append("no-goal-key")
        return out

    own_store = store is None
    if own_store:
        import memory_store as _ms
        store = _ms.MemoryStore()
    try:
        modes = []
        recs = []

        # ۱) exact — دستورِ ثبت‌شدهٔ مالک: فقط می‌بندد.
        veto_row = store.get("owner_fact", f"veto:{gk}")
        if isinstance(veto_row, dict):
            out["veto"] = True
            out["veto_ref"] = veto_row.get("memory_id")
            recs.append(veto_row)
            modes.append("exact")
            out["reasons"].append("owner-veto")

        # ۲) episodic — تجربهٔ قبلیِ همین هدف (شواهد، نه حکم).
        ep = store.search(gk, namespace="episodic", k=max(1, int(k)))
        if ep:
            recs.extend(ep)
            modes.append("episodic")

        # ۳) procedural — روشِ اثبات‌شده برای این هدف، اگر ثبت شده.
        pr = store.search(gk, namespace="procedural", k=max(1, int(k)))
        if pr:
            recs.extend(pr)
            modes.append("procedural")

        out["mode"] = "+".join(modes) if modes else "no-match"
        out["memories_used"] = store.as_memories_used(recs) if recs else []
        if not recs:
            out["reasons"].append("no-admitted-memory")
        return out
    finally:
        if own_store:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":   # pragma: no cover — نمای دستیِ اپراتور
    import json
    import sys
    gk = sys.argv[1] if len(sys.argv) > 1 else ""
    print(json.dumps(route(goal_key=gk), ensure_ascii=False, indent=1))
