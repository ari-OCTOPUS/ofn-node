#!/usr/bin/env python3
"""self_insight — لایه‌ای که از **یافته** به **فرضیه** می‌رسد، و بعد نمرهٔ خودش را می‌دهد.

تفاوت با یک linter
──────────────────
`self_scan` فهرست می‌دهد: «۳۷ فلگ تعریف‌نشده، ۴ فایلِ تک‌ارجاع، ۴۹ نمادِ مرده».
یک فهرست هرچقدر هم دقیق، تصمیم تولید نمی‌کند — چون نمی‌گوید کدام‌یک **مهم** است،
چرا، و چه چیزی ثابت می‌کند اشتباه است.

این ماژول سه کارِ دیگر می‌کند که یک فهرست نمی‌کند:

 ۱. **پیوند می‌زند.** یک فلگِ تاریک + ماژولِ بی‌تستِ همان + فایلِ stateِ بی‌مصرفِ
    همان = **یک** داستان، نه سه یافته. زنجیرهٔ علّی ساخته می‌شود.
 ۲. **پیش‌بینی می‌کند.** هر فرضیه یک `predicted_observation`ِ ماشین‌خوان دارد:
    «اگر این را درست کنی، فلانی از فلان فهرست ناپدید می‌شود».
 ۳. **نمرهٔ خودش را می‌دهد.** اجرای بعدی پیش‌بینی‌های قبلی را می‌سنجد و
    calibration گزارش می‌کند: از N پیش‌بینی، M تا درست بود.

بندِ ۳ همان چیزی است که این را از «گزارش» جدا می‌کند. سیستمی که پیش‌بینی
می‌کند ولی هرگز نمرهٔ خودش را نمی‌بیند، فقط دارد با اطمینان حرف می‌زند.
این همان قاعدهٔ دفترِ تز است، این‌بار روی خودِ ابزارِ تشخیص.

رتبه‌بندی: `rank = impact × confidence ÷ cost`. هیچ‌کدام از سه عامل پنهان
نمی‌شود؛ هر سه در خروجی می‌آیند تا بشود با عددِ مالک مخالفت کرد.

ناوردی‌ها: فقط‌خواندنی روی کد · تنها نوشتنش ژورنالِ خودش است · fail-soft.

اجرا:
    python _ops/self_insight.py             # کارت
    python _ops/self_insight.py --json
    python _ops/self_insight.py --no-journal
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SCHEMA = "self-insight.v1"
CARD_TITLE = "بینش — از یافته تا فرضیه"
JOURNAL = "self-insight.jsonl"
JOURNAL_CAP = 400

COST = {"cheap": 1.0, "medium": 2.5, "expensive": 6.0}


def _h(rule, subject, claim, mechanism, predicted, falsifier,
       confidence, why, impact, cost, test):
    """یک فرضیه. هیچ فیلدی اختیاری نیست — یک ادعا بدونِ ابطال‌کننده وارد نمی‌شود."""
    return {
        "id": f"{rule}:{subject}",
        "rule": rule, "subject": subject,
        "claim": claim, "mechanism": mechanism,
        "predicted_observation": predicted,      # ماشین‌خوان، برای نمره‌دهی
        "falsifier": falsifier,
        "confidence": round(float(confidence), 2), "confidence_why": why,
        "impact": int(impact), "cost": cost,
        "rank": round(impact * float(confidence) / COST.get(cost, 2.5), 3),
        "cheapest_test": test,
    }


# ══════════════════════════════════════════════════════════════════════════
#  قواعد — هر کدام تابعی خالص روی خروجیِ self_scan
# ══════════════════════════════════════════════════════════════════════════

def rule_silent_default(scan) -> list:
    """فلگی که تعریف نشده ولی کد پیش‌فرضی برایش دارد.

    این بدترین نوعِ تاریکی است: رفتار **همین حالا روشن یا خاموش است** و مالک
    هرگز رأی نداده. برخلافِ فلگِ مسلحِ بی‌خواننده که فقط بی‌اثر است.
    """
    f = scan.get("checks", {}).get("flags", {}) or {}
    defaults = f.get("defaults") or {}
    out = []
    for flag, uses in defaults.items():
        d = uses[0].get("default")
        mods = sorted({u["module"] for u in uses})
        # نسخهٔ اول هر پیش‌فرضی را بولی فرض می‌کرد و `'3600'` را «خاموش»
        # می‌خواند. یک ادعای صریحاً غلط دربارهٔ یک مدت‌زمان. سه دسته لازم است:
        v = str(d).strip().lower()
        if v in ("1", "true", "yes", "on"):
            state, impact = "روشن", 4          # رفتاری فعال که تأیید نشده
        elif v in ("0", "false", "no", "off", ""):
            state, impact = "خاموش", 2
        else:
            state, impact = f"با مقدارِ {d!r}", 3   # پیکربندیِ بی‌رأی
        conf = 0.9 if len(mods) == 1 else 0.75
        out.append(_h(
            "silent_default", flag,
            f"«{flag}» در هیچ‌کجای flags.cmd نیست، ولی کد پیش‌فرضِ {d!r} دارد — "
            f"یعنی این رفتار همین حالا {state} است و رأیی داده نشده.",
            [f"{m} → os.environ.get({flag!r}, {d!r})" for m in mods],
            {"check": "flags.read_unarmed", "absent": flag},
            f"اگر {flag} در flags.cmd اعلام شود (با هر مقداری) این فرضیه بسته می‌شود.",
            conf,
            f"پیش‌فرض مستقیم از AST خوانده شد، نه حدس؛ {len(mods)} مصرف‌کننده",
            impact, "cheap",
            f'یک خط به OCTOPUS-flags.cmd: @set "{flag}={d or 0}"'))
    return out


def rule_starved_consumer(scan) -> list:
    """فایلی که نوشته می‌شود و هیچ‌کس نمی‌خواندش."""
    st = scan.get("checks", {}).get("state", {}) or {}
    out = []
    for row in (st.get("single_referencer") or []):
        by = row.get("by") or []
        size = row.get("bytes") or 0
        impact = 4 if size > 10_000 else 3 if size > 1_000 else 2
        out.append(_h(
            "starved_consumer", row["file"],
            f"«{row['file']}» ({size:,} بایت) فقط در {', '.join(by)} نامش می‌آید — "
            "یعنی نویسنده دارد و مصرف‌کننده ندارد.",
            [f"{by[0] if by else '?'} می‌نویسد", "هیچ ماژولِ دیگری نامش را نمی‌برد"],
            {"check": "state.single_referencer", "absent": row["file"]},
            "کافی است یک ماژولِ دیگر نامش را ببرد (مصرفش کند) تا بسته شود. "
            "اگر نامش پویا ساخته شود، این فرضیه از اول غلط بوده.",
            0.7, "ارجاعِ ایستا؛ نامِ ساخته‌شده با f-string دیده نمی‌شود",
            impact, "medium",
            f"rg -n '{Path(row['file']).name}' _ops --type py"))
    return out


def rule_blast_radius(scan) -> list:
    """ماژولِ بی‌تستی که خیلی‌ها به آن وابسته‌اند."""
    t = scan.get("checks", {}).get("tests", {}) or {}
    out = []
    for row in (t.get("untested") or []):
        fan = int(row.get("fan_in") or 0)
        if fan < 3:
            continue
        out.append(_h(
            "blast_radius", row["module"],
            f"«{row['module']}» ({row['lines']} خط) هیچ تستی نامش را نمی‌برد، "
            f"ولی {fan} ماژول به آن ارجاع دارند.",
            [f"fan-in = {fan}", "پوششِ تست = صفر"],
            {"check": "tests.untested", "absent": row["module"]},
            "یک تست که نامش را import کند این را می‌بندد — "
            "ولی «اشاره‌شده» با «تست‌شده» یکی نیست.",
            min(0.95, 0.5 + fan * 0.05),
            f"شواهدِ مستقل: fan-in={fan}", min(5, 2 + fan // 3), "medium",
            f"python _ops/self_scan.py --only tests --json"))
    return out


def rule_ghost_flag(scan) -> list:
    """فلگی که مسلح است و هیچ کدی نمی‌خواندش."""
    f = scan.get("checks", {}).get("flags", {}) or {}
    ghosts = f.get("armed_unread") or []
    if not ghosts:
        return []
    # عمداً یک فرضیهٔ جمعی، نه N تا: علتشان معمولاً یکی است (کدِ حذف‌شده یا
    # تغییرِ نام)، و N اخطارِ جدا فقط کارت را می‌ترکاند.
    return [_h(
        "ghost_flag", "armed_unread",
        f"{len(ghosts)} فلگ در flags.cmd مسلح‌اند که هیچ خطِ کدی نمی‌خواندشان.",
        ["یا کدشان حذف شده", "یا نامشان غلط تایپ شده", "در هر دو حالت بی‌اثر"],
        {"check": "flags.armed_unread", "count_below": max(0, len(ghosts) - 1)},
        "روی یک درختِ ناقص این عدد بی‌معناست — اول روی درختِ کامل اجرا کن. "
        "و فلگی که نامش در کد ساخته می‌شود این‌جا دیده نمی‌شود.",
        0.45, "روی درختِ ناقص اندازه گرفته شد؛ اطمینان عمداً پایین است",
        2, "cheap",
        "python _ops/self_scan.py --only flags --json  # روی درختِ کامل")]


def rule_dead_cluster(scan) -> list:
    """ماژولی که چند نمادِ مردهٔ بزرگ در آن جمع شده."""
    y = scan.get("checks", {}).get("symbols", {}) or {}
    per: dict = {}
    for d in (y.get("dead") or []):
        per.setdefault(d["file"], []).append(d)
    out = []
    for file, items in per.items():
        if len(items) < 3:
            continue
        lines = sum(i["lines"] for i in items)
        out.append(_h(
            "dead_cluster", file,
            f"«{file}» {len(items)} نمادِ عمومیِ بی‌مصرف دارد ({lines} خط) — "
            "احتمالاً بخشی از آن ماژول هرگز اجرا نمی‌شود.",
            [f"{i['symbol']} ({i['lines']} خط)" for i in items[:5]],
            {"check": "symbols.dead", "file_count_below": len(items)},
            "فراخوانیِ پویا (getattr / رجیستری / رشته) این را باطل می‌کند — "
            "هر نماد باید دستی تأیید شود، نه دسته‌جمعی حذف.",
            0.5, "اکتشافی؛ فراخوانیِ پویا دیده نمی‌شود",
            3, "expensive",
            f"rg -n 'getattr|registry|globals\\\\(\\\\)' {file}"))
    return out


RULES = (rule_silent_default, rule_starved_consumer, rule_blast_radius,
         rule_ghost_flag, rule_dead_cluster)


# ══════════════════════════════════════════════════════════════════════════
#  حافظه و نمره‌دهیِ خود
# ══════════════════════════════════════════════════════════════════════════

def _checkable(pred, scan) -> "bool | None":
    """آیا پیش‌بینی الان برقرار است؟ None = نمی‌شود سنجید."""
    try:
        path = str(pred.get("check", "")).split(".")
        node = scan.get("checks", {})
        for part in path:
            node = node[part]
        if "absent" in pred:
            target = pred["absent"]
            if isinstance(node, list):
                flat = [x.get("flag") or x.get("module") or x.get("file")
                        if isinstance(x, dict) else x for x in node]
                return target not in flat
            return target not in node
        if "count_below" in pred:
            n = len(node) if isinstance(node, (list, dict)) else int(node)
            return n <= int(pred["count_below"])
        if "file_count_below" in pred:
            return None
    except (KeyError, TypeError, ValueError):
        return None
    return None


def score_previous(scan, journal_path) -> dict:
    """پیش‌بینی‌های اجرای قبل را می‌سنجد. این بند، ماژول را از «گزارش» جدا می‌کند."""
    prev = []
    try:
        p = Path(journal_path)
        if p.exists():
            rows = [json.loads(l) for l in
                    p.read_text(encoding="utf-8").splitlines() if l.strip()]
            if rows:
                prev = rows[-1].get("hypotheses") or []
    except Exception:  # noqa: BLE001
        prev = []
    resolved, still_open, unmeasurable = [], [], []
    for h in prev:
        v = _checkable(h.get("predicted_observation") or {}, scan)
        (resolved if v is True else still_open if v is False
         else unmeasurable).append(h["id"])
    measured = len(resolved) + len(still_open)
    return {
        "previous_hypotheses": len(prev),
        "resolved": resolved, "still_open": still_open,
        "unmeasurable": unmeasurable,
        "measured": measured,
        "resolution_rate": round(len(resolved) / measured, 3) if measured else None,
        "note": "«حل‌شده» یعنی پیش‌بینی محقق شد، نه اینکه لزوماً کسی به‌خاطرِ "
                "این گزارش کاری کرد. همبستگی، نه علیت.",
    }


def run(root=None, journal=True) -> dict:
    root = Path(root) if root else Path(__file__).resolve().parent
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import self_scan as ss

    t0 = time.time()
    scan = ss.run(root)
    hyps, errors = [], {}
    for rule in RULES:
        try:
            hyps.extend(rule(scan))
        except Exception as exc:  # noqa: BLE001 — یک قاعدهٔ شکسته بقیه را نمی‌کشد
            errors[rule.__name__] = f"{type(exc).__name__}: {exc}"
    hyps.sort(key=lambda h: -h["rank"])

    jpath = Path(root) / "state" / JOURNAL
    calib = score_previous(scan, jpath)
    out = {
        "schema": SCHEMA, "ts": time.time(),
        "elapsed_s": round(time.time() - t0, 2),
        "corpus": scan.get("corpus"),
        "hypotheses": hyps,
        "counts": {"total": len(hyps),
                   "by_rule": {r.__name__: sum(1 for h in hyps
                                               if h["rule"] == r.__name__.replace("rule_", ""))
                               for r in RULES}},
        "calibration": calib,
        "rule_errors": errors,
    }
    if journal:
        try:
            jpath.parent.mkdir(parents=True, exist_ok=True)
            rows = []
            if jpath.exists():
                rows = [l for l in jpath.read_text(encoding="utf-8").splitlines()
                        if l.strip()][-(JOURNAL_CAP - 1):]
            rows.append(json.dumps(
                {k: out[k] for k in ("schema", "ts", "hypotheses", "calibration")},
                ensure_ascii=False))
            jpath.write_text("\n".join(rows) + "\n", encoding="utf-8")
            out["journal"] = str(jpath)
        except Exception as exc:  # noqa: BLE001
            out["journal_error"] = f"{type(exc).__name__}: {exc}"
    return out


def card(root=None, top=6) -> str:
    r = run(root, journal=False)
    c = r["calibration"]
    lines = ["🧠 بینش — از یافته تا فرضیه", ""]
    if c["previous_hypotheses"]:
        rr = c["resolution_rate"]
        lines.append(
            f"📊 نمرهٔ خودم از اجرای قبل: {len(c['resolved'])} از {c['measured']} "
            f"پیش‌بینیِ سنجیدنی محقق شد"
            + (f" ({rr:.0%})" if rr is not None else "")
            + (f"، {len(c['unmeasurable'])} سنجیدنی نبود" if c["unmeasurable"] else ""))
    else:
        lines.append("📊 اولین اجراست — هنوز پیش‌بینی‌ای برای نمره‌دادن ندارم.")
    lines.append("")
    if not r["hypotheses"]:
        lines.append("هیچ فرضیه‌ای ساخته نشد.")
    for h in r["hypotheses"][:top]:
        lines += [
            f"▸ [{h['rank']:.2f}] {h['claim']}",
            f"    اثر {h['impact']}/5 · اطمینان {h['confidence']:.0%} "
            f"({h['confidence_why']}) · هزینه {h['cost']}",
            f"    ابطال: {h['falsifier']}",
            f"    ارزان‌ترین تست: {h['cheapest_test']}",
            "",
        ]
    n = r["counts"]["total"]
    if n > top:
        lines.append(f"… و {n - top} فرضیهٔ دیگر با رتبهٔ پایین‌تر.")
    if r["rule_errors"]:
        lines.append(f"🚩 {len(r['rule_errors'])} قاعده خطا داد: "
                     + ", ".join(r["rule_errors"]))
    lines += ["", f"({r['elapsed_s']}s · {r['corpus']['files']} فایل)"]
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = next((a for a in argv if not a.startswith("--")), None)
    if "--json" in argv:
        print(json.dumps(run(root, journal="--no-journal" not in argv),
                         ensure_ascii=False, indent=2))
    else:
        print(card(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
