#!/usr/bin/env python3
"""organ_dialogue.py — Task 3 (2026-07-24): لایهٔ گفت‌وگوی owner↔organ (Doctor/Brains/Hearts).

نقش: helperهای مشترکِ **رندر + persist** برای دیالوگِ دوطرفه — هیچ transportِ جدیدی
نمی‌سازد؛ ارسال همیشه از راهِ همان `TelegramApprovalChannel`ِ in-processِ ارگانیسم
(`_chan`) انجام می‌شود و نوشتن‌ها همه atomic/LockedJson و whitelisted‌اند.

مرزهای سخت:
  · propose-only بیرونِ owner-gate: تنها مسیرِ نوشتنِ پارامتر، callback/کامندِ owner-gated
    در approval_channel است که به `heart_set_apply` می‌رسد — آن هم فقط از راهِ
    `heart.interface.HeartParams.validate()` (ADR-001: هیچ فیلدِ rate/period وجود ندارد).
  · هیچ secret/PII در هیچ digest — همه‌چیز عدد/шناسه/برچسبِ وضعیت است و خروجی از
    پاسِ `_redact`ِ خودِ channel هم می‌گذرد.
  · fail-soft همه‌جا: خطای هر digest هرگز tick/کامند را نمی‌کشد.
  · $0: فقط خواندنِ فایل‌های state — هیچ LLM/شبکه.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402


# ─── ابزارهای کوچک ────────────────────────────────────────────────────────────
def _sd(state_dir=None) -> Path:
    return Path(state_dir) if state_dir else opslib.STATE_DIR


def _read_json(p: Path, default=None):
    try:
        if p.exists():
            return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        pass
    return {} if default is None else default


def _esc(v, cap: int = 160) -> str:
    return html.escape(str(v if v is not None else "—")[:cap])


def _h(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


# T1 (2026-07-25): severity از self_knowledge به‌صورت برچسبِ رشته‌ای می‌رسد
# ("high"/"متوسط") و int() مستقیم ۳۴۸ کرشِ doctor_digest_beat ساخته بود.
# نگاشتِ برچسب→عدد دو‌زبانه؛ برچسبِ ناشناخته کرش نمی‌کند و خودِ رشته نمایش داده می‌شود.
_SEV_LABELS = {
    "critical": 5, "بحرانی": 5,
    "high": 4, "بالا": 4,
    "medium": 3, "متوسط": 3,
    "low": 2, "کم": 2, "پایین": 2,
    "info": 1, "اطلاع": 1,
}


def _sev_num(v) -> int:
    """شدت را به عدد تبدیل می‌کند؛ هرگز raise نمی‌کند."""
    if v is None:
        return 0
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        try:
            return int(v)
        except (TypeError, ValueError, OverflowError):
            return 0
    s = str(v).strip()
    if not s:
        return 0
    try:
        return int(s)
    except ValueError:
        pass
    return _SEV_LABELS.get(s.lower(), _SEV_LABELS.get(s, 0))


def _sev_text(v) -> str:
    """نمایشِ شدت: عددِ نگاشت‌شده، یا خودِ برچسبِ ناشناخته (صداقت به‌جای صفرِ ساختگی)."""
    n = _sev_num(v)
    if n:
        return str(n)
    s = str(v if v is not None else "").strip()
    return s if s else "0"


def _tail_jsonl(p: Path, max_bytes: int = 4096) -> dict:
    """آخرین رکوردِ سالمِ یک jsonl (فقط دُم — فایلِ بزرگ کامل خوانده نمی‌شود)."""
    try:
        size = p.stat().st_size
        with open(p, "rb") as f:
            f.seek(max(0, size - max_bytes))
            lines = f.read().decode("utf-8", "replace").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except ValueError:
                    continue
    except OSError:
        pass
    return {}


# ════════════════════════════════════════════════════════════════════════════════
# Doctor — digest (efferent) + owner focus/revision (afferent persist)
# ════════════════════════════════════════════════════════════════════════════════
def doctor_digest(state_dir=None) -> dict:
    """خلاصهٔ «حرفِ دکتر» برای مالک: تشخیص (self-knowledge) + RFCهای باز.
    خروجی: {text(HTML), hash, rfc_open, focus}. فقط‌خواندنی."""
    sd = _sd(state_dir)
    sk = _read_json(sd / "doctor" / "self-knowledge-latest.json")
    rf = _read_json(sd / "doctor" / "rfcs.json")
    rfcs = [r for r in (rf.get("rfcs") or []) if isinstance(r, dict)]
    open_states = ("drafted", "submitted", "submitted-no-channel", "sandboxed",
                   "sandbox-skip", "reconcile-required")
    open_rfcs = [r for r in rfcs if r.get("status") in open_states]
    und = sk.get("understanding") or {}
    pathology = und.get("pathology") or []
    focus = sk.get("focus") or ""
    lines = ["🩺 <b>دکتر — تشخیص و پیشنهادها</b>", "──────────"]
    if focus:
        lines.append(f"🎯 تمرکز: {_esc(focus)}")
    for p in pathology[:3]:
        if isinstance(p, dict):
            lines.append(f"• (شدت {_sev_text(p.get('severity'))}) {_esc(p.get('symptom'))} — {_esc(p.get('root_cause'), 90)}")
    # نسخه، نه فقط تشخیص (۲۰۲۶-۰۷-۲۷). `deep_dive.smallest_fix` دقیق‌ترین جمله‌ای
    # است که کلِ لایهٔ خودآگاهی تولید می‌کند — روی ۱۸ چرخه محاسبه شده و **هیچ
    # ماژولی نمی‌خواندش**. تا امروز مالک تشخیص را می‌دید و نسخه را نه.
    dd = sk.get("deep_dive") if isinstance(sk.get("deep_dive"), dict) else {}
    fix = dd.get("smallest_fix")
    if fix:
        lines.append(f"🔧 کوچک‌ترین فیکس: {_esc(fix, 140)}")
        # `blocked_by` در دادهٔ زنده گاهی رشته است و گاهی لیست — `[0]` روی رشته
        # یک حرفِ فارسی رندر می‌کرد. هر دو شکل پذیرفته می‌شود.
        blk = dd.get("blocked_by")
        blk = blk[0] if isinstance(blk, list) and blk else blk
        if isinstance(blk, str) and blk.strip():
            lines.append(f"⛔ سدِ راه: {_esc(blk, 100)}")
    owner_focus = load_owner_focus(state_dir)
    if owner_focus:
        lines.append(f"🧭 steeringِ تو: {_esc(owner_focus, 90)}")
    # تصحیحِ تازهٔ مالک باید در همان دایجست دیده شود، وگرنه حرفش را می‌زند و
    # هیچ نشانه‌ای نمی‌بیند که شنیده شده.
    corr = sk.get("owner_corrections") or []
    if corr:
        lines.append(f"✍️ تصحیحِ تو ({len(corr)}): {_esc(corr[-1], 100)}")
    if open_rfcs:
        lines.append(f"📋 RFCهای باز ({len(open_rfcs)}):")
        for r in open_rfcs[:4]:
            lines.append(f"  · <code>{_esc(r.get('rfc_id'), 20)}</code> "
                         f"[{_esc(r.get('status'), 24)}] {_esc(r.get('bottleneck'), 70)}")
    else:
        lines.append("📋 RFC باز ندارد.")
    lines.append("<i>پاسخ: دکمه‌های کارتِ RFC، یا «/doctor focus &lt;متن&gt;»، "
                 "یا «/doctor edit &lt;RFC-id&gt; &lt;متن&gt;»</i>")
    hsh = _h(sk.get("snapshot_hash"), sk.get("version"), focus, owner_focus,
             *sorted(f"{r.get('rfc_id')}:{r.get('status')}" for r in open_rfcs))
    return {"text": "\n".join(lines), "hash": hsh,
            "rfc_open": len(open_rfcs), "focus": focus}


def save_owner_focus(text: str, state_dir=None, by: str = "owner") -> dict:
    """persistِ «doctor focus X» — steering hint برای mine()/self_knowledge (نه فرمان)."""
    t = str(text or "").strip()[:200]
    if not t:
        return {"ok": False, "error": "متنِ خالی"}
    p = _sd(state_dir) / "doctor" / "owner-policy.json"
    try:
        with opslib.LockedJson(p) as lj:
            d = lj.read() or {}
            d.update({"focus": t, "ts": opslib.now_iso(), "by": str(by)[:40]})
            lj.write(d)
        return {"ok": True, "focus": t}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": type(e).__name__}


def load_owner_focus(state_dir=None) -> str:
    d = _read_json(_sd(state_dir) / "doctor" / "owner-policy.json")
    return str(d.get("focus") or "")


def save_rfc_revision(rfc_id: str, text: str, state_dir=None) -> dict:
    """persistِ متنِ ویرایش/بازنگریِ مالک برای یک RFC — دکتر در cycleِ بعد مصرف می‌کند
    (`Doctor._consume_owner_revisions`). atomic/LockedJson؛ هرگز مستقیم rfcs.json را
    دست نمی‌زند (تک-writer ماندنِ registryِ دکتر)."""
    rid = str(rfc_id or "").strip()[:40]
    t = str(text or "").strip()[:800]
    if not rid or not t:
        return {"ok": False, "error": "rfc_id/متن خالی"}
    p = _sd(state_dir) / "doctor" / "owner-revisions.json"
    try:
        with opslib.LockedJson(p) as lj:
            d = lj.read() or {}
            d[rid] = {"text": t, "ts": opslib.now_iso()}
            lj.write(d)
        return {"ok": True, "rfc_id": rid}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": type(e).__name__}


def pop_rfc_revisions(state_dir=None) -> dict:
    """خواندن + پاک‌کردنِ atomic صفِ بازنگری‌ها (مصرف‌کننده: Doctor)."""
    p = _sd(state_dir) / "doctor" / "owner-revisions.json"
    try:
        if not p.exists():
            return {}
        with opslib.LockedJson(p) as lj:
            d = lj.read() or {}
            lj.write({})
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


# ════════════════════════════════════════════════════════════════════════════════
# Brains — digest از state-file (cortex هرگز channel نمی‌گیرد؛ ضدِ 409)
# ════════════════════════════════════════════════════════════════════════════════
def _debate_verdict_on() -> bool:
    return os.environ.get("OCTOPUS_WIRE_DEBATE_VERDICT") == "1"


def debate_survivor_card(state_dir=None) -> dict:
    """ایده‌های مناظرهٔ منتظرِ رأی — **متن**، برای کارتِ مغز (WS-E).

    منبع: پروژکشنِ `_ops/debate/survivors-pending.jsonl` (نوشتهٔ خودِ حلقهٔ مناظره،
    همین پروسه) منهای آن‌هایی که مالک قبلاً رأی داده (`state/telegram/approvals/
    <id>.json`، نوشتهٔ مرکز). عمداً `approval_store` را import نمی‌کند: قفلش
    درون‌پروسه‌ای است و این تابع در پروسهٔ ارگانیسم صدا زده می‌شود
    (گارد: S1-05 t_o_single_consumer_process_invariant).

    ⚠️ صادقانه: اینجا **دکمه‌ای** برنمی‌گردد. تنها صداکنندهٔ زندهٔ brain_digest
    (`wiring.brain_digest_beat`) کیبوردِ خودش را hardcode می‌کند و هر kbای که از
    اینجا برگردد خوانده نمی‌شود؛ دکمه‌سازی برای همین در کارتِ `mn:ap` انجام شده
    که مصرف‌کنندهٔ واقعی دارد. fail-soft → {}."""
    try:
        rows, order = {}, []
        # opslib.DEBATE_DIR = env-اول؛ `_HERE / "debate"` بی‌صدا به درختِ زنده می‌خورد.
        p = opslib.DEBATE_DIR / "survivors-pending.jsonl"
        if not p.exists():
            return {}
        for ln in p.read_text("utf-8", errors="replace").splitlines()[-200:]:
            try:
                rec = json.loads(ln)
            except ValueError:
                continue
            if not (isinstance(rec, dict) and rec.get("id")):
                continue
            jid = str(rec["id"])
            if jid not in rows:
                order.append(jid)
            rows[jid] = rec
        vdir = _sd(state_dir) / "telegram" / "approvals"
        open_rows = [rows[j] for j in order if not (vdir / f"{j}.json").exists()]
        if not open_rows:
            return {}
        lines = [f"⚖️ <b>مناظره</b> — {len(open_rows)} ایده منتظرِ رأیِ توست "
                 "(کارتِ رأی: 📮 صف تأیید)"]
        for i, r in enumerate(open_rows[:3], 1):
            lines.append(f"<b>{i}.</b> {_esc(r.get('title'), 150)}")
        if len(open_rows) > 3:
            lines.append(f"▸ {len(open_rows) - 3} ایدهٔ دیگر")
        return {"text": "\n".join(lines), "kb": [], "n": len(open_rows),
                "sig": _h(*[str(r.get("id", "")) for r in open_rows])}
    except (OSError, ValueError):  # دیالوگ هرگز tick را نمی‌کشد
        return {}


def brain_digest(state_dir=None) -> dict:
    """خلاصهٔ «حرفِ مغز» از artifactهای cortex + صفِ بازمانده‌های debate.
    منبع‌ها همه state-file‌اند (پلِ درست برای پروسهٔ out-of-process). فقط‌خواندنی."""
    sd = _sd(state_dir)
    cx = _read_json(sd / "cortex" / "cortex-state.json")
    st = _read_json(sd / "cortex" / "stress-latest.json")
    last = _tail_jsonl(sd / "cortex" / "journal.jsonl")
    stress_level = str(st.get("level") or (cx.get("stress") or {}).get("level") or "—")
    coherence = cx.get("coherence")
    cycle = cx.get("cycle")
    stale = cx.get("stale_members") or []
    thought = str(last.get("thought") or "")[:160]
    guid = {}
    try:
        _cx_dir = str(_HERE / "cortex")
        if _cx_dir not in sys.path:
            sys.path.insert(0, _cx_dir)
        import owner_guidance as _og
        guid = _og.effective(sd)
    except Exception:  # noqa: BLE001
        guid = {}
    # debate: بازمانده‌های در انتظارِ arbitrateِ انسان (فقط شمارش + آخرین)
    debate_n, debate_last = 0, ""
    try:
        qp = Path(sd).parent / "debate" / "SURVIVORS-QUEUE.md"
        if qp.exists():
            qlines = [ln for ln in qp.read_text("utf-8").splitlines()
                      if "— " in ln and " ·" in ln]
            debate_n = len(qlines)
            if qlines:
                debate_last = qlines[-1][:120]
    except OSError:
        pass
    lines = ["🧠 <b>مغز (cortex) — گزارش</b>", "──────────",
             f"cycle {_esc(cycle, 12)} · coherence {_esc(coherence, 12)} · تنش: {_esc(stress_level, 30)}"]
    if stale:
        lines.append(f"⚠️ اعضای کهنه: {_esc(', '.join(map(str, stale)), 90)}")
    if thought:
        lines.append(f"💭 آخرین فکر: {_esc(thought)}")
    if guid:
        g = []
        if guid.get("focus"):
            g.append(f"focus={guid['focus'][:40]}")
        if guid.get("think_every_n"):
            g.append(f"think_every_n={guid['think_every_n']}")
        if guid.get("paused"):
            g.append("paused")
        lines.append(f"🧭 steeringِ فعالِ تو: {_esc(' · '.join(g), 120)}")
    # ۲۰۲۶-۰۷-۲۸ (WS-E) — تا امروز رأیِ خواسته‌شده از مالک به‌شکلِ **یک عدد** + یک خطِ
    # بریده‌شده به ۱۲۰ کاراکتر می‌رسید؛ نه ایده‌ای خوانا، نه دکمه‌ای برای جواب‌دادن.
    # با فلگ روشن، همان اطلاعات از صفِ واقعیِ تأیید می‌آید و کیبوردش (kb) هم برمی‌گردد.
    # فلگ خاموش → dbt تهی → دقیقاً همان یک‌خطِ امروز.
    dbt = debate_survivor_card(sd) if _debate_verdict_on() else {}
    if dbt.get("text"):
        lines.append(dbt["text"])
    elif debate_n:
        lines.append(f"⚖️ debate: {debate_n} بازمانده در صفِ رأیِ تو — {_esc(debate_last, 90)}")
    lines.append("<i>پاسخ: «/brain guide &lt;متن&gt;» — bounded: focus:… · "
                 "think_every_n:N · pause/resume: think</i>")
    # ۲۰۲۶-۰۷-۲۸ — `cycle` از کلیدِ تشخیصِ تغییر حذف شد (در متن می‌ماند).
    # همان دلیلِ `spent` در کارتِ قلب: شمارندهٔ چرخهٔ کورتکس یک‌طرفه بالا می‌رود،
    # پس hash هر چرخه عوض می‌شد و «فکرِ تازه» با «چرخهٔ تازه» یکی گرفته می‌شد.
    # آنچه واقعاً تغییرِ معنادار است همین‌جا مانده: خودِ فکر، انسجام، سطحِ استرس،
    # شمارِ مناظره و راهنماییِ مالک. اگر هیچ‌کدام عوض نشد، کارت حرفِ تازه‌ای ندارد.
    _extra = [dbt.get("sig", "")] if dbt else []   # فلگ خاموش → لیستِ تهی → hashِ امروز
    hsh = _h(coherence, stress_level, thought, debate_n,
             json.dumps(guid, sort_keys=True, ensure_ascii=False), *_extra)
    return {"text": "\n".join(lines), "hash": hsh, "stress_level": stress_level,
            "coherence": coherence, "debate_pending": debate_n,
            # همیشه [] — و عمداً. دکمه جایی ساخته می‌شود که مصرف‌کننده دارد
            # (کارتِ `mn:ap`)؛ کیبوردی که هیچ‌کس نمی‌خواند همان «مکانیزمِ خاموش
            # دقیقاً روی خطی که رفتار عوض می‌شود» است. کلید برای صداکنندهٔ آینده می‌ماند.
            "kb": [], "debate_open": (dbt.get("n") or 0) if dbt else 0}


def brain_guide(text: str, state_dir=None, by: str = "owner") -> dict:
    """پلِ afferentِ owner→brain: اعتبارسنجیِ bounded + append به owner-guidance.jsonl.
    (delegation به cortex/owner_guidance — منبعِ واحدِ حقیقتِ parse.)"""
    try:
        _cx_dir = str(_HERE / "cortex")
        if _cx_dir not in sys.path:
            sys.path.insert(0, _cx_dir)
        import owner_guidance as _og
        return _og.append(text, state_dir=_sd(state_dir), by=by)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": type(e).__name__}


# ════════════════════════════════════════════════════════════════════════════════
# Hearts — digest + stall detector (efferent) و setpoint preview/apply (afferent)
# ════════════════════════════════════════════════════════════════════════════════
HEART_PARAM_ALIASES = {
    "sigma": "target_sigma", "target_sigma": "target_sigma",
    "band_lo": "viable_band_lo", "lo": "viable_band_lo", "viable_band_lo": "viable_band_lo",
    "band_hi": "viable_band_hi", "hi": "viable_band_hi", "viable_band_hi": "viable_band_hi",
    "cap": "daily_beat_cap", "beat_cap": "daily_beat_cap", "daily_beat_cap": "daily_beat_cap",
    "baro": "baroreflex_gain", "gain": "baroreflex_gain", "baroreflex_gain": "baroreflex_gain",
}
# ADR-001: هیچ نامِ نرخ/دوره در whitelist نیست و هرگز اضافه نمی‌شود (حذفِ ساختاری).
_FORBIDDEN_PARAMS = frozenset({"period", "period_s", "rate", "bpm", "hr"})


def _heart_iface():
    hp = str(_HERE / "heart")
    if hp not in sys.path:
        sys.path.insert(0, hp)
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    from heart import interface as hi  # noqa: WPS433
    return hi


def _setpoint_path(state_dir=None) -> Path:
    return _sd(state_dir) / "pulse" / "heart-setpoint-latest.json"


def heart_stall_check(beat=None, state_dir=None, now=None, stall_s=None) -> dict:
    """آشکارسازِ frozen-beat: اگر شمارندهٔ beat در حالی که ساعتِ دیواری جلو می‌رود
    ثابت بماند، pacemaker مرده/خفته است (INC واقعیِ 2026-07-23: thread با halted()
    برای همیشه return کرد و beat روی 9890 ماند — برای مالک نامرئی بود).
    state: pulse/heart-card-state.json. فقط تشخیص — هیچ restart/clearی نمی‌کند."""
    sd = _sd(state_dir)
    now = float(now if now is not None else time.time())
    stall_s = float(stall_s if stall_s is not None
                    else os.environ.get("HEART_STALL_ALERT_S", "1800"))
    p = sd / "pulse" / "heart-card-state.json"
    st = _read_json(p)
    out = {"stalled": False, "beat": beat, "stall_s": stall_s, "age_s": 0.0}
    try:
        if beat is None:
            return out
        beat = int(beat)
        if st.get("last_beat") != beat:
            st.update({"last_beat": beat, "last_change_ts": now, "stall_alerted": False})
        age = now - float(st.get("last_change_ts") or now)
        out["age_s"] = round(age, 1)
        if beat > 0 and age > stall_s:
            out["stalled"] = True
            out["already_alerted"] = bool(st.get("stall_alerted"))
            st["stall_alerted"] = True
        st["ts"] = opslib.now_iso()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError):
        pass
    return out


def heart_digest(state_dir=None, beat=None) -> dict:
    """کارتِ cardiac برای مالک: mode/تنش، period مؤثر، velocity vs باند، σ، بودجهٔ
    ضربانِ امروز، baro، setpoint فعلی، و stall. فقط‌خواندنی + stall-state کوچک."""
    sd = _sd(state_dir)
    hs = _read_json(sd / "pulse" / "heartstate-latest.json")
    shadow = _read_json(sd / "pulse" / "heart-shadow-latest.json")
    budget = _read_json(sd / "cardiac-budget.json")
    setp = _read_json(sd / "pulse" / "heart-setpoint-latest.json")
    org = _read_json(sd / "ORGANISM-STATE.json")
    sh = hs.get("shadow") or {}
    stress = hs.get("stress") or {}
    sig = shadow.get("signal") or {}
    tele = shadow.get("telemetry") or {}
    b = beat if beat is not None else shadow.get("beat") or (org.get("chrono") or {}).get("beat")
    stall = heart_stall_check(beat=b, state_dir=sd)
    period = sh.get("period_s") or sig.get("period_s")
    vel = tele.get("velocity_per_hr") or sh.get("velocity")
    band_lo = tele.get("band_lo", setp.get("viable_band_lo"))
    band_hi = tele.get("band_hi", setp.get("viable_band_hi"))
    sigma_now = sig.get("sigma_now", sh.get("sigma"))
    baro = sig.get("baro_factor")
    cap = setp.get("daily_beat_cap") or int(os.environ.get("CARDIAC_DAILY_BEAT_CAP", "288"))
    spent = budget.get("spent", 0)
    remaining = max(0, int(cap) - int(spent or 0))
    depleted = int(spent or 0) >= int(cap)
    stress_level = str(stress.get("level") or "—")
    mode = "🔴" if "🔴" in stress_level else ("🟡" if "🟡" in stress_level else "🟢")
    innerv = hs.get("innervation") or {}
    alerts = []
    if stall.get("stalled"):
        alerts.append(f"⛔ نبض یخ‌زده: beat={_esc(b, 12)} از {int(stall['age_s'] // 60)} دقیقه پیش "
                      "جلو نرفته — pacemaker احتمالاً مرده (نیاز به restartِ organism)")
    if depleted:
        alerts.append(f"🪫 بودجهٔ ضربانِ امروز تمام ({spent}/{cap}) — فقط resting")
    if "🔴" in stress_level:
        alerts.append(f"🔴 تنشِ ارگانیسم بالا: {_esc(stress_level, 30)}"
                      + (f" (in_fear: {_esc(', '.join(map(str, stress.get('in_fear') or [])), 60)})"
                         if stress.get("in_fear") else ""))
    if org.get("protective_skip"):
        alerts.append("🛡 protective redirect فعال (درد/nociceptor)")
    dead = innerv.get("dead_spots") or []
    if dead:
        alerts.append(f"⚫ نقطهٔ مرده: {_esc(', '.join(map(str, dead)), 60)}")
    lines = [f"🫀 <b>قلب — گزارشِ ریتم</b> {mode}", "──────────",
             f"beat {_esc(b, 12)} · period {_esc(period, 10)}s · baro {_esc(baro, 8)}",
             f"velocity {_esc(vel, 10)}/hr در باند [{_esc(band_lo, 8)}, {_esc(band_hi, 8)}] · σ {_esc(sigma_now, 8)}",
             f"بودجهٔ ضربانِ امروز: {_esc(spent, 8)}/{_esc(cap, 8)} (مانده {remaining})",
             f"setpoint: epoch {_esc(setp.get('epoch_seq'), 8)} · target_σ {_esc(setp.get('target_sigma'), 8)} "
             f"· cap {_esc(setp.get('daily_beat_cap'), 8)}"]
    if alerts:
        lines.append("──────────")
        lines.extend(alerts)
    lines.append("<i>تنظیم (فقط setpoint، هرگز period — ADR-001): "
                 "«/heart set sigma 0.8» · «/heart set hi 6» · «/heart set cap 288»</i>")
    # ۲۰۲۶-۰۷-۲۸ — `spent` از کلیدِ تشخیصِ تغییر **حذف شد** (در متنِ کارت می‌ماند).
    #
    # `spent` بودجهٔ ضربانِ مصرف‌شدهٔ امروز است و هر ضربان (۶۰ثانیه) یکی بالا
    # می‌رود. یعنی hash **به‌طور ساختاری** هر دقیقه عوض می‌شد و کارت هر دقیقه
    # «تغییرکرده» شمرده می‌شد. اندازه‌گیریِ زنده: ۳۲ کارتِ قلب در ۲۵ دقیقه، و
    # بعد از فیکسِ گاردِ دیالوگ همچنان ۱.۴۵ در دقیقه — چون گارد روی تطبیقِ hash
    # کار می‌کند و hashی که هر دقیقه عوض شود هرگز تطبیق نمی‌دهد.
    #
    # `spent` برای تشخیصِ تغییر **زائد** است: لحظهٔ معنادارش «بودجه ته کشید»
    # است که `depleted` از قبل جدا در کلید هست. سومین نمونهٔ یک الگو در یک روز
    # (شمارندهٔ هشدار در کارتِ نیازها، و همین‌جا): **شمارندهٔ یک‌طرفه هرگز نباید
    # داخلِ کلیدِ dedup باشد** — وگرنه «تغییر» را با «گذشتِ زمان» یکی می‌گیری.
    hsh = _h(mode, depleted, bool(alerts), stall.get("stalled"),
             setp.get("epoch_seq"), round(float(vel or 0), 1))
    return {"text": "\n".join(lines), "hash": hsh, "mode": mode, "alerts": alerts,
            "stalled": bool(stall.get("stalled")),
            "stall_new": bool(stall.get("stalled")) and not stall.get("already_alerted"),
            "depleted": depleted, "stress_level": stress_level, "beat": b}


def heart_params_current(state_dir=None):
    """setpointِ فعلی (fail-soft → پیش‌فرضِ HeartParams)."""
    hi = _heart_iface()
    hp = hi.read_setpoint(path=_setpoint_path(state_dir))
    return hp if hp is not None else hi.HeartParams()


def _coerce_value(canon: str, value):
    if canon == "daily_beat_cap":
        return int(float(value))
    return float(value)


def heart_set_preview(param: str, value, state_dir=None) -> dict:
    """اعتبارسنجیِ کاملِ یک تغییرِ setpoint، بدونِ نوشتن. خروجی برای کارتِ confirm."""
    key = str(param or "").strip().lower()
    if key in _FORBIDDEN_PARAMS:
        return {"ok": False, "errs": ["ADR-001: قلب regulator است نه commander — "
                                      "period/نرخ هرگز مستقیم set نمی‌شود؛ setpoint (باند/σ/cap) بده"]}
    canon = HEART_PARAM_ALIASES.get(key)
    if canon is None:
        return {"ok": False, "errs": [f"پارامترِ ناشناخته «{key}». مجاز: "
                                      f"{sorted(set(HEART_PARAM_ALIASES.values()))}"]}
    try:
        val = _coerce_value(canon, value)
    except (TypeError, ValueError):
        return {"ok": False, "errs": [f"مقدارِ نامعتبر برای {canon}: {value!r}"]}
    hi = _heart_iface()
    cur = heart_params_current(state_dir)
    import dataclasses
    new = dataclasses.replace(cur, **{canon: val})
    errs = new.validate()
    return {"ok": not errs, "errs": errs, "param": canon,
            "old": getattr(cur, canon), "new": val, "epoch_now": cur.epoch_seq}


def heart_set_apply(param: str, value, state_dir=None, by: str = "owner-telegram") -> dict:
    """اعمالِ owner-approvedِ یک تغییرِ setpoint: epochِ نو از راهِ
    `HeartParams.validate()` + `write_setpoint` (LockedJson atomic) + auditِ append-only.
    برگشت‌پذیر: مقدارِ قبلی در audit ثبت می‌شود."""
    pv = heart_set_preview(param, value, state_dir)
    if not pv.get("ok"):
        return pv
    hi = _heart_iface()
    cur = heart_params_current(state_dir)
    import dataclasses
    new = dataclasses.replace(cur, **{pv["param"]: pv["new"]},
                              epoch_seq=int(cur.epoch_seq) + 1)
    errs = new.validate()
    if errs:
        return {"ok": False, "errs": errs}
    if not hi.write_setpoint(new, path=_setpoint_path(state_dir)):
        return {"ok": False, "errs": ["write_setpoint شکست (validate/IO)"]}
    audit = {"ts": opslib.now_iso(), "by": str(by)[:40], "param": pv["param"],
             "old": pv["old"], "new": pv["new"], "epoch_seq": new.epoch_seq}
    try:
        ap = _sd(state_dir) / "pulse" / "heart-setpoint-audit.jsonl"
        ap.parent.mkdir(parents=True, exist_ok=True)
        with open(ap, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit, ensure_ascii=False) + "\n")
    except OSError:
        pass
    try:
        opslib.heartbeat(f"heart setpoint by owner: {pv['param']} "
                         f"{pv['old']}→{pv['new']} (epoch {new.epoch_seq})")
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "param": pv["param"], "old": pv["old"], "new": pv["new"],
            "epoch_seq": new.epoch_seq}
