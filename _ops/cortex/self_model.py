#!/usr/bin/env python3
"""self_model.py — خودمدلیِ عمیقِ لایهٔ فراشناختی (جلسه ۴۶، رأی مالک:
«کدِ خودش رو بخونه و درک کنه»).

سیستم سورسِ خودش را (فقط‌خواندنی) می‌پیماید و یک نقشهٔ ماشین‌خوان می‌سازد:
هر ماژول → مسیر، حجم، جملهٔ اولِ داکِ‌استرینگ (خودتوصیفی)، تعدادِ تابع/کلاس،
پرچم‌های wire که می‌خواند، و importهای درون‌خانه. خروجی:
`state/cortex/self-model.json` (schema self-model.v1) — خوراکِ improve/سنتز/پنل.

$0، stdlib-only (ast)، fail-soft. هرگز فایلِ secret/ignored را نمی‌خواند
(فقط *.py داخلِ _ops، و الگوهای حساس رد می‌شوند).
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

MODEL_PATH = opslib.STATE_DIR / "cortex" / "self-model.json"
# ── طرفِ «خود» برای واسنجیِ برخط (ORPH-SELF-CLAIMS) ────────────────────────────
# calibration_probe فقط این لِجِر را می‌خواند و هرگز خودش نمی‌نویسدش؛ اینجا تنها
# تولیدکننده است. رکورد: {key, confidence∈[0,1], ts, ...} — دقیقاً شِمایی که
# calibration_probe._load_claims انتظار دارد (key + confidence). هم‌مسیر با
# calibration_probe.CLAIMS.
SELF_CLAIMS_PATH = opslib.STATE_DIR / "cortex" / "self-claims.jsonl"
# همان فلگی که calibration_probe استفاده می‌کند — خاموش (پیش‌فرض) = صفر نوشتن.
SELF_MONITOR_FLAG = "CORTEX_SELF_MONITOR"
# دفاعِ عمقی: حتی داخلِ _ops هم الگوهای حساس را رد کن (هم‌راستا با .agentignore)
_SKIP_PAT = re.compile(r"(secret|wallet|seed|\.env|key)", re.I)
_SKIP_DIRS = {"__pycache__", "state", "secrets-export", "node_modules", ".git"}
_FLAG_RE = re.compile(r'OCTOPUS_WIRE_[A-Z_]+|ACTIVATION-[A-Z-]+\.flag')


def _describe_module(p: Path) -> dict | None:
    """یک ماژولِ پایتون را read-only توصیف کن. خطا → None (fail-soft)."""
    try:
        src = p.read_text("utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception:  # noqa: BLE001 — سورسِ ناخوانا/سینتکسِ خراب → skip
        return None
    doc = ast.get_docstring(tree) or ""
    first_line = doc.strip().splitlines()[0][:160] if doc.strip() else ""
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef,
                                                          ast.AsyncFunctionDef))]
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    imports: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    flags = sorted(set(_FLAG_RE.findall(src)))
    return {
        "purpose": first_line,
        "lines": src.count("\n") + 1,
        "n_funcs": len(funcs), "n_classes": len(classes),
        "top_defs": (classes + funcs)[:8],
        "wire_flags": flags[:10],
        "house_imports": sorted(i for i in imports
                                if i in {"opslib", "chrono", "wiring", "organism",
                                         "local_llm", "model_router", "self_audit",
                                         "improve", "web_research", "registry"}),
    }


def build_model(root: Path | None = None) -> dict:
    """کلِ _ops را بپیما → نقشهٔ خود. read-only، $0."""
    root = root or _OPS
    modules: dict[str, dict] = {}
    total_lines = 0
    all_flags: set[str] = set()
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        if _SKIP_PAT.search(rel) or any(d in p.parts for d in _SKIP_DIRS):
            continue
        if rel.startswith("tests/"):
            continue                       # نقشهٔ بدن، نه تست‌ها (تست‌ها جدا شمرده می‌شوند)
        info = _describe_module(p)
        if info is None:
            continue
        modules[rel] = info
        total_lines += info["lines"]
        all_flags |= set(info["wire_flags"])
    n_tests = len(list((root / "tests").glob("test_*.py"))) if (root / "tests").exists() else 0
    # خودتوصیفی: ماژول‌های بدونِ داکِ‌استرینگ = گپِ خودآگاهی
    undocumented = [m for m, i in modules.items() if not i["purpose"]]
    return {
        "ts": opslib.now_iso(), "schema": "self-model.v1",
        "n_modules": len(modules), "total_lines": total_lines,
        "n_tests": n_tests,
        "n_wire_flags": len(all_flags), "wire_flags": sorted(all_flags)[:40],
        "undocumented": undocumented[:10],
        "self_awareness_pct": round(100.0 * (len(modules) - len(undocumented))
                                    / max(1, len(modules)), 1),
        "modules": modules,
    }


def summarize(model: dict, max_modules: int = 12) -> str:
    """خلاصهٔ متنیِ نقشهٔ خود — ورودیِ مغز (سنتز/local). کوتاه و عمومی."""
    lines = [f"بدن: {model['n_modules']} ماژول · {model['total_lines']} خط · "
             f"{model['n_tests']} فایلِ تست · خودآگاهیِ سند: {model['self_awareness_pct']}%"]
    biggest = sorted(model["modules"].items(), key=lambda kv: -kv[1]["lines"])[:max_modules]
    for name, i in biggest:
        lines.append(f"- {name} ({i['lines']}L): {i['purpose'] or '(بدونِ توصیف)'}")
    return "\n".join(lines)


def _self_monitor_on() -> bool:
    """فلگِ CORTEX_SELF_MONITOR روشن؟ (وجود/truthy = روشن — دقیقاً منطقِ calibration_probe)."""
    v = str(os.environ.get(SELF_MONITOR_FLAG, "")).strip().lower()
    return v not in ("", "0", "false", "no", "off")


def _self_claims(model: dict) -> list[dict]:
    """ادعاهای صادقانهٔ خود را از سیگنال‌های واقعیِ نقشهٔ خود بساز.

    تنها سیگنالِ [0,1]-پذیرِ موجود، «خودآگاهیِ سند» است (نسبتِ ماژول‌های دارای
    داکِ‌استرینگ) — یک پروکسیِ راستِ انسجام/خوداکتشافی. هیچ چیزی جعل نمی‌شود؛ اگر
    self_awareness_pct نبود، ادعایی صادر نمی‌شود. calibration_probe این را با
    حقیقتِ بیرونیِ لِجِرها (نه با خودِ ادعا) گرید می‌کند."""
    claims: list[dict] = []
    ts = opslib.now_iso()
    pct = model.get("self_awareness_pct")
    if isinstance(pct, (int, float)):
        conf = max(0.0, min(1.0, float(pct) / 100.0))
        claims.append({
            "key": "self_model.coherence",           # key ماتِ پایدار (بی‌محتوای خصوصی)
            "confidence": round(conf, 6),
            "ts": ts,
            "source": "self_model",
            "schema": "self-claim.v1",
        })
    return claims


def emit_self_claims(model: dict) -> int:
    """ادعاهای خود را زیرِ فلگ به self-claims.jsonl الحاق کن (تولیدکنندهٔ ORPH-SELF-CLAIMS).

    فلگ خاموش (پیش‌فرض) → صفر نوشتن (byte-identical). fail-soft: هر خطا بلعیده
    می‌شود تا حلقهٔ فراخوان هرگز نمیرد. خروجی = تعدادِ رکوردهای نوشته‌شده."""
    if not _self_monitor_on():
        return 0
    try:
        written = 0
        for claim in _self_claims(model):
            opslib.append_jsonl(SELF_CLAIMS_PATH, claim)
            written += 1
        return written
    except Exception as e:  # noqa: BLE001 — تولیدِ ادعا هرگز run_and_persist را نمی‌کشد
        try:
            opslib.alert([f"self_model emit_self_claims failed: {e}"])
        except Exception:  # noqa: BLE001
            pass
        return 0


def run_and_persist(root: Path | None = None) -> dict:
    """ساخت + نوشتنِ اتمیک. خروجیِ کوچک برای لاگ/کورتکس."""
    model = build_model(root)
    try:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(MODEL_PATH) as lj:
            lj.write(model)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    claims_written = emit_self_claims(model)   # زیرِ فلگ؛ خاموش → صفر اثر، fail-soft
    return {"ok": True, "n_modules": model["n_modules"],
            "total_lines": model["total_lines"],
            "self_awareness_pct": model["self_awareness_pct"],
            "self_claims_written": claims_written}


if __name__ == "__main__":
    print(json.dumps(run_and_persist(), ensure_ascii=False, indent=2))
