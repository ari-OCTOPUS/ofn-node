#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_reach_probe — «واقعاً دوید» در برابرِ «حدس می‌زنم قابلِ اجراست».

    زمینه: `orphan_scan.py` تحلیلِ **ایستا** است و در docstring ِ خودش نوشته
    «عمداً محافظه‌کار است و کم‌گزارش می‌دهد»؛ یک بار ۳۱ مثبتِ کاذب داد.
    `sys.monitoring` (PEP 669) همان سؤال را از حدس به واقعیت می‌برد.

    ادعاهای زیرِ آزمون (هرکدام با جهشِ کُشنده روی لنگرِ یکتا):
      · تابعی که واقعاً اجرا شود در دفتر می‌آید؛ تابعِ تعریف‌شده‌ولی‌نادویده نه.
      · **قیدِ تیز:** غیاب ≠ «نپرید». هر پروسه یک ردیفِ provenance می‌نویسد،
        و بدونِ آن ردیف خواننده باید UNKNOWN بگوید. این همان صفرِ جعلی است
        که منشور ممنوع کرده، فقط با لباسِ تازه.
      · فقط **نام** ثبت می‌شود: هیچ آرگومان، متغیرِ محلی یا مقدارِ بازگشتی
        به دفتر نمی‌رسد (منشور §۱۰).
      · فلگِ خاموش = no-op مطلق: نه دفتری، نه پروبی.
      · تصادمِ tool-id ⇒ نصب رد می‌شود، نه اینکه رویش بنشیند و مالکِ قبلی
        را کور کند.
      · کدِ خارج از درختِ رصدشده ثبت نمی‌شود (وگرنه دفتر پر از stdlib است).

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("reach-probe")

import reach_probe as rp  # noqa: E402


def _child(module_src, flag="1", extra="", after=""):
    """پروب را در یک زیرپروسهٔ تازه بدوان، با هدف در یک **فایلِ واقعی**.

    ⚠️ زیرپروسه اجباری است نه سلیقه: `sys.monitoring` سراسریِ مفسر است و
    نصبش داخلِ خودِ تست، بقیهٔ سوییت را هم رصد می‌کند و tool-id را اشغال
    می‌گذارد. هر تست باید مفسرِ خودش را داشته باشد.

    ⚠️ و هدف باید فایلِ روی دیسک باشد نه رشتهٔ `-c`: کدِ `-c` نامِ فایلش
    `<string>` است و فیلترِ درخت — که **درست** است — ردش می‌کند. نسخهٔ اولِ
    این تست همین را نفهمید و چهار قرمزِ کاذب داد؛ خطا از تست بود نه از
    پروب. تولید همیشه از فایل می‌آید، پس تست هم باید.
    """
    d = Path(tempfile.mkdtemp(prefix="reach-t-"))
    (d / "target_mod.py").write_text(module_src, encoding="utf-8")
    lines = [
        "import sys, os, json",
        'sys.path.insert(0, r"%s")' % _OPS,
        'sys.path.insert(0, r"%s")' % d,
        'os.environ["OCTOPUS_REACH"] = "%s"' % flag,
        "import reach_probe as rp",
        "from pathlib import Path",
        'rp.LEDGER = Path(r"%s") / "ledger.jsonl"' % d,
        'rp.PROVENANCE = Path(r"%s") / "probes.jsonl"' % d,
        'rp.ROOT = r"%s".lower()' % d,
    ]
    if extra:
        lines.append(extra)
    lines.append("res = rp.install()")
    lines.append("import target_mod")
    if after:
        lines.append(after)
    lines.append("n = rp.flush()")
    lines.append('print(json.dumps({"install": res, "flushed": n}, ensure_ascii=False))')
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", "\n".join(lines)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(_OPS), timeout=90,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                            "PYTHONIOENCODING": "utf-8"})
    out = {"dir": d, "stdout": r.stdout, "stderr": r.stderr, "rc": r.returncode}
    try:
        out["res"] = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        out["res"] = {}

    def rows(name):
        try:
            return [json.loads(x) for x
                    in (d / name).read_text(encoding="utf-8").splitlines() if x.strip()]
        except Exception:  # noqa: BLE001
            return []

    out["ledger"] = rows("ledger.jsonl")
    out["prov"] = rows("probes.jsonl")
    return out


#: ماژولِ هدف: یک تابع صدا زده می‌شود، یکی فقط تعریف.
_MOD = ("def ran_for_real(x):\n"
        "    return x + 1\n"
        "\n"
        "def never_called(x):\n"
        "    return x - 1\n"
        "\n"
        "ran_for_real(41)\n")


def t_a_function_that_ran_appears_and_one_that_did_not_does_not():
    """هستهٔ ابزار — و **هر دو جهت**.

    فقط «دویده آمد» کافی نیست: ابزاری که همه‌چیز را ثبت کند هم آن را پاس
    می‌کند و هیچ چیزی دربارهٔ یتیم نمی‌گوید.
    """
    r = _child(_MOD)
    quals = {x["qual"] for x in r["ledger"]}
    assert "ran_for_real" in quals, \
        f"تابعِ دویده در دفتر نیامد: {sorted(quals)[:8]} · rc={r['rc']} · {r['stderr'][:200]}"
    assert "never_called" not in quals, "تابعِ نادویده در دفتر آمد — ابزار بی‌معناست"


def t_absence_without_a_probe_record_is_unknown_not_never_ran():
    """قیدِ تیز: نبودِ نام دو معنی دارد و باید قابلِ تفکیک باشد.

    اگر پروب نصب نبوده، دفتر خالی است — ولی این **هیچ چیزی** دربارهٔ اجرا
    نمی‌گوید. رندرکردنش به‌عنوان «یتیم» همان صفرِ جعلیِ ممنوع است. ردیفِ
    provenance تنها چیزی است که این دو را جدا می‌کند.
    """
    on = _child(_MOD, flag="1")
    off = _child(_MOD, flag="0")
    assert on["prov"], "پروبِ نصب‌شده ردیفِ provenance ننوشت"
    assert not off["prov"], "پروبِ خاموش ردیفِ provenance نوشت"
    assert not off["ledger"], "پروبِ خاموش دفتر نوشت — no-op نبود"
    p = on["prov"][0]
    for k in ("pid", "proc", "ts", "probe"):
        assert k in p, f"ردیفِ provenance کلیدِ {k} ندارد: {sorted(p)}"


def t_the_ledger_records_names_only_never_values():
    """منشور §۱۰: هیچ مقداری به لاگ نمی‌رسد.

    نشانگرِ یکتا داخلِ **آرگومان** و **متغیرِ محلی** می‌گذارم؛ اگر روزی کسی
    callback را غنی‌تر کند، همین‌جا می‌میرد.
    """
    mark = "SECRETMARKER-9911-DONOTLOG"
    mod = ("def handler(token):\n"
           '    secret_local = "%s" + token\n'
           "    return len(secret_local)\n"
           "\n"
           'handler("%s")\n') % (mark, mark)
    r = _child(mod)
    blob = json.dumps(r["ledger"] + r["prov"], ensure_ascii=False)
    assert "handler" in blob, f"تابع اصلاً ثبت نشد — گرپ کور است · {r['stderr'][:200]}"
    assert mark not in blob, "مقدارِ آرگومان/محلی به دفتر نشت کرد"
    for row in r["ledger"]:
        assert set(row) <= {"ts", "pid", "proc", "file", "qual"}, \
            f"کلیدِ خارج از allowlist در دفتر: {sorted(set(row))}"


def t_a_taken_tool_id_is_refused_not_squatted():
    """‏sys.monitoring هر شناسه را فقط به یک مالک می‌دهد.

    نشستن روی شناسهٔ گرفته‌شده یعنی کورکردنِ مالکِ قبلی — بدتر از نداشتنِ
    پروب، چون او فکر می‌کند دارد رصد می‌کند.
    """
    r = _child(_MOD, extra='sys.monitoring.use_tool_id(3, "someone-else")')
    res = r["res"].get("install", {})
    assert res.get("ok") is False, f"روی شناسهٔ گرفته‌شده نشست: {res!r}"
    assert "owned" in str(res.get("reason", "")), res


def t_only_watched_tree_is_recorded():
    """کدِ بیرونِ درخت ثبت نمی‌شود، وگرنه دفتر پر از stdlib می‌شود."""
    mod = ("import json as _j\n"
           '_j.dumps({"a": 1})\n'
           "\n"
           "def mine():\n"
           "    return 1\n"
           "\n"
           "mine()\n")
    r = _child(mod)
    assert any(x["qual"] == "mine" for x in r["ledger"]), \
        f"تابعِ خودی ثبت نشد · {r['stderr'][:200]}"
    outside = [x["file"] for x in r["ledger"]
               if "target_mod" not in x["file"]]
    assert not outside, f"کدِ بیرونِ درختِ رصدشده ثبت شد: {outside[:5]}"


def t_flush_is_incremental_not_repeating():
    """‏flush دوم نباید همان ردیف‌ها را دوباره بنویسد.

    وگرنه دفتر با هر ضربان باد می‌کند و روی دیسکِ ۵۴۰۰ دور همان کاری را
    می‌کند که یک بار `du` را نُه دقیقه‌ای کرد.
    """
    r = _child(_MOD, after="rp.flush()")
    n2 = r["res"].get("flushed")
    assert isinstance(n2, int), r["res"]
    assert n2 == 0, f"‏flush دوم {n2} ردیف نوشت — تکراری است"


def t_each_function_costs_exactly_one_callback():
    """‏callback باید `DISABLE` برگرداند — وگرنه هزینه از ~۵٪ به ~۲۰۰۰٪ می‌رود.

    ⚠️ چرا این تست وجود دارد: جهشِ «`DISABLE` برنگردان» **زنده ماند** و
    درست هم بود — رفتار عوض نمی‌شود، فقط هزینه. آن یک جهشِ کارایی است و
    شش تستِ دیگر که همه دربارهٔ درستی‌اند، نمی‌توانند بگیرندش.

    سنجهٔ رفتاری به‌جای زمان‌سنجی: زمان روی دیسکِ ۵۴۰۰ دور ±۴۴۱٪ پراکندگی
    دارد و بی‌فایده است. ولی شمارِ **فراخوانِ callback** قطعی است: یک تابع
    که هزار بار صدا زده شود باید دقیقاً **یک** callback بگیرد.
    """
    mod = ("import reach_probe as _rp\n"
           "_hits = []\n"
           "_real = _rp._cb\n"
           "def _counting(code, offset):\n"
           "    _hits.append(code.co_qualname)\n"
           "    return _real(code, offset)\n"
           "_rp._cb = _counting\n"
           "import sys as _s\n"
           "_s.monitoring.register_callback(_rp.TOOL_ID, _s.monitoring.events.PY_START, _counting)\n"
           "\n"
           "def hot(x):\n"
           "    return x + 1\n"
           "\n"
           "for _i in range(1000):\n"
           "    hot(_i)\n"
           "import json as _j\n"
           'print("HOTCOUNT=" + str(_hits.count("hot")))\n')
    r = _child(mod)
    line = [x for x in (r["stdout"] or "").splitlines() if x.startswith("HOTCOUNT=")]
    assert line, f"شمارنده چاپ نشد · rc={r['rc']} · {r['stderr'][:200]}"
    n = int(line[0].split("=")[1])
    assert n == 1, (f"تابعی که ۱۰۰۰ بار صدا شد {n} بار callback گرفت — "
                    "‏DISABLE برنگشته و هزینه خطی است")


def t_reachability_readers_agree_with_the_ledger():
    """`reached()` همان چیزی را برمی‌گرداند که در دفتر است."""
    r = _child(_MOD)
    saved_l, saved_p = rp.LEDGER, rp.PROVENANCE
    rp.LEDGER = r["dir"] / "ledger.jsonl"
    rp.PROVENANCE = r["dir"] / "probes.jsonl"
    try:
        hits = rp.reached(since_s=300)
        procs = rp.probed_processes(since_s=300)
    finally:
        rp.LEDGER, rp.PROVENANCE = saved_l, saved_p
    assert any(h.endswith("::ran_for_real") for h in hits), sorted(hits)[:6]
    assert procs, "خوانندهٔ provenance هیچ پروسه‌ای نداد"


def t_the_ledger_is_flushed_without_process_exit():
    """دفتر باید **بدونِ** خروجِ پروسه هم نوشته شود.

    ⚠️ نسخهٔ اول فقط `atexit` داشت، پس داده تا خروجِ پروسه در RAM می‌ماند —
    و این پنج پروسه بلندعمرند و بعضی با kill بسته می‌شوند، یعنی atexit
    اصلاً نمی‌دود. نتیجه: پروبی که کار می‌کند و دفترش همیشه خالی است.
    باز هم «قابلیت هست، صداکننده نیست»، این بار در کدِ خودم.

    سنجه: نخِ flusher باید وجود داشته باشد و daemon باشد (وگرنه جلوی خروجِ
    پروسه را می‌گیرد).
    """
    mod = "\n".join([
        "import threading, json",
        "_names = [t.name for t in threading.enumerate()]",
        "_dae = {t.name: t.daemon for t in threading.enumerate()}",
        'print("THREADS=" + json.dumps({"names": _names, "daemon": _dae}))',
        "",
    ])
    r = _child(mod)
    line = [x for x in (r["stdout"] or "").splitlines() if x.startswith("THREADS=")]
    assert line, f"نخ‌ها چاپ نشد · {r['stderr'][:200]}"
    info = json.loads(line[0].split("=", 1)[1])
    assert "reach-flush" in info["names"], \
        f"نخِ flusher وجود ندارد — دفتر تا خروجِ پروسه خالی می‌ماند: {info['names']}"
    assert info["daemon"].get("reach-flush") is True,         "نخِ flusher daemon نیست — جلوی خروجِ پروسه را می‌گیرد"


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_reach_probe: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
