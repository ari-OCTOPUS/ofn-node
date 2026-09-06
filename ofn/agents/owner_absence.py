"""owner_absence — بایست بدون اینکه بلغزد (OCTOPUS-AUTONOMY-SPEC §3).

فرقِ خودمختاریِ کار از خودمختاریِ اختیار: این ماژول غیبتِ مالک را می‌سنجد و
سیستم را محافظه‌کار می‌کند — «سقفِ مجاز در غیابِ ناظر، مجوز نیست» (سقفِ
۱۰/روز با فرضِ حضور تصویب شده). آستانه‌ها با رأیِ تفویض 2026-09-03 پذیرفته
شد (پیشنهاد §7 سند: absent_hard=7d؛ ارسال در غیبت = صفر مطلق).

منبعِ «آخرین اقدام مالک»: آخرین commit روی main (هر merge = رأیِ معتبرِ
GOV-V6 = حضور) + فایلِ دستی owner-heartbeat.txt (هر پیام مالک، ایجنتش را
مهر می‌زند). dead-man معکوس: اگر گزارشِ دکتر بیش از ۳ تیکِ متوالی نیامده
باشد، خودِ غیبت مستقل از سن، Conservation را روشن می‌کند — نبودِ تشخیص =
بدترین فرض.

نوشتن‌های مجاز این ماژول: فایل حالت conservation-mode.json و OWNER-QUEUE.md
در STATE_DIR — هیچ‌چیز دیگر؛ هیچ ارسال؛ هیچ merge (ادغام فقط با رأی معتبر
انسان روی GitHub می‌گذرد و این ماژول به آن مسیر دست نمی‌زند).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "octopus.owner-absence.v1"
CONSERVATION_FILE = "conservation-mode.json"
OWNER_QUEUE_FILE = "OWNER-QUEUE.md"
HEARTBEAT_FILE = "owner-heartbeat.txt"
GITHUB_MAIN = "https://api.github.com/repos/ari-OCTOPUS/ofn-node/commits/main"

# آستانه‌ها (ساعت) — پذیرفته با رأی تفویض مالک 2026-09-03
ABSENT_SOFT_H = 24.0     # صف‌بندی ادامه؛ هیچ تغییر رفتار
ABSENT_HARD_H = 7 * 24.0   # Conservation Mode (صفر ارسال لید)
ABSENT_DEEP_H = 30 * 24.0  # + حداقل‌سازی نرخ کار
DOCTOR_SILENT_TICKS = 3   # تیکِ ساعتیِ دکتر
TICK_H = 1.0


def _state_dir() -> Path:
    return opslib.STATE_DIR


def fetch_last_main_commit(timeout: int = 15) -> tuple[str | None, str]:
    """آخرین commit روی main از API عمومی — خطا = UNKNOWN، نه حدس."""
    req = urllib.request.Request(
        GITHUB_MAIN, headers={"Accept": "application/vnd.github+json",
                              "User-Agent": "octopus-owner-absence"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            date = json.loads(r.read().decode("utf-8")) \
                .get("commit", {}).get("committer", {}).get("date")
            return date, "github-api"
    except Exception as e:  # noqa: BLE001
        return None, f"err:{type(e).__name__}"


def _parse_iso(s: str) -> float:
    import datetime as _dt
    return _dt.datetime.fromisoformat(
        s.replace("Z", "+00:00")).timestamp()


def last_owner_action(
    now: float | None = None,
    fetch=None,
    heartbeat: Path | None = None,
) -> dict:
    """جدیدترین نشانهٔ حضور: max(آخرین commit مالک‌سو، مهرِ دستی)."""
    import datetime as _dt
    now = now if now is not None else _dt.datetime.now(
        _dt.timezone.utc).timestamp()
    fetch = fetch or fetch_last_main_commit
    stamps: list[tuple[str, str]] = []
    iso, src = fetch()
    if iso:
        stamps.append((iso, src))
    hb = heartbeat or (_state_dir() / HEARTBEAT_FILE)
    if hb.exists():
        try:
            stamps.append((hb.read_text(encoding="utf-8").strip(),
                           "owner-heartbeat"))
        except OSError:
            pass
    if not stamps:
        return {"last_action": None, "age_h": None, "source":
                "none — UNKNOWN, fail-closed tier"}
    best_iso, best_src = max(stamps, key=lambda t: _parse_iso(t[0]))
    age_h = (now - _parse_iso(best_iso)) / 3600.0
    return {"last_action": best_iso, "source": best_src,
            "age_h": round(age_h, 1)}


def absence_tier(age_h: float | None) -> str:
    """present | soft | hard | deep — نبودِ داده = بدترین فرض نیست؛
    hard کافی است چون conservation همان‌جا شروع می‌شود."""
    if age_h is None:
        return "hard"          # UNKNOWN → محافظه‌کار
    if age_h <= ABSENT_SOFT_H:
        return "present"
    if age_h <= ABSENT_HARD_H:
        return "soft"
    if age_h <= ABSENT_DEEP_H:
        return "hard"
    return "deep"


def evaluate_conservation(
    age_h: float | None,
    doctor_report_age_h: float | None = None,
) -> dict:
    """حکم: خاموش | روشن (absent) | روشن (doctor-silent). خروجی reason دارد."""
    if doctor_report_age_h is not None and \
            doctor_report_age_h > DOCTOR_SILENT_TICKS * TICK_H:
        return {"on": True, "reason":
                f"doctor-silent>{DOCTOR_SILENT_TICKS}ticks — worst-case assume"}
    tier = absence_tier(age_h)
    if tier in ("hard", "deep"):
        return {"on": True, "reason":
                f"owner-absent tier={tier} (>{ABSENT_HARD_H}h)"}
    return {"on": False, "reason": f"tier={tier}"}


# ── فایل حالت (خواندنِ گیتِ ارسال) ─────────────────────────────────────────

def conservation_active(state_dir: Path | None = None) -> str:
    """رشتهٔ خالی = خاموش. غیرخالی = دلیلِ deny (فایل روشن یا corrupt).

    فایلِ ناموجود = خاموش (حالت اولیهٔ عادی؛ تیک اولش را می‌سازد)؛
    فایلِ خراب = روشن با دلیلِ unreadable — fail-closed."""
    p = (state_dir or _state_dir()) / CONSERVATION_FILE
    if not p.exists():
        return ""
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("on"):
            return str(data.get("reason") or "conservation-on")
        return ""
    except (OSError, ValueError):
        return "conservation-state-unreadable"


def write_conservation(verdict: dict, state_dir: Path | None = None) -> Path:
    p = (state_dir or _state_dir()) / CONSERVATION_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "on": verdict["on"], "reason": verdict["reason"],
        "since": opslib.now_iso(),
    }, ensure_ascii=False), encoding="utf-8")
    return p


def doctor_report_age_h(state_dir: Path | None = None,
                        now: float | None = None) -> float | None:
    import datetime as _dt
    p = (state_dir or _state_dir()) / "doctor" / "report.json"
    if not p.exists():
        return None          # دکتر هنوز هرگز اجرا نشده — نه سالم نه خراب
    now = now if now is not None else _dt.datetime.now(
        _dt.timezone.utc).timestamp()
    try:
        gen = _parse_iso(json.loads(
            p.read_text(encoding="utf-8"))["generated_at"])
        return (now - gen) / 3600.0
    except (OSError, ValueError, KeyError):
        return None


# ── OWNER-QUEUE.md — مهم‌ترین خروجیِ غیبت ──────────────────────────────────

def build_owner_queue(
    absence: dict,
    verdict: dict,
    doctor_report: Path | None = None,
) -> str:
    """یک فایل، مرتب، هر آیتم با id پایدار. مالک بعد از یک ماه باید در
    ۱۵ دقیقه بتواند همه‌چیز را جبران کند."""
    lines = [
        "# OWNER-QUEUE — جمع‌بندی تصمیم‌های در انتظار مالک",
        "",
        f"به‌روزرسانی: {opslib.now_iso()} · "
        f"آخرین اقدام مالک: {absence.get('last_action') or 'UNKNOWN'} "
        f"({absence.get('age_h')}h پیش) · conservation: "
        f"{'ON' if verdict['on'] else 'off'} ({verdict['reason']})",
        "",
    ]
    items: list[tuple[str, str]] = []
    dr = doctor_report or (_state_dir() / "doctor" / "report.json")
    if dr.exists():
        try:
            rep = json.loads(dr.read_text(encoding="utf-8"))
            for m in rep.get("measurements", []):
                if m.get("verdict") in ("unhealthy", "unknown"):
                    items.append((
                        f"OQ-{m['name'].replace('.', '-')}",
                        f"[{m['verdict'].upper()}] {m['name']} — "
                        f"{m.get('detail') or 'see doctor report'} "
                        f"(بازآزمایی: `{m['command']}`)"))
        except (OSError, ValueError):
            items.append(("OQ-doctor-report",
                          "[UNKNOWN] گزارش دکتر ناخواناست — خودش یک آیتم است"))
    if verdict["on"]:
        items.append(("OQ-conservation",
                      "[POLICY] Conservation فعال است — بازگشت مالک: "
                      "مهر `owner-heartbeat.txt` + یک تیک، خاموشش می‌کند"))
    if not items:
        items.append(("OQ-none",
                      "صف خالی — همهٔ اندازه‌گیری‌ها سبز بودند"))
    for oid, body in items:
        lines.append(f"- **{oid}** · {body}")
    lines.append("")
    return "\n".join(lines)


def write_owner_queue(text: str, state_dir: Path | None = None) -> Path:
    p = (state_dir or _state_dir()) / OWNER_QUEUE_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# ── تیک ─────────────────────────────────────────────────────────────────────

def run(state_dir: Path | None = None) -> dict:
    absence = last_owner_action(heartbeat=(state_dir or _state_dir())
                                / HEARTBEAT_FILE)
    doc_age = doctor_report_age_h(state_dir)
    verdict = evaluate_conservation(absence.get("age_h"), doc_age)
    write_conservation(verdict, state_dir)
    queue = build_owner_queue(absence, verdict,
                              (state_dir or _state_dir()) / "doctor"
                              / "report.json")
    qp = write_owner_queue(queue, state_dir)
    return {
        "schema": SCHEMA,
        "generated_at": opslib.now_iso(),
        "absence": absence,
        "tier": absence_tier(absence.get("age_h")),
        "doctor_report_age_h": doc_age,
        "conservation": verdict,
        "owner_queue": str(qp),
    }


def main() -> int:
    print(json.dumps(run(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
