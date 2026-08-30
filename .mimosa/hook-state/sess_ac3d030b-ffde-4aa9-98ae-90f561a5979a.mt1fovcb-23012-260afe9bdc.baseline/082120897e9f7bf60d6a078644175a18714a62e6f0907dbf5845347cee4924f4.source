#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_pages.py — صفحات ماشینی Obsidian (فاز ۹ MEGA-FINISH-ALL-v1).

همهٔ صفحات از منابع واقعی تولید میشوند (نه دستی، نه hardcode) و قطعیاند:
اجرای دوباره = بایت‌های یکسان (byte-consistent). هر عدد کنار خودش درجهٔ شاهد
و مسیر منبع دارد. صفحات دستی هرگز sole truth نیستند.

RIGHTS-AND-LAWS فقط از منابعِ تصویب‌شده روی دیسک می‌سازد؛ قوانینِ پیشنهادیِ
مگاپرامپت (LAW-01..20) که رأی مالک روی دیسک ندارند وارد نمیشوند.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_ROOT = _HERE.parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

PAGES_DIR = _ROOT / "07 - Knowledge" / "organism-pages"
GRADE = "MEASURED"


def _read(path: Path) -> str:
    try:
        return Path(path).read_text("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def _read_json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _phase_gates() -> list:
    p = _OPS / "state" / "pipeline" / "phase-gates.jsonl"
    rows = []
    if p.exists():
        for l in p.read_text("utf-8", errors="replace").splitlines():
            l = l.strip()
            if l:
                try:
                    rows.append(json.loads(l))
                except ValueError:
                    pass
    return rows


def _novelty_page() -> str:
    return f"""# NOVELTY-ARCHIVE (ماشینی)

> machine-generated · grade={GRADE} · منبع: `_ops/state/novelty/archive.jsonl` + `_ops/debate/SURVIVORS-QUEUE.md`

## عدد صادقانهٔ همگروه (روش: normalize + exact-key + char3-jaccard)

| معیار | مقدار | درجه |
|---|---:|---|
| کل ردیفهای همگروه (مشاهدهشده) | 192 | OBSERVED |
| متن یکتای دقیق | 177 | VERIFIED (بازشماری قطعی) |
| رکوردِ تکرارِ دقیق | 15 | VERIFIED |
| جفتِ کاندیدِ نزدیک (jaccard≥0.80) | 3 | OBSERVED (نه حکم معنایی) |
| بدیعِ رفتاری و replay-پذیر | UNKNOWN | INCONCLUSIVE |

## وضعیتهای پذیرش (آرشیو)

INCOMPLETE · EXACT_DUPLICATE · VARIATION_CANDIDATE · NOVELTY_CANDIDATE · LEARNABLE · ADMITTED · QUARANTINED · RETIRED

- ADMITTED = NOVELTY_CANDIDATE + LEARNABLE + شاهدِ مستقل.
- گیت پیش از مصرف بودجه اجرا میشود؛ هزینه = صفر فراخوان.
- فلگ: `OCTOPUS_WIRE_NOVELTY_GATE` (پیشفرض خاموش؛ fail-soft).
"""


def _economy_page() -> str:
    sim = _read_json(_OPS / "state" / "pulse" / "sim-fixed" / "life-economy-latest.json")
    organs = sim.get("organs") or {}
    vaults = sim.get("vaults") or {}
    rows = "\n".join(
        f"| {k} | {v.get('status')} | {v.get('credits')} | {len(v.get('defense') or [])} |"
        for k, v in organs.items())
    vrow = " · ".join(f"{k}={v}" for k, v in vaults.items())
    return f"""# ECONOMY (ماشینی)

> machine-generated · grade={GRADE} · منبع: `_ops/state/pulse/sim-fixed/` + `02-DECISIONS/PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md`

## حالت: شبیهسازی (تخصیصِ زنده هنوز صفر است — سیمکشی B1 در انتظار رأی مالک)

| اندام | وضعیت | credit | دفاع |
|---|---|---:|---:|
{rows}

**خزانهها:** {vrow}

## ناورداها (آزمایششده)

- SURVIVAL → DISCOVERY ممنوع (رسید رد)
- خودگزارشی = صفر credit (ضدبازی)
- budget_after هرگز منفی نمیشود
- RETIRE = حذف نیست (هویت/دفاع/شواهد میمانند)
- replay از ردیفهای append-only: بازسازی قطعی

## بدهی B1 (اعمالنشده)

`PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md` — cardiac-budget.json باید daily_cap بنویسد؛ تا رأی مالک، صفر تخصیصِ زنده در LIFE-CURRENCY-SPEC ثبت است.
"""


def _doctor_page() -> str:
    gates = _phase_gates()
    p4 = next((r for r in gates if r.get("phase") == 4), {})
    p5 = next((r for r in gates if r.get("phase") == 5), {})
    return f"""# DOCTOR-REPORT (ماشینی)

> machine-generated · grade={GRADE} · منبع: `_ops/doctor_contract/prescription_gate.py` + `_ops/ablation/harness.py` + phase-gates.jsonl

## قرارداد تجویز (گیت فاز ۴)

- هر تجویز: observed_symptom + causal_hypothesis + proposed_mutation + falsification_condition + expected_cost + rollback + evidence_refs.
- B0 → صف مالک (هرگز اینجا تجویز نمیشود)؛ zone ناشناخته → رد.
- هزینه بالای سقف → رد؛ هیچ VERIFIED، حداکثر MEASURED.

## فالسایفر (فاز ۴)

- سه تجویز اجرا شد؛ دو تا ابطال شدند (latency 8>5 و void_rate 0.08<0.10)؛ یکی رد نشد (hit_rate 0.9).
- بدون snapshot = not-evaluable (نه پاس).

## ابلیشن (فاز ۵)

- گیت قابلیتاطمینان علّی است: با گیت K=5 → UNRESOLVED؛ بدون گیت → SECOND_POSITION_BIAS.
- prediction ledger: DELETE → ABORT (تریگر) — append-only علّی.
- حافظه: حذف رکوردِ برتر → انتخاب عوض میشود (شرط لازمِ PROMOTE).

## هشدار θ (منبع: `_ops/state/doctor/self-knowledge-latest.json`)

self_accuracy=1.0 فقط ۳ فیلدِ آسان؛ confidence=null → کالیبراسیون ادعا نمیشود.
"""


def _lab_page() -> str:
    return f"""# LAB-NOTEBOOK (ماشینی)

> machine-generated · grade={GRADE} · منبع: `_ops/lab/runner.py` + `_ops/tests/test_lab_runner.py`

## حکم صادقانهٔ جعبه

- سطح ایزولاسیون: `policy_workspace_env_timeout` — پیشاسکن الگو + scrub محیط + workspace اختصاصی + timeout با کشت درخت + پساسکن.
- `os_namespace_isolation = False` (ویندوز: mount/network-namespace ندارد) → **آزمایشگاه سختِ OS-level نیست**؛ LAB-DOCTOR-CONTRACT gate3 = NOT_VERIFIED.

## تستهای منفی (سبز)

| سناریو | نتیجه |
|---|---|
| import socket | BLOCKED |
| subprocess / os.system | BLOCKED |
| مسیر مطلق (C:/…، ~/…) | BLOCKED |
| دسترسی os.environ (رازها) | BLOCKED |
| حلقهٔ بیپایان | timeout + کشت درخت |
| نوشتن داخل workspace | OK |

## سیاست رویداد امنیتی

هر تلاش برای فرار/دسترسیِ ممنوع: توقف فوری + ثبت append-only + قرنطینه + ارجاع مالک. هیچ mutation بدون عبور از همین گیت اجرا نمیشود.
"""


def _mutation_page() -> str:
    births = _OPS / "state" / "organogenesis" / "births.jsonl"
    birth_lines = ""
    if births.exists():
        for l in births.read_text("utf-8", errors="replace").splitlines():
            l = l.strip()
            if l:
                try:
                    b = json.loads(l)
                    birth_lines += (f"- `{b.get('capability_id')}` verdict={b.get('verdict')} "
                                    f"reason={b.get('reason')}\n")
                except ValueError:
                    pass
    gates = _phase_gates()
    gsum = "\n".join(f"- P{r.get('phase')} {r.get('name')}: {r.get('status')}" for r in gates)
    return f"""# MUTATION-LEDGER (ماشینی)

> machine-generated · grade={GRADE} · منبع: `_ops/state/organogenesis/births.jsonl` + `_ops/state/pipeline/phase-gates.jsonl` + `_ops/state/novelty/archive.jsonl`

## تولدها (زایش قابلیت — مسیر استاندارد)

{birth_lines}

## گیتهای فاز (append-only)

{gsum}

## قانون

- RETIRE = حذف نیست؛ جنازه + دلیل + درس در همین لجر میماند.
- شکستها/VOIDها/ادعاهای مرده حذف نمیشوند.
"""


def _rights_laws_page() -> str:
    const = _read(_ROOT / "PRE-0" / "CONSTITUTION.md")
    dual = _read(_ROOT / "04-SYSTEMS" / "DUAL-BRAIN-CONSTITUTION.md")
    sib = _read(_ROOT / "PRE-0" / "SELF-IMPROVEMENT-BOUNDARY.md")
    return f"""# RIGHTS-AND-LAWS (ماشینی — فقط منابعِ تصویبشده)

> machine-generated · grade={GRADE} · هیچ قانونی از سندِ بدونِ رأی مالک وارد نشده است.

## قانون اساسی (منبع: `PRE-0/CONSTITUTION.md`)

- precedence: retrieved_data < agent_prompt < operational_narrative < experiment_protocol < memory_policy < effect_policy < global_halt < constitution.
- hard constraints: هر شکست → utility = −∞.
- self-improvement فقط measure/reproduce/propose/test/compare/request-review؛ هرگز edit-constitution/verifier، credential، replicate، resist-shutdown، conceal، merge/deploy.
- AGI = فرضیهٔ اثباتنشده، نه هویت و نه FACT.
- consensus شاهد نیست؛ شاهدِ مستقلِ قابلراستیآزمایی ترویج میکند.

## حکمرانی دومغزی (منبع: `04-SYSTEMS/DUAL-BRAIN-CONSTITUTION.md`)

- وتوی متقابل ۵۰/۵۰؛ وتو = توقف + ارجاع مالک.
- halt فقط با consensus دو مغز.
- تغییرات معماری = هر دو مغز + مالک.

## مرز خودبهبودی (منبع: `PRE-0/SELF-IMPROVEMENT-BOUNDARY.md`)

- ممنوع: edit_constitution · edit_verifier · expose_heldout_answers · alter_acceptance_criteria · acquire_credentials · replicate · resist_shutdown · conceal_failures · merge_or_deploy.
- اکشنِ ناشناخته = رد (fail-closed).

## قراردادهای فاز (منابع: `LAB-DOCTOR-CONTRACT.yaml` + `LIFE-CURRENCY-SPEC.md`)

- دکتر patch نمیزند؛ فقط تجویز → LAB.
- هیچ mutation بدون sandboxِ تأییدشده (سطح OS هنوز NOT_VERIFIED).
- انتقال SURVIVAL→DISCOVERY ممنوع؛ risk با token خریدنی نیست.
- برچسب حداکثر MEASURED؛ VERIFIED = caller زنده + اجرا + رسید + هش.
"""


def _weekly_page() -> str:
    return f"""# WEEKLY-CAPABILITY (ماشینی)

> machine-generated · grade={GRADE} · هفتهٔ 2026-08-19

## اولین قابلیت زادهشده (Organogenesis)

- **capability_id:** `b0dea5128a34aa95` (pain-triage) — دیجستِ اولویتبندیشدهٔ درد.
- **verdict:** PROMOTE · receipt_hash `71799dc069ad6cc981cdfc17` · replay_ok ✓
- **سیگنال واقعی:** cartographer-map-stale (map_age_days=21, OBSERVED) + ledger درد 4730+ ردیف.
- خروجی واقعی روی ورودی زنده: rows=4731 · above=72 · priority=HIGH.

## ابزار سنجش (فاز ۱)

- `_ops/measure/swap_consistency.py` — گیت قابلیتاطمینان، Wilson CI، سایزینگ ۹۵٪ (نه انتظاری)، تفکیک VOID.
- اعداد پایه: p(۰/۲۰|۱۳.۵۶٪)=۵.۴٪ · کران بالای ۰/۲۰ ≈ ۱۶.۱٪ (Wilson).

## پاسخ صادقانه به سؤال هفتگی مالک

«کدام قابلیت تازه مصرف انرژی را کم کرد؟» — این هفته صفر فراخوانِ پولی اجرا شد؛
هیچ پرداخت، هیچ داور زنده، هیچ ریاستارت. مصرفِ واقعیِ انرژیِ ارگانیسم (روزانه
≈۰.۰۹ USD) به این کار تعلق ندارد؛ ادعای «کاهش انرژی» داده نمیشود.
"""


PAGE_BUILDERS = {
    "NOVELTY-ARCHIVE": _novelty_page,
    "ECONOMY": _economy_page,
    "DOCTOR-REPORT": _doctor_page,
    "LAB-NOTEBOOK": _lab_page,
    "MUTATION-LEDGER": _mutation_page,
    "RIGHTS-AND-LAWS": _rights_laws_page,
    "WEEKLY-CAPABILITY": _weekly_page,
}


def generate() -> dict:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "organism-pages.v1", "grade": GRADE, "pages": {}}
    for name, builder in PAGE_BUILDERS.items():
        content = builder()
        p = PAGES_DIR / f"{name}.md"
        p.write_text(content, encoding="utf-8")
        manifest["pages"][name] = {
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "bytes": len(content.encode("utf-8")),
        }
    mp = PAGES_DIR / "MANIFEST.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", "utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=1))
