#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scanner.py — چشمِ دکتر: خواندنِ ارگانیسمِ زنده ⟶ تولیدِ اسکن.

این تنها قطعه‌ای بود که واقعاً کم داشتیم. بدونِ آن دکتر **کور** است: حافظه دارد،
مغز دارد، دست دارد — ولی نمی‌تواند ببیند امروز چه خبر است.

**فقط‌خواندنی.** هیچ فایلی در `F:\\backup` نوشته یا لمس نمی‌شود.
خروجی dictی است که `ingest.ingest_scan()` مستقیم می‌خورد.

هر سنجه با **منشأ** و **رسید** بیرون می‌آید — نه عددِ لخت. این همان چیزی است که
`R-01` را قابل‌اجرا می‌کند: سنجهٔ درون‌زاد وارد می‌شود ولی رأی نمی‌دهد.

گامِ ۱۲ ِ UNIFICATION-DESIGN-2026-08-03 — سه چیز اضافه شد:

  ۱. **هر ردیفِ سنجه یک تمبرِ اصالت حمل می‌کند.** `_m()` خروجیِ
     `_ops/provenance.py::stamp()` را داخلِ همان ردیف merge می‌کند، پس هر عدد
     `source / observed_ts / age_s / cadence_s / dof / mode` را **اعلام** می‌کند.
     کلیدهای قدیمی (`value/provenance/receipt/status`) دست‌نخورده ماندند چون
     `ingest.ingest_scan()` دقیقاً همان چهارتا را می‌خواند — افزودن، نه تغییرِ نام.

  ۲. **`UNKNOWN` رنگِ سوم شد.** تا امروز منبعِ غایب به رنگِ ثابتِ همان خط
     می‌افتاد؛ سه ردیف ساختاراً **سبز** می‌شدند وقتی فایلشان اصلاً وجود نداشت
     (`fugu_used` سبزِ ثابت، `organism_stress` با `or 0` سبز، و
     `beat_budget_remaining` با `depleted=None` سبز). حالا `value is None`
     ⇒ رنگِ `⬜` و مقدارِ `[UNKNOWN]` — نه سبز و نه صفر.

  ۳. **تصادمِ نامِ «خودآگاهی» برداشته شد.** دو کمیتِ کاملاً بی‌ربط هم‌نام بودند:
     · `_octopus/state/octopus_state.json::status.self_awareness = "green"` —
       یک لفظِ منجمد از `2026-07-18T12:04:31`، صفر نویسنده و صفر خواننده.
     · `self_awareness_pct = 99.7` — که **پوششِ docstring** روی `_ops/` است و
       `_ops/cortex/self_model.py::build_model` می‌سازدش.
     سنجه‌ای که *این فایل* منتشر می‌کرد از `self_awareness_pct` به
     `docstring_coverage_pct` تغییرِ نام داد. کلیدِ داخلِ `self-model.json`
     **دست‌نخورده** ماند (۱۲+ خواننده در `_ops/`؛ تغییرش کارِ این lane نیست).
     لفظِ منجمد حالا ردیفِ خودش را دارد و `CONSTANT since …, N writers,
     N readers` رندر می‌شود، نه سبز.
"""
from __future__ import annotations

import ast, importlib.util, json, os, re, sqlite3, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

# منشأِ هر سنجه — یک‌بار اینجا تعریف می‌شود، نه پراکنده در کد
PROV = {
    "beat": ("درون‌زاد", "ORGANISM-STATE.json → beat"),
    "velocity_per_hr": ("درون‌زاد", "pulse/heart-signals-latest.json — ۹۶٪ متروَنوم"),
    "innervation_pct": ("درون‌زاد", "cortex/innervation-latest.json — file-freshness"),
    "docstring_coverage_pct": ("درون‌زاد",
                               "cortex/self-model.json → self_awareness_pct — پوششِ docstring"
                               " (نامِ قبلیِ این سنجه: self_awareness_pct)"),
    "control_plane_self_awareness": ("درون‌زاد",
                                     "_octopus/state/octopus_state.json → status.self_awareness"),
    "improvement_rate": ("درون‌زاد", "cortex/upgrades-digest.json"),
    "organism_stress": ("برون‌زاد", "cortex/stress-latest.json"),
    "confirmed_revenue": ("برون‌زاد", "fitness-latest.json → attribution.confirmed"),
    "memory_rows": ("برون‌زاد", "state/memory/memory.db → SELECT count(*)"),
    "suite": ("برون‌زاد", "_ops/tests/run_all.py → exit code + شمار"),
    "delta_self_raw": ("برون‌زاد", "pulse/heart-signals-latest.json → delta_self_raw"),
    "period_s": ("برون‌زاد", "ORGANISM-STATE.json → arbiter.effective_period_s"),
    "beat_budget_remaining": ("برون‌زاد", "state/cardiac-budget.json"),
    "fugu_used": ("برون‌زاد", "state/fugu-quota.json → used_total"),
    "alert_signatures": ("برون‌زاد", "governor/governor-alerts.md — امضای یکتا"),
}

#: ریتمِ **اعلام‌شدهٔ** هر ظرف بر حسبِ ثانیه. آینهٔ `_ops/cortex/registry.py::MEMBERS`
#: (`sla_s`) و `_ops/goal_action_bridge.py` برای `self-model.json`. مقدارِ `0.0`
#: یعنی «هیچ ریتمی اعلام نشده» — در آن حالت قاعدهٔ `HELD` ِ provenance خاموش است
#: و تنها چیزی که تمبر می‌تواند بگوید حضور/غیابِ `observed_ts` است.
#: ⚠️ این یک **آینه** است نه خوانشِ زنده؛ اگر `registry.py` عوض شود اینجا رانش می‌کند.
CADENCE_S = {
    "beat": 1800.0,                      # registry: organism / ORGANISM-STATE.json
    "period_s": 1800.0,                  # همان ظرف
    "beat_budget_remaining": 1800.0,     # همان ظرف (cardiac.budget)
    "velocity_per_hr": 3600.0,           # registry: producers / heart-signals-latest.json
    "delta_self_raw": 3600.0,            # همان ظرف
    "confirmed_revenue": 172800.0,       # registry: fitness / fitness-latest.json
    "docstring_coverage_pct": 7200.0,    # goal_action_bridge: self-model.json sla_s=7200
}

#: رنگ‌ها. تا امروز فقط 🔴/🟢 وجود داشت و «منبع نیست» به یکی از آن دو می‌افتاد.
COLOR_UNKNOWN = "⬜"     # منبع غایب یا ناخوانا — نه سبز، نه صفر
COLOR_CONSTANT = "🔒"    # ظرفِ بی‌نویسنده — عددش نمی‌تواند حرکت کند
UNKNOWN_VALUE = "[UNKNOWN]"

#: مسیرِ صفحهٔ کنترلِ منجمد، نسبت به والدِ `_ops`.
CONTROL_PLANE_REL = ("_octopus", "state", "octopus_state.json")

# ── شمارشِ ارجاع‌های کدی ────────────────────────────────────────────────────
#: دامنهٔ اعلام‌شدهٔ شمارش. عدد فقط داخلِ همین دامنه معنا دارد و در رسید می‌آید.
REF_ROOTS = ("_ops", "_octopus", "OCTOPUS-DOCTOR")
REF_SUFFIXES = (".py", ".ps1", ".cmd", ".bat", ".js", ".mjs", ".ts")
#: `tests` عمداً اینجاست: شمارش دنبالِ **خوانندهٔ تولیدی** است. فیکسچرِ یک تست
#: که همان ظرف را می‌سازد تا رفتارِ اسکنر را بسنجد، نویسندهٔ آن ظرف نیست — و
#: اگر شمرده شود، خودِ این اسکنر با افزودنِ تستش عددِ خودش را عوض می‌کند
#: (آرتیفکتِ خودساخته؛ دقیقاً همین یک‌بار در ۰۸-۰۳ اتفاق افتاد و گرفته شد).
REF_SKIP_DIRS = {".git", ".claude", "__pycache__", "node_modules", "venv", ".venv",
                 "_Archive", "_Duplicates", "_code", "site-packages", ".pytest_cache",
                 "tests"}
REF_SKIP_FILE_PREFIXES = ("test_", "S1-", "conftest")
REF_MAX_FILES = 6000
REF_MAX_BYTES = 2_000_000
_WRITE_HINT = re.compile(r"open\s*\(|write_text|write_bytes|\.write\s*\(|json\.dump|"
                         r"os\.replace|shutil\.|Set-Content|Out-File|Add-Content")
_COMMENT_LINE = re.compile(r"^\s*(#|//|::|REM\b|rem\b|\*|>)")

_NUM = re.compile(r"\d+")


def _j(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def load_provenance(ops: str | Path):
    """`provenance.py` را از **همان درختی که اسکن می‌شود** بارگذاری می‌کند.

    عمداً هیچ fallbackِ `sys.path` ی ندارد و عمداً هیچ نسخهٔ محلی از قواعدِ
    `LIVE/HELD/CONSTANT/UNKNOWN` اینجا نیست: اگر ماژول نبود، هر ردیف صادقانه
    `mode=UNKNOWN, reason='provenance-module-absent'` می‌گیرد. یک پیاده‌سازیِ
    دومِ همان قواعد دقیقاً همان «منبعِ حقیقتِ دوم»ی است که این طرح ممنوع کرده.
    """
    p = Path(ops) / "provenance.py"
    if not p.exists():
        return None
    # ⚠️ `exec_module` به‌طور پیش‌فرض `<ops>/__pycache__/provenance.*.pyc` را
    # **می‌نویسد** — یعنی همین اسکنِ «فقط‌خواندنی» یک بایت در درختِ ارگانیسم
    # می‌گذاشت. تستِ ایزوله همین را گرفت.
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("_doctor_provenance", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)          # noqa: S102 — سورسِ خودِ ارگانیسم
    except Exception:                          # noqa: BLE001
        return None
    finally:
        sys.dont_write_bytecode = old
    return mod if hasattr(mod, "stamp") and hasattr(mod, "Mode") else None


def _no_stamp(source: str, cadence: float, writer: str, reason: str) -> dict:
    """تمبرِ جانشین وقتی ماژولِ provenance در دسترس نیست — همان شکل، بدونِ ادعا."""
    return {"source": source, "observed_ts": None, "age_s": None,
            "cadence_s": cadence, "last_change_ts": None, "dof": 0,
            "mode": "UNKNOWN", "writer": writer, "reason": reason}


def _m(name: str, value, status: str = "", extra: str = "", *,
       P=None, observed_ts=None, history=None, writer: str = "") -> dict:
    """یک ردیفِ سنجه: کلیدهای قدیمی + تمبرِ اصالت.

    `value/provenance/receipt/status` عمداً همان‌هایی هستند که
    `ingest.ingest_scan()` می‌خواند؛ بقیه **افزوده**اند. تمبر هرگز `value` را
    تعیین نمی‌کند (`stamp()` روی UNKNOWN اصلاً کلیدِ `value` ندارد) — مقدار را
    دکتر می‌گذارد تا نبودِ منبع به `[UNKNOWN]` برود نه به یک صفرِ بی‌صدا.
    """
    prov, receipt = PROV.get(name, ("نامعلوم", ""))
    cadence = float(CADENCE_S.get(name, 0.0))
    source = receipt or name
    if P is None:
        row = _no_stamp(source, cadence, writer, "provenance-module-absent")
    else:
        row = dict(P.stamp(value, source, observed_ts, cadence,
                           history=history, writer=writer))
        row.pop("value", None)             # مقدار کارِ دکتر است، نه تمبر
    if value is None:                      # منبع غایب/ناخوانا ⇒ رنگِ سوم
        status = COLOR_UNKNOWN
        value = UNKNOWN_VALUE
        row["reason"] = "source-missing"
    bits = [b for b in (extra, f"mode={row.get('mode')}") if b]
    if row.get("reason"):
        bits.append(f"reason={row['reason']}")
    tail = " · ".join(bits)
    row.update({"value": value, "provenance": prov,
                "receipt": (receipt + (" · " + tail if tail else "")) or None,
                "status": status})
    return row


# ── ارجاع‌های کدی به یک نامِ فایل ───────────────────────────────────────────
def _py_ref_lines(src: str, needle: str):
    """شماره‌خطِ ارجاع‌های **کدی** به `needle` — docstring و کامنت حساب نمی‌شوند.

    درسِ ثبت‌شدهٔ این vault: «grep کامنت را می‌شمارد». ماژولی که فقط در
    docstringش اسمِ یک ظرف را برده خوانندهٔ آن ظرف نیست.
    برمی‌گرداند `None` اگر فایل پارس نشود — نامعلوم، نه صفر.
    """
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    docs = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and body:
            first = body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                docs.add(id(first.value))
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and needle in node.value and id(node) not in docs):
            out.append(getattr(node, "lineno", 0))
    return out


def _text_ref_lines(src: str, needle: str):
    """همان، برای فایلِ غیرِ پایتون: خطِ کامنت حساب نمی‌شود."""
    return [i for i, line in enumerate(src.splitlines(), 1)
            if needle in line and not _COMMENT_LINE.match(line)]


def count_code_refs(root: str | Path, needle: str, exclude: set[str] | None = None) -> dict:
    """چند فایلِ **کد** به `needle` ارجاع می‌دهند، و چندتاشان می‌نویسند.

    دامنه صریح و اعلام‌شده است (`REF_ROOTS` × `REF_SUFFIXES`) و در رسید می‌آید،
    پس عدد ابطال‌پذیر است. اگر اسکن به سقف بخورد `truncated=True` و
    `writers/readers = None` — «اسکنی که به سقف خورده عدد تولید نمی‌کند».
    """
    root = Path(root)
    skip = set(exclude or ())
    writers = readers = files = unparsed = 0
    truncated = False
    for top in REF_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in REF_SKIP_DIRS]
            for fn in filenames:
                if not fn.endswith(REF_SUFFIXES):
                    continue
                if fn.startswith(REF_SKIP_FILE_PREFIXES):
                    continue          # فیکسچرِ تست خوانندهٔ تولیدی نیست
                p = Path(dirpath) / fn
                if str(p.resolve()) in skip:
                    continue          # ناظر هرگز خودش را «خواننده» نمی‌شمارد
                if files >= REF_MAX_FILES:
                    truncated = True
                    break
                files += 1
                try:
                    if p.stat().st_size > REF_MAX_BYTES:
                        continue
                    src = p.read_text("utf-8", errors="replace")
                except OSError:
                    continue
                if needle not in src:
                    continue
                lines = _py_ref_lines(src, needle) if fn.endswith(".py") \
                    else _text_ref_lines(src, needle)
                if lines is None:
                    unparsed += 1
                    continue
                if not lines:
                    continue
                body = src.splitlines()
                wrote = any(_WRITE_HINT.search(body[n - 1])
                            for n in lines if 0 < n <= len(body))
                writers += 1 if wrote else 0
                readers += 0 if wrote else 1
            if truncated:
                break
        if truncated:
            break
    return {"writers": None if truncated else writers,
            "readers": None if truncated else readers,
            "files_scanned": files, "unparsed": unparsed, "truncated": truncated,
            "scope": f"{'+'.join(REF_ROOTS)} × {','.join(REF_SUFFIXES)}"}


def control_plane_row(ops: str | Path, P=None) -> dict:
    """ردیفِ `_octopus/state/octopus_state.json::status.self_awareness`.

    این لفظ از `2026-07-18T12:04:31` تکان نخورده و **هیچ کدی** — نه نویسنده و
    نه خواننده — به فایلش ارجاع نمی‌دهد. تا امروز هیچ سطحی این را منتشر نمی‌کرد؛
    اگر می‌کرد، `"green"` را به‌عنوان یک سبزِ عادی نشان می‌داد و هرگز قرمز
    نمی‌شد چون چیزی نیست که قرمزش کند.

    **چرا حالتش از `stamp()` نمی‌آید (تفاوتِ سنجیده‌شده با متنِ طرح):**
    قاعدهٔ `CONSTANT` در `provenance.stamp()` شرطِ `cadence_s > 0` دارد — یعنی
    ظرفی که *تازه می‌شود* ولی مقدارش تکان نمی‌خورد (مثالِ طرح: `control_law`).
    ظرفی با **صفر نویسنده** اصلاً ریتم ندارد؛ با هر cadenceِ اعلامی یا `HELD`
    می‌شود یا `LIVE`، و `LIVE` دقیقاً همان دروغی است که این ردیف باید بکشد.
    پس حالتِ منتشرشده از یک قاعدهٔ **جدا و سنجیدنی** می‌آید — «صفر نویسنده ⇒
    نمی‌تواند حرکت کند ⇒ CONSTANT» — و حالتِ خامِ تمبر در همان ردیف زیرِ
    `stamp_mode` می‌ماند تا اختلاف پنهان نشود.
    """
    root = Path(ops).parent
    path = root.joinpath(*CONTROL_PLANE_REL)
    doc = _j(path)
    rel = "/".join(CONTROL_PLANE_REL)
    if not doc:
        return _m("control_plane_self_awareness", None, extra=f"{rel} خوانده نشد", P=P)

    raw = (doc.get("status") or {}).get("self_awareness")
    created, updated = doc.get("created_at"), doc.get("updated_at")
    refs = count_code_refs(root, CONTROL_PLANE_REL[-1],
                           exclude={str(Path(__file__).resolve())})
    if refs["truncated"]:
        return _m("control_plane_self_awareness", None,
                  extra=f"شمارشِ ارجاع به سقفِ {REF_MAX_FILES} فایل خورد", P=P)

    hist = [(t, raw) for t in (created, updated) if t]
    row = _m("control_plane_self_awareness", raw, "🔴",
             extra=f"refs scope={refs['scope']} · files={refs['files_scanned']}",
             P=P, observed_ts=updated, history=hist or None, writer="(هیچ)")
    w, r = refs["writers"], refs["readers"]
    row["writers"], row["readers"] = w, r
    row["raw_value"] = raw
    row["ref_scan"] = refs
    if w == 0 and updated:
        row["stamp_mode"] = row.get("mode")
        row["mode"] = "CONSTANT"
        row["mode_rule"] = "zero-writers"
        row["constant_since"] = updated
        row["status"] = COLOR_CONSTANT
        row["value"] = f"CONSTANT since {updated}, {w} writers, {r} readers"
    return row


def scan(ops: str | Path, run_suite: bool = False) -> dict:
    """اسکنِ فقط‌خواندنیِ `_ops/`. `run_suite=True` سوئیت را هم اجرا می‌کند (~۳ دقیقه)."""
    O = Path(ops)
    S = O / "state"
    P = load_provenance(O)
    out: dict = {"date": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"),
                 "metrics": {}, "findings": [], "unknown": []}
    M = out["metrics"]
    if P is None:
        out["unknown"].append(
            "provenance.py در درختِ اسکن‌شده نیست — هر تمبر UNKNOWN است")

    org = _j(S / "ORGANISM-STATE.json")
    if not org:
        out["unknown"].append("ORGANISM-STATE.json خوانده نشد — ارگانیسم خاموش است؟")
        return out

    # ⚠️ ناوردیِ ۴ ِ provenance: `ts` ِ **سطحِ بالای** ORGANISM-STATE تازگیِ هیچ
    # کلیدی را اثبات نمی‌کند (مسیرِ `merge_prev` در `organism.py::_write_state`
    # کلیدِ غایب را back-fill می‌کند و هم‌زمان `ts` را جلو می‌برد). پس عمداً
    # `observed_in` روی **خودِ زیرمقدار** صدا زده می‌شود؛ اگر آنجا نباشد، تمبر
    # صادقانه UNKNOWN می‌شود.
    _in = (lambda d: P.observed_in(d)) if P else (lambda d: None)

    out["beat"] = org.get("beat")
    M["beat"] = _m("beat", org.get("beat"), P=P, observed_ts=None,
                   writer="organism.py::_write_state")

    arb = org.get("arbiter") or {}
    bio = ((org.get("cardiac") or {}).get("bio_rhythm") or {})
    per = arb.get("effective_period_s")
    M["period_s"] = _m("period_s", per,
                       "🔴" if arb.get("driver", "").startswith("brake") else "🟢",
                       f"driver={arb.get('driver')} · bio={bio.get('period_s')}",
                       P=P, observed_ts=_in(arb), writer="organism.py::_write_state")
    if str(arb.get("driver", "")).startswith("brake"):
        out["findings"].append({
            "id": "F-AUTO-BRAKE", "title": "قلب ترمز خورده", "status": "🔴",
            "body": f"`effective_period_s={per}` با راننده `{arb.get('driver')}` "
                    f"در حالی که ریتمِ زیستی `{bio.get('period_s')}` است."})

    bud = (org.get("cardiac") or {}).get("budget") or _j(S / "cardiac-budget.json")
    rem = bud.get("remaining")
    M["beat_budget_remaining"] = _m("beat_budget_remaining", rem,
                                    "🔴" if bud.get("depleted") else "🟢",
                                    f"spent={bud.get('spent')}/{bud.get('daily_cap')}",
                                    P=P, observed_ts=_in(bud))

    hs = _j(S / "pulse" / "heart-signals-latest.json")
    hs_ts = _in(hs)
    vel = (hs.get("velocity") or {})
    share = vel.get("metronome_share")
    M["velocity_per_hr"] = _m("velocity_per_hr", vel.get("velocity_per_hr"),
                              "🔴" if (share or 0) > 0.9 else "🟡",
                              f"metronome_share={share}",
                              P=P, observed_ts=_in(vel) or hs_ts,
                              writer="heart/producers.compute_all")
    ds = (hs.get("delta_self") or {})
    raw = ds.get("delta_self_raw")
    M["delta_self_raw"] = _m("delta_self_raw", raw, "🔴" if (raw or 0) < 0 else "🟢",
                             f"S_blind={ds.get('S_blind')} S_informed={ds.get('S_informed')}",
                             P=P, observed_ts=_in(ds) or hs_ts,
                             writer="heart/producers.compute_all")
    if raw is not None and raw < 0:
        # اتهامِ clamp فقط وقتی معتبر است که عددِ منتشرشده با خام فرق کند؛
        # اسکنِ 07-29 با raw==live هم همین قالب را چاپ می‌کرد و فیکسِ 07-25
        # (publish_signed) را کتمان می‌کرد — یافتهٔ درست، تشخیصِ غلط.
        live = ds.get("delta_self_live")
        try:
            clamped = live is not None and float(live) != float(raw)
        except (TypeError, ValueError):
            clamped = False
        body = (f"`delta_self_raw={raw}` ولی `delta_self_live={live}` منتشر "
                f"می‌شود — clamp، خلافِ [[R-02]]." if clamped else
                f"`delta_self_raw={raw}` و همان عدد صادقانه منتشر می‌شود "
                f"(R-02 ✅)؛ مسئله خودِ منفی‌بودن است — مدلِ خودی از پیش‌بینِ "
                f"کور بدتر پیش‌بینی می‌کند.")
        out["findings"].append({
            "id": "F-AUTO-DELTASELF", "title": "خودشناسیِ منفی", "status": "🔴",
            "body": body})

    st = _j(S / "cortex" / "stress-latest.json")
    M["organism_stress"] = _m("organism_stress", st.get("organism_stress"),
                              "🔴" if (st.get("organism_stress") or 0) >= 0.9 else "🟢",
                              f"in_fear={st.get('in_fear')}",
                              P=P, observed_ts=_in(st))

    inn = _j(S / "cortex" / "innervation-latest.json")
    M["innervation_pct"] = _m("innervation_pct", inn.get("coverage_pct"), "🔴",
                              P=P, observed_ts=_in(inn))

    # ⚠️ کلیدِ داخلِ فایل هنوز `self_awareness_pct` است و عمداً تغییر نکرد
    # (`_ops/cortex/self_model.py::build_model` می‌نویسدش، ۱۲+ خواننده). فقط
    # نامِ سنجه‌ای که *دکتر* منتشر می‌کند عوض شد تا با لفظِ منجمدِ صفحهٔ کنترل
    # اشتباه گرفته نشود. این کمیت پوششِ docstring است، نه خودآگاهی.
    sm = _j(S / "cortex" / "self-model.json")
    M["docstring_coverage_pct"] = _m("docstring_coverage_pct",
                                     sm.get("self_awareness_pct"), "🔴",
                                     P=P, observed_ts=_in(sm),
                                     writer="cortex/self_model.build_model")

    # لفظِ منجمدِ صفحهٔ کنترل — همان کمیتی که تا امروز با بالایی هم‌نام بود
    M["control_plane_self_awareness"] = cp = control_plane_row(O, P)
    if cp.get("mode") == "CONSTANT":
        out["findings"].append({
            "id": "F-AUTO-FROZEN-CONTROL-PLANE",
            "title": "سبزی که هرگز قرمز نمی‌شود", "status": "🔴",
            "body": f"`{'/'.join(CONTROL_PLANE_REL)} → status.self_awareness` "
                    f"مقدارِ `{cp.get('raw_value', 'green')}` را از "
                    f"`{cp.get('constant_since')}` نگه داشته و **هیچ کدی** آن را "
                    f"نه می‌نویسد و نه می‌خواند "
                    f"({cp.get('writers')} نویسنده / {cp.get('readers')} خواننده در "
                    f"`{(cp.get('ref_scan') or {}).get('scope')}`). چیزی وجود ندارد "
                    f"که بتواند قرمزش کند، پس سبزبودنش اطلاعات ندارد."})

    fit = _j(S / "fitness-latest.json")
    M["confirmed_revenue"] = _m("confirmed_revenue",
                                (fit.get("attribution") or {}).get("confirmed"),
                                "🔴" if not (fit.get("attribution") or {}).get("confirmed") else "🟢",
                                P=P, observed_ts=_in(fit))

    fq = _j(S / "fugu-quota.json")
    M["fugu_used"] = _m("fugu_used", fq.get("used_total"), "🟢",
                        P=P, observed_ts=_in(fq))

    # حافظه — شمارِ واقعی، نه ادعا
    mdb = S / "memory" / "memory.db"
    if mdb.exists():
        try:
            c = sqlite3.connect(f"file:{mdb}?mode=ro", uri=True)
            n = c.execute("select count(*) from memory").fetchone()[0]
            c.close()
            M["memory_rows"] = _m("memory_rows", n, "🔴" if n < 10 else "🟢", P=P)
            if n < 10:
                out["findings"].append({
                    "id": "F-AUTO-MEMORY", "title": "حافظهٔ بلندمدت تقریباً خالی",
                    "status": "🔴", "body": f"جدولِ `memory` فقط **{n} سطر** دارد."})
        except sqlite3.Error as e:
            out["unknown"].append(f"memory.db خوانده نشد: {e}")
    else:
        out["unknown"].append("memory.db وجود ندارد")

    # هشدارهای تکراری — امضا، نه تعداد خام
    ga = O / "governor" / "governor-alerts.md"
    if ga.exists():
        try:
            lines = [l for l in ga.read_text("utf-8", errors="replace").splitlines()
                     if l.strip().startswith("- ")]
            sigs: dict[str, int] = {}
            for l in lines:
                k = _NUM.sub("N", l)[:90]
                sigs[k] = sigs.get(k, 0) + 1
            top = sorted(sigs.items(), key=lambda x: -x[1])[:5]
            # این فایل هیچ `ts` ِ درونی ندارد؛ عمداً `Mtime` داده می‌شود تا
            # تمبر صادقانه `UNKNOWN/mtime-only` شود، نه اینکه mtime به‌جای
            # تازگی جا بزند (ناوردیِ ۳ ِ provenance).
            mt = P.Mtime(ga.stat().st_mtime) if P else None
            M["alert_signatures"] = _m("alert_signatures", len(sigs),
                                       "🔴" if top and top[0][1] > 50 else "🟢",
                                       f"{len(lines)} خط، پرتکرارترین ×{top[0][1] if top else 0}",
                                       P=P, observed_ts=mt)
            for sig, n in top:
                if n > 50:
                    out["findings"].append({
                        "id": f"F-AUTO-ALERT-{abs(hash(sig)) % 1000}",
                        "title": f"هشدارِ تکراری ×{n}", "status": "🔴",
                        "body": f"```\n{sig.strip()}\n```\nیک امضا، **{n}** بار."})
        except OSError as e:
            out["unknown"].append(f"governor-alerts خوانده نشد: {e}")

    if run_suite:
        try:
            r = subprocess.run(["python", "-X", "utf8", str(O / "tests" / "run_all.py")],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=900, cwd=str(O.parent))
            n = None
            for l in (r.stdout or "").splitlines()[-30:]:
                mm = re.search(r"(\d+)\s*فایل تست", l) or re.search(r"(\d+)\s*passed", l)
                if mm:
                    n = int(mm.group(1))
            out["suite"] = f"{n}/{n}" if (n and r.returncode == 0) else f"exit={r.returncode}"
            M["suite"] = _m("suite", out["suite"], "🟢" if r.returncode == 0 else "🔴",
                            P=P, observed_ts=datetime.now(timezone.utc).timestamp())
        except Exception as e:                                   # noqa: BLE001
            out["unknown"].append(f"سوئیت اجرا نشد: {type(e).__name__}")
    else:
        out["unknown"].append("سوئیت اجرا نشد (run_suite=False) — عددِ تست [UNKNOWN]")

    try:
        g = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(O.parent),
                           capture_output=True, text=True, timeout=20)
        if g.returncode == 0:
            out["branch"] = g.stdout.strip()
    except Exception:                                            # noqa: BLE001
        pass
    return out


if __name__ == "__main__":
    print(json.dumps(scan(sys.argv[1] if len(sys.argv) > 1 else r"F:\backup\_ops"),
                     ensure_ascii=False, indent=2))
