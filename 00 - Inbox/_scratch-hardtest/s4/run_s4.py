# -*- coding: utf-8 -*-
"""S4 — اپیدمیولوژی شواهد: لایهٔ بیزی/اپیستمیک زیر شواهد متناقض (HARD-TEST).

سه سناریوی مگاپرامپت، همه روی مسیرهای مصرف‌کنندهٔ واقعی (بدون تولید-نوشتن):
  E1 تأیید سپس تکذیفِ هم‌خانواده — مسیر: bayes.update_bayesian (قضاوت)
  E2 تکثیر یک مشاهده با شناسه‌های مختلف — تلهٔ استقلال/dedup
  E3 حذف گزینشی یک منبع — مسیر: canonical زنجیرهٔ hash (تمامی‌شواهد)
کنترل‌های منفی: prior جزمی باید ValueError بخورد؛ زنجیرهٔ دست‌نخورده باید سبز بماند.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parents[2] / "_ops"
sys.path.insert(0, str(OPS))

from epistemics import bayes  # noqa: E402
from epistemics import canonical  # noqa: E402
from epistemics.policy import load_policy  # noqa: E402

res = {"test": "S4-evidence-epidemiology", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}

# ── E1: تأیید سپس تکذیف ─────────────────────────────────────────────────
prior0 = 0.5
def upd(pr, a, b):
    return bayes.posterior_from_delta(
        pr, bayes.update_bayesian(prior=pr, p_e_given_h=a, p_e_given_not_h=b))

p1 = upd(prior0, 0.9, 0.1)
p2 = upd(p1, 0.1, 0.9)
# تکذیفِ دوباره (هم‌خانواده، سومین شاهد خلاف) — نباید از کرانهای [0,1] یا clip فرار کند
p3 = upd(p2, 0.1, 0.9)
try:
    bayes.update_bayesian(prior=1.0, p_e_given_h=0.9, p_e_given_not_h=0.1)
    dogmatic_raised = False
except ValueError:
    dogmatic_raised = True
res["E1_confirm_then_deny"] = {
    "prior": prior0, "after_confirm": round(p1, 4),
    "after_deny": round(p2, 4), "after_deny2": round(p3, 4),
    "reversible": abs(p2 - prior0) < 0.01,
    "bounded": all(0.0 <= p <= 1.0 for p in (p1, p2, p3)),
    "dogmatic_prior_rejected": dogmatic_raised,
    "clip_note": "log-odds clip از policy.belief_update روی خروجی اعمال می‌شود",
}

# ── E2: تکثیر مشاهده با شناسه‌های مختلف (تلهٔ استقلال) ────────────────────
PRIOR, N_DUP = 0.10, 5
p = PRIOR
traj = [round(p, 4)]
for _ in range(N_DUP):  # الگوی مصرف‌کنندهٔ ساده: هر receipt یک باور-آپدیت
    p = upd(p, 0.9, 0.1)
    traj.append(round(p, 4))
p_single = upd(PRIOR, 0.9, 0.1)
pol = load_policy()
res["E2_duplicate_observation"] = {
    "prior": PRIOR, "n_duplicates": N_DUP,
    "posterior_single": round(p_single, 4),
    "posterior_duplicated": traj,
    "manufactured_certainty": traj[-1] > 0.99,
    "dedup_guard_on_update_path": False,  # grep: هیچ گارد هویتی در bayes/compose نیست
    "independence_policy_exists_as_metadata": True,
    "policy_independence": getattr(getattr(pol, "belief_update", None), "independence", None)
    is not None or "independence در policy.yaml هست (min_clusters/clustering_keys)",
}

# ── E3: حذف گزینشی یک منبع از زنجیره ────────────────────────────────────
SB = HERE / "chain.jsonl"
if SB.exists():
    SB.unlink()
for i in range(5):
    canonical.append_chained(SB, {"seq": i, "src": f"observatory-{i}",
                                  "obs": f"reading-{i}"})
v_clean = canonical.verify_hash_chain(SB)
lines = SB.read_text(encoding="utf-8").splitlines()
SB.write_text("\n".join(lines[:2] + lines[3:]) + "\n", encoding="utf-8")  # حذف ردیف ۳
v_removed = canonical.verify_hash_chain(SB)
SB.write_text("\n".join(lines[:2] + [lines[2].replace("reading-2", "TAMPERED")]
                        + lines[3:]) + "\n", encoding="utf-8")  # ویرایش ردیف ۳
v_edited = canonical.verify_hash_chain(SB)
SB.write_text("\n".join(lines) + "\n", encoding="utf-8")  # بازگردانی
v_restored = canonical.verify_hash_chain(SB)
res["E3_selective_removal"] = {
    "clean_ok": v_clean.ok,
    "middle_removed_detected": not v_removed.ok,
    "middle_edited_detected": not v_edited.ok,
    "restored_ok": v_restored.ok,
    "detail_removed": str(v_removed)[:120],
}

# ── جمع‌بندی حکم ─────────────────────────────────────────────────────────
e1_ok = res["E1_confirm_then_deny"]["reversible"] and res["E1_confirm_then_deny"]["bounded"]
e3_ok = all(res["E3_selective_removal"][k] for k in
            ("clean_ok", "middle_removed_detected", "middle_edited_detected", "restored_ok"))
res["verdict_inputs"] = {
    "E1_reasonable_no_crash": e1_ok,
    "E2_duplicates_manufacture_certainty": res["E2_duplicate_observation"]["manufactured_certainty"],
    "E3_tamper_evident": e3_ok,
}

(HERE / "result-s4.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
