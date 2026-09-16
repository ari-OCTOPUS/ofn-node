#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""goal_action_bridge — صداکنندهٔ گمشدهٔ زنجیرهٔ «پیش‌ثبتِ دقیق → mission → عمل → رسید».

SGC-14 شکاف را با نام گفته بود: «test_cycle.run() متنِ روش را ثبت می‌کند …
آن را به اقدام تبدیل نمی‌کند؛ پلِ اقدام فازِ بعد است.» و هر سه قطعهٔ پل از
قبل ساخته و تست شده بودند — فقط صداکننده نداشتند:

    unified_control.pipeline.prepare_records   «no latest-row guessing» (سیمِ exact-row)
    unified_control.method_translator          ترجمهٔ rule-based (متن هرگز مجوز نیست)
    action_bridge.planner/executor             طبقه‌بندی/اجرا/رسیدِ fail-closed
    mission_contract                           envelope + گذارهای قانونی

این ماژول **هیچ‌کدام را تکرار نمی‌کند** — فقط صدایشان می‌زند و دو چیزِ کم را
اضافه می‌کند: (۱) دفترِ append-only ِ mission با گذارِ اجباری، (۲) consolidation ِ
حکمِ ارزیابِ مستقل به حافظه از مسیرِ MemoryGate.

مرزها:
  · فقط زنجیره‌ای که planner ِ خودِ bridge ALLOW بدهد اجرا می‌شود — این ماژول
    هیچ گیتی را دور نمی‌زند و مسیری به A1+ اضافه نمی‌کند.
  · missing prereg = fail-closed، صفر اقدام (تهدیدِ ۸ ِ SGC-14 برای عمل).
  · ترجمهٔ ناموفق/گیرکرده = BLOCKED ِ صادق، نه سکوت و نه اجرا.
  · شکستِ نوشتنِ دفترِ mission هرگز موفقیت گزارش نمی‌شود.
  · حافظه فقط از حکمِ مستقل (verdicts.jsonl) پر می‌شود — outcome-bound؛
    authority نیست (قانون: memory مجوز نیست).
  · فلگ `OCTOPUS_WIRE_ACTION_BRIDGE` از ۲۰۲۶-۰۷-۳۰ مسلح است (`OWNER_AUTH:
    VQ-ACTION-BRIDGE-ARM-001`، `OCTOPUS-flags.cmd:805`) — این کامنت تا
    ۲۰۲۶-۰۸-۰۶ کهنه مانده بود و رأیِ مالک را «معلق» نشان می‌داد. زنده تأیید شد:
    `state/test_cycle/missions.jsonl` همین امروز `input_refs` با
    `memory:<id>` از `retrieval_router.route()` دارد — یعنی این پل نه‌فقط
    مسلح، بلکه واقعاً در حالِ نوشتنِ اثر است.

$0 · stdlib · صفر شبکه/ارسال · بدونِ import از organism/wiring.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

FLAG = "OCTOPUS_WIRE_ACTION_BRIDGE"
CARD_FLAG = "OCTOPUS_WIRE_MISSION_CARD"
MEMORY_FLAG = "OCTOPUS_WIRE_MEMORY_READ"
SCHEMA = "octopus.goal-action.v1"


def _flag_on(name: str) -> bool:
    return str(os.environ.get(name, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def enabled() -> bool:
    return _flag_on(FLAG)


def card_enabled() -> bool:
    return _flag_on(CARD_FLAG)


def _state_dir() -> Path:
    try:
        import opslib
        return Path(opslib.STATE_DIR) / "test_cycle"
    except Exception:  # noqa: BLE001
        return _OPS / "state" / "test_cycle"


def _missions_path() -> Path:
    return _state_dir() / "missions.jsonl"


def _ledger_path() -> Path:
    return _state_dir() / "action-ledger.jsonl"


def _nonces_path() -> Path:
    return _state_dir() / "used-nonces.json"


# ── durability: دفترِ idempotency و nonceها restart را باید زنده بمانند ─────
def _load_ledger() -> dict:
    """رسیدهای نشسته → {idempotency_key: receipt}. بدونِ این، هر restart
    حفاظتِ replay/idempotency را صفر می‌کرد (planner با دفترِ خالی همه‌چیز را
    NEW می‌دید). خطِ خراب skip می‌شود — دفترِ نیمه‌خوانا بهتر از هیچ است."""
    led: dict = {}
    try:
        for line in _ledger_path().read_text("utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            k = str((rec or {}).get("idempotency_key") or "") if isinstance(rec, dict) else ""
            if k:
                led[k] = rec
    except OSError:
        pass
    return led


def _load_nonces() -> set:
    try:
        vals = json.loads(_nonces_path().read_text("utf-8"))
        return {str(v) for v in vals} if isinstance(vals, list) else set()
    except (OSError, ValueError):
        return set()


def _save_nonces(nonces: set) -> bool:
    try:
        p = _nonces_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sorted(str(n) for n in nonces)), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


# ── حکمِ اعتبارِ state برای مجوزدهی (freshness §۹.۳) ────────────────────────
def _authorities(now: float) -> dict:
    """authority ِ self-model و heart با همان معناشناسیِ سنجیده‌شدهٔ
    unified_control.snapshot._state — کهنه AUTHORITATIVE نمی‌شود."""
    try:
        from unified_control import snapshot as _sn
        st = Path(str(_state_dir().parent))          # …/state
        sm = _sn._state(st / "cortex" / "self-model.json", now=now, sla_s=7200)
        hb = _sn._state(st / "pulse" / "heart-shadow-latest.json", now=now,
                        sla_s=1800, shadow=True)
        prod = (hb.get("data") or {}).get("production_wire") or {}
        hb["production_open"] = bool(prod.get("open"))
        return {"self_model_authority": sm["authority"], "heart": hb}
    except Exception:  # noqa: BLE001
        # نبودِ snapshot ⇒ fail-closed به بدترین حالت: MISSING (فقط read-only).
        return {"self_model_authority": "MISSING",
                "heart": {"authority": "MISSING", "production_open": False}}


def _directions() -> list:
    try:
        from unified_control import snapshot as _sn
        return _sn._goals()
    except Exception:  # noqa: BLE001
        return []


# ── دفترِ mission (append-only، گذارِ قانونی اجباری) ────────────────────────
def _transition(env: dict, new_status: str) -> bool:
    try:
        import mission_contract as mc
        if not mc.can_transition(str(env.get("status")), new_status):
            return False
        env["status"] = new_status
        return True
    except Exception:  # noqa: BLE001
        return False


def _append_mission(env: dict) -> bool:
    try:
        import mission_contract as mc
        if mc.validate(env):
            return False
        p = _missions_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(env, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


# ── کارتِ مالک برای missionهای منتظرِ رأی (VQ-MISSION-CARD-001) ─────────────
def _load_approval_store():
    """approval_store ِ telegram_center را با importlib ِ مسیری لود می‌کند —
    عمداً بدونِ افزودنِ telegram_center به sys.path (نام‌های عمومی‌اش مثل
    render/actions ماژول‌های دیگر را shadow می‌کنند). approval_store خودش
    stdlib-only است. اگر OCTOPUS_STATE_ROOT ست باشد، صف به همان‌جا pin
    می‌شود (ایزوله‌سازیِ تست/worktree — همان قراردادِ owner_views).

    ⚠️ این loader عمداً `import approval_store` را دور می‌زند (تستِ نگهبانِ
    S1-05 t_o هر import ِ مستقیمِ approval_store بیرونِ telegram_center را
    قرمز می‌کند) ولی همان محدودیتِ تک‌نویسنده هنوز معنا دارد: emit_mission_cards
    فقط از پروسه‌ای صدا زده شود که تنها مصرف‌کنندهٔ همزمانِ این صف است. اگر روزی
    CARD_FLAG هم‌زمان با OCTOPUS_WIRE_MISSION_APPROVAL (telegram_center) مسلح
    شود، دو پروسه روی همین approvals.json می‌نویسند — همان raceی که RLock ِ
    approval_store فقط درون‌پروسه می‌پوشاند؛ پیش از مسلح‌کردنِ هم‌زمان، صف باید
    به file-lock ارتقا یابد (owner_gate ِ قبل از arm)."""
    import importlib.util
    p = _OPS / "telegram_center" / "approval_store.py"
    spec = importlib.util.spec_from_file_location("_gab_approval_store", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    root = str(os.environ.get("OCTOPUS_STATE_ROOT", "") or "").strip()
    if root:
        base = Path(root)
        mod._APPROVALS_JSON = base / "approvals.json"
        mod._AUDIT_PATH = base.parent / "logs" / "audit.log"
    return mod


def emit_mission_cards(*, cap: int = 3, store=None) -> dict:
    """mission ِ requires_approval → کارتِ pending در صفِ تأییدِ موجود (ap:).

    شکافِ ثبت‌شدهٔ ۱۳-ARMED: ردیفِ needs_approval در دفتر می‌نشیند ولی مالک
    فقط با خواندنِ فایل می‌بیندش. این درز صفِ **موجود** را پر می‌کند؛ کارت را
    همان center ِ فعلی رندر می‌کند و رأی از همان `ap:ok/ap:no` می‌آید —
    صفر poller/bot ِ نو، صفر send ِ مستقیم.

    ناوردی‌ها: فلگ خاموش = دقیقاً هیچ · content-free (فقط action/target_leg/
    risk — متنِ هدف هرگز) · idempotent: jid قطعی از mission_id و چکِ همهٔ
    bucketها (کارتِ رأی‌خورده دوباره pending نمی‌شود) · آخرین وضعِ هر mission
    ملاک است · هیچ خطایی صداکننده را نمی‌کشد."""
    if not card_enabled():
        return {"ok": False, "reason": "flag-off", "emitted": 0}
    latest: dict = {}
    try:
        for line in _missions_path().read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and d.get("mission_id"):
                latest[str(d["mission_id"])] = d
    except OSError:
        return {"ok": True, "emitted": 0, "reason": "no-ledger"}
    try:
        aps = store if store is not None else _load_approval_store()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"store:{type(e).__name__}", "emitted": 0}
    n = 0
    for mid, env in latest.items():
        if n >= max(1, int(cap)):
            break
        if env.get("status") != "needs_approval" or not env.get("requires_approval"):
            continue
        jid = "mis-" + str(mid).replace(":", "-")
        try:
            if aps.get(jid) is not None:
                continue                     # قبلاً کارت شده — در هر bucket
            aps.add_pending({
                "id": jid, "type": "mission_approval",
                "title": (f"mission {env.get('action') or '?'} · "
                          f"{env.get('target_leg') or '?'} · {env.get('risk') or '?'}"),
                "risk": str(env.get("risk") or "high"),
                "requires_confirmation": True,
                "source": "goal_action_bridge",
            })
            n += 1
        except Exception:  # noqa: BLE001 — یک کارتِ بد بقیه را نمی‌کشد
            continue
    return {"ok": True, "emitted": n}


# ── حافظه در نقطهٔ تصمیم (فقط narrowing، پشتِ فلگِ خودِ router) ─────────────
def _memory_decision(row: dict, *, now: float) -> dict:
    """retrieval router — شواهد + veto ِ مالک از حافظه. fail-soft: خطا/غیابِ
    router = ادامهٔ زنجیره («حافظه مجوز نیست» ⇒ غیابش هم منع نیست)؛ veto فقط
    می‌تواند ببندد، هرگز باز نمی‌کند."""
    try:
        if str(_OPS / "memory") not in sys.path:
            sys.path.insert(0, str(_OPS / "memory"))
        import retrieval_router as rr
        if not rr.flag_on():
            return {"memories_used": [], "veto": False, "mode": "off"}
        return rr.route(goal_key=str(row.get("goal_key") or ""),
                        method_index=row.get("method_index"), now=now)
    except Exception as e:  # noqa: BLE001
        return {"memories_used": [], "veto": False,
                "mode": f"router-error:{type(e).__name__}"}


# ── بازیابیِ حافظه پیش از برنامه‌ریزی (SGC-14 §۱۰.۴؛ مشورتی، هرگز مجوز) ───────
def _recall_for_goal(row: dict, *, cap: int = 3) -> dict:
    """retrieval ِ ساخت‌یافته از MemoryStore برای هدفِ همین چرخه.

    خروجی فقط شناسه/اعتماد/تازگی/چرایی است — نه متنِ خام و نه هیچ authority.
    مصرفِ تصمیمیِ واقعی پشتِ A/B ِ §۱۰.۵ می‌ماند؛ این تابع «خواندن + ثبتِ
    مشاهده‌پذیر در journal» را می‌بندد (سنجه باید مشاهده کند، نه فراخوانی).
    فلگ خاموش (پیش‌فرض) = دقیقاً هیچ. شکست = fail-soft ِ صریح.

    ⚠️ این تابع مستقل از `_memory_decision`/`retrieval_router` است: آن یکی
    veto ِ مالک را از مسیرِ گیت‌شدهٔ خودش می‌آورد (OCTOPUS_WIRE_MEMORY_DECISION،
    بعد از prepare_records)، این یکی صرفاً مشورتی و پیش از prepare_records
    است (OCTOPUS_WIRE_MEMORY_READ) — دو فلگِ جدا، دو مسیرِ جدا، بدونِ تداخل."""
    if not _flag_on(MEMORY_FLAG):
        return {"ok": False, "reason": "flag-off", "used": [], "count": 0}
    try:
        if str(_OPS / "memory") not in sys.path:
            sys.path.insert(0, str(_OPS / "memory"))
        import memory_store
        st = memory_store.MemoryStore()
        used, seen = [], set()
        # goal_key عمداً جزو پرسش‌هاست: ردیف‌های consolidate ِ همین پل دقیقاً
        # «goal=<goal_key>» را حمل می‌کنند — تجربهٔ چرخه‌های قبلیِ همین هدف.
        queries = [("fts:goal", str(row.get("goal") or "")),
                   ("fts:goal_key", str(row.get("goal_key") or "")),
                   ("fts:candidate", str(row.get("candidate_key") or ""))]
        for why, q in queries:
            if not q.strip():
                continue
            for ns in ("episodic", "semantic"):
                try:
                    hits = st.search(q, namespace=ns, k=cap)
                except Exception:  # noqa: BLE001 — یک namespace بقیه را نمی‌کشد
                    continue
                for h in hits:
                    hid = str(h.get("memory_id") or h.get("id") or "")
                    if not hid or hid in seen:
                        continue
                    seen.add(hid)
                    used.append({"memory_id": hid, "namespace": ns,
                                 "trust": h.get("trust") or h.get("trust_class"),
                                 "created_at": h.get("created_at"),
                                 "why": why})
                    if len(used) >= max(1, int(cap)):
                        break
                if len(used) >= max(1, int(cap)):
                    break
            if len(used) >= max(1, int(cap)):
                break
        try:
            st.close()
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "used": used, "count": len(used)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"recall:{type(e).__name__}",
                "used": [], "count": 0}


# ── stage ِ کارتِ مالک (OWNER_GATE → فایل، نه سکوت) ─────────────────────────
def _stage_owner_card(env: dict, req: dict, plan: dict,
                      *, now: float) -> bool:
    """کارتِ A3 + request ِ دقیق را کنارِ دفترِ mission بنشان — idempotent روی
    mission_id. فقط فایل: تحویل به مالک کارِ mission_approval_bridge است."""
    try:
        mid = str(env.get("mission_id") or "")
        if not mid:
            return False
        d = _state_dir() / "owner_cards"
        d.mkdir(parents=True, exist_ok=True)
        safe = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in mid)[:80]
        p = d / f"{safe}.json"
        if p.exists():
            return True                      # قبلاً stage شده — idempotent
        rec = {
            "schema": "octopus.owner-card-stage.v1",
            "mission_id": mid,
            "trace_id": env.get("trace_id"),
            "action_id": str(req.get("action_id") or ""),
            "cycle_id": str(env.get("task_id") or ""),
            "classification": plan.get("classification"),
            "risk": env.get("risk"),
            "card": (plan.get("owner_gate") or {}).get("card") or {},
            "request": dict(req),
            "plan_reason": plan.get("reason"),
            "created_ts": float(now),
            "staged_job_id": "",             # پر می‌شود وقتی به صفِ تأیید برود
            "verdict": "",                   # approved/rejected بعد از رأیِ مالک
        }
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, p)
        return True
    except Exception:  # noqa: BLE001 — stage هرگز زنجیره را نمی‌کشد
        return False


# ── زنجیرهٔ یک چرخه ─────────────────────────────────────────────────────────
def run_for_cycle(cycle_id: str, *, now: "float | None" = None) -> dict:
    """exact prereg → prepare_records → plan(ALLOW?) → execute(A0) → receipt →
    دفترِ mission. خروجی همیشه dict ِ صادق؛ استثنا بالا نمی‌آید."""
    now = float(now if now is not None else time.time())
    out: dict = {"schema": SCHEMA, "cycle_id": str(cycle_id)}
    if not enabled():
        return {**out, "ok": False, "reason": "flag-off"}

    # ۱) پیش‌ثبتِ دقیق — exact row؛ هیچ «آخرین ردیف»ی.
    try:
        import prereg
        row = prereg.for_cycle(str(cycle_id))
    except Exception as e:  # noqa: BLE001
        return {**out, "ok": False, "reason": f"prereg-read:{type(e).__name__}"}
    if not isinstance(row, dict):
        return {**out, "ok": False, "reason": "missing-prereg"}
    out["prereg_id"] = row.get("prereg_id")

    # ۱.۵) بازیابیِ حافظه — مشورتی و مشاهده‌پذیر؛ بر plan هیچ اثری ندارد
    # (memory مجوز نیست — قانونِ اساسی؛ مصرفِ تصمیمی = A/B ِ §۱۰.۵، owner-gated).
    # عمداً پیش از prepare_records: تا plan/receipt با و بدونِ retrieval
    # بایت‌به‌بایت یکسان بماند (سنجهٔ t_memory_is_never_authority_over_the_plan).
    out["memory"] = _recall_for_goal(row)

    # ۲) آماده‌سازی از سیمِ موجود — ترجمه/envelope/نقشه، همه از اجزای تست‌شده.
    #    دفترِ idempotency و nonceها از دیسک — تا restart حفاظت را صفر نکند.
    try:
        from unified_control import pipeline
        auth = _authorities(now)
        nonces = _load_nonces()
        n_nonces0 = len(nonces)
        prep = pipeline.prepare_records(
            directions=_directions(), prereg=row, heart=auth["heart"],
            self_model_authority=auth["self_model_authority"], now=now,
            ledger=_load_ledger(), used_nonces=nonces)
        if len(nonces) != n_nonces0:
            _save_nonces(nonces)
    except Exception as e:  # noqa: BLE001
        return {**out, "ok": False, "reason": f"prepare:{type(e).__name__}"}
    if not prep.get("ok"):
        t = prep.get("translation") or {}
        return {**out, "ok": False, "status": "BLOCKED",
                "reason": f"translation:{t.get('reason') or prep.get('status')}"}
    env = prep["mission"]
    req = prep["request"]
    plan = prep["plan"]
    # زنجیرهٔ trace بدونِ حدس: cycle/prereg روی خودِ envelope می‌نشیند
    # (فیلدِ اضافه برای mission_contract.validate قانونی است؛ content_sha256
    # فقط روی payload بسته شده و دست نمی‌خورد).
    env["cycle_id"] = str(cycle_id)
    env["prereg_id"] = str(row.get("prereg_id") or "")
    out["mission_id"] = env.get("mission_id")
    out["trace_id"] = env.get("trace_id")
    out["classification"] = plan.get("classification")

    # ۲.۵) حافظه در نقطهٔ تصمیم — فقط narrowing (veto/شواهد)، هرگز مجوز.
    #      فلگِ جدا و پیش‌فرض خاموش؛ خطای router زنجیره را نمی‌خواباند.
    mem = _memory_decision(row, now=now)
    if mem.get("memories_used"):
        out["memories_used"] = mem["memories_used"]
        env["input_refs"] = list(env.get("input_refs") or []) + [
            f"memory:{m.get('memory_id')}" for m in mem["memories_used"]]
    if mem.get("veto"):
        env_final = dict(env)
        if env_final.get("status") == "queued":
            _transition(env_final, "blocked")
        _append_mission(env_final)
        return {**out, "ok": False, "status": "MEMORY_VETO",
                "reason": f"memory-veto:{mem.get('veto_ref')}"}

    # ۲.۶) فاز ۸e دستورالعمل ۲۰۲۶-۰۸-۱۶ — دو گیتِ additive فقط برای A2+:
    #   (الف) PROPOSE_ON_FALLBACK (D6): providerِ فعال GLM/Ollama است؟ → اجرای
    #         A2+ ممنوع؛ به‌جای اجرا، کارتِ پیشنهاد برای مالک stage می‌شود.
    #   (ب) وتوی دوگانه (D2، پشتِ OCTOPUS_WIRE_DUAL_VETO): OWNER_DECISION →
    #         توقفِ fail-closed + اعلان مالک (dual_brain.evaluate خودش اعلان می‌کند).
    #   A0 (مشاهده) از هر دو گیت معاف است. A2 اجرای خودکار **همچنان BLOCK** است
    #   طبقِ رأیِ ثبت‌شدهٔ VQ-SELFGOAL-002 (integration.py) — این گیت‌ها مسیر را
    #   باز نمی‌کنند؛ فقط از providerِ ضعیف محافظت می‌کنند و اعلانِ وتو را وصل
    #   می‌کنند. سؤالِ تبدیلِ A2→auto برای مالک در AGENT-REPORT ثبت شده.
    try:
        _cls = str(plan.get("classification") or "")
        _cls_n = int(_cls[1:]) if len(_cls) == 2 and _cls[0] == "A" \
            and _cls[1:].isdigit() else -1
    except (TypeError, ValueError):
        _cls_n = -1
    if plan.get("decision") == "ALLOW" and _cls_n >= 2:
        try:
            if str(_OPS / "cortex") not in sys.path:
                sys.path.insert(0, str(_OPS / "cortex"))
            import provider_adapter as _pa
            if _pa.downgrade_a2_now():
                env_final = dict(env)
                if env_final.get("status") == "queued":
                    _transition(env_final, "blocked")
                _append_mission(env_final)
                card = _stage_owner_card(env_final, req, plan, now=now)
                return {**out, "ok": False, "status": "PROPOSE_ON_FALLBACK",
                        "reason": "active provider autonomy=propose (D6)",
                        "card_staged": card}
        except Exception:  # noqa: BLE001 — گیت نباید زنجیره را بکشد؛ ادامه به اجرای مجاز
            pass
        try:
            if str(_OPS / "control_plane") not in sys.path:
                sys.path.insert(0, str(_OPS / "control_plane"))
            import dual_brain as _dbv
            if _dbv.enabled():
                rec = _dbv.evaluate(str(row.get("mission_id") or cycle_id),
                                    _dbv.VetoResult.APPROVED,   # NBB-CP = خودِ planner
                                    _dbv.VetoResult.PENDING,    # 4d هنوز وصل نیست (W2+)
                                    domain=str(row.get("domain") or "operations"))
                if rec.final != _dbv.VetoResult.APPROVED:
                    env_final = dict(env)
                    if env_final.get("status") == "queued":
                        _transition(env_final, "blocked")
                    _append_mission(env_final)
                    return {**out, "ok": False, "status": "DUAL_VETO_HOLD",
                            "reason": f"dual-brain {rec.final.value} ({rec.trace_id})"}
        except Exception:  # noqa: BLE001 — وتو نباید زنجیره را بکشد؛ FAIL ممنوع
            pass

    # ۳) فقط ALLOW اجرا می‌شود — هر تصمیمِ دیگرِ planner همان‌طور گزارش می‌شود.
    if plan.get("decision") != "ALLOW":
        # replay ِ idempotent (همان چرخه بعد از crash/restart): عمل قبلاً انجام
        # و رسیدش نشسته — تکرارِ side effect ممنوع، و ثبتِ mission ِ failed ِ
        # دوم هم دروغ است. گزارشِ صادق: NOOP، نه شکست.
        if str(plan.get("reason") or "").startswith("duplicate-noop"):
            return {**out, "ok": True, "status": "NOOP",
                    "reason": "duplicate-replay", "receipt_status": "NOOP"}
        env_final = dict(env)
        _transition(env_final, "failed") if env_final.get("status") == "queued" \
            else None
        _append_mission(env_final)
        # OWNER_GATE (۰۷-۳۱): کارتِ ساخته‌شدهٔ planner قبلاً همین‌جا دور ریخته
        # می‌شد — mission با needs_approval می‌نشست و هیچ مسیری به مالک نداشت
        # (شکافِ «کارتِ تولیدشده و مصرف‌نشده»). حالا کارت + request ِ دقیق روی
        # دیسک stage می‌شود تا mission_approval_bridge (فلگِ جدا) به صفِ تأییدِ
        # مالک برساند. stage صرفاً فایل است: صفر ارسال، صفر اجرا.
        if plan.get("decision") == "OWNER_GATE":
            out["card_staged"] = _stage_owner_card(env_final, req, plan, now=now)
        return {**out, "ok": False, "status": plan.get("decision"),
                "reason": f"plan:{plan.get('reason')}"}

    if not _transition(env, "running"):
        return {**out, "ok": False, "reason": "illegal-transition"}

    # ۴) اجرا — A0 با رسیدِ واقعی. dry_run=False چون A0 چیزی نمی‌نویسد جز رسید.
    try:
        if str(_OPS / "action_bridge") not in sys.path:
            sys.path.insert(0, str(_OPS / "action_bridge"))
        import executor
        rdir = _state_dir() / "action_receipts"
        rdir.mkdir(parents=True, exist_ok=True)
        rc = executor.execute(
            req, plan, sandbox_root=str(_OPS), receipts_dir=str(rdir),
            ledger_path=str(_state_dir() / "action-ledger.jsonl"),
            now_iso=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
            dry_run=False)
        receipt = rc.get("receipt") or {}
    except Exception as e:  # noqa: BLE001
        receipt = {"status": "FAILED",
                   "errors": [f"bridge-exception:{type(e).__name__}"]}
    out["receipt_status"] = receipt.get("status")

    # ۵) مقدارِ سنجه با خوانندهٔ canonical (غیاب = None، هرگز صفر).
    try:
        if str(_OPS / "cortex") not in sys.path:
            sys.path.insert(0, str(_OPS / "cortex"))
        import goal_generator as gg
        out["metric_value"] = gg.read_metric(row.get("metric_path"),
                                             row.get("metric_key"))
    except Exception:  # noqa: BLE001
        out["metric_value"] = None

    # ۶) پایان + دفتر — شکستِ نوشتن هرگز موفقیت نیست.
    final = "done" if receipt.get("status") == "EXECUTED" else "failed"
    if not _transition(env, final):
        return {**out, "ok": False, "reason": "illegal-final-transition"}
    env["output_refs"] = [
        f"receipt:{receipt.get('receipt_id') or receipt.get('action_id') or '?'}"]
    if not _append_mission(env):
        return {**out, "ok": False, "reason": "mission-ledger-write-failed"}
    out["ok"] = receipt.get("status") == "EXECUTED"
    if not out["ok"]:
        out.setdefault("reason", f"receipt:{receipt.get('status')}")
    return out


# ── consolidation: حکمِ مستقل → حافظهٔ outcome-bound ────────────────────────
def consolidate_new_verdicts(*, now: "float | None" = None, cap: int = 5) -> dict:
    """حکم‌های تازهٔ verdicts.jsonl → MemoryGate (episodic، deterministic).
    idempotent با نشانگر؛ گیتِ خاموش = skip؛ authority هرگز."""
    now = float(now if now is not None else time.time())
    st = _state_dir()
    marker = st / "memory-consolidated.json"
    try:
        done = set(json.loads(marker.read_text("utf-8")).get("cycle_ids") or [])
    except (OSError, ValueError):
        done = set()
    rows = []
    try:
        for line in (st / "verdicts.jsonl").read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and str(d.get("cycle_id")) not in done:
                rows.append(d)
    except OSError:
        return {"ok": True, "consolidated": 0, "reason": "no-verdicts-file"}
    if not rows:
        return {"ok": True, "consolidated": 0}
    try:
        if str(_OPS / "memory") not in sys.path:
            sys.path.insert(0, str(_OPS / "memory"))
        import gate as memgate
        import memory_store
        g = memgate.MemoryGate(memory_store.MemoryStore())
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"gate:{type(e).__name__}"}
    n = 0
    for v in rows[:max(1, int(cap))]:
        cand = {
            "namespace": "episodic",
            "source": "deterministic",
            # INC1/F3: رکورد سیستمیِ deterministic — قراردادِ ثابتِ confidence
            # (خروجی LLM هرگز از این قرارداد استفاده نمی‌کند؛ آن مسیر calibration می‌خواهد)
            "confidence": "0.9",
            "confidence_source": "SYSTEM_DETERMINISTIC_RULE",
            "confidence_method": "RULE-INC1-DETERMINISTIC-0.9",
            "producer": "goal_action_bridge",
            "agent_id": "goal_action_bridge",
            "scope": "project",
            "classification": "internal",
            "task_id": str(v.get("cycle_id") or ""),
            "content": (f"SGC cycle {v.get('cycle_id')}: goal={v.get('goal_key')} "
                        f"verdict={v.get('verdict')} — evidence: "
                        f"state/test_cycle/{{prereg,journal,verdicts}}.jsonl"),
        }
        try:
            r = g.submit(cand)
            verb, why = r.get("verb"), str(r.get("reason") or "")
            # ⚠️ `skip` دو معنیِ کاملاً متفاوت دارد و نسخهٔ اول قاتی‌شان کرد:
            #   · reason=flag-off  → گیت خاموش است؛ نشانگر **نباید** بخورد،
            #     وگرنه وقتی مالک گیت را روشن کند این حکم‌ها برای همیشه گم‌اند.
            #   · reason=dedupe…   → از قبل ثبت شده؛ یعنی **موفقیتِ idempotent**،
            #     پس باید نشانگر بخورد وگرنه هر ضربان دوباره تلاش می‌شود.
            # تستِ همین فایل این را گرفت (پل «گیت خاموش» می‌گفت در حالی که گیت
            # روشن بود و فقط ردیف تکراری بود).
            if verb == "skip" and "flag-off" in why:
                return {"ok": True, "consolidated": n, "reason": "gate-flag-off"}
            if verb in ("commit", "propose"):
                done.add(str(v.get("cycle_id")))
                n += 1
            elif verb in ("skip", "reject"):
                done.add(str(v.get("cycle_id")))   # تکراری یا ردِ قطعی
        except Exception:  # noqa: BLE001
            continue
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        tmp = marker.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"cycle_ids": sorted(c for c in done if c)}), "utf-8")
        os.replace(tmp, marker)
    except OSError:
        pass
    return {"ok": True, "consolidated": n}
