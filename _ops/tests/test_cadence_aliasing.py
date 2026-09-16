#!/usr/bin/env python3
"""تستِ رفعِ باگِ aliasingِ کادنس (تری‌اسکن 2026-07-17).

باگِ ریشه‌ای: tickِ واقعی ~۹۰۰s ضربانِ ۶۰s را با فازِ آفست نمونه‌برداری می‌کند، پس
`beat % every_n == 0` هرگز روی مضرب نمی‌افتد و beatها ماه‌ها خاموش می‌مانند
(lead_discovery = سنسورِ پول؛ afferent = تنها مسیرِ یادگیری). رفع: هلپرِ
`wiring._epoch_fire` — هر پنجرهٔ epoch حداکثر یک شلیک، مستقل از فازِ نمونه.

این سوئیت هم رفتار را اثبات می‌کند هم مهاجرتِ ۸ سایت را قفل می‌کند (رگرسیون‌گارد).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("cadence-aliasing")
_OPS = (harness.SELF_OPS)
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402


def t_old_modulo_missed_under_offset():
    """با فازِ آفست (شرایطِ واقعی)، منطقِ کهنهٔ `beat % every_n` هرگز شلیک نمی‌کرد."""
    samples = list(range(7, 7 + 30 * 30, 15))   # beat از ۷، گامِ ~۱۵ (=900s/60s)، every_n=30
    mod_fires = sum(1 for b in samples if b > 0 and b % 30 == 0)
    assert mod_fires == 0, f"این سناریو باید باگ را نشان دهد، ولی modulo {mod_fires} بار شلیک کرد"


def t_epoch_fires_reliably():
    """هلپرِ نو در همان سناریو قابل‌اعتماد شلیک می‌کند — تقریباً یک‌بار در هر پنجرهٔ epoch."""
    wiring._EPOCH_STATE.clear()
    samples = list(range(7, 7 + 30 * 30, 15))
    fires = sum(1 for b in samples if wiring._epoch_fire("t", b, 30))
    assert fires >= 25, f"epoch باید قابل‌اعتماد شلیک کند، شد {fires}"


def t_epoch_idempotent_per_window():
    """در یک پنجرهٔ epoch فقط یک‌بار True؛ پنجرهٔ بعد دوباره True."""
    wiring._EPOCH_STATE.clear()
    assert wiring._epoch_fire("x", 30, 30) is True
    assert wiring._epoch_fire("x", 31, 30) is False
    assert wiring._epoch_fire("x", 45, 30) is False
    assert wiring._epoch_fire("x", 60, 30) is True   # epoch بعدی


def t_beat_zero_never_fires():
    wiring._EPOCH_STATE.clear()
    assert wiring._epoch_fire("z", 0, 30) is False
    assert wiring._epoch_fire("z", 29, 30) is False   # هنوز داخلِ epoch 0


def t_every_n_zero_is_safe():
    """every_n<=0 یا خراب = «هر beat» (هم‌معنیِ منطقِ کهنه، بدونِ crash)."""
    wiring._EPOCH_STATE.clear()
    assert wiring._epoch_fire("q", 5, 0) is True      # every_n<=0 = همیشه شلیک
    assert wiring._epoch_fire("q", 5, None) is True   # خراب → 0 → همیشه شلیک


def t_names_are_isolated():
    """هر beat نامِ جدا دارد — شلیکِ یکی، دیگری را مصرف نمی‌کند."""
    wiring._EPOCH_STATE.clear()
    assert wiring._epoch_fire("a", 30, 30) is True
    assert wiring._epoch_fire("b", 30, 30) is True   # نامِ متفاوت، مستقل


def t_no_modulo_cadence_remains():
    """رگرسیون‌گارد: هیچ `beat % every_n` در wiring.py نماند (مهاجرتِ کامل)."""
    src = (_OPS / "wiring.py").read_text("utf-8")
    assert "beat % every_n" not in src, "یک سایتِ کادنسِ modulo مهاجرت‌نشده باقی ماند"


def t_eight_sites_migrated():
    """هر ۸ سایتِ کادنس به epoch-gate وصل‌اند (۸ فراخوانی + ۱ تعریف = ۹)."""
    src = (_OPS / "wiring.py").read_text("utf-8")
    calls = len(re.findall(r"_epoch_fire\(", src))
    assert calls >= 9, f"انتظار ≥۹ ارجاع (۸ سایت + تعریف)، شد {calls}"
    for name in ("epistemics", "afferent", "ideas", "email",
                 "lead_discovery", "asset_map", "cultivate", "ziman"):
        assert f'_epoch_fire("{name}"' in src, f"سایتِ {name} مهاجرت نکرد"


if __name__ == "__main__":
    failed = harness.run([
        ("[باگ] modulo با آفست هرگز شلیک نمی‌کرد", t_old_modulo_missed_under_offset),
        ("[رفع] epoch قابل‌اعتماد شلیک می‌کند", t_epoch_fires_reliably),
        ("[رفع] یک شلیک per epoch", t_epoch_idempotent_per_window),
        ("[مرز] beat=0 هرگز شلیک نمی‌کند", t_beat_zero_never_fires),
        ("[مرز] every_n=0 امن است", t_every_n_zero_is_safe),
        ("[مرز] نام‌ها ایزوله‌اند", t_names_are_isolated),
        ("[گارد] هیچ modulo کادنس نماند", t_no_modulo_cadence_remains),
        ("[گارد] هر ۸ سایت مهاجرت کرد", t_eight_sites_migrated),
    ])
    sys.exit(1 if failed else 0)
