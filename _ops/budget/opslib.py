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
# C1 (تری‌اسکن 2026-07-17): مسیرِ لجرِ ژنوم به absolute canonical پین شد تا worktreeی با
# ORG_ROOTِ متفاوت لجرِ زنده را fork نکند. arm env همان اول است (تستِ harness که GENOME_DIR
# را به sandbox می‌برد هنوز برنده است). لیترالِ F:\backup عیناً پیش‌فرضِ ORG_ROOT (خطِ ۳۲).
_GENOME_CANONICAL = pathlib.Path(r"F:\backup") / "07 - Knowledge" / "genome-system"
GENOME_DIR = pathlib.Path(os.environ.get("GENOME_DIR", str(_GENOME_CANONICAL)))
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
HALT_ALL       = OPS / "HALT-ALL"          # 🔴 مرزِ سختِ سراسری (پنیک): هر حلقه/کانکتور/باتِ بیرونی بی‌استثنا honor می‌کند
ALERTS_MD      = OPS / "governor" / "governor-alerts.md"     # همان مقصد governor_shadow
HEARTBEAT_MD   = ORG_ROOT / "_memory" / "HEARTBEAT.md"       # صریحاً _memory ریشه (نه 04/_memory)
AGENT_QUESTIONS = ORG_ROOT / "00 - Inbox" / "AGENT_QUESTIONS.md"

# germline vital (verdict آری 2026-07-07 #4): سن تازه‌ترین مصنوع بک‌آپ off-box
OFFBOX_DIR      = pathlib.Path(os.environ.get("GERMLINE_OFFBOX", r"E:\germline"))
GERMLINE_WARN_H = 2.0
GERMLINE_ERR_H  = 26.0

# de-mask بک‌آپ (OBS-02): پرچمِ صریحِ شکستِ git-write. مصنوعِ mtime می‌تواند دروغ بگوید
# (لاگی که کارِ شکست‌خورده «FAIL» به آن append می‌کند mtimeِ تازه دارد → بک‌آپِ مدام‌شکست‌خورده
# سبز خوانده می‌شود). این پرچم تنها منبعِ حقیقتِ صریح است — تا امروز هیچ‌کس نمی‌خواندش.
BACKUP_DIR      = OPS / "backup"
GITWRITE_FAILED = BACKUP_DIR / "GITWRITE-FAILED.flag"


def germline_lag_hours(offbox=None):
    """سن تازه‌ترین مصنوع germline (ساعت)؛ None = هیچ مصنوعی در دسترس نیست (خودش ERROR-سطح).
    فقط می‌خواند — دسترس‌ناپذیری دیسک دوم نباید حلقه را بکشد (fail-soft؛ آلارم با مصرف‌کننده)."""
    ob = pathlib.Path(offbox) if offbox else OFFBOX_DIR
    cands = [ob / "last_backup_manifest.json", ob / "hourly-latest.bundle"]
    try:
        cands += list(ob.glob("vault-*.bundle"))
    except OSError:
        pass
    stamps = []
    for p in cands:
        try:
            if p.exists():
                stamps.append(p.stat().st_mtime)
        except OSError:
            continue
    if not stamps:
        return None
    import time as _time
    return round((_time.time() - max(stamps)) / 3600.0, 2)


def gitwrite_failed() -> str | None:
    """دلیلِ شکستِ آخرین git-write اگر پرچمِ GITWRITE-FAILED.flag برافراشته باشد؛ وگرنه None.
    (OBS-02: تا امروز هیچ مصرف‌کننده‌ای این پرچم را نمی‌خواند.) فقط می‌خواند، fail-soft — ولی
    وجودِ فایل هرگز پنهان نمی‌شود: حتی اگر خواندنِ محتوا شکست بخورد، یک دلیلِ پیش‌فرض برمی‌گردد
    (پرچمِ برافراشته باید همیشه ناسالم شود، نه سبزِ کاذب)."""
    try:
        if not GITWRITE_FAILED.exists():
            return None
    except OSError:
        return None
    try:
        txt = GITWRITE_FAILED.read_text("utf-8", errors="replace")
    except OSError:
        txt = ""
    txt = txt.lstrip("﻿").strip()          # BOMِ ویندوز/فاصلهٔ ابتدایی
    first = txt.splitlines()[0].strip() if txt else ""
    return first or "GITWRITE-FAILED (بدونِ دلیلِ متنی)"


def backup_health(offbox=None) -> dict:
    """سلامتِ بک‌آپ = تازگیِ germline (mtime) + پرچمِ صریحِ شکستِ git-write.
    پرچمِ برافراشته همیشه غالب است و ناسالم می‌کند — صرف‌نظر از اینکه mtimeِ تازه سبز نشان دهد
    (رفعِ OBS-02: لاگِ مدامِ FAIL دیگر سبزِ کاذب نمی‌سازد). فقط می‌خواند، fail-soft، بدونِ وابستگیِ نو.
    خروجی: {healthy, level(ok|warn|err), lag_h, gitwrite_failed, reason}."""
    try:
        lag = germline_lag_hours(offbox)
    except Exception:  # noqa: BLE001 — مشاهده هرگز حلقه را نمی‌کشد
        lag = None
    try:
        failed = gitwrite_failed()
    except Exception:  # noqa: BLE001
        failed = None
    # سطح از سنِ mtime (رفتارِ germline_lag_hours دست‌نخورده — فقط تفسیر می‌شود)
    if lag is None:
        lag_level, lag_reason = "err", "هیچ مصنوعِ germline در دسترس نیست"
    elif lag >= GERMLINE_ERR_H:
        lag_level, lag_reason = "err", f"germline lag {lag}h ≥ {GERMLINE_ERR_H}h"
    elif lag >= GERMLINE_WARN_H:
        lag_level, lag_reason = "warn", f"germline lag {lag}h ≥ {GERMLINE_WARN_H}h"
    else:
        lag_level, lag_reason = "ok", None
    # پرچمِ صریحِ شکست غالب است — mtime هرچه باشد، ناسالم
    if failed:
        return {"healthy": False, "level": "err", "lag_h": lag,
                "gitwrite_failed": failed, "reason": f"GITWRITE-FAILED: {failed}"}
    return {"healthy": lag_level == "ok", "level": lag_level, "lag_h": lag,
            "gitwrite_failed": None, "reason": lag_reason}


def armed_activation_flags() -> list[str]:
    """نامِ همهٔ ACTIVATION-*.flag ِ برافراشته در _ops (اهرمِ فعال‌سازیِ فقط-مالک؛ وجودِ فایل = verdict).
    DSH-02: این کلیدها روی داشبورد نامرئی بودند. فقط می‌خواند، fail-soft."""
    try:
        return sorted(p.name for p in OPS.glob("ACTIVATION-*.flag"))
    except OSError:
        return []


def halt_reason() -> str | None:
    """اوراکلِ توقفِ سراسری برای نمایشِ داشبورد (fail-soft). اگر master_halted موجود بود
    (مرزِ سختِ سراسری) از همان استفاده می‌کند — HALT-ALL ← STOP(architect)؛ وگرنه به halted()
    برمی‌گردد (سازگارِ عقب: STOP معمار → 'STOP(architect)'). None = هیچ توقفِ سراسری.
    این تابع فقط سطحِ نمایش است و master_halted را باز تعریف نمی‌کند (نه شرطِ توقف اضافه/کم)."""
    fn = globals().get("master_halted")
    try:
        if callable(fn):
            return fn()
        return halted()
    except Exception:  # noqa: BLE001
        return None

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
        # VQ-STATE-WRITE-001: روی ویندوز `os.replace` گاهی با WinError 5 (قفلِ
        # گذرای AV/ایندکسر روی فایلِ مقصد) می‌شکند — نتیجه: `.tmp` تازه کنارِ
        # فایلِ اصلیِ کهنه، و heartbeat زنده بدونِ هیچ زنگی. retry ِ محدود با
        # backoff؛ شکستِ نهایی fail-loud می‌ماند (استثنا بالا می‌رود — بلعیدنش
        # کارِ این لایه نیست) + یک breadcrumb ِ ماشین‌خوان کنارِ فایل تا کهنگی
        # قابلِ تشخیصِ قطعی باشد نه حدسی.
        last: Exception | None = None
        delay = 0.05
        for _ in range(6):
            try:
                os.replace(tmp, self.path)
                return
            except (PermissionError, OSError) as e:
                last = e
                time.sleep(delay)
                delay = min(delay * 2, 0.8)
        try:
            pathlib.Path(str(self.path) + ".replace-failed.json").write_text(
                json.dumps({"ts": now_iso(), "error": str(last),
                            "tmp": str(tmp), "attempts": 6},
                           ensure_ascii=False), "utf-8")
        except OSError:
            pass
        raise last if last is not None else OSError("replace-failed")


def append_jsonl(path: pathlib.Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─── پرچم‌ها ─────────────────────────────────────────────────────────────────
def master_halted() -> str | None:
    """🔴 مرزِ سختِ سراسری: دو سوییچی که هر حلقه/کانکتور/باتِ بیرونی **بی‌استثنا** honor
    می‌کند. ترتیب = شدت (HALT-ALL ِ پنیک مقدم بر STOP ِ معمار). این تنها لایه‌ای است که
    هیچ‌کس حق نادیده‌گرفتنش را ندارد — نه tg-center، نه launchpad، نه هیچ connector.
    (رجوع: نقشهٔ کنترل‌پلین [[06 - Architecture Maps/CONTROL-PLANE-HALT-2026-07-13]].)"""
    if HALT_ALL.exists():
        return "HALT-ALL"
    if STOP_ARCHITECT.exists():
        return "STOP(architect)"
    return None


def halted(*, for_debate: bool = False) -> str | None:
    """اولین دلیل توقف یا None. ترتیب = شدت؛ مرزِ سختِ سراسری (master_halted) همیشه مقدم است.
    سازگارِ عقب: با STOP ِ معمار همچنان دقیقاً "STOP(architect)" برمی‌گرداند."""
    m = master_halted()
    if m:
        return m
    if STOP_METABOLIC.exists():
        return "STOP-METABOLIC"
    if for_debate and STOP_DEBATE.exists():
        return "STOP-DEBATE"
    return None


def raise_halt_all(reason: str) -> None:
    """🔴 پنیک: مرزِ سختِ سراسری را می‌نویسد (idempotent). هر حلقه تیکِ بعد تمیز می‌ایستد.
    آزادسازی فقط با clear_halt_all (مالک/پنل). کد این فایل را فقط از مسیرِ پنیکِ صریح می‌سازد
    (هم‌الگو با نوشتنِ STOP-ORGANISM توسط dashboard/approval_channel)."""
    HALT_ALL.parent.mkdir(parents=True, exist_ok=True)
    if not HALT_ALL.exists():
        HALT_ALL.write_text(f"{now_iso()} {reason}\n", "utf-8")
    alert([f"HALT-ALL raised: {reason}"])


def clear_halt_all() -> bool:
    """آزادسازیِ مرزِ سخت. خروجی: آیا فایلی وجود داشت که آزاد شود."""
    try:
        HALT_ALL.unlink()
        return True
    except OSError:
        return False


def frozen() -> bool:
    return FREEZE_FLAG.exists()


def freeze(reason: str) -> None:
    """I3: ناسازگاری = FREEZE همهٔ grantها + ثبت دلیل (idempotent)."""
    FREEZE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    if not FREEZE_FLAG.exists():
        FREEZE_FLAG.write_text(f"{now_iso()} {reason}\n", "utf-8")
    alert([f"FREEZE: {reason}"])


# ─── گزارش‌دهی (قراردادهای موجود governor_shadow) ────────────────────────────
_ALERT_ROTATE_BYTES = 2_000_000          # ~2MB؛ آرشیو = انتقال، نه حذف (قانونِ vault §۱)
_ALERT_DEDUP_WINDOW_S = 21600.0          # ۶ ساعت — همان کفِ زمانیِ consolidation
_ALERT_ESCALATION_MARKS = (10, 100, 1000)


def _alert_rotate_if_huge() -> None:
    """چرخشِ دفترِ هشدار وقتی از سقف گذشت — انتقال به آرشیوِ تاریخ‌دار، نه حذف.
    بدونِ این، طوفانِ یک شب (اسکنِ 07-29: یک امضا ×۳۴۶) برای همیشه در هر
    اسکنِ دکتر دوباره شمرده می‌شود و «اکنون» از «تاریخ» تفکیک‌ناپذیر می‌ماند."""
    if not ALERTS_MD.exists() or ALERTS_MD.stat().st_size < _ALERT_ROTATE_BYTES:
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = ALERTS_MD.with_name(f"governor-alerts-archive-{stamp}.md")
    ALERTS_MD.replace(dst)   # اتمیک؛ بازندهٔ race فقط OSError می‌گیرد (caller می‌بلعد)
    ALERTS_MD.write_text(f"# دفترِ تازه — قبلی چرخید به {dst.name} در {now_iso()}\n\n",
                         "utf-8")


def alert(items: list[str]) -> None:
    """append + dedupِ امضامحور با **escalation، نه سرکوبِ خاموش** (2026-07-29).

    قاعده‌ها: متن/امضای نو همیشه فوراً نوشته می‌شود؛ سه تکرارِ اول هم نوشته
    می‌شوند؛ از آن به بعد فقط شمرده می‌شود و در نشانه‌های ×۱۰/×۱۰۰/×۱۰۰۰ یک
    سطرِ escalation می‌آید. پنجره ۶ساعته است — بیرونِ پنجره، همان امضا دوباره
    «نو» شمرده می‌شود (خرابیِ پایدار روزی چند بار دیده می‌شود، نه ×۳۴۶).
    هر خطای مسیرِ dedup → appendِ سادهٔ قدیمی (آلارمِ گم‌شده بدتر از تکراری)."""
    ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)
    suffix = ""
    try:
        _alert_rotate_if_huge()
        import hashlib as _hashlib   # noqa: WPS433 — الگویِ importِ محلیِ همین ماژول
        sig = _hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()[:16]
        p = STATE_DIR / "alert-signatures.json"
        now = time.time()
        try:
            st = json.loads(p.read_text("utf-8")) if p.exists() else {}
            if not isinstance(st, dict):
                st = {}
        except Exception:  # noqa: BLE001 — fail-open
            st = {}
        rec = st.get(sig) if isinstance(st.get(sig), dict) else {}
        try:
            last = float(rec.get("ts") or 0)
        except (TypeError, ValueError):
            last = 0.0
        count = int(rec.get("count") or 0) if (now - last) < _ALERT_DEDUP_WINDOW_S else 0
        count += 1
        st[sig] = {"ts": now, "count": count,
                   "head": (str(items[0])[:120] if items else "")}
        if len(st) > 400:   # کرانِ ایندکس (نه دفتر): کهنه‌ترین امضاها از شمارش می‌افتند
            st = dict(sorted(st.items(), key=lambda kv: (kv[1] or {}).get("ts", 0))[-200:])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(st, ensure_ascii=False), "utf-8")
        if count > 3 and count not in _ALERT_ESCALATION_MARKS:
            return   # شمرده شد؛ دفتر و تلگرام دوباره پر نمی‌شوند
        if count > 3:
            suffix = f" (×{count} در پنجرهٔ ۶ساعته — escalation)"
    except Exception:  # noqa: BLE001 — fail-open: dedup هرگز آلارم را نمی‌خورد
        suffix = ""
    with ALERTS_MD.open("a", encoding="utf-8") as f:
        f.write(f"## {now_iso()} (metabolism)\n"
                + "\n".join(f"- ⚠️ {i}{suffix}" for i in items) + "\n\n")


def alert_throttled(items: list[str], key: str, window_s: float = 3600.0) -> bool:
    """alert با پنجرهٔ dedupe — **فقط برای سایت‌هایی که روی مسیرِ داغ می‌نشینند.**

    چرا لازم شد (۲۰۲۶-۰۷-۲۵): `alert()` یک appendِ خالص بدونِ هیچ throttle است (برخلافِ
    `conflict_to_human` که سقفِ روزانه per-tag دارد) و آلارم به تلگرامِ مالک می‌رود. تنها
    اقدامِ context_fence روی screenِ مثبت همین alert است؛ با سه مسیرِ LLMِ مسلح، یک
    payloadِ regex-تریگر در هر epoch سیلِ آلارم می‌سازد و **اعلانِ واقعیِ halt را زیر نویز
    می‌برد** — یعنی یک گامِ مهاری، خودش رگرسیونِ مهار-همجوار می‌شود.

    قاعده‌ها (به ترتیبِ اهمیت):
      · **متنِ نو همیشه فوراً عبور می‌کند.** throttle فقط رویِ تکرارِ *عینِ همان* پیام است.
      · fail-open: هر خطای I/O → alert نوشته می‌شود. آلارمِ گم‌شده بدتر از آلارمِ تکراری است.
      · وقتی پنجره بسته می‌شود، شمارِ سرکوب‌شده‌ها در همان خط گزارش می‌شود (صفر پنهان‌کاری).
    خروجی: True اگر نوشته شد، False اگر در پنجره سرکوب شد."""
    import hashlib as _hashlib   # noqa: WPS433 — الگویِ importِ محلیِ همین ماژول
    sig = _hashlib.sha256(("\n".join(items)).encode("utf-8")).hexdigest()[:16]
    p = STATE_DIR / "alert-throttle.json"
    try:
        st = json.loads(p.read_text("utf-8")) if p.exists() else {}
        if not isinstance(st, dict):
            st = {}
    except Exception:  # noqa: BLE001 — fail-open
        st = {}
    rec = st.get(key) if isinstance(st.get(key), dict) else {}
    now = time.time()
    try:
        last = float(rec.get("ts", 0) or 0)
    except (TypeError, ValueError):
        last = 0.0
    same = (rec.get("sig") == sig)
    suppressed = int(rec.get("suppressed", 0) or 0)
    if same and (now - last) < max(1.0, float(window_s)):
        rec.update({"sig": sig, "ts": last, "suppressed": suppressed + 1})
        st[key] = rec
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(st, ensure_ascii=False), "utf-8")
        except Exception:  # noqa: BLE001 — نتوانستیم بشماریم؛ آلارم را از دست نمی‌دهیم
            alert(items)
            return True
        return False
    out = list(items)
    if suppressed:
        out.append(f"(+{suppressed} تکرارِ سرکوب‌شده در پنجرهٔ {int(window_s)}s — کلید {key})")
    alert(out)
    st[key] = {"sig": sig, "ts": now, "suppressed": 0}
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(st, ensure_ascii=False), "utf-8")
    except Exception:  # noqa: BLE001 — آلارم نوشته شد؛ شمارنده مهم‌تر نیست
        pass
    return True


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


GO_LIVE_FLAG = OPS / "ACTIVATION-GO-LIVE.flag"


def live_gate_open(activation_flag: pathlib.Path) -> tuple[bool, str]:
    """گیت دوقفله برای هر مسیر زنده: (۱) تاریخ ≥ 2026-07-21 (سپر فاز −۱)، (۲) فایل پرچم
    که فقط مالک می‌سازد.

    اهرمِ go-live (تصمیمِ صریحِ مالک 2026-07-10): اگر `ACTIVATION-GO-LIVE.flag` باشد
    (فقط مالک می‌سازد)، سپرِ تاریخ زودتر باز می‌شود — ولی پرچمِ per-activation همچنان
    لازم است. **این هیچ‌یک از ایمنی‌های هسته را دور نمی‌زند:** سقفِ بودجهٔ ماهانه
    (budget_gate)، kill-switch، σ≤1، و human-append همه مسیرهای جدا و دست‌نخورده‌اند."""
    early = GO_LIVE_FLAG.exists()
    if _dt.date.today() < LIVE_GATE_DATE and not early:
        return False, f"live locked until {LIVE_GATE_DATE.isoformat()} (phase -1 shield)"
    if not activation_flag.exists():
        return False, f"activation flag missing: {activation_flag.name} (owner-only)"
    return True, ("open (owner go-live — سپرِ تاریخ زودتر باز شد)"
                  if (early and _dt.date.today() < LIVE_GATE_DATE) else "open")
