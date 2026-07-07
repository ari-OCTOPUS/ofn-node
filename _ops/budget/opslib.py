#!/usr/bin/env python3
"""
opslib.py — کتابخانهٔ مشترک لایهٔ متابولیسم (STAGE 1..3 پک متابولیسم-مناظره-تکثیر).

نقش: مسیرها، بارگذاری budgets.yaml (تک‌منبع حقیقت — فقط‌خواندنی، H7)، واحد micro-USD،
نرخ ارز پین‌شده، قفل فایل به سبک budget_gate، پل ledger ژنوم، پرچم‌های STOP/FREEZE.

ناوردی‌ها (از ORGANISM-SPEC §ناوردی‌ها):
  I2: این لایه فقط MEASURE/propose می‌کند — تنها enforcer، budget_gate است.
  I3: fail-closed — ناسازگاری تلمتری↔budgets = FREEZE + [CONFLICT] به صف انسان.
  I6: هیچ ویرایشی روی budgets.yaml — فقط diff پیشنهادی (budgets-proposed-diff.md).
status: propose (ساخته‌شده به دستور «تا کد کامل برو» 2026-07-06؛ صفر اتوماسیون روشن نشد).
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import os
import pathlib
import sys
import time

# ─── تلهٔ cp1252 ویندوز: خروجی کنسول همیشه UTF-8 (پک B.1) ───────────────────
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

# ─── مسیرها (قرارداد env موجود: OPS_DIR/BUDGET_STATE + نام‌های نو ORG_*) ─────
ORG_ROOT   = pathlib.Path(os.environ.get("ORG_ROOT", r"F:\backup"))
OPS        = pathlib.Path(os.environ.get("OPS_DIR", str(ORG_ROOT / "_ops")))
BUDGET_DIR = OPS / "budget"
STATE_DIR  = OPS / "state"
DEBATE_DIR = OPS / "debate"
ARCHITECT  = ORG_ROOT / "04 - Architect System"
SCRIPTS    = pathlib.Path(os.environ.get("SCRIPTS_DIR", str(ARCHITECT / "scripts")))
PROMPTS    = ARCHITECT / "prompts"
GENOME_DIR = pathlib.Path(os.environ.get("GENOME_DIR",
                                         str(ORG_ROOT / "07 - Knowledge" / "genome-system")))
BRAIN_DIR  = pathlib.Path(os.environ.get("BRAIN_DIR",
                                         str(ORG_ROOT / "_launchpad" / "second-brain-live" / "control-brain")))
BUDGETS_YAML   = BUDGET_DIR / "budgets.yaml"
BUDGET_STATE   = pathlib.Path(os.environ.get("BUDGET_STATE", str(BUDGET_DIR / "budget-state.json")))
ORGAN_STATE    = BUDGET_DIR / "organ-state.json"
ORGAN_LOG      = BUDGET_DIR / "organ-gate-log.jsonl"
FREEZE_FLAG    = BUDGET_DIR / "FREEZE.flag"
STOP_ARCHITECT = ARCHITECT / "STOP"            # kill کلان (governor_shadow هم همین را چک می‌کند)
STOP_METABOLIC = OPS / "STOP-METABOLIC"
STOP_DEBATE    = OPS / "STOP-DEBATE"
STOP_ORGANISM  = OPS / "STOP-ORGANISM"
ALERTS_MD      = OPS / "governor" / "governor-alerts.md"     # همان مقصد governor_shadow
HEARTBEAT_MD   = ORG_ROOT / "_memory" / "HEARTBEAT.md"       # صریحاً _memory ریشه (نه 04/_memory)
AGENT_QUESTIONS = ORG_ROOT / "00 - Inbox" / "AGENT_QUESTIONS.md"

# فعال‌سازی زندهٔ مناظره/تکثیر پیش از این تاریخ ممنوع است (سپر pitch فاز −۱، پک §D.3)
LIVE_GATE_DATE = _dt.date(2026, 7, 21)
# پرچم‌های فعال‌سازی فقط-مالک (وجود فایل = verdict؛ کد هرگز خودش نمی‌سازد)
ACT_DEBATE      = OPS / "ACTIVATION-DEBATE.flag"
ACT_REPLICATION = OPS / "ACTIVATION-REPLICATION.flag"
ACT_GOV_LLM     = OPS / "ACTIVATION-GOVERNOR-LLM.flag"


def now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def today() -> str:
    return _dt.date.today().isoformat()


def month() -> str:
    return today()[:7]


# ─── micro-USD: محور انرژی در یک واحد صحیح (پک T1) ──────────────────────────
def micro(usd: float) -> int:
    return int(round(usd * 1_000_000))


def usd(micro_usd: int) -> float:
    return micro_usd / 1_000_000.0


# ─── budgets.yaml: فقط‌خواندنی، تک‌منبع حقیقت ────────────────────────────────
_budgets_cache: dict | None = None


def load_budgets(force: bool = False) -> dict:
    """budgets.yaml را می‌خواند. نبود فایل/کلید ضروری = استثنا (fail-closed، نه پیش‌فرض خیالی)."""
    global _budgets_cache
    if _budgets_cache is not None and not force:
        return _budgets_cache
    import yaml  # PyYAML 6.x موجود روی ماشین (چک‌شده 2026-07-06)
    data = yaml.safe_load(BUDGETS_YAML.read_text("utf-8"))
    if not isinstance(data, dict) or "global" not in data or "projects" not in data:
        raise RuntimeError("budgets.yaml unreadable or missing global/projects — FREEZE")
    _budgets_cache = data
    return data


def fx_aud_per_usd() -> tuple[float, str]:
    """نرخ پین‌شدهٔ USD→AUD. اگر در budgets.yaml نبود، 1.5 (هم‌ارز budget_gate.AUD) با تگ EST.
    عدد داخل budgets.yaml = پیشنهاد diff (budgets-proposed-diff.md)، نه ویرایش ما."""
    g = load_budgets().get("global", {})
    if "aud_per_usd" in g:
        return float(g["aud_per_usd"]), "FACT(budgets.yaml)"
    return 1.5, "EST(default=budget_gate.AUD)"


def organ_table() -> dict[str, dict]:
    """ارگان‌های رسمی از budgets.yaml + ارگان مصنوعی DEBATE_LOOP (پیش‌فرض V1: cap ماهانه 5 AUD).
    اگر مالک بخش loop را به budgets.yaml اضافه کند (diff پیشنهادی)، همان مرجع می‌شود."""
    b = load_budgets()
    organs = {str(k): dict(v or {}) for k, v in b.get("projects", {}).items()}
    loop_cfg = (b.get("loop") or {}).get("DEBATE_LOOP", {"cap_monthly": 5, "floor": 0})
    organs.setdefault("DEBATE_LOOP", {})
    organs["DEBATE_LOOP"].setdefault("floor", loop_cfg.get("floor", 0))
    organs["DEBATE_LOOP"]["cap_monthly"] = loop_cfg.get("cap_monthly", 5)   # V1 پیش‌فرض پک [SPEC]
    return organs


# ─── قفل + state اتمیک (همان الگوی budget_gate: O_EXCL + steal قفل کهنه) ────
class LockedJson:
    def __init__(self, path: pathlib.Path, stale_s: float = 30.0):
        self.path = pathlib.Path(path)
        self.lock = pathlib.Path(str(path) + ".lock")
        self.stale = stale_s
        self._fd: int | None = None

    def __enter__(self) -> "LockedJson":
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(50):
            try:
                self._fd = os.open(str(self.lock), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.lock) > self.stale:
                        os.unlink(self.lock)
                        continue
                except OSError:
                    pass
                time.sleep(0.1)
        raise TimeoutError(f"lock busy: {self.lock}")

    def __exit__(self, *exc) -> None:
        if self._fd is not None:
            os.close(self._fd)
        try:
            os.unlink(self.lock)
        except OSError:
            pass

    def read(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text("utf-8"))

    def write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, self.path)


def append_jsonl(path: pathlib.Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─── پرچم‌ها ─────────────────────────────────────────────────────────────────
def halted(*, for_debate: bool = False) -> str | None:
    """اولین دلیل توقف یا None. ترتیب = شدت."""
    if STOP_ARCHITECT.exists():
        return "STOP(architect)"
    if STOP_METABOLIC.exists():
        return "STOP-METABOLIC"
    if for_debate and STOP_DEBATE.exists():
        return "STOP-DEBATE"
    return None


def frozen() -> bool:
    return FREEZE_FLAG.exists()


def freeze(reason: str) -> None:
    """I3: ناسازگاری = FREEZE همهٔ grantها + ثبت دلیل (idempotent)."""
    FREEZE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    if not FREEZE_FLAG.exists():
        FREEZE_FLAG.write_text(f"{now_iso()} {reason}\n", "utf-8")
    alert([f"FREEZE: {reason}"])


# ─── گزارش‌دهی (قراردادهای موجود governor_shadow) ────────────────────────────
def alert(items: list[str]) -> None:
    ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_MD.open("a", encoding="utf-8") as f:
        f.write(f"## {now_iso()} (metabolism)\n" + "\n".join(f"- ⚠️ {i}" for i in items) + "\n\n")


def heartbeat(line: str) -> None:
    """فقط سطر خودت را append کن — هرگز بازنویسی (الگوی governor_shadow.beat)."""
    HEARTBEAT_MD.parent.mkdir(parents=True, exist_ok=True)
    with HEARTBEAT_MD.open("a", encoding="utf-8") as f:
        f.write(f"- {now_iso()} · {line}\n")


def conflict_to_human(tag: str, question: str) -> None:
    """[CONFLICT] به صف انسان (AGENT_QUESTIONS، append-only). حداکثر یک‌بار در روز به‌ازای هر tag."""
    marker = f"[CONFLICT-{tag}-{today()}]"
    try:
        existing = AGENT_QUESTIONS.read_text("utf-8")
    except OSError:
        existing = ""
    if marker in existing:
        return
    with AGENT_QUESTIONS.open("a", encoding="utf-8") as f:
        f.write(f"\n## {now_iso()} — metabolism (خودکار) {marker}\n\n{question}\n")


# ─── پل ledger ژنوم (تنها حافظهٔ ماشینی مشترک؛ NOTE + subtype طبق V2 پیش‌فرض) ─
_ledger = None


def genome_ledger():
    """نمونهٔ Ledger ژنوم‌سیستم؛ EVENT_TYPES بسته است → همیشه NOTE + payload.subtype."""
    global _ledger
    if _ledger is None:
        sys.path.insert(0, str(GENOME_DIR / "ledger"))
        from ledger import Ledger  # noqa: E402
        _ledger = Ledger(GENOME_DIR / "ledger" / "ledger.jsonl")
    return _ledger


def ledger_note(subtype: str, payload: dict, actor: str) -> dict | None:
    """NOTE امن به ledger ژنوم. شکست = alert (خطای خاموش ممنوع) ولی جریان ادامه می‌یابد
    (مشاهده fail-soft است؛ خرج‌کردن fail-closed است و جای دیگری گیت می‌شود)."""
    try:
        return genome_ledger().append("NOTE", {"subtype": subtype, **payload}, actor=actor)
    except Exception as e:  # noqa: BLE001
        alert([f"ledger append failed ({subtype}): {e}"])
        append_jsonl(STATE_DIR / "ledger-fallback.jsonl",
                     {"ts": now_iso(), "subtype": subtype, "payload": payload, "actor": actor})
        return None


def live_gate_open(activation_flag: pathlib.Path) -> tuple[bool, str]:
    """گیت دوقفله برای هر مسیر زنده: (۱) تاریخ ≥ 2026-07-21 (سپر فاز −۱)، (۲) فایل پرچم
    که فقط مالک می‌سازد. کد حتی با پرچم، پیش از تاریخ باز نمی‌شود."""
    if _dt.date.today() < LIVE_GATE_DATE:
        return False, f"live locked until {LIVE_GATE_DATE.isoformat()} (phase -1 shield)"
    if not activation_flag.exists():
        return False, f"activation flag missing: {activation_flag.name} (owner-only)"
    return True, "open"
