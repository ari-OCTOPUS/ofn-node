"""trajectory_log — دفترِ مسیر (G0 از قوسِ جفت‌گیری).

چه چیزی و چرا
─────────────
تا امروز اختاپوس هزار تصمیم گرفته و هیچ‌کدام به شکلی ذخیره نشده که بشود از آن
**یاد گرفت**. لاگ‌ها هست، ledger هست، رویداد هست — ولی هیچ‌کدام سه‌تاییِ کاملِ
«وضعیت → تصمیم → نتیجه» را کنارِ هم نگه نمی‌دارد. بدونِ آن سه‌تایی، هر شکلی از
تقطیر (W5) روی هوا ساخته می‌شود: مدل نمی‌داند در چه وضعیتی چه کرد و چه شد.

این ماژول فقط همان سه‌تایی را می‌نویسد. هیچ یادگیری این‌جا نیست، هیچ تغییرِ
رفتاری هم نیست — فقط ثبت.

سه قیدِ سختی که شکلِ فایل را تعیین کرد
──────────────────────────────────────
۱) **redact ِ fail-closed.** یک دفترِ مسیر بدترین جای ممکن برای نشتِ راز است،
   چون هدفِ وجودی‌اش این است که بعداً به یک مدل خورانده شود. اگر redaction در
   دسترس نباشد، رکورد **دور ریخته می‌شود** — نه اینکه خام نوشته شود. این تنها
   جایی در ماژول است که سکوت پذیرفته نیست: افتادنِ رکورد شمرده و گزارش می‌شود.

۲) **نتیجه بعداً می‌آید.** لحظهٔ تصمیم و لحظهٔ نتیجه یکی نیستند. پس رکورد در دو
   نوبت نوشته می‌شود و با `traj_id` به هم وصل می‌شود — append-only، هرگز
   بازنویسی. یک مسیرِ بی‌نتیجه هم داده است («تصمیم گرفتیم و هیچ‌وقت نفهمیدیم چه
   شد» خودش یافته است).

۳) **کرانِ رشد.** دفتری که بی‌مرز رشد کند، روزی دیسک را پر می‌کند و آن روز
   ارگانیسم می‌خوابد. سقفِ خطی دارد و کهنه‌ها به فایلِ چرخشی می‌روند — منتقل،
   نه حذف.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_TRAJECTORY_LOG"
SCHEMA = "trajectory.v1"
MAX_LINES = 20_000                 # ~۲۰ هزار قدم؛ بعد چرخش
MAX_FIELD = 2_000                  # هر فیلدِ متنی کران‌دار


def _path() -> Path:
    return opslib.OPS / "state" / "trajectories.jsonl"


def _rotated() -> Path:
    return opslib.OPS / "state" / "trajectories-prev.jsonl"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ─── redaction: تنها دروازه ────────────────────────────────────────────────
_DROPPED = {"n": 0, "why": ""}


def _safe(value):
    """هر مقدارِ متنی از پاسِ redaction رد می‌شود. شکست → استثنا (fail-closed).

    عمداً استثنا می‌دهد و None برنمی‌گرداند: `None` را می‌شود ناخواسته نوشت،
    استثنا را نمی‌شود ناخواسته نادیده گرفت."""
    if isinstance(value, dict):
        return {str(k)[:120]: _safe(v) for k, v in list(value.items())[:40]}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in list(value)[:40]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    import cockpit_readmodel as _crm      # نبودش = استثنا = رکورد دور ریخته می‌شود
    return _crm.redact(str(value))[:MAX_FIELD]


def _append(rec: dict) -> bool:
    p = _path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        return False
    _maybe_rotate(p)
    return True


def _maybe_rotate(p: Path) -> None:
    """کهنه‌ها **منتقل** می‌شوند، نه حذف — قاعدهٔ اولِ این vault."""
    try:
        if sum(1 for _ in open(p, encoding="utf-8")) <= MAX_LINES:
            return
        prev = _rotated()
        if prev.exists():
            prev.unlink()          # فقط نسخهٔ چرخشیِ قبلی؛ دادهٔ زنده هرگز
        p.replace(prev)
    except OSError:
        pass


# ─── API ───────────────────────────────────────────────────────────────────
def step(*, traj_id: str, phase: str, state=None, action=None,
         decision=None, meta=None) -> bool:
    """یک قدمِ مسیر. `phase` ∈ observe|decide|act|outcome.

    خروجی True یعنی نوشته شد. False یعنی یا فلگ خاموش بود یا رکورد به‌خاطرِ
    شکستِ redaction **عمداً** دور ریخته شد — در حالتِ دوم شمارنده بالا می‌رود."""
    if not enabled():
        return False
    try:
        rec = {
            "schema": SCHEMA,
            "ts": opslib.now_iso(),
            "traj_id": str(traj_id or "")[:64],
            "phase": str(phase or "")[:24],
            "state": _safe(state),
            "action": _safe(action),
            "decision": _safe(decision),
            "meta": _safe(meta),
        }
    except Exception as e:  # noqa: BLE001 — fail-closed: هیچ رکوردِ خامی
        _DROPPED["n"] += 1
        _DROPPED["why"] = type(e).__name__
        try:
            if _DROPPED["n"] in (1, 10, 100):
                opslib.alert([f"دفترِ مسیر: {_DROPPED['n']} رکورد به‌خاطرِ "
                              f"شکستِ redaction دور ریخته شد ({_DROPPED['why']})"])
        except Exception:  # noqa: BLE001
            pass
        return False
    return _append(rec)


def outcome(*, traj_id: str, result: str, detail=None, reward=None) -> bool:
    """نتیجهٔ یک مسیر — معمولاً دقایق یا ساعت‌ها بعد از تصمیم."""
    return step(traj_id=traj_id, phase="outcome",
                decision={"result": str(result or "")[:64], "reward": reward},
                meta=detail)


def dropped() -> dict:
    """چند رکورد به‌خاطرِ redaction افتاد. صفر نبودنش یعنی چیزی خراب است."""
    return dict(_DROPPED)


def read(limit: int = 200) -> list:
    """آخرین قدم‌ها — برای کارت و برای W5. fail-soft."""
    try:
        lines = open(_path(), encoding="utf-8").read().splitlines()
    except OSError:
        return []
    out = []
    for ln in lines[-max(1, int(limit)):]:
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def card() -> str:
    """کارتِ «چه چیزی از خودم یاد گرفته‌ام» — شمارش، نه محتوا."""
    import html
    rows = read(2000)
    if not enabled():
        return ("🧭 <b>دفترِ مسیر: خاموش</b>\n"
                "▸ هیچ قدمی ثبت نمی‌شود.\n"
                "▸ نکنی: همین‌طور می‌ماند.")
    trajs = {}
    for r in rows:
        trajs.setdefault(r.get("traj_id"), []).append(r.get("phase"))
    closed = sum(1 for v in trajs.values() if "outcome" in v)
    drop = _DROPPED["n"]
    lines = ["🧭 <b>دفترِ مسیر</b>",
             f"▸ {len(rows)} قدم در {len(trajs)} مسیر",
             f"▸ {closed} مسیر نتیجه‌اش را می‌دانیم، "
             f"{len(trajs) - closed} هنوز نه"]
    if drop:
        lines.append(f"▸ ⚠️ {drop} رکورد افتاد ({html.escape(_DROPPED['why'])}) "
                     "— یعنی لایهٔ redaction مشکل دارد")
    lines += ["", "▸ نکنی: هیچ — این فقط دفتر است، نه یادگیری."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "path": str(_path()),
                      "steps": len(read(5000)), "dropped": dropped()},
                     ensure_ascii=False, indent=1))
