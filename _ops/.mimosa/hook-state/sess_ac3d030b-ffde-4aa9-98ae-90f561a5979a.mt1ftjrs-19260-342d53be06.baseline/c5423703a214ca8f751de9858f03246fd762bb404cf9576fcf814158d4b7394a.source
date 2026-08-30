#!/usr/bin/env python3
"""
_ops/synapse/sense.py — اندامِ SENSE: ریاضیِ SOG روی تله‌متریِ خودِ ارگانیسم.

چیست
----
نخستین متریکِ خودآگاهیِ *عملیاتی* (نه تزئینی): جریانِ رویدادِ خودِ اختاپوس
(`_ops/state/events.jsonl`) را می‌خواند و با همان قلبِ ریاضیِ 4d_system
(`core/metrics.py::empirical_shadow / fit_shadow_parameters` — importِ read-only،
بدونِ تکرارِ کد) ساختارِ زمانیِ «ضربانِ خود» را برآورد می‌کند:

  - cpm proxy: نرخِ رویداد در دقیقه (ضربانِ مشاهده‌شده‌ی ارگانیسم).
  - temporal_mi / lag1_rho: از empirical_shadow روی سریِ شمارشِ رویداد در دقیقه.
  - E_shadow_proxy / rho_hat: از fit_shadow_parameters روی همان سری.
  - delta_self_proxy [hypothesis]: شکافِ temporal_mi بین سریِ «تنوعِ عامل‌ها»
    (سیگنالِ مرزِ درونی) و سریِ «شمارشِ خام» — مثبت یعنی سیگنالِ درونی از
    مشاهده‌ی بیرونی غنی‌تر است. این canonical Δ_self=0.122520 نیست؛ پروکسی است
    و با همین برچسب گزارش می‌شود.

قراردادها (سخت)
---------------
  * propose-only — خروجی فقط فایلِ proposal در _ops/synapse/out/ با قالبِ
    FROZENِ b6.sog.proposal.v1 (authority="propose-only"). هیچ کلیدِ اضافه‌ای
    نسبت به اسکیما تولید نمی‌شود.
  * پیش‌فرضِ خاموش — بدونِ SYNAPSE_ENABLED=1 هیچ‌کاری نمی‌کند (no-op کامل).
  * fail-closed — هر خطا → بازگشتِ {"ran": False} یا proposalِ تخفیف‌یافته از
    نوعِ observation با نشانِ degraded. هرگز exception به caller نشت نمی‌کند.
  * هرگز نمی‌نویسد روی: genome/، ledger.jsonl، state/، .env، budget، kill-switch.
  * سقفِ روزانه: SYNAPSE_DAILY_MAX proposal در روزِ UTC (پیش‌فرض ۳).

مصرفِ LLM: صفر. این اندام هیچ کالِ ابری/محلی ندارد — فقط ریاضی.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── ثابت‌ها ──────────────────────────────────────────────────────────────────

FLAG = "SYNAPSE_ENABLED"
# ۲۰۲۶-۰۷-۲۸ — نامِ canonical با قاعدهٔ کلیِ OCTOPUS_ prefix (هم‌الگو با بقیهٔ wiring).
# SYNAPSE_ENABLED (بدونِ prefix) برای backward-compat با README/SOT نگه داشته شد.
FLAG_OCTOPUS = "OCTOPUS_SYNAPSE_ENABLED"
DAILY_CAP_ENV = "SYNAPSE_DAILY_MAX"
DAILY_CAP_DEFAULT = 3

PRODUCER = "synapse_sense"
MODEL_VERSION = "synapse/0.1.0 + 4d core.metrics (worktree import)"

# لنگرهای تغییرناپذیرِ SOG — [FACT: 4d_system/core/model.py، مستند در
# MEGAPROMPT--4d-x-blackbox-synthesis-next-agent.md، ۲۰۲۶-۰۷-۱۷]
ANCHORS = {"E_shadow": 0.012553, "delta_self": 0.122520, "identity": 0.135073}

TAIL_N_DEFAULT = 2000          # چند رویدادِ آخر خوانده شود
TAIL_BYTES = 512 * 1024        # سقفِ خواندن از انتهای فایل
MIN_SERIES_POINTS = 20         # حداقلِ نقاطِ سری برای fit (هم‌راستا با metrics.py)
CPM_ANOMALY = 240.0            # بالای این نرخ → anomaly [hypothesis: آستانه‌ی اولیه]

_HERE = Path(__file__).resolve()
_OPS_ROOT = _HERE.parents[1]
_VAULT_ROOT = _HERE.parents[2]
DEFAULT_EVENTS = _OPS_ROOT / "state" / "events.jsonl"
DEFAULT_4D_ROOT = _VAULT_ROOT / "4d_system"
DEFAULT_OUT_DIR = _HERE.parent / "out"

# ۲۰۲۶-۰۷-۲۸ — سریِ زمانیِ صداقت (C8). بازسنجیِ ۰۷-۲۵ گفت C8 «حاضر و اجراشونده ولی نه
# سنجش‌پذیر» است: sinkهای per-cycle نه self_referential را می‌نوشتند نه gate0 را نه
# علامتِ Δ. این ردیف‌ها شکافِ «اندام ساخته شد ولی هیچ‌کس خروجی‌اش را در زمان نمی‌دید»
# را می‌بندند. مسیر با DEFAULT_OUT_DIR سازگار است (پشتِ همان فایلِ flags-off no-op).
DEFAULT_TRAIL = _OPS_ROOT / "state" / "synapse-trail.jsonl"


# ── ابزارهای پایه ────────────────────────────────────────────────────────────

def flag_on() -> bool:
    """روشن است اگر FLAG_OCTOPUS (canonical، OCTOPUS_ prefix) یا FLAG (backward-compat)
    هر یک روشن باشند. هر دو نام پشتیبانی می‌شوند تا wiring از قاعدهٔ کلی پیروی کند
    و README/SOT قدیمی هم honor شود."""
    for k in (FLAG_OCTOPUS, FLAG):
        if str(os.environ.get(k, "")).strip().lower() in ("1", "true", "yes", "on"):
            return True
    return False


def _daily_cap() -> int:
    try:
        return max(1, int(os.environ.get(DAILY_CAP_ENV, DAILY_CAP_DEFAULT)))
    except Exception:
        return DAILY_CAP_DEFAULT


def _anchor_hash() -> str:
    """sha256 روی کانونیکالِ E_shadow|Δ_self|identity (الگوی b6.sog.proposal.v1)."""
    canonical = f"{ANCHORS['E_shadow']:.6f}|{ANCHORS['delta_self']:.6f}|{ANCHORS['identity']:.6f}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_z(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def _coerce_iso_z(s: object) -> str | None:
    """رشته‌ی timestampِ رویداد را به ISO-UTC با پسوندِ Z تبدیل می‌کند (اگر ممکن)."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s or "T" not in s:
        return None
    if s.endswith("Z") or "+" in s[10:]:
        return s
    if s[-1].isdigit():
        return s + "Z"
    return None


def _tail_jsonl(path: Path, n: int) -> tuple[list[dict], str]:
    """n رویدادِ آخرِ JSONL را می‌خواند. خروجی: (لیستِ dict، متنِ خامِ همان خطوط برای hash).
    fail-closed: هر خطا → ([], "")."""
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            fh.seek(max(0, size - TAIL_BYTES))
            raw = fh.read().decode("utf-8", errors="replace")
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        tail = lines[-n:]
        events: list[dict] = []
        kept: list[str] = []
        for ln in tail:
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if isinstance(obj, dict):
                events.append(obj)
                kept.append(ln)
        return events, "\n".join(kept)
    except Exception:
        return [], ""


def _import_4d_metrics(fourd_root: Path):
    """importِ read-onlyِ core.metrics از 4d_system — بدونِ کپیِ کد.
    fail-closed: هر خطا/ناسازگاری → None (حالتِ degraded، نه fallbackِ جعلی)."""
    try:
        metrics_py = fourd_root / "core" / "metrics.py"
        if not metrics_py.exists():
            return None
        root = str(fourd_root)
        inserted = False
        if root not in sys.path:
            sys.path.insert(0, root)
            inserted = True
        try:
            mod = importlib.import_module("core.metrics")
        finally:
            if inserted:
                try:
                    sys.path.remove(root)
                except ValueError:
                    pass
        # دفاع در برابرِ تصادمِ نامِ پکیج: باید همین فایل باشد و API را داشته باشد.
        mod_file = str(getattr(mod, "__file__", "") or "")
        if not mod_file.replace("/", "\\").lower().startswith(root.replace("/", "\\").lower()):
            return None
        if not (hasattr(mod, "empirical_shadow") and hasattr(mod, "fit_shadow_parameters")):
            return None
        return mod
    except Exception:
        return None


# ── سری‌های زمانی ────────────────────────────────────────────────────────────

def _per_minute_counts(ts_list: list[float]) -> list[int]:
    """شمارشِ رویداد در هر دقیقه (مرتب‌شده بر زمان) — سریِ «ضربانِ خام»."""
    buckets: dict[int, int] = {}
    for t in ts_list:
        b = int(t // 60)
        buckets[b] = buckets.get(b, 0) + 1
    return [buckets[k] for k in sorted(buckets)]


def _per_minute_agent_diversity(events: list[dict]) -> list[int]:
    """تعدادِ عاملِ یکتا (agent_id) در هر دقیقه — سریِ «سیگنالِ مرزِ درونی»."""
    buckets: dict[int, set] = {}
    for e in events:
        t = e.get("ts")
        if not isinstance(t, (int, float)):
            continue
        b = int(t // 60)
        buckets.setdefault(b, set()).add(str(e.get("agent_id", "?")))
    return [len(buckets[k]) for k in sorted(buckets)]


# ── محاسبه‌ی اصلی ────────────────────────────────────────────────────────────

def compute_sense(events: list[dict], metrics_mod=None) -> dict:
    """از لیستِ رویدادها، متریک‌های SENSE را می‌سازد. هرگز raise نمی‌کند."""
    out: dict = {
        "n_events": len(events),
        "cpm": 0.0,
        "series_points": 0,
        "empirical": None,
        "fit": None,
        "delta_self_proxy": None,
        "degraded": metrics_mod is None,
    }
    try:
        ts = sorted(
            float(e["ts"]) for e in events
            if isinstance(e.get("ts"), (int, float)) and e.get("ts")
        )
        if len(ts) >= 2:
            span_min = max((ts[-1] - ts[0]) / 60.0, 1e-9)
            out["cpm"] = round(len(ts) / span_min, 3)
        series = _per_minute_counts(ts)
        out["series_points"] = len(series)

        if metrics_mod is not None and len(series) >= MIN_SERIES_POINTS:
            arr = [float(x) for x in series]
            emp = metrics_mod.empirical_shadow(arr)
            if isinstance(emp, dict):
                out["empirical"] = {
                    k: emp.get(k)
                    for k in ("temporal_mi", "lag1_rho", "verdict")
                    if k in emp
                }
            fit = metrics_mod.fit_shadow_parameters(arr)
            if isinstance(fit, dict) and "error" not in fit:
                out["fit"] = {
                    k: fit.get(k)
                    for k in ("rho_hat", "E_shadow_proxy", "detectable", "classification")
                    if k in fit
                }
            elif isinstance(fit, dict):
                out["fit_error"] = str(fit.get("error", "unknown"))[:200]

            diversity = _per_minute_agent_diversity(events)
            if len(diversity) >= MIN_SERIES_POINTS:
                emp2 = metrics_mod.empirical_shadow([float(x) for x in diversity])
                mi_raw = float((out["empirical"] or {}).get("temporal_mi") or 0.0)
                mi_div = float((emp2 or {}).get("temporal_mi") or 0.0)
                out["delta_self_proxy"] = round(mi_div - mi_raw, 6)
    except Exception as exc:  # fail-closed
        out["compute_error"] = f"{type(exc).__name__}: {exc}"[:200]
    return out


def _is_anomalous(metrics: dict) -> bool:
    """قاعده‌ی ساده‌ی anomaly (مستند، [hypothesis] آستانه‌ها):
    نرخِ رویدادِ غیرعادی، یا منفی‌شدنِ delta_self_proxy (سیگنالِ نشتِ مرزِ خود)."""
    if metrics.get("compute_error"):
        return False
    if float(metrics.get("cpm") or 0.0) > CPM_ANOMALY:
        return True
    d = metrics.get("delta_self_proxy")
    return d is not None and d < 0


def _summarize(metrics: dict, kind: str) -> str:
    bits = [
        f"SENSE روی {metrics.get('n_events', 0)} رویدادِ ارگانیسم",
        f"cpm={metrics.get('cpm', 0.0)}",
        f"points={metrics.get('series_points', 0)}",
    ]
    if metrics.get("empirical"):
        bits.append(f"temporal_mi={metrics['empirical'].get('temporal_mi')}")
    if metrics.get("fit"):
        bits.append(f"E_shadow_proxy={metrics['fit'].get('E_shadow_proxy')}")
    if metrics.get("delta_self_proxy") is not None:
        bits.append(f"delta_self_proxy={metrics['delta_self_proxy']}")
    if metrics.get("degraded"):
        bits.append("degraded(بدونِ core.metrics)")
    if metrics.get("fit_error"):
        bits.append(f"fit_error={metrics['fit_error']}")
    if metrics.get("compute_error"):
        bits.append(f"compute_error={metrics['compute_error']}")
    head = "ناهنجاری در ضربانِ خودِ ارگانیسم" if kind == "anomaly" else "مشاهده‌ی SENSE از ضربانِ خودِ ارگانیسم"
    return (head + " — " + " · ".join(bits))[:2000]


def build_proposal(*, metrics: dict, snapshot: dict, model_version: str = MODEL_VERSION) -> dict:
    """payloadِ دقیقاً مطابقِ b6.sog.proposal.v1 (additionalProperties=false)."""
    content_hash = snapshot["content_hash"]
    idem_src = f"{PRODUCER}|{content_hash}|{model_version}"
    kind = "anomaly" if _is_anomalous(metrics) else "observation"

    evidence: list[dict] = [
        {
            "metric": "organism.cpm",
            "value": float(metrics.get("cpm") or 0.0),
            "baseline": None,
            "note": "events/min over tail window [proxy]",
        }
    ]
    if metrics.get("empirical"):
        evidence.append({
            "metric": "organism.temporal_mi",
            "value": float(metrics["empirical"].get("temporal_mi") or 0.0),
            "baseline": None,
            "note": "empirical_shadow on organism's own event stream",
        })
    if metrics.get("fit"):
        evidence.append({
            "metric": "organism.E_shadow_proxy",
            "value": float(metrics["fit"].get("E_shadow_proxy") or 0.0),
            "baseline": ANCHORS["E_shadow"],
            "note": "proxy on organism telemetry; anchor shown for scale only",
        })
        evidence.append({
            "metric": "organism.rho_hat",
            "value": float(metrics["fit"].get("rho_hat") or 0.0),
            "baseline": None,
            "note": "lag-1 structure of own event rhythm",
        })
    if metrics.get("delta_self_proxy") is not None:
        evidence.append({
            "metric": "organism.delta_self_proxy",
            "value": float(metrics["delta_self_proxy"]),
            "baseline": ANCHORS["delta_self"],
            "note": "[hypothesis] internal-vs-raw MI gap; NOT canonical delta_self",
        })
    if metrics.get("degraded"):
        evidence.append({
            "metric": "synapse.degraded",
            "value": True,
            "baseline": False,
            "note": "4d core.metrics import unavailable; observation-only mode",
        })

    proposal: dict = {
        "event": "b6.sog.proposal",
        "schema_version": 1,
        "producer": PRODUCER,
        "authority": "propose-only",
        "model_version": model_version,
        "anchor_hash": _anchor_hash(),
        "idempotency_key": hashlib.sha256(idem_src.encode("utf-8")).hexdigest(),
        "created_utc": _iso_z(_utc_now()),
        "input_snapshot": snapshot,
        "proposal": {
            "kind": kind,
            "summary": _summarize(metrics, kind),
            "evidence": evidence[:32],
            "suggested_next": (
                "اگر anomaly است: در پنل /ops علت را ببینید؛ "
                "در غیر این صورت هیچ اقدامی لازم نیست (propose-only)."
            ),
        },
    }
    return proposal


def _snapshot(events_path: Path, events: list[dict], raw_text: str) -> dict:
    snap: dict = {
        "source": "_ops/state/events.jsonl (tail)",
        "content_hash": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        "row_count": len(events),
    }
    if events:
        t0 = _coerce_iso_z(events[0].get("timestamp"))
        t1 = _coerce_iso_z(events[-1].get("timestamp"))
        if t0 and t1:
            snap["time_range_utc"] = [t0, t1]
    return snap


# ── اجرای یک‌باره ────────────────────────────────────────────────────────────

def _daily_count(out_dir: Path, day_key: str) -> int:
    try:
        return sum(1 for p in out_dir.glob(f"proposal-{day_key}-*.json") if p.is_file())
    except Exception:
        return 0


def _write_atomic(out_dir: Path, proposal: dict, now: datetime) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"proposal-{now.strftime('%Y%m%d-%H%M%S')}-{proposal['idempotency_key'][:8]}.json"
    final = out_dir / name
    tmp = out_dir / (name + ".tmp")
    tmp.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, final)
    return final


def _append_trail(metrics: dict, proposal_kind: str, trail_path: Path | None = None) -> None:
    """سریِ زمانیِ صداقت (C8، ۲۰۲۶-۰۷-۲۸) — append-only، atomic-per-line.

    هر چرخهٔ SENSE یک ردیف با فیلدهای {ts, self_referential, gate0, delta, cpm, kind}
    می‌نویسد. این دقیقاً همان چیزی است که بازسنجیِ ۰۷-۲۵ گفت «وجود ندارد»: یک سریِ
    زمانیِ قابل‌رصد که نشان می‌دهد حسِ خود-ارجاعیِ ارگانیسم در طولِ زمان چه می‌کند.
    fail-closed: هر خطای I/O بی‌صدا — اندامِ Sense هرگز ارگانیسم را نمی‌کشد."""
    try:
        p = Path(trail_path) if trail_path else DEFAULT_TRAIL
        p.parent.mkdir(parents=True, exist_ok=True)
        emp = metrics.get("empirical") or {}
        fit = metrics.get("fit") or {}
        rec = {
            "ts": _iso_z(_utc_now()),
            "cpm": metrics.get("cpm"),
            "series_points": metrics.get("series_points"),
            "self_referential": emp.get("temporal_mi"),     # MI خود-سریِ ضربان
            "gate0": fit.get("detectable"),                  # آیا ساختارِ قابل‌تشخیص بود؟
            "delta": metrics.get("delta_self_proxy"),        # شکافِ درونی vs خام
            "kind": proposal_kind,
            "degraded": bool(metrics.get("degraded")),
        }
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — trail هرگز Sense را نمی‌کشد
        pass


def sense_once(
    ops_root: Path | None = None,
    fourd_root: Path | None = None,
    out_dir: Path | None = None,
    tail_n: int = TAIL_N_DEFAULT,
    trail_path: Path | None = None,
) -> dict:
    """یک چرخه‌ی SENSE. خروجیِ dict؛ هرگز raise نمی‌کند.
    پیش‌فرضِ flag خاموش → {"ran": False, "reason": "flag-off"}.
    trail_path: مسیرِ سریِ زمانیِ صداقت (پیش‌فرض state/synapse-trail.jsonl)؛ برای
    تست‌های ایزوله قابلِ override است."""
    if not flag_on():
        return {"ran": False, "reason": "flag-off"}
    try:
        ops_root = Path(ops_root) if ops_root else _OPS_ROOT
        fourd_root = Path(fourd_root) if fourd_root else DEFAULT_4D_ROOT
        out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
        events_path = ops_root / "state" / "events.jsonl"

        events, raw = _tail_jsonl(events_path, tail_n)
        if not events:
            return {"ran": False, "reason": "no-events"}

        now = _utc_now()
        day_key = now.strftime("%Y%m%d")
        if _daily_count(out_dir, day_key) >= _daily_cap():
            return {"ran": False, "reason": "daily-cap"}

        metrics_mod = _import_4d_metrics(fourd_root)
        m = compute_sense(events, metrics_mod)
        snap = _snapshot(events_path, events, raw)
        proposal = build_proposal(metrics=m, snapshot=snap)
        path = _write_atomic(out_dir, proposal, now)
        # سریِ زمانیِ صداقت (C8) — حتی در حالتِ degraded هم نوشته می‌شود تا رصدِ «هیچ
        # چرخه‌ای نچرخیده» ممکن باشد. شکافِ «حاضر ولی نه سنجش‌پذیر» (از ۰۷-۲۵).
        _append_trail(m, proposal["proposal"]["kind"], trail_path)
        return {
            "ran": True,
            "proposal_path": str(path),
            "kind": proposal["proposal"]["kind"],
            "degraded": bool(m.get("degraded")),
            "cpm": m.get("cpm"),
        }
    except Exception as exc:  # fail-closed: هرگز ارگانیسم را نکش
        return {"ran": False, "reason": f"error:{type(exc).__name__}"}


# ── self-test (بدونِ نیاز به 4d و بدونِ فلگ) ────────────────────────────────

def self_test() -> dict:
    """تستِ دودِ آفلاین: pipeline روی داده‌ی ساختگی + اعتبارِ کلیدهای اسکیما.
    خروجی dict از چک‌ها؛ True/False. هیچ فایلی بیرون از tmp نمی‌نویسد."""
    import tempfile

    checks: dict[str, bool] = {}

    # ۱) anchor_hash: قطعی و ۶۴-hex
    h = _anchor_hash()
    checks["anchor_hash_64hex"] = len(h) == 64 and all(c in "0123456789abcdef" for c in h)
    checks["anchor_hash_deterministic"] = h == _anchor_hash()

    # ۲) سریِ ساختگی: ۶۰ دقیقه با ریتمِ AR(1)-مانند (بدونِ numpy)
    events: list[dict] = []
    t = 1_700_000_000.0
    gap = 1.0
    for i in range(1500):
        gap = 0.8 * gap + 0.2 * (1.0 + ((i * 37) % 7) / 10.0)  # ساختگیِ قطعی
        t += max(gap, 0.05)
        events.append({
            "timestamp": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(timespec="seconds"),
            "ts": t,
            "agent_id": f"organ-{i % 5}",
            "event_name": "task.completed" if i % 3 else "heartbeat",
            "status": "ok",
        })
    m = compute_sense(events, metrics_mod=None)  # مسیرِ degraded
    checks["compute_sense_no_crash"] = isinstance(m, dict) and m.get("n_events") == 1500
    checks["cpm_positive"] = float(m.get("cpm") or 0) > 0
    checks["degraded_marked"] = m.get("degraded") is True

    snap = _snapshot(Path("dummy"), events, "x")
    p = build_proposal(metrics=m, snapshot=snap)
    required = {"event", "schema_version", "producer", "authority", "model_version",
                "anchor_hash", "idempotency_key", "created_utc", "proposal"}
    checks["proposal_exact_top_keys"] = set(p.keys()) <= required | {"input_snapshot"} and required <= set(p.keys())
    checks["proposal_consts"] = (
        p["event"] == "b6.sog.proposal" and p["schema_version"] == 1
        and p["authority"] == "propose-only"
    )
    checks["proposal_evidence_shape"] = all(
        set(ev.keys()) <= {"metric", "value", "baseline", "note"}
        and {"metric", "value"} <= set(ev.keys())
        for ev in p["proposal"]["evidence"]
    )
    checks["idempotency_deterministic"] = (
        p["idempotency_key"] == build_proposal(metrics=m, snapshot=snap)["idempotency_key"]
    )

    # ۳) sense_once: flag خاموش → no-op؛ flag روشن → فایل در tmp
    os.environ.pop(FLAG, None)
    checks["flag_off_noop"] = sense_once()["ran"] is False
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        ops = tdp / "ops"
        (ops / "state").mkdir(parents=True)
        with (ops / "state" / "events.jsonl").open("w", encoding="utf-8") as fh:
            for e in events:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        os.environ[FLAG] = "1"
        try:
            r1 = sense_once(ops_root=ops, fourd_root=tdp / "no4d", out_dir=tdp / "out")
            checks["sense_once_writes"] = r1.get("ran") is True and Path(r1["proposal_path"]).exists()
            os.environ[DAILY_CAP_ENV] = "1"
            r2 = sense_once(ops_root=ops, fourd_root=tdp / "no4d", out_dir=tdp / "out")
            checks["daily_cap"] = r2.get("ran") is False and r2.get("reason") == "daily-cap"
        finally:
            os.environ.pop(FLAG, None)
            os.environ.pop(DAILY_CAP_ENV, None)

    checks["ALL"] = all(checks.values())
    return checks


if __name__ == "__main__":
    if flag_on():
        print(json.dumps(sense_once(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
