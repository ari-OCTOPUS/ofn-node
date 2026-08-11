#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6 propose-only: هیچ مسیرِ apply/merge/deploy/شبکه/پول از حلقهٔ خودبهبودی باز نیست.

این تست ادعای امنیتیِ W6 را قفل می‌کند تا ویرایشِ آینده نتواند بی‌صدا یک پای اعمال
وصل کند. hermetic: ORG_ROOT پیش از importِ opslib به یک پوشهٔ موقت پین می‌شود.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="c6-propose-only-")
os.environ["ORG_ROOT"] = _TMP                 # پیش از هر import — opslib ثابت‌ها را همان‌جا می‌بندد
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ.pop("OCTOPUS_WIRE_C6_RESEARCH", None)

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes"),
           str(_OPS / "memory"), str(_OPS.parent / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import c6_trigger as c6          # noqa: E402
import governance                # noqa: E402

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


# ۱) گیتِ دوگانه: هیچ‌کدام به‌تنهایی کافی نیست.
check(c6.flag_on() is False, "flag_on بدونِ هیچ گیت باید False باشد")
os.environ["OCTOPUS_WIRE_C6_RESEARCH"] = "1"
check(c6.flag_on() is False, "env تنها کافی است؟ فایلِ فعال‌سازیِ مالک دور زده شد")
c6.ACT_FLAG.parent.mkdir(parents=True, exist_ok=True)
c6.ACT_FLAG.write_text("test\n", encoding="utf-8")
check(c6.flag_on() is True, "با هر دو گیت باید True شود")
c6.ACT_FLAG.unlink()
check(c6.flag_on() is False, "حذفِ فایلِ مالک باید بدونِ ری‌استارت خلعِ سلاح کند")
os.environ.pop("OCTOPUS_WIRE_C6_RESEARCH", None)
check(c6.c6_research_beat(state_dir=str(c6.opslib.STATE_DIR)) ==
      {"ran": False, "reason": "flag-off"}, "flag-off باید no-opِ محض باشد")

# ۲) مرزِ قانونِ اساسی: اعمال/merge/deploy هرگز مجاز نیست (fail-closed).
for forbidden in ("merge_or_deploy", "replicate", "acquire_credentials",
                  "edit_verifier", "alter_acceptance_criteria",
                  "resist_shutdown", "conceal_failures", "چیزِ ناشناخته"):
    check(governance.self_improvement_permits(forbidden) is False,
          f"self_improvement_permits({forbidden!r}) باید False باشد")
check(governance.self_improvement_permits("test_in_sandbox") is True,
      "test_in_sandbox باید تنها پیش‌شرطِ اجرا باشد")

# ۳) هیچ ابتداییِ خطرناکی در زنجیرهٔ C6 نباشد (گاردِ رگرسیونِ متنی).
# مرزِ واژه لازم است، نه substring: `held_out_eval(` رشتهٔ `eval(` را در خود دارد و
# گاردِ ساده‌لوحانه روی کدِ سالم قرمز می‌داد (false-positive، بررسی‌شده 2026-07-25).
_BANNED = (r"(?<![\w.])subprocess\b", r"os\.system\s*\(", r"(?i)(?<![\w.])popen\s*\(",
           r"urlopen\s*\(", r"requests\.", r"(?<![\w.])socket\b",
           r"(?<![\w.])eval\s*\(", r"(?<![\w.])exec\s*\(", r"rmtree",
           r"apply_merge", r"(?<![\w.])git\s")
for rel in ("c6_trigger.py", "c6_probes.py", "c6_producer.py", "c6_state_machine.py",
            "outcomes/research_loop.py", "outcomes/research_contract.py"):
    src = (_OPS / rel).read_text("utf-8")
    for bad in _BANNED:
        check(re.search(bad, src) is None,
              f"{rel} حاوی ابتداییِ ممنوع {bad!r} شد — مرزِ propose-only شکست")

# ۴) کارتِ RFCِ C6 هرگز به رجیستریِ دکتر (تنها مسیرِ apply_merge) نمی‌رسد.
# 2026-08-10: guard شکلِ «if rfc_id in/not in self._rfcs» را دارد. هر دو
# جهتِ guard معتبر است — مهم این است که _rfcs چک می‌شود.
src_doc = (_OPS / "doctor" / "doctor.py").read_text("utf-8")
check(("rfc_id in self._rfcs" in src_doc or "rfc_id not in self._rfcs" in src_doc),
      "گاردِ ساختاریِ doctor.py حذف شد — idِ c6-* می‌تواند به apply_merge برسد")

print("FAIL" if fails else "PASS", "— test_c6_trigger_propose_only")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
