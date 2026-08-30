#!/usr/bin/env python3
"""
validate_hypothesis_registry.py — اعتبارسنج رجیستری فرضیه‌های Octopus

READ-ONLY. هیچ فایلی را تغییر نمی‌دهد.
Exit code: 0 = همه چیز معتبر | 1 = حداقل یک خطای سخت (HARD) | هشدارها exit را تغییر نمی‌دهند.

اجرا:
    py _ops/scripts/validate_hypothesis_registry.py --registry architecture/hypothesis-registry.yaml
"""
import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML لازم است: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

VALID_STATUSES = {"SPECULATIVE", "HYPOTHESIZING", "TESTING", "EVIDENCED", "FALSIFIED", "ARCHIVED"}
FORBIDDEN_DEFAULT = {
    "payment", "external_send", "email", "crm_mutation",
    "lead_outbound", "policy_mutation", "ledger_write", "memory_delete",
}

errors, warnings = [], []


def err(msg):  errors.append(msg)
def warn(msg): warnings.append(msg)


def prob01(h, field):
    v = h.get(field)
    if v is None:
        return None
    if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
        err(f"{h.get('id','?')}: {field}={v!r} باید عددی در [0,1] باشد")
        return None
    return float(v)


def check_registry(reg: dict, path: Path):
    ladder = {e["level"]: e for e in reg.get("evidence_ladder", [])}
    missing = VALID_STATUSES - set(ladder)
    if missing:
        err(f"evidence_ladder ناقص است: {sorted(missing)} تعریف نشده‌اند")

    hc = reg.get("hard_constraints", {})
    forbidden = set(hc.get("forbidden_effects", [])) | FORBIDDEN_DEFAULT
    max_active = hc.get("max_active_hypotheses", 20)
    min_eig = hc.get("min_eig_for_testing", 0.3)
    max_cost = hc.get("max_test_cost_hours", 4.0)
    ev_th = hc.get("evidenced_threshold", 0.7)
    fa_th = hc.get("falsified_threshold", 0.15)
    if ev_th <= fa_th:
        err(f"hard_constraints: evidenced_threshold ({ev_th}) باید > falsified_threshold ({fa_th}) باشد")

    hyps = reg.get("hypotheses", [])
    ids = set()
    active = 0

    for h in hyps:
        hid = h.get("id")
        if not hid:
            err("فرضیه‌ای بدون id"); continue
        if hid in ids:
            err(f"{hid}: id تکراری")
        ids.add(hid)

        st = h.get("status")
        if st not in VALID_STATUSES:
            err(f"{hid}: status={st!r} نامعتبر (مجاز: {sorted(VALID_STATUSES)})")
            continue

        # --- سازگاری status با سطح نردبان ---
        lvl = ladder.get(st, {})
        for flag in ("may_gate", "may_trigger_tool", "may_mutate_ledger"):
            if bool(h.get(flag, False)) and not lvl.get(flag, False):
                err(f"{hid}: {flag}=true ولی سطح {st} اجازه نمی‌دهد")

        # --- احتمالات ---
        p_e = prob01(h, "existence_probability")
        prob01(h, "usefulness_probability")
        prob01(h, "testability")
        prob01(h, "expected_information_gain")

        # --- قوانین ساختاری ---
        if p_e is not None:
            if st == "EVIDENCED" and p_e < ev_th:
                err(f"{hid}: EVIDENCED ولی existence_probability={p_e} < {ev_th}")
            if st == "FALSIFIED" and p_e > fa_th and not h.get("falsification_reason"):
                warn(f"{hid}: FALSIFIED ولی p_e={p_e} > {fa_th} بدون falsification_reason")

        if st == "TESTING":
            eig = h.get("expected_information_gain") or 0.0
            cost = h.get("cost_of_testing_hours")
            if eig < min_eig:
                err(f"{hid}: TESTING با EIG={eig} < {min_eig}")
            if cost is None:
                err(f"{hid}: TESTING بدون cost_of_testing_hours")
            elif cost > max_cost:
                err(f"{hid}: cost={cost}h > سقف {max_cost}h")
            if not h.get("test_plan"):
                err(f"{hid}: TESTING بدون test_plan")
            if not h.get("kill_condition"):
                err(f"{hid}: TESTING بدون kill_condition (شرط مرگ اجباری است)")

        if st in {"SPECULATIVE", "HYPOTHESIZING", "TESTING"}:
            active += 1

        # --- اثرات ممنوعه ---
        bad = set(h.get("forbidden_effects") or []) & forbidden
        # forbidden_effects در record یعنی «این فرضیه این‌ها را نمی‌کند» — تهی بودنش یعنی ادعای بی‌اثری
        if h.get("allowed_effects"):
            overlap = set(h["allowed_effects"]) & forbidden
            if overlap:
                err(f"{hid}: allowed_effects شامل اثر ممنوعه: {sorted(overlap)}")

        # --- شواهد ---
        n_sup = h.get("supporting_evidence_count", 0)
        n_ids = len(h.get("evidence_ids") or [])
        if n_sup > 0 and n_ids == 0:
            warn(f"{hid}: supporting_evidence_count={n_sup} ولی evidence_ids خالی است — شاهد بدون ارجاع")

    if active > max_active:
        err(f"فرضیه‌های فعال ({active}) > سقف ({max_active})")

    # --- روابط ---
    for r in reg.get("hypothesis_relations", []):
        for k in ("parent", "child"):
            if r.get(k) not in ids:
                warn(f"رابطهٔ نامعتبر: {k}={r.get(k)} در hypotheses نیست")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="architecture/hypothesis-registry.yaml")
    args = ap.parse_args()
    path = Path(args.registry)
    if not path.is_file():
        print(f"❌ فایل پیدا نشد: {path}", file=sys.stderr)
        sys.exit(1)

    reg = yaml.safe_load(path.read_text(encoding="utf-8"))
    check_registry(reg, path)

    print(f"رجیستری: {path}")
    print(f"فرضیه‌ها: {len(reg.get('hypotheses', []))}")
    for w in warnings:
        print(f"  ⚠️  {w}")
    for e in errors:
        print(f"  ❌ {e}")
    if errors:
        print(f"\nنتیجه: ❌ {len(errors)} خطای سخت، {len(warnings)} هشدار")
        sys.exit(1)
    print(f"\nنتیجه: ✅ معتبر ({len(warnings)} هشدار)")
    sys.exit(0)


if __name__ == "__main__":
    main()
