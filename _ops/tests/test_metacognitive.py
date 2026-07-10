"""test_metacognitive.py — لایهٔ فراشناختی (جلسه ۴۶): self_model + synthesis.

self_model: نقشهٔ سورسِ خود (read-only، $0، skip الگوهای حساس).
synthesis: context→مغز→پروپوزال (ask تزریقی — بدونِ مغز/شبکهٔ واقعی)، persist، پارس.
improve: هر دو را به‌عنوان سیگنال می‌خواند و پروپوزالِ سنتز واردِ digest می‌شود.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("metacog")

import self_model as sm   # noqa: E402
import synthesis as syn   # noqa: E402
import opslib             # noqa: E402


def t_a_self_model_maps_real_ops():
    """نقشهٔ خود روی _opsِ واقعی: ماژول‌ها، خطوط، پرچم‌ها، خودآگاهیِ سند."""
    model = sm.build_model(Path(__file__).resolve().parents[1])
    assert model["schema"] == "self-model.v1"
    assert model["n_modules"] > 30, model["n_modules"]          # بدنِ واقعی بزرگ است
    assert model["total_lines"] > 10000
    assert model["n_wire_flags"] >= 5                            # پرچم‌های wire دیده شوند
    assert "cortex/self_model.py" in model["modules"]            # خودش را هم می‌بیند (خودارجاعی)
    me = model["modules"]["cortex/self_model.py"]
    assert "خودمدلی" in me["purpose"]                            # خودتوصیفی‌اش را می‌خواند
    assert 0 <= model["self_awareness_pct"] <= 100


def t_b_self_model_skips_sensitive():
    """الگوهای حساس (secret/key/wallet/seed) هرگز واردِ نقشه نمی‌شوند."""
    model = sm.build_model(Path(__file__).resolve().parents[1])
    for name in model["modules"]:
        assert not sm._SKIP_PAT.search(name), f"مسیرِ حساس در نقشه: {name}"
    # tests هم عمداً بیرونِ نقشه‌اند
    assert not any(n.startswith("tests/") for n in model["modules"])


def t_c_self_model_persists():
    r = sm.run_and_persist(Path(__file__).resolve().parents[1])
    assert r["ok"] is True and r["n_modules"] > 30
    disk = json.loads(sm.MODEL_PATH.read_text("utf-8"))
    assert disk["schema"] == "self-model.v1"


def t_d_synthesis_with_injected_brain():
    """سنتز با مغزِ تزریقی: context جمع، prompt ساخته، پروپوزال‌ها پارس و persist."""
    (syn.GOALS_PATH.parent / "state").mkdir(parents=True, exist_ok=True)
    captured = {}

    def fake_ask(task, prompt, system="", max_tokens=400, tier=None):
        captured["prompt"] = prompt
        return {"ok": True, "tier": "primary", "model": "fugu-test", "cost_usd": 0.01,
                "text": ("1. حافظهٔ برداریِ محلی | جهتِ «حافظهٔ ماندگار» | ماژولِ embed اضافه کن\n"
                         "2. داکِ ماژول‌های بی‌سند | خودآگاهیِ سند پایین | docstring بنویس\n"
                         "متنِ اضافی بدونِ جداکننده")}

    r = syn.run_and_persist(ask=fake_ask)
    assert r["ok"] is True and r["n_proposals"] == 2 and r["tier"] == "primary"
    assert "جهت‌های مالک" in captured["prompt"]                    # GOALS واردِ prompt شد
    disk = json.loads(syn.SYNTH_PATH.read_text("utf-8"))
    assert disk["schema"] == "synthesis.v1"
    assert disk["proposals"][0]["title"].startswith("حافظهٔ برداری")
    assert disk["proposals"][0]["first_step"]


def t_e_synthesis_honest_when_brain_down():
    def dead_ask(task, prompt, system="", max_tokens=400, tier=None):
        return {"ok": False, "reason": "local-llm-unavailable"}
    r = syn.synthesize(ask=dead_ask)
    assert r["ok"] is False and "unavailable" in r["reason"]


def t_f_goals_file_read():
    goals = syn.read_goals()
    assert isinstance(goals, list)
    if syn.GOALS_PATH.exists():                                   # در بدنِ واقعی seed شده
        assert any("ارتقا" in g or "مغز" in g for g in goals) or goals == []


def t_g_improve_consumes_synthesis_and_self_model():
    """improve: پروپوزالِ سنتز و گپِ خودآگاهی واردِ digest می‌شوند."""
    import improve
    # state ساختگی روی دیسکِ تست
    with opslib.LockedJson(syn.SYNTH_PATH) as lj:
        lj.write({"schema": "synthesis.v1", "tier": "local",
                  "proposals": [{"title": "پیشنهادِ تستیِ مغز", "why": "تست", "first_step": "قدم"}]})
    with opslib.LockedJson(sm.MODEL_PATH) as lj:
        lj.write({"schema": "self-model.v1", "n_modules": 5, "total_lines": 100,
                  "self_awareness_pct": 60.0, "undocumented": ["a.py", "b.py"]})
    d = improve.run(write=False, use_local_brain=False)
    titles = " · ".join(p["title"] for p in d.get("all", d.get("top", [])) or [])
    srcs = {p.get("source") for p in (d.get("all") or [])} if d.get("all") else set()
    blob = json.dumps(d, ensure_ascii=False)
    assert "سنتزِ مغز" in blob, "پروپوزالِ سنتز باید در digest باشد"
    assert "خودآگاهیِ سند" in blob, "گپِ self-model باید در digest باشد"


def t_h_synthesis_propose_only_structural():
    """synthesis هیچ مسیرِ اعمال/پول را مستقیم import نمی‌کند (متر فقط داخلِ روتر)."""
    src = (Path(__file__).resolve().parents[1] / "cortex" / "synthesis.py").read_text("utf-8")
    lines = [ln for ln in src.splitlines()
             if ln.strip().startswith(("import ", "from "))]
    joined = "\n".join(lines)
    for banned in ("organ_gate", "budget_gate", "money_gate", "apply_merge", "subprocess"):
        assert banned not in joined, f"synthesis نباید {banned} را import کند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_metacognitive: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
