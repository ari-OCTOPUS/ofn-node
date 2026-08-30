"""teacher_loop — حلقهٔ معلم (G1 از قوسِ جفت‌گیری).

ایده در یک جمله: همان سؤال را از مغزِ گران و مغزِ محلی بپرس، هر دو جواب را با یک
شناسهٔ مسیرِ مشترک ثبت کن، و **هر جا که داورِ عینی وجود دارد** بگو کدام بهتر بود.

چرا این شکل و نه شکلِ ساده‌تر
──────────────────────────────
شکلِ ساده‌تر این بود: از معلم بپرس، جوابش را ذخیره کن، بعداً مدلِ محلی را رویش
تربیت کن. مشکلِ آن شکل این است که **هیچ‌وقت نمی‌فهمی معلم اشتباه کرده**. جوابِ
گران‌تر لزوماً درست‌تر نیست؛ فقط گران‌تر است. اگر بی‌داوری ذخیره‌اش کنی، خطاهای
معلم را با همان اطمینانی یاد می‌گیری که درست‌هایش را — و بدتر، دیگر راهی برای
تشخیصشان نمی‌ماند چون همه‌شان یک‌جور به‌نظر می‌رسند.

پس این‌جا هر جفت یکی از دو برچسب را می‌گیرد:
  · `graded`   — داورِ عینی داشت (JSON پارس شد؟ اسکیما درست بود؟ عدد در بازه بود؟)
  · `ungraded` — نداشت. ذخیره می‌شود ولی **صریحاً بی‌نمره**.

و جفتِ بی‌نمره برای تقطیر تقریباً بی‌ارزش است. این را همین‌جا می‌نویسم چون
وسوسهٔ مرحلهٔ بعد این خواهد بود که «داده داریم» — و اگر نسبتِ graded پایین باشد،
نداریم؛ فقط حجم داریم.

مرزها
─────
· فلگ‌دار و پیش‌فرض خاموش. خاموش = صفر تماس، صفر خرج، صفر بایت.
· سقفِ روزانه. هر تماسِ معلم پول است.
· هیچ وزنی این‌جا عوض نمی‌شود و هیچ رفتاری تغییر نمی‌کند — فقط داده تولید می‌شود.
· ورودیِ وظیفه از فراخوان می‌آید، نه از دیسک: این ماژول خودش کارِ جدید اختراع
  نمی‌کند.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_TEACHER_LOOP"
SCHEMA = "teacher-pair.v1"
DAILY_DEFAULT = 12                 # سقفِ جفت در روز — هر جفت یک تماسِ پولی است
MAX_TOKENS = 700
STATE = None                       # تنبل، تا opslib.OPS در تست قابلِ جابه‌جایی بماند


def _state_path() -> Path:
    return opslib.OPS / "state" / "teacher-loop.json"


def _pairs_path() -> Path:
    return opslib.OPS / "state" / "teacher-pairs.jsonl"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _today(now: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(now))


def _load_state(now: float) -> dict:
    try:
        d = json.loads(_state_path().read_text("utf-8"))
    except (OSError, ValueError):
        d = {}
    if not isinstance(d, dict) or d.get("day") != _today(now):
        d = {"day": _today(now), "used": 0}
    return d


def _save_state(d: dict) -> None:
    try:
        p = _state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
    except OSError:
        pass


def daily_cap() -> int:
    try:
        v = int(os.environ.get("OCTOPUS_TEACHER_DAILY", "") or DAILY_DEFAULT)
    except (TypeError, ValueError):
        return DAILY_DEFAULT
    return v if 1 <= v <= 60 else DAILY_DEFAULT


# ─── داورهای عینی ───────────────────────────────────────────────────────────
def grade_json(text: str, required: "list | None" = None) -> dict:
    """داورِ عینیِ «JSON درست»: پارس می‌شود؟ کلیدهای لازم را دارد؟

    عمداً کوچک و بی‌ابهام است. داورِ مبهم بدتر از نداشتنِ داور است، چون نمرهٔ
    بی‌پایه را با نمرهٔ واقعی قاطی می‌کند و بعد نمی‌شود جدایشان کرد."""
    try:
        from client import extract_json
        obj = extract_json(str(text or ""))
    except Exception:  # noqa: BLE001
        obj = None
    if not isinstance(obj, dict):
        return {"graded": True, "score": 0.0, "why": "JSON پارس نشد"}
    miss = [k for k in (required or []) if k not in obj]
    if miss:
        return {"graded": True, "score": 0.3,
                "why": f"کلیدهای غایب: {', '.join(map(str, miss))[:80]}"}
    return {"graded": True, "score": 1.0, "why": "JSON کامل"}


UNGRADED = {"graded": False, "score": None, "why": "داورِ عینی نداشت"}


# ─── حلقه ──────────────────────────────────────────────────────────────────
def pair(*, task: str, prompt: str, system: str = "",
         grader=None, teacher_fn=None, student_fn=None,
         now: "float | None" = None) -> dict:
    """یک جفتِ معلم/شاگرد روی یک سؤال.

    خروجی: {ok, reason, pair?} — `ok=False` یعنی هیچ تماسی زده نشد."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    now = time.time() if now is None else float(now)
    st = _load_state(now)
    cap = daily_cap()
    if st.get("used", 0) >= cap:
        return {"ok": False, "reason": "daily-cap", "cap": cap}

    # سهمیه **قبل** از تماس می‌سوزد. اگر بعد بسوزد، هر انفجارِ وسطِ راه یعنی
    # سهمیه دست‌نخورده می‌ماند و تیکِ بعدی دوباره پول خرج می‌کند — همان اشتباهی
    # که در ماژولِ ابتکار یک بار گرفته شد.
    st["used"] = int(st.get("used", 0)) + 1
    _save_state(st)

    traj = f"tp-{int(now)}-{st['used']}"
    t_out = s_out = ""
    t_err = s_err = ""
    try:
        if teacher_fn is None:
            import model_router
            teacher_fn = model_router.ask
        r = teacher_fn(task, prompt, system=system, max_tokens=MAX_TOKENS,
                       tier="primary")
        if not r.get("ok"):
            t_err = str(r.get("reason") or "no-answer")[:80]
        elif r.get("tier") == "local" or r.get("fallback_from"):
            # ⚠️ اگر مسیر به محلی افتاده باشد، این جفت **معلم ندارد** — دو جوابِ
            # یک مغز است. ذخیره‌اش به‌عنوان جفتِ معلم/شاگرد دروغ است.
            t_err = "به مغزِ محلی افتاد — معلمی در کار نبود"
        else:
            t_out = str(r.get("text") or "")
    except Exception as e:  # noqa: BLE001
        t_err = type(e).__name__

    # شاگرد هم از **همان در** می‌رود، نه از `local_llm.ask` مستقیم. سه دلیل:
    # فنسِ تزریق روی ورودی اعمال می‌شود، سوخت شمرده می‌شود، و امضای هر دو طرفِ
    # جفت یکی می‌ماند. گاردِ inventory دقیقاً همین را همان لحظه گرفت.
    try:
        if student_fn is None:
            import model_router
            student_fn = model_router.ask
        s = student_fn(task, prompt, system=system, max_tokens=MAX_TOKENS,
                       tier="local")
        s_out = str((s or {}).get("text") if isinstance(s, dict) else s or "")
    except Exception as e:  # noqa: BLE001
        s_err = type(e).__name__

    g = grader or (lambda _t: dict(UNGRADED))
    t_grade = g(t_out) if t_out else {"graded": True, "score": 0.0, "why": t_err or "خالی"}
    s_grade = g(s_out) if s_out else {"graded": True, "score": 0.0, "why": s_err or "خالی"}

    rec = {
        "schema": SCHEMA, "ts": opslib.now_iso(), "traj_id": traj,
        "task": str(task or "")[:60],
        "teacher": {"ok": bool(t_out), "err": t_err, "grade": t_grade},
        "student": {"ok": bool(s_out), "err": s_err, "grade": s_grade},
        "usable_for_distill": bool(
            t_out and s_out and t_grade.get("graded") and s_grade.get("graded")
            and (t_grade.get("score") or 0) > (s_grade.get("score") or 0)),
    }
    _write_pair(rec, t_out, s_out, prompt, system)

    try:
        import trajectory_log as tl
        tl.step(traj_id=traj, phase="decide", action=str(task)[:120],
                state={"has_teacher": bool(t_out), "has_student": bool(s_out)},
                decision={"usable": rec["usable_for_distill"],
                          "teacher_score": t_grade.get("score"),
                          "student_score": s_grade.get("score")},
                meta={"source": "teacher_loop.pair"})
    except Exception:  # noqa: BLE001
        pass

    return {"ok": True, "reason": "", "pair": rec}


def _write_pair(rec: dict, t_out: str, s_out: str, prompt: str, system: str) -> bool:
    """متنِ کاملِ جفت — از همان دروازهٔ fail-closed دفترِ مسیر.

    متنِ خام این‌جا لازم است (بدونش تقطیر ممکن نیست) و دقیقاً به همین دلیل
    خطرناک‌ترین فایلِ ماست. اگر redaction نشد، جفت **نوشته نمی‌شود**."""
    try:
        import trajectory_log as tl
        body = dict(rec)
        body["texts"] = {
            "prompt": tl._safe(prompt), "system": tl._safe(system),
            "teacher": tl._safe(t_out), "student": tl._safe(s_out),
        }
    except Exception:  # noqa: BLE001
        return False
    try:
        p = _pairs_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(body, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def stats() -> dict:
    """نسبتی که تعیین می‌کند مرحلهٔ بعد ارزش دارد یا نه."""
    rows = []
    try:
        for ln in _pairs_path().read_text("utf-8").splitlines():
            if ln.strip():
                try:
                    rows.append(json.loads(ln))
                except ValueError:
                    continue
    except OSError:
        pass
    graded = sum(1 for r in rows
                 if (r.get("teacher") or {}).get("grade", {}).get("graded"))
    usable = sum(1 for r in rows if r.get("usable_for_distill"))
    return {"pairs": len(rows), "graded": graded, "usable": usable}


def card() -> str:
    """کارت — و صادقانه می‌گوید داده هنوز به دردِ تقطیر می‌خورد یا نه."""
    s = stats()
    if not enabled():
        return ("🎓 <b>حلقهٔ معلم: خاموش</b>\n"
                "▸ هیچ تماسی، هیچ خرجی.\n"
                "▸ نکنی: همین‌طور می‌ماند.")
    lines = ["🎓 <b>حلقهٔ معلم</b>",
             f"▸ {s['pairs']} جفت، {s['graded']} تای‌شان نمره‌دار",
             f"▸ {s['usable']} جفت واقعاً به دردِ تقطیر می‌خورد"]
    if s["pairs"] and s["usable"] / max(1, s["pairs"]) < 0.2:
        lines.append("▸ ⚠️ نسبت پایین است — این حجم داده نیست، فقط حجم است.")
    lines += ["", "▸ نکنی: هیچ — هیچ وزنی این‌جا عوض نمی‌شود."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "cap": daily_cap(), **stats()},
                     ensure_ascii=False, indent=1))
