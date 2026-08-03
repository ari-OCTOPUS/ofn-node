#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تست‌های دکترِ اختاپوس — هر تست یک خاصیت را ثابت می‌کند."""
from __future__ import annotations
import json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent

from vault import Vault              # noqa: E402
from fugu import Fugu, Quota, MODELS, PRICING, price, CONTEXT_WINDOW  # noqa: E402
from diagnose import Doctor          # noqa: E402
from ingest import ingest_scan       # noqa: E402

P, F = [], []
def check(n, c, d=""):
    (P if c else F).append(n); print(f"  {'✅' if c else '❌'} {n}" + (f"  — {d}" if d else ""))

print("\n📚 والت")
v = Vault(ROOT); notes = v.load(); st = v.stats()
check("والت بارگذاری می‌شود", len(notes) >= 45, f"{len(notes)} نوت")
check("هر نوت frontmatter دارد", all(n.fm for n in notes))
check("لایه‌بندی درست است",
      st["by_layer"].get("semantic",0) >= 30 and st["by_layer"].get("episodic",0) >= 8,
      json.dumps(st["by_layer"], ensure_ascii=False))
check("wikilinkها پارس می‌شوند", st["links"] > 100, f"{st['links']} لینک")
check("یافته‌های قرمز شمرده می‌شوند", st["red"] >= 7, f"{st['red']} قرمز")

print("\n🔎 بازیابی")
hits = v.search("ضربان قلب بودجه ترمز")
check("جست‌وجو نوتِ مرتبط می‌آورد", any("EQ-01" in n.rel or "EQ-03" in n.rel for n in hits),
      hits[0].title if hits else "—")
hm = v.search("نردبان هارمونیک شومان")
check("جست‌وجوی مغناطیس کار می‌کند", any("MAG-06" in n.rel for n in hm))
check("جست‌وجوی بی‌ربط چیزی برنمی‌گرداند", len(v.search("زززقققووو")) == 0)

print("\n🧠 مغز — fail-closed")
with tempfile.TemporaryDirectory() as td:
    old = os.environ.pop("SAKANA_API_KEY", None)
    f = Fugu(td)
    check("بدونِ کلید ready=False", not f.ready)
    r = f.ask("s", "u")
    check("بدونِ کلید هیچ متنی تولید نمی‌شود — نه mock نه حدس",
          r.text is None and not r.ok and "SAKANA_API_KEY" in r.reason)
    check("سهمیه با شکستِ کلید مصرف نمی‌شود", Quota(Path(td)).used == 0)
    q = Quota(Path(td), cap=3)
    took = sum(q.take() for _ in range(10))
    check("سقفِ سهمیه enforce می‌شود", took == 3 and q.remaining == 0, f"took={took}")
    # ۲۹ جولای (رأیِ مالک): tier ِ چهارمِ propose — پچ‌سازی با effort=high چون max
    # با توکن‌های فکر فرمتِ JSON را می‌شکست (۴ تلاش، ۳ فرمتِ خراب، رسیددار)
    check("چهار لایهٔ مدل تعریف شده", set(MODELS) == {"fast","deep","cyber","propose"})
    check("تشخیصِ عمیق از fugu-ultra-v1.1 با max استفاده می‌کند",
          MODELS["deep"] == ("fugu-ultra-v1.1","max"))
    check("پچ‌سازی ultra با effortِ فرمان‌پذیر (high/xhigh)، نه max",
          MODELS["propose"][0] == "fugu-ultra-v1.1"
          and MODELS["propose"][1] in ("high", "xhigh"))
    check("`max` فقط روی مدلی که واقعاً پشتیبانی می‌کند استفاده شده",
          all(e in ("high","xhigh") for m,e in MODELS.values() if m != "fugu-ultra-v1.1"))
    # --- هزینه: «صفر» هرگز پیش‌فرض نیست ---
    check("تعرفهٔ ultra از منبعِ اولیه ثبت شده",
          PRICING["fugu-ultra-v1.1"]["in"] == 5.0 and PRICING["fugu-ultra-v1.1"]["out"] == 30.0)
    check("تعرفهٔ `fugu` پایه [UNKNOWN] است، نه حدس",
          PRICING["fugu"]["in"] is None and price("fugu", 1000, 1000) is None)
    check("هزینه درست حساب می‌شود",
          abs(price("fugu-ultra-v1.1", 20_000, 4_000) - 0.22) < 1e-9,
          f"${price('fugu-ultra-v1.1', 20_000, 4_000)}")
    check("تعرفهٔ contextِ بلند (>۲۷۲K) اعمال می‌شود",
          price("fugu-ultra-v1.1", 300_000, 0) == 3.0)
    q2 = Quota(Path(td)/"c", cap=99, usd_cap=0.30)
    q2.take(); q2.charge(0.22)
    check("سقفِ دلار جدا از سقفِ تعداد شمرده می‌شود",
          abs(q2.spent_usd - 0.22) < 1e-9 and q2.remaining == 98)
    q2.take(); q2.charge(0.22)
    check("⛔ عبور از سقفِ دلار جلوی فراخوانِ بعدی را می‌گیرد",
          q2.spent_usd > 0.30 and q2.take() is False)
    q3 = Quota(Path(td)/"d", cap=9, usd_cap=1.0)
    q3.charge(None)
    check("فراخوانِ بی‌تعرفه صفر فرض نمی‌شود — جدا شمرده می‌شود",
          q3.spent_usd == 0.0 and q3._load()["unpriced_calls"] == 1)
    check("پنجرهٔ context از منبعِ اولیه ثبت شده", CONTEXT_WINDOW == 1_000_000)
    f2 = Fugu(td)
    check("شکلِ پارامتر حدس زده نمی‌شود — سه شکل امتحان می‌شود",
          f2.SHAPES == ("flat","nested","bare")
          and "reasoning_effort" in f2._body("flat","m","s","u","max",10)
          and f2._body("nested","m","s","u","max",10)["reasoning"] == {"effort":"max"}
          and "reasoning" not in f2._body("bare","m","s","u","max",10))
    if old: os.environ["SAKANA_API_KEY"] = old

print("\n🩺 دکتر")
doc = Doctor(ROOT)
ctx, used = doc.bundle("چرا حافظه خالی است؟")
check("Context Bundle همیشه قوانین را دارد",
      sum(1 for n in used if n.fm.get("type")=="law") >= 6)
check("Bundle شاهدِ مرتبط هم دارد", any(n.fm.get("type")!="law" for n in used))
check("Bundle کلِ والت را dump نمی‌کند", len(used) < len(notes), f"{len(used)} از {len(notes)}")
check("پرامپتِ سیستم قانونِ خودارجاعی را قفل کرده",
      "وجودِ خودش را می‌سنجد" in __import__("diagnose").SYSTEM)
t = doc.triage()
check("triage آفلاین بدونِ مغز کار می‌کند", t["notes"] >= 45 and len(t["red"]) >= 7)
check("triage سنجه‌های درون‌زاد را جدا می‌کند",
      len(t["self_referential_metrics"]) >= 5, f"{len(t['self_referential_metrics'])} تا")
d = doc.ask("تست")
check("بدونِ کلید، ask صادقانه شکست می‌خورد نه اینکه جواب بسازد",
      not d.ok and d.answer is None and d.reasons)
check("خروجیِ ناموفق هم markdown معتبر می‌دهد", "!failure" in d.as_markdown())

print("\n📥 ورودِ اسکن")
with tempfile.TemporaryDirectory() as td:
    tv = Vault(td)
    (Path(td)/"20-معادلات").mkdir(parents=True)
    eq = Path(td)/"20-معادلات"/"EQ-01-تست.md"
    eq.write_text("---\ntype: equation\n---\n\n# دست‌نخورده\n", encoding="utf-8")
    before = eq.read_text("utf-8")
    res = ingest_scan(tv, {
        "date":"2026-07-26","suite":"294/294","beat":12000,
        "metrics":{
            "confirmed_revenue":{"value":250,"provenance":"برون‌زاد","receipt":"CSV بانک","status":"🟢"},
            "velocity_per_hr":{"value":5.9,"provenance":"درون‌زاد","status":"🔴"},
            "innervation_pct":{"value":100,"provenance":"برون‌زاد","status":"🔴"}},
        "findings":[{"id":"F-08","title":"تستی","status":"🔴","body":"شاهد"}]})
    check("اسکن نوشته شد", any("SCAN-2026-07-26" in w for w in res["written"]))
    check("یافته نوشته شد", any("F-08" in w for w in res["written"]))
    check("سنجهٔ درون‌زاد flag شد",
          any("velocity" in f for f in res["flagged_metrics"]))
    check("سنجهٔ بی‌رسید هم flag شد",
          any("innervation" in f and "رسید" in f for f in res["flagged_metrics"]))
    check("سنجهٔ سالم flag نشد",
          not any("confirmed_revenue" in f for f in res["flagged_metrics"]))
    txt = (Path(td)/"50-اسکن‌ها"/"SCAN-2026-07-26.md").read_text("utf-8")
    check("جدولِ رأی در نوت هست", "| ✅ |" in txt and "| ❌ |" in txt)
    check("⛔ ورودِ اسکن معادله را overwrite نکرد", eq.read_text("utf-8") == before)

print("\n👁 چشم — اسکنرِ ارگانیسمِ زنده")
from scanner import scan, PROV        # noqa: E402

def _fake_ops(td: str) -> Path:
    """درختِ `_ops` ساختگی با اعدادِ *واقعیِ* ۲۵ جولای."""
    O = Path(td) / "_ops"; S = O / "state"
    for d in ("pulse", "cortex", "memory"):
        (S / d).mkdir(parents=True, exist_ok=True)
    (O / "governor").mkdir(parents=True, exist_ok=True)
    (S / "ORGANISM-STATE.json").write_text(json.dumps({
        "beat": 11862,
        "arbiter": {"effective_period_s": 900.0, "driver": "brake:budget"},
        "cardiac": {"bio_rhythm": {"period_s": 61.0},
                    "budget": {"spent": 288, "daily_cap": 288,
                               "remaining": 0, "depleted": True}},
    }, ensure_ascii=False), encoding="utf-8")
    (S / "pulse" / "heart-signals-latest.json").write_text(json.dumps({
        "velocity": {"velocity_per_hr": 5.8583, "metronome_share": 0.9644},
        "delta_self": {"delta_self_raw": -0.02573, "delta_self_live": 0.0,
                       "S_blind": 0.61, "S_informed": 0.58},
    }, ensure_ascii=False), encoding="utf-8")
    (S / "cortex" / "stress-latest.json").write_text(
        json.dumps({"organism_stress": 0.94, "in_fear": True}), encoding="utf-8")
    (S / "cortex" / "innervation-latest.json").write_text(
        json.dumps({"coverage_pct": 100.0}), encoding="utf-8")
    (S / "cortex" / "self-model.json").write_text(
        json.dumps({"self_awareness_pct": 87.0}), encoding="utf-8")
    (S / "fitness-latest.json").write_text(
        json.dumps({"attribution": {"confirmed": 0}}), encoding="utf-8")
    import sqlite3
    c = sqlite3.connect(S / "memory" / "memory.db")
    c.execute("create table memory(id integer primary key, body text)")
    c.execute("insert into memory(body) values ('تنها سطرِ موجود')")
    c.commit(); c.close()
    (O / "governor" / "governor-alerts.md").write_text(
        "\n".join(f"- ⚠️ leg lead-naghshi restarted {i} times" for i in range(358))
        + "\n- ⚠️ germline fallback used\n", encoding="utf-8")
    return O

def _tree_sig(root: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode()); h.update(p.read_bytes())
    return h.hexdigest()

with tempfile.TemporaryDirectory() as td:
    O = _fake_ops(td)
    sig_before = _tree_sig(O)
    s = scan(O, run_suite=False)
    check("⛔ اسکن فقط‌خواندنی است — هیچ بایتی در درختِ ارگانیسم تغییر نکرد",
          _tree_sig(O) == sig_before)
    M = s["metrics"]
    check("چشم ضربان را می‌بیند", s.get("beat") == 11862, str(s.get("beat")))
    check("هر سنجه منشأ دارد، نه عددِ لخت",
          all("provenance" in m for m in M.values()), f"{len(M)} سنجه")
    check("سنجه‌های درون‌زاد به‌درستی برچسب می‌خورند",
          all(M[k]["provenance"] == "درون‌زاد"
              # ۲۰۲۶-۰۸-۰۳ (گامِ ۱۲): نامِ سنجه‌ای که *دکتر منتشر می‌کند* از
              # `self_awareness_pct` به `docstring_coverage_pct` رفت، چون دو کمیتِ
              # کاملاً نامرتبط یک نام داشتند: یک عددِ یخ‌زدهٔ کنترل‌پلین، و پوششِ
              # docstring روی `_ops/`. کلیدِ داخلِ خودِ `self-model.json` (خطِ ۱۵۹
              # بالا) عمداً دست‌نخورده ماند — ۱۲+ خواننده دارد.
              for k in ("beat","velocity_per_hr","innervation_pct","docstring_coverage_pct")))
    check("سنجه‌های برون‌زاد با درون‌زاد قاطی نمی‌شوند",
          M["confirmed_revenue"]["provenance"] == "برون‌زاد"
          and M["memory_rows"]["provenance"] == "برون‌زاد")
    ids = {f["id"] for f in s["findings"]}
    check("قلبِ ترمزخورده خودکار کشف می‌شود", "F-AUTO-BRAKE" in ids)
    check("delta_self منفی خودکار کشف می‌شود — clamp پنهانش نمی‌کند",
          "F-AUTO-DELTASELF" in ids and M["delta_self_raw"]["value"] < 0)
    check("حافظهٔ یک‌سطری خودکار کشف می‌شود",
          "F-AUTO-MEMORY" in ids and M["memory_rows"]["value"] == 1)
    check("۳۵۸ هشدارِ هم‌امضا ⇒ یک یافته، نه ۳۵۸ تا",
          sum(1 for f in s["findings"] if f["id"].startswith("F-AUTO-ALERT")) == 1
          and M["alert_signatures"]["value"] == 2,
          f"امضا={M['alert_signatures']['value']}")
    check("سوئیتِ اجرانشده ⇒ [UNKNOWN] صریح، نه عددِ ساختگی",
          "suite" not in M and any("سوئیت" in u for u in s["unknown"]))
    check("PROV هر سنجهٔ منتشرشده را پوشش می‌دهد",
          all(k in PROV for k in M), str([k for k in M if k not in PROV]))

with tempfile.TemporaryDirectory() as td:
    s0 = scan(Path(td) / "غایب", run_suite=False)
    check("ارگانیسمِ خاموش ⇒ [UNKNOWN]، نه crash و نه صفرِ ساختگی",
          s0["metrics"] == {} and s0["unknown"])

print("\n🔁 حلقهٔ کامل: ارگانیسم ⟶ چشم ⟶ والت")
with tempfile.TemporaryDirectory() as td:
    O = _fake_ops(td)
    tv = Vault(Path(td) / "vault")
    res = ingest_scan(tv, scan(O, run_suite=False))
    check("حلقه بسته می‌شود و نوت تولید می‌کند", len(res["written"]) >= 4,
          f"{len(res['written'])} نوت")
    check("درون‌زادها در والت هم flag می‌مانند",
          any("velocity" in f for f in res["flagged_metrics"])
          and any("beat" in f for f in res["flagged_metrics"]))

print("\n✋ دست — از نثر تا پچِ اجراشدنی")
from propose import (parse_patchset, PatchSet, Patch, GateError,   # noqa: E402
                     PROPOSE_SYSTEM, MAX_FILES)

GOOD = """اینجا کمی حرفِ اضافه که مدل‌ها می‌نویسند.
```json
{"mission_id":"fix-leg-cause","title":"ثبتِ علتِ افتادنِ لِگ",
 "rationale":"۶۶ ری‌استارت و صفر تشخیص — شاهد: governor-alerts.md",
 "risk":"low","rollback":"حذفِ همان دو خط",
 "patches":[{"file":"_ops/legs/runner.py","anchor":"    except Exception:\\n        pass",
             "replacement":"    except Exception as e:\\n        rec.record(capture(e))\\n        raise",
             "why":"علت ثبت می‌شود، رفتارِ ری‌استارت دست‌نخورده"}]}
```
"""
ps = parse_patchset(GOOD)
check("JSON از میانِ نثر و ``` بیرون کشیده می‌شود",
      ps.mission_id == "fix-leg-cause" and len(ps.patches) == 1)
check("کارتِ نیت قبل از هر اجرایی ساخته می‌شود",
      "fix-leg-cause" in ps.card() and "بازگشت" in ps.card())
check("پرامپت خودش می‌گوید پیشنهادِ حدسی بدتر از نپیشنهادن است",
      "[UNKNOWN]" in PROPOSE_SYSTEM and "افزایشی" in PROPOSE_SYSTEM)

def gated(**kw) -> str:
    base = dict(mission_id="m-ok", title="t", rationale="r",
                patches=[Patch("a/b.py", "x", "y")])
    base.update(kw)
    try:
        PatchSet(**base).gate(); return ""
    except GateError as e:
        return str(e)

check("گیت ۱ — mission_idِ نامعتبر رد می‌شود", "گیت ۱" in gated(mission_id="BAD ID!"))
check("گیت ۲ — پچ‌ستِ خالی اجرا نمی‌شود", "گیت ۲" in gated(patches=[]))
check("گیت ۳ — پچِ بیش از حد پهن رد می‌شود",
      "گیت ۳" in gated(patches=[Patch(f"f{i}.py","x","y") for i in range(MAX_FILES+1)]))
check("گیت ۴ — تغییرِ غول‌پیکر رد می‌شود",
      "گیت ۴" in gated(patches=[Patch("a.py","x","y"*50_000)]))
for bad in ("../../etc/passwd", "/etc/passwd", r"C:\windows\x.py"):
    check(f"گیت ۵ — فرار از مسیر رد می‌شود: {bad}",
          "گیت ۵" in gated(patches=[Patch(bad,"x","y")]))
for red in ("_ops/.env", "OCTOPUS-flags.cmd", "_ops/state/ORGANISM-STATE.json",
            "_ops/genome/ledger.jsonl", "core/kill-switch.py"):
    check(f"⛔ گیت ۶ — خطِ قرمز لمس نمی‌شود: {red}",
          "گیت ۶" in gated(patches=[Patch(red,"x","y")]))
check("گیت ۷ — پچِ بی‌اثر رد می‌شود", "گیت ۷" in gated(patches=[Patch("a.py","x","x")]))

with tempfile.TemporaryDirectory() as td:
    wt = Path(td); (wt/"_ops").mkdir()
    f = wt/"_ops"/"m.py"
    f.write_text("def f():\n    return 1\n", encoding="utf-8")
    ok = PatchSet("m1","t","r",[Patch("_ops/m.py","return 1","return 2")])
    ok.as_apply()(wt)
    check("پچِ سالم واقعاً اعمال می‌شود", f.read_text("utf-8") == "def f():\n    return 2\n")

    f.write_text("a = 1\nb = 1\n", encoding="utf-8")
    amb = PatchSet("m2","t","r",[Patch("_ops/m.py","= 1","= 2")])
    try:
        amb.as_apply()(wt); r = ""
    except GateError as e:
        r = str(e)
    check("⛔ لنگرِ مبهم (۲ بار) رد می‌شود — نه اینکه اولی را کور عوض کند",
          "مبهم" in r and f.read_text("utf-8") == "a = 1\nb = 1\n")

    miss = PatchSet("m3","t","r",[Patch("_ops/m.py","نیست‌درفایل","x")])
    try:
        miss.as_apply()(wt); r = ""
    except GateError as e:
        r = str(e)
    check("لنگرِ پیدانشده صادقانه شکست می‌خورد", "لنگر پیدا نشد" in r)

    esc = PatchSet("m4","t","r",[Patch("_ops/../../out.py","x","y")])
    try:
        esc.as_apply()(wt); r = ""
    except GateError as e:
        r = str(e)
    check("⛔ فرار از ریشه حتی در زمانِ اعمال هم گرفته می‌شود", "گیت ۵" in r or "فرار" in r)

for junk in ("", "سلام، پچی ندارم", "{ناقص", "[]"):
    try:
        parse_patchset(junk); r = "پذیرفت!"
    except GateError:
        r = ""
    check(f"خروجیِ بی‌ربطِ مغز پذیرفته نمی‌شود: {junk[:14]!r}", r == "")

nop = parse_patchset('{"mission_id":"m-none","title":"t",'
                     '"rationale":"[UNKNOWN] شاهدِ کافی نیست","patches":[]}')
check("«شاهد ندارم» یک پاسخِ معتبر است، نه شکست",
      nop.empty and nop.notes and "شاهد کافی" in nop.card())

print("\n📡 صدا — کانالِ تلگرام")
from channel import TelegramChannel, Card, Vote, ChannelError, mask, MODE_DIRECT  # noqa: E402

TOK = "123456:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
check("توکن هرگز لو نمی‌رود — فقط اثرِ انگشت",
      TOK not in mask(TOK) and mask(TOK).startswith("tg:") and len(mask(TOK)) == 15)

class FakeTG:
    def __init__(self): self.sent = []; self.updates = []
    def post(self, method, payload):
        if method == "sendMessage":
            self.sent.append(payload); return {"ok": True, "result": {"message_id": len(self.sent)}}
        if method == "getUpdates":
            u, self.updates = self.updates, []; return {"ok": True, "result": u}
        return {"ok": False}

with tempfile.TemporaryDirectory() as td:
    os.environ.pop("OCTOPUS_DOCTOR_OWNS_POLLING", None)
    tg = FakeTG()
    ch = TelegramChannel(td, chat_id="-100777", topic_id=12, owner_id=42, transport=tg)
    r = ch.send(Card("m-1", "intent", "متنِ کارت"))
    check("پیش‌فرض outbox است — هیچ اتصالِ دومی به تلگرام باز نمی‌شود",
          r.get("queued") and not tg.sent)
    try:
        ch.poll_votes(); r = "خواند!"
    except ChannelError as e:
        r = str(e)
    check("⛔ در حالتِ outbox خواندن ممنوع است — تا آپدیتِ باتِ زنده دزدیده نشود",
          "ممنوع" in r)

    pl = Card("m-1", "intent", "x").payload("-100777", 12)
    check("کارت به topicِ درست می‌رود", pl["message_thread_id"] == 12)
    kb = pl["reply_markup"]["inline_keyboard"][0]
    check("دکمه‌ها ماموریت و گیت را با خود حمل می‌کنند",
          kb[0]["callback_data"] == "ok:intent:m-1" and kb[1]["callback_data"] == "no:intent:m-1")

    ch.ingest_external([{"id": "c1", "data": "ok:intent:m-1", "from": {"id": 42}}])
    check("رأیِ مالک پذیرفته می‌شود", ch.verdict("m-1", "intent") is True)
    ch.ingest_external([{"id": "c1", "data": "no:intent:m-1", "from": {"id": 42}}])
    check("⛔ همان رأی دوباره اعمال نمی‌شود (ضدِ تکرار)",
          ch.verdict("m-1", "intent") is True and len(ch.votes()) == 1)
    ch.ingest_external([{"id": "c9", "data": "ok:intent:m-2", "from": {"id": 999}}])
    check("⛔ رأیِ غیرِ مالک ثبت می‌شود ولی اثر ندارد", ch.verdict("m-2", "intent") is None)
    check("«هنوز رأی نداده» با «رد» یکی نیست — None نه False",
          ch.verdict("m-3", "intent") is None)
    check("سلامت کانال هیچ رازی چاپ نمی‌کند",
          TOK not in json.dumps(ch.health(), ensure_ascii=False))

with tempfile.TemporaryDirectory() as td:
    tg = FakeTG()
    ch = TelegramChannel(td, chat_id="-1", owner_id=42, mode=MODE_DIRECT, transport=tg)
    ch.send(Card("m-9", "diff", "کارت"))
    check("حالتِ direct واقعاً می‌فرستد و رسید هم می‌گذارد", len(tg.sent) == 1)
    try:
        ch.poll_votes(); r = "خواند!"
    except ChannelError as e:
        r = str(e)
    check("⛔ direct هم بدونِ اعلامِ مالکیتِ توکن حق خواندن ندارد", "OWNS_POLLING" in r)
    os.environ["OCTOPUS_DOCTOR_OWNS_POLLING"] = "1"
    tg.updates = [{"update_id": 5, "callback_query":
                   {"id": "z1", "data": "ok:diff:m-9", "from": {"id": 42}}}]
    got = ch.poll_votes()
    check("با مالکیتِ صریح، رأی خوانده می‌شود", len(got) == 1 and got[0].approved)
    check("offset ذخیره می‌شود تا آپدیت دوباره خوانده نشود",
          json.loads((Path(td)/"tg-offset.json").read_text("utf-8"))["offset"] == 6)
    os.environ.pop("OCTOPUS_DOCTOR_OWNS_POLLING", None)

print("\n♾ حلقهٔ بسته — daemon")
from daemon import Daemon, Mission                                # noqa: E402

class FakeDoctor:
    def __init__(self, ps): self.ps = ps; self.calls = 0
    def propose(self, goal, **kw):
        self.calls += 1
        return self.ps, [], ["50-اسکن‌ها/SCAN.md"]

class FakeRes:
    def __init__(self, ok): self.may_merge = ok
    def card(self): return "کارتِ دیف: سوئیت 294/294 · درختِ زنده دست‌نخورده: بله"

class FakeRunner:
    def __init__(self, ok=True): self.ok = ok; self.ran = []; self.merged = []
    def run(self, mid, apply_fn): self.ran.append(mid); return FakeRes(self.ok)
    def merge(self, mid, apply_fn, files=None, **kw):
        assert callable(apply_fn), "merge باید تابعِ اعمال بگیرد، نه فقط id"
        assert files, "merge باید فهرستِ صریحِ فایل‌ها بگیرد"
        self.merged.append((mid, tuple(files)))
        return {"ok": True, "commit": "abc1234"}

def mk(td, ps, runner=None, dry=True):
    O = _fake_ops(td)
    v = Path(td) / "vault"; (v / "90-_meta").mkdir(parents=True)
    ch = TelegramChannel(v / "90-_meta" / "state", chat_id="-1", owner_id=42,
                         transport=FakeTG())
    return Daemon(O, v, doctor=FakeDoctor(ps), channel=ch, runner=runner,
                  scan_fn=scan, dry_run=dry), ch

from propose import PatchSet, Patch                                # noqa: E402
PS = PatchSet("fix-memory", "حافظه را پر کن", "شاهد: memory.db یک سطر دارد",
              [Patch("_ops/m.py", "a", "b")], rollback="revert")

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PS, FakeRunner())
    r1 = d.cycle()
    check("چرخه ارگانیسم را می‌بیند و یافته می‌سازد", r1["beat"] == 11862 and r1["findings"] >= 3)
    check("کارتِ نیت ساخته می‌شود و ماموریت در حالتِ proposed می‌ماند",
          len(r1["missions"]) == 1 and r1["missions"][0]["state"] == "proposed")
    r2 = d.cycle()
    check("⛔ بدونِ رأی هیچ چیزی جلو نمی‌رود — و پیشنهادِ دوم ساخته نمی‌شود",
          len(r2["missions"]) == 1 and r2["missions"][0]["state"] == "proposed"
          and d.doctor.calls == 1)
    ch.ingest_external([{"id": "v1", "data": "ok:intent:fix-memory", "from": {"id": 42}}])
    r3 = d.cycle()
    check("✅ نیت ⇒ ماموریت اجرا و کارتِ دیف می‌آید",
          r3["missions"][0]["state"] == "awaiting-merge" and d.runner.ran == ["fix-memory"])
    ch.ingest_external([{"id": "v2", "data": "ok:diff:fix-memory", "from": {"id": 42}}])
    r4 = d.cycle()
    check("⛔ dry_run روشن ⇒ حتی با ✅ دیف هم merge نمی‌شود",
          r4["missions"][0]["state"] == "awaiting-merge" and d.runner.merged == [])

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PS, FakeRunner(), dry=False)
    os.environ["OCTOPUS_DOCTOR_MAY_MERGE"] = "1"
    d.cycle()
    ch.ingest_external([{"id": "a", "data": "ok:intent:fix-memory", "from": {"id": 42}}])
    d.cycle()
    ch.ingest_external([{"id": "b", "data": "ok:diff:fix-memory", "from": {"id": 42}}])
    r = d.cycle()
    check("با dry_run خاموش + flag + دو رأیِ ✅ ⇒ merge انجام می‌شود",
          r["missions"][0]["state"] == "merged" and d.runner.merged == [("fix-memory", ("_ops/m.py",))])
    os.environ.pop("OCTOPUS_DOCTOR_MAY_MERGE")

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PS, FakeRunner(), dry=False)
    d.cycle()
    ch.ingest_external([{"id": "a", "data": "ok:intent:fix-memory", "from": {"id": 42}}])
    d.cycle()
    ch.ingest_external([{"id": "b", "data": "ok:diff:fix-memory", "from": {"id": 42}}])
    r = d.cycle()
    check("⛔ بدونِ OCTOPUS_DOCTOR_MAY_MERGE هیچ merge — دو قفل، نه یکی",
          r["missions"][0]["state"] == "awaiting-merge" and d.runner.merged == [])

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PS, FakeRunner())
    d.cycle()
    ch.ingest_external([{"id": "n", "data": "no:intent:fix-memory", "from": {"id": 42}}])
    r = d.cycle()
    check("❌ نیت ⇒ ماموریت رد و هرگز اجرا نمی‌شود",
          r["missions"][0]["state"] == "rejected" and d.runner.ran == [])

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PS, FakeRunner(ok=False))
    d.cycle()
    ch.ingest_external([{"id": "a", "data": "ok:intent:fix-memory", "from": {"id": 42}}])
    r = d.cycle()
    check("سوئیتِ قرمز ⇒ failed و کارتِ بی‌دکمه — رأی‌گیری روی چیزِ خراب معنا ندارد",
          r["missions"][0]["state"] == "failed")

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PatchSet("m-x", "t", "[UNKNOWN] شاهد ندارم", []))
    r = d.cycle()
    check("«شاهد ندارم» ⇒ هیچ ماموریتی ساخته نمی‌شود و هیچ کارتی نمی‌رود",
          r["missions"] == [] and ch.pending() == 0)

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, PS, FakeRunner())
    sig0 = _tree_sig(Path(td) / "_ops")
    d.cycle()
    ch.ingest_external([{"id": "a", "data": "ok:intent:fix-memory", "from": {"id": 42}}])
    d.cycle()
    check("⛔ کلِ حلقه هیچ بایتی در درختِ ارگانیسم تغییر نمی‌دهد",
          _tree_sig(Path(td) / "_ops") == sig0)
    v = d.vitals()
    check("حیاتی‌های دکتر منشأ دارند (R-07)",
          v["missions_total"]["provenance"] == "درون‌زاد"
          and v["owner_approvals"]["provenance"] == "برون‌زاد")
    check("فقط رأیِ انسان و کامیتِ واقعی برون‌زادند",
          {k for k, x in v.items() if isinstance(x, dict) and x.get("provenance") == "برون‌زاد"}
          == {"missions_merged", "owner_approvals", "owner_rejections"})
    check("حیاتی‌ها روی دیسک نوشته می‌شوند",
          (Path(td)/"vault"/"90-_meta"/"state"/"doctor-vitals.json").exists())

print("\n🌀 لایه‌های فکر — ناخودآگاهِ جمعی")
from mind import (Layer, TIMESCALE_S, Episode, Archetype, CollectiveUnconscious,  # noqa: E402
                  Mind, signature, MAX_BIAS, MIN_ACTORS, MIN_DAYS)

DAY = 86400.0
T0 = 1_760_000_000.0

check("لایه‌ها با مقیاسِ زمانی تعریف شده‌اند، نه با «هوش»",
      TIMESCALE_S[Layer.REFLEX] < TIMESCALE_S[Layer.PERCEPT] < TIMESCALE_S[Layer.EPISODE]
      < TIMESCALE_S[Layer.PATTERN] < TIMESCALE_S[Layer.ARCHETYPE]
      < TIMESCALE_S[Layer.CHARTER])
mind = Mind()
check("⛔ هیچ لایه‌ای حق نوشتن در منشور را ندارد — حتی کهن‌الگو",
      not mind.may_write(Layer.ARCHETYPE, Layer.CHARTER)
      and not mind.may_write(Layer.CHARTER, Layer.CHARTER))
check("هر لایه فقط انبارِ خودش را می‌نویسد",
      mind.may_write(Layer.PATTERN, Layer.PATTERN)
      and not mind.may_write(Layer.PATTERN, Layer.EPISODE))
check("رنگ‌دادن فقط از بالا به پایین است",
      mind.may_bias(Layer.ARCHETYPE, Layer.EPISODE)
      and not mind.may_bias(Layer.EPISODE, Layer.ARCHETYPE))
check("امضا اعداد را حذف می‌کند — «۳ ری‌استارت» و «۵۰ ری‌استارت» یکی‌اند",
      signature("لِگ 3 بار افتاد") == signature("لِگ 50 بار افتاد"))

def eps(n, actor="leg-a", day_span=1, out="green", exo=True, text="لِگ N بار افتاد"):
    return [Episode(T0 + (i % day_span) * DAY, "failure", text,
                    actor=actor if isinstance(actor, str) else actor[i % len(actor)],
                    outcome=out, exogenous=exo) for i in range(n)]

cu = CollectiveUnconscious()
cu.consolidate(eps(9, actor="leg-a", day_span=1))
a = list(cu.arch.values())[0]
check("⛔ ۹ بار از **یک** actor در **یک** روز ⇒ کهن‌الگو نمی‌شود",
      not a.collective and a.weight(T0) == 0.0, a.why(T0))

cu = CollectiveUnconscious()
cu.consolidate(eps(6, actor=["leg-a", "leg-b", "leg-c"], day_span=3))
a = list(cu.arch.values())[0]
check(f"شاهد از ≥{MIN_ACTORS} actor و ≥{MIN_DAYS} روز ⇒ کهن‌الگو متولد می‌شود",
      a.collective and a.weight(T0) > 0, f"قوت={a.strength(T0)}")

cu = CollectiveUnconscious()
cu.consolidate(eps(8, actor=["a", "b"], day_span=4, exo=False))
a = list(cu.arch.values())[0]
check("⛔ کهن‌الگویی که فقط از حرفِ خودِ سیستم ساخته شده، دیده می‌شود ولی **رأی ندارد**",
      a.collective and a.strength(T0) > 0 and a.weight(T0) == 0.0
      and "برون‌زاد" in a.why(T0))

cu = CollectiveUnconscious()
cu.consolidate(eps(8, actor=["a", "b"], day_span=4))
a = list(cu.arch.values())[0]
w_now, w_later = a.weight(T0 + 4 * DAY), a.weight(T0 + 64 * DAY)
check("فراموشی ویژگی است — بدونِ تأییدِ نو، یقین محو می‌شود",
      0 < w_later < w_now / 2, f"{w_now:.3f} ⟶ {w_later:.3f}")

cu.challenge("لِگ N بار افتاد", n=4)
check("لایهٔ شکاک: شاهدِ خلاف ⇒ سوگیری صفر می‌شود، نه «کم»",
      a.contested and a.weight(T0) == 0.0 and a.bias(T0) == 0.0)

cu = CollectiveUnconscious()
cu.consolidate(eps(400, actor=["a", "b", "c"], day_span=9))
a = list(cu.arch.values())[0]
check("⛔ حتی با ۴۰۰ شاهد، ناخودآگاه از سقف رد نمی‌شود — مایل می‌کند، نمی‌بُرد",
      abs(a.bias(T0)) <= MAX_BIAS + 1e-9, f"bias={a.bias(T0):+.3f}")

cu = CollectiveUnconscious()
cu.consolidate(eps(6, actor=["a", "b"], day_span=3, text="قلب را سریع‌تر کن"))
check("نمونه‌گیری فقط کهن‌الگوی مرتبط را می‌آورد",
      len(cu.sample("قلب کند است چه کنم", now=T0)) == 1
      and cu.sample("رنگِ لوگو", now=T0) == [])
check("prior برای EFE بیرون می‌آید، نه تصمیم",
      all(abs(v) <= MAX_BIAS for v in cu.priors("قلب", now=T0).values()))

print("\n🌑 سایه — آنچه مرتب رد می‌شود")
cu = CollectiveUnconscious()
cu.consolidate([Episode(T0 + i * DAY, "verdict", "بودجهٔ ضربان را زیاد کن",
                        actor="owner", outcome="rejected", exogenous=True)
                for i in range(3)])
th = cu.shadow.themes()
check("سه بار ❌ روی یک ایده ⇒ مضمونِ سایه ثبت می‌شود",
      len(th) == 1 and th[0]["n"] == 3)
check("سایه جلوی پیشنهادِ تکراری را می‌گیرد",
      cu.shadow.blocks("بودجهٔ ضربان را زیاد کن")
      and not cu.shadow.blocks("حافظه را پر کن"))
check("ردشدن هم valence منفی می‌سازد — پرهیز، نه بی‌تفاوتی",
      cu.arch[signature("بودجهٔ ضربان را زیاد کن")].valence < 0)
ctx = Mind().cu.__class__().__class__  # noqa: F841  (فقط برای خوانایی زیر)
m = Mind(); m.cu = cu
c = m.context("بودجهٔ ضربان")
check("متنِ ناخودآگاه، سایه را صریح به دکتر می‌گوید",
      "سایه" in c and "دوباره پیشنهادش نده" in c)
check("وقتی ناخودآگاه چیزی ندارد، **ساکت** است نه پرحرف",
      Mind().context("هرچیزی") == "")

print("\n🦿 ساختِ فایلِ نو — «یک پا اضافه کن»")
from propose import CREATE_ALLOW                                  # noqa: E402

leg = Patch("_ops/legs/leg_schumann.py", "", "# لِگِ نو\ndef tick():\n    pass\n",
            "پای رصدِ شومان", create=True)
ok_ps = PatchSet("add-leg-schumann", "افزودنِ پای رصدِ شومان", "مالک خواست", [leg])
ok_ps.gate()
check("ساختِ فایلِ نو در مسیرِ مجاز از گیت رد می‌شود", True)
# ⚠️ این‌ها اول با mission_id="m" نوشته شده بودند و **به دلیلِ غلط** سبز بودند:
# گیتِ ۱ زودتر شلیک می‌کرد و تستِ من فقط دنبالِ کلمهٔ «گیت» می‌گشت. یعنی خودِ سوئیتِ
# من هم همان بیماری را داشت: «❌ ندیدم ⇒ حتماً سبز است». حالا هر تست **شمارهٔ گیت** را می‌خواهد.
for bad, want in (("_ops/wiring.py", "گیت ۸"), ("setup.py", "گیت ۸"),
                  ("_ops/state/x.py", "گیت ۶")):
    try:
        PatchSet("m-ok", "t", "r", [Patch(bad, "", "x=1\n", create=True)]).gate()
        r = "پذیرفت!"
    except GateError as e:
        r = str(e)
    check(f"⛔ ساختِ فایلِ نو رد می‌شود ({want}): {bad}", want in r, r[:60])
try:
    PatchSet("m-ok", "t", "r", [Patch("_ops/legs/a.py", "لنگر", "x", create=True)]).gate()
    r = "پذیرفت!"
except GateError as e:
    r = str(e)
check("فایلِ نو نباید لنگر داشته باشد", "لنگر داشته" in r, r[:60])

# ⛔ گیتِ ۹ — حریم. از حالتِ شکستِ **مشاهده‌شدهٔ** Darwin Gödel Machine (۲۰۲۵):
# ایجنت لاگِ تست را جعل کرد، و در موردی دیگر گاردِ تشخیصِ توهم را حذف کرد.
# هیچ‌کدام در فهرستِ DENY نبودند ⇒ این یک سوراخِ واقعی در طراحیِ من بود.
for holy in ("_ops/tests/run_all.py", "doctor/propose.py", "os_v1/policy_sampler.py",
             "OCTOPUS-DOCTOR/10-قوانین/R-01-قانونِ-خودارجاعی.md"):
    ps_h = PatchSet("m-ok", "t", "r", [Patch(holy, "الف", "ب")])
    try:
        ps_h.gate(); r = "پذیرفت!"
    except GateError as e:
        r = str(e)
    check(f"⛔ گیت ۹ — حریم: {holy.split('/')[-1][:22]}", "گیت ۹" in r, r[:44])
    check("   ...ولی با اجازهٔ صریحِ مالک ممکن است (تکامل ممنوع نیست)",
          ps_h.gate(allow_sanctum=True) is None and ps_h.touches_sanctum)
ps_ok = PatchSet("m-ok", "t", "r", [Patch("_ops/legs/a.py", "x", "y")])
check("پچِ عادی حریم را لمس نمی‌کند و گیت ۹ سرِ راهش نیست",
      not ps_ok.touches_sanctum and ps_ok.gate() is None)

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    ok_ps.as_apply()(root)
    f = root / "_ops" / "legs" / "leg_schumann.py"
    check("پای نو واقعاً روی دیسک ساخته می‌شود", f.exists() and "لِگِ نو" in f.read_text("utf-8"))
    try:
        ok_ps.as_apply()(root); r = "دوباره ساخت!"
    except GateError as e:
        r = str(e)
    check("⛔ «ساختن» بازنویسی نیست — فایلِ موجود دست نمی‌خورد", "از قبل هست" in r)

print("\n💬 درخواستِ مالک از تلگرام ⟶ ماموریت")
with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, ok_ps, FakeRunner())
    r = d.request("یک پا اضافه کن که رزونانسِ شومان را رصد کند")
    check("متنی که تو می‌نویسی به ماموریتِ واقعی تبدیل می‌شود",
          r["ok"] and r["mission_id"] == "add-leg-schumann")
    check("فایل‌هایی که قرار است **ساخته** شوند صریح گزارش می‌شوند",
          r["creates"] == ["_ops/legs/leg_schumann.py"])
    check("کارتِ نیت رفت و ماموریت منتظرِ رأی ماند",
          ch.pending() == 1 and d.missions()[0].state == "proposed")
    r2 = d.request("یک کارِ دیگر")
    check("⛔ دو ماموریتِ باز هم‌زمان ممنوع", not r2["ok"] and "ماموریتِ باز" in r2["why"])
    ch.ingest_external([{"id": "q", "data": "ok:intent:add-leg-schumann", "from": {"id": 42}}])
    out = d.cycle()
    check("✅ ⇒ در worktreeِ ایزوله اجرا شد و کارتِ دیف آمد",
          out["missions"][0]["state"] == "awaiting-merge" and d.runner.ran == ["add-leg-schumann"])
    check("رأیِ تو به‌عنوانِ شاهدِ **برون‌زاد** وارد ناخودآگاه شد",
          out["mind"]["episodes"] > 0)

with tempfile.TemporaryDirectory() as td:
    d, ch = mk(td, ok_ps, FakeRunner())
    d.mind.cu.consolidate([Episode(T0 + i * DAY, "verdict",
                                   "یک پا اضافه کن که رزونانسِ شومان را رصد کند",
                                   actor="owner", outcome="rejected", exogenous=True)
                           for i in range(3)])
    r = d.request("یک پا اضافه کن که رزونانسِ شومان را رصد کند")
    check("سایه جلوی مالک را نمی‌گیرد، ولی **یادش می‌آورد** چند بار ردش کرده",
          r["ok"] and "رد کرده‌ای" in r["warn"], r["warn"][:40])

print("\n💸 مسیریابِ هزینه‌محور — کد ⟶ محلی ⟶ ابر")
from router import Router, Task, Tier                            # noqa: E402

full = Router(local_available=True, cloud_ready=True, usd_remaining=10.0)
check("جوابِ معین ⇒ کد، حتی وقتی ابر آزاد است",
      full.route(Task("dedupe")).tier is Tier.CODE)
check("کارِ کم‌ریسکِ متنی ⇒ محلی، نه ابر",
      full.route(Task("summarize", "خلاصهٔ لاگ")).tier is Tier.LOCAL)
d = full.route(Task("propose", "علتِ لِگ را ثبت کن"))
check("نوشتنِ پچ ⇒ ابر، و هزینه‌اش از قبل اعلام می‌شود",
      d.tier is Tier.CLOUD and abs(d.est_usd - 0.22) < 1e-9)
check("متنِ پرمخاطره خودش کار را به ابر می‌برد",
      full.route(Task("classify", "این پیام دربارهٔ حذفِ .env است")).tier is Tier.CLOUD)

poor = Router(local_available=True, cloud_ready=True, usd_remaining=0.05)
d = poor.route(Task("propose"))
check("⛔ سقفِ دلار بر ترجیح مقدم است — کارِ پرریسک هم تنزل می‌کند",
      d.tier is Tier.LOCAL and d.degraded and any("سقفِ دلار" in r for r in d.reasons))

nokey = Router(local_available=True, cloud_ready=False, usd_remaining=99.0)
check("نبودِ کلید ⇒ تنزل به محلی، با دلیلِ صریح",
      nokey.route(Task("propose")).degraded)

nolocal = Router(local_available=False, cloud_ready=True, usd_remaining=99.0)
d = nolocal.route(Task("summarize", "خلاصه"))
check("⛔ نبودِ مدلِ محلی ⇒ **سقوط به کد**، نه ترفیع به ابر",
      d.tier is Tier.CODE and d.degraded and d.est_usd == 0.0,
      "وگرنه یک نصبِ ناقص قبض را ده‌برابر می‌کند")
d2 = nolocal.route(Task("propose"))
check("ولی کارِ واقعاً پرریسک هنوز به ابر می‌رود", d2.tier is Tier.CLOUD)

none_ = Router(local_available=False, cloud_ready=False)
check("نه ابر نه محلی ⇒ NONE و گزارش به مالک، نه تظاهر به انجام",
      none_.route(Task("propose")).tier is Tier.NONE)

plan = full.plan([Task("dedupe"), Task("count"), Task("summarize", "x"),
                  Task("propose"), Task("root-cause")])
check("پیش‌بینیِ هزینهٔ روز **قبل از** خرج‌شدنش",
      abs(plan["est_usd_total"] - 0.44) < 1e-9 and plan["by_tier"]["CODE"] == 2,
      f"${plan['est_usd_total']}")

print("\n" + "="*58)
print(f"نتیجه: {len(P)} سبز · {len(F)} قرمز")
for x in F: print("  ❌", x)
print("="*58)
sys.exit(1 if F else 0)
