#!/usr/bin/env python3
"""acquisition_pipeline.py — Project-F · خطِ لولهٔ محتوایِ propose-only.

جریان: auto_plan (draft از AcquisitionBrain یا هوکِ امن) → صف → approve/reject (یک‌تاپِ مالک)
       → finalize (payloadِ آماده برای **پستِ دستیِ انسان**).

قاعدهٔ ساختاری (مثلِ Leg): **هیچ متدِ post/send/dm/pay/publishِ واقعی وجود ندارد.** این ماژول
هرگز به شبکه/پلتفرم/اکانت وصل نمی‌شود؛ AI درفت می‌زند، انسان می‌فرستد (ToS-safe، ACQUISITION-ENGINE §۴).
`PF_LIVE_PUBLISH` فقط *برچسبِ* readiness را عوض می‌کند — هرگز چیزی را خودکار منتشر نمی‌کند.

content-free (بدونِ هویت/رسانه/شهر/فارسی — گاردِ rule #6) · $0 offline · stdlib · fail-closed.
مرجع: 01 - Strategy/Identity/CLAIMS-REGISTER · ACQUISITION-ENGINE-2026-07-05 · 05 - Acquisition/AUTO-ACQUISITION-BLUEPRINT.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DEFAULT_STORE = _HERE / "acq_queue.json"

# safety nets (اختیاری — fail-soft اگه guards.py غایب باشد)
try:
    from guards import check_all_guards, WarmupGuard, ChannelLocks
except ImportError:  # pragma: no cover — standalone use بدونِ guards
    check_all_guards = None  # type: ignore
    WarmupGuard = None       # type: ignore
    ChannelLocks = None      # type: ignore

CHANNELS = ("reddit", "x", "of", "fansly")
# گاردِ کپیِ عمومی — best-effort denylist (نه جامع؛ انسان هر آیتم را هم بازبینی می‌کند).
# پاریته با _ops/events.py _BANNED_ECHO (هویت/پلتفرم) + شهرِ ممنوع + قومیتِ متنی + claimِ ممنوع.
# توجه: «Aussie / Australia / Down Under» کشوری‌اند و مجاز — عمداً بن نمی‌شوند (VOICE-AND-STYLE).
_BANNED_COPY = (
    "اونلی", "onlyfans", "fansly", "صبا", "saba",              # هویت/پلتفرم (containment)
    "sydney", "سیدنی", "harbour", "harbor", "bondi", "nsw",     # شهرِ ممنوع (rule #6)
    "melbourne", "opera house",
    "persian", "iranian",                                       # قومیتِ متنیِ ممنوع (rule #6/#9)
    "best in", "guaranteed", "fresh flower",                    # claimِ ممنوع
)
_FLAG = "(draft flagged: rule #6/containment — بازنویسی لازم)"
# هوک‌های امنِ پیش‌فرض (زیرمجموعهٔ P4 — feet-only، Aussie، بدونِ شهر/فارسی/explicit)
_SAFE_HOOKS = (
    ("reddit", "arch-of-the-day", "Arch of the Day — this one's a toll bridge."),
    ("x", "sole-sunday", "Sole Sunday, ep. — the softest one yet."),
    ("reddit", "polish-poll", "Nude polish or deep red? You decide."),
    ("x", "soft-cta", "The preview is free. The good angle isn't."),
    ("of", "welcome", "You'll never see my face. That's the whole point."),
)


def _now() -> float:
    return time.time()


class AcquisitionPipeline:
    """صفِ محتوایِ propose-only. هیچ افکتورِ بیرونی. انسان پست می‌کند.

    Safety nets (2026-07-16 launch guard):
      - ``warmup`` (WarmupGuard): جلوی finalizeِ آیتمِ فروشی تا رسیدنِ کارما به آستانه.
      - ``locks`` (ChannelLocks): kill-switch per-channel و full_stop.
      - ``vault`` (VaultBank): منبعِ draft از محتوای واقعی (لایهٔ ۲، 2026-07-16).
    هر سه اختیاری‌اند (None = غیرفعال) ولی در production باید وصل باشند."""

    def __init__(self, store_path=None, brain=None, warmup=None, locks=None,
                 vault=None):
        self._store = Path(store_path) if store_path else DEFAULT_STORE
        self._brain = brain                      # AcquisitionBrain (injectable؛ None → هوکِ امن)
        self._warmup = warmup                     # WarmupGuard اختیاری
        self._locks = locks                       # ChannelLocks اختیاری
        self._vault = vault                       # VaultBank اختیاری (لایهٔ ۲)
        self._items = self._load()

    # ── persistence (fail-soft) ──────────────────────────────────────────────
    def _load(self) -> list:
        try:
            if self._store.exists():
                d = json.loads(self._store.read_text("utf-8"))
                return d if isinstance(d, list) else []
        except (OSError, ValueError):
            pass
        return []

    def _save(self) -> None:
        try:
            self._store.write_text(
                json.dumps(self._items, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _find(self, item_id: str):
        for i in self._items:
            if i.get("id") == item_id:
                return i
        return None

    # ── copy guard (rule #6 / CLAIMS-REGISTER) ───────────────────────────────
    @staticmethod
    def _copy_ok(text: str) -> bool:
        low = (text or "").lower()
        return not any(b in low for b in _BANNED_COPY)

    @classmethod
    def _all_clean(cls, *texts) -> bool:
        """همهٔ رشته‌های خروجی (caption+hook+tag) باید از گارد رد شوند."""
        return all(cls._copy_ok(t) for t in texts)

    # ── AUTO: plan → draft → enqueue (propose-only) ──────────────────────────
    def _seeds(self, n: int) -> list:
        """seedهای draft (ترتیبِ اولویت، fail-soft):
          ۱. VaultBank (اگه وصل باشد و asset داشته باشد) — محتوای واقعی certify‌شده
          ۲. brain.plan_week (اگه مغز وصل باشد) — insights هوشمند
          ۳. _SAFE_HOOKS (همیشه) — fallback هوک‌های امنِ نمونه

        لایهٔ ۲ (2026-07-16): vault اولویتِ اول است چون محتوای واقعی certify‌شده
        دارد، نه نمونه. اگه vault خالی باشد، transparently به brain/fallback می‌رود."""
        seeds = []
        # ۱. VaultBank — کم‌استفاده‌ترین assetها (fair rotation)
        if self._vault is not None:
            try:
                # همهٔ channelها را بپرس، n تا
                assets = self._vault.pick(n=n)
                for a in assets:
                    seeds.append({"channel": a.get("channel", "reddit"),
                                  "tag": a.get("tag", ""),
                                  "hook": a.get("hook", ""),
                                  "caption": a.get("caption") or a.get("hook", ""),
                                  "vault_id": a.get("id")})   # برای mark_used بعدی
            except Exception:  # noqa: BLE001 — fail-soft به brain
                seeds = []
        # ۲. brain.plan_week (اگه هنوز تعداد کم است)
        if len(seeds) < n and self._brain is not None:
            try:
                plan = self._brain.plan_week()
                posts = getattr(plan, "posts", None) or (plan.get("posts") if isinstance(plan, dict) else None)
                for p in (posts or [])[:n - len(seeds)]:
                    if isinstance(p, dict):
                        seeds.append({"channel": p.get("platform") or p.get("channel") or "reddit",
                                      "tag": p.get("tag", ""), "hook": p.get("hook") or p.get("title", ""),
                                      "caption": p.get("caption") or p.get("hook") or ""})
            except Exception:  # noqa: BLE001
                pass
        # ۳. fallback: هوک‌های امن (همیشه)
        while len(seeds) < n:
            ch, tag, hook = _SAFE_HOOKS[len(seeds) % len(_SAFE_HOOKS)]
            seeds.append({"channel": ch, "tag": tag, "hook": hook, "caption": hook})
        return seeds[:n]

    def auto_plan(self, n: int = 3) -> list:
        """n آیتمِ draft بساز و صف کن. draftهای ناقضِ برند flag می‌شوند (approve نمی‌شوند)."""
        out = []
        for s in self._seeds(max(1, int(n))):
            cap = str(s.get("caption", ""))
            hook = str(s.get("hook", ""))
            tag = str(s.get("tag", ""))
            # گارد روی هر سه فیلدِ خروجی (نه فقط caption)؛ flag اگر هرکدام ناپاک باشد
            flagged = not self._all_clean(cap, hook, tag)
            item = {
                "id": "PF-" + uuid.uuid4().hex[:10],
                "status": "drafted",
                "channel": s.get("channel", "reddit") if s.get("channel") in CHANNELS else "reddit",
                # وقتی flagged: هر سه فیلد پاک‌سازی می‌شوند (متنِ ناپاک هرگز persist نمی‌شود)
                "tag": (_FLAG if flagged else tag[:40]),
                "hook": (_FLAG if flagged else hook[:120]),
                "caption": (_FLAG if flagged else cap[:280]),
                "flagged": flagged,
                "created": _now(),
                "approved_by": None,
                # لایهٔ ۲: اگه از vault آمده، id را نگه دار برای mark_used در finalize
                "vault_id": s.get("vault_id"),
            }
            self._items.append(item)
            out.append(item)
        self._save()
        return out

    # ── queries ──────────────────────────────────────────────────────────────
    def by_status(self, status: str) -> list:
        return [i for i in self._items if i.get("status") == status]

    def pending(self) -> list:
        return self.by_status("drafted")

    # ── owner one-tap (approve/reject) — propose-only، بدونِ اثرِ بیرونی ───────
    def approve(self, item_id: str, actor: str = "owner") -> dict:
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        if it.get("flagged"):
            return {"ok": False, "error": "brand-flagged draft — بازنویسی لازم پیش از approve"}
        if it.get("status") not in ("drafted", "approved"):
            return {"ok": False, "error": f"cannot approve from {it.get('status')}"}
        it["status"] = "approved"
        it["approved_by"] = str(actor)[:24]
        it["approved_at"] = _now()
        self._save()
        return {"ok": True, "id": item_id, "status": "approved"}

    def reject(self, item_id: str, reason: str = "") -> dict:
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        it["status"] = "rejected"
        it["reject_reason"] = str(reason)[:120]
        self._save()
        return {"ok": True, "id": item_id, "status": "rejected"}

    # ── finalize: payloadِ آماده برای پستِ *دستیِ انسان* (هرگز auto-post) ──────
    def finalize(self, item_id: str) -> dict:
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        if it.get("status") != "approved":
            return {"ok": False, "error": "must be approved first (fail-closed)"}
        # belt-and-suspenders: گاردِ نهاییِ payloadِ خروجی (fail-closed) — هرگز متنِ ناپاک بیرون نده
        if not self._all_clean(it.get("caption", ""), it.get("hook", ""), it.get("tag", "")):
            it["status"] = "rejected"
            it["reject_reason"] = "containment/rule#6 at finalize (fail-closed)"
            self._save()
            return {"ok": False, "error": "payload failed containment guard at finalize (fail-closed)"}
        # safety-net (2026-07-16): warm-up guard + channel-lock check قبل از ready.
        # اگه فروشی است و کارما کم، یا کانال locked، یا full_stop → deny (fail-closed).
        # توجه: آیتم reject نمی‌شود — فقط finalize می‌ایستد تا شرایط جور شود (آری بعداً دوباره).
        if self._warmup is not None or self._locks is not None:
            ok, reason = check_all_guards(
                it.get("channel", "reddit"),
                hook=it.get("hook", ""), caption=it.get("caption", ""), tag=it.get("tag", ""),
                warmup=self._warmup, locks=self._locks)
            if not ok:
                self._save()   # state بدون تغییرِ آیتم
                return {"ok": False, "error": f"finalize blocked by safety net — {reason}",
                        "item_status": it.get("status"),
                        "note": "آیتم approved ماند؛ وقتی شرایط جور شد دوباره /pf_ready بزن."}
        live_labeled = os.environ.get("PF_LIVE_PUBLISH", "0") == "1"
        it["status"] = "ready"
        it["ready_at"] = _now()
        # لایهٔ ۲: اگه از vault آمده، استفاده را ثبت کن (fair rotation)
        vault_id = it.get("vault_id")
        if vault_id and self._vault is not None:
            try:
                self._vault.mark_used(vault_id)
            except Exception:  # noqa: BLE001 — fail-soft، finalize را نمی‌شکند
                pass
        self._save()
        return {
            "ok": True, "id": item_id, "status": "ready",
            "auto_posted": False,   # همیشه — این ماژول هرگز خودش پست نمی‌کند
            "mode": "ready-for-live-human-post" if live_labeled else "shadow-human-post",
            "payload": {"channel": it["channel"], "hook": it["hook"], "caption": it["caption"]},
            "note": ("payload برای پستِ دستیِ انسان. اتصالِ اکانتِ واقعی، انتشار و هر اتوماسیونِ "
                     "بیرونی = دستِ مالک، پس از GATE 0 + verdict (این ماژول افکتورِ زنده ندارد)."),
        }

    # ── admin digest (content-free — برای UIِ ادمینِ اختاپوس) ─────────────────
    def admin_digest(self) -> dict:
        d = {
            "drafted": len(self.by_status("drafted")),
            "approved": len(self.by_status("approved")),
            "ready": len(self.by_status("ready")),
            "rejected": len(self.by_status("rejected")),
            "flagged": len([i for i in self._items if i.get("flagged")]),
            "next": "approve/reject در تلگرام؛ انتشارِ واقعی = دستیِ انسان پس از GATE 0",
            "outward_execution": False,
        }
        # safety-net snapshot اگه guards وصل باشند
        if self._warmup is not None:
            d["warmup"] = {"karma": self._warmup.get_karma(),
                           "threshold": self._warmup.threshold(),
                           "met": self._warmup.threshold_met()}
        if self._locks is not None:
            d["locks"] = self._locks.snapshot()
        if self._vault is not None:
            try:
                vs = self._vault.summary()
                d["vault"] = {"enabled": True, "total": vs.get("total", 0),
                              "channels": vs.get("channels", []), "tags": vs.get("tags", [])}
            except Exception:  # noqa: BLE001 — فقط شفافیت status؛ pipeline نباید بشکند
                d["vault"] = {"enabled": False, "total": 0, "error": "summary failed"}
        return d

    # ── KPI feedback → brain (یادگیری) ────────────────────────────────────────
    def record_kpi(self, item_id: str, upvotes: int = 0, comments: int = 0,
                   unlocks: int = 0, day: str = "") -> dict:
        if self._brain is None:
            return {"ok": False, "error": "no brain"}
        it = self._find(item_id)
        if it is None:
            return {"ok": False, "error": "not found"}
        try:
            self._brain.feedback_loop(it.get("tag", ""), it.get("channel", ""),
                                      int(upvotes), int(comments), int(unlocks), str(day))
        except Exception:  # noqa: BLE001
            return {"ok": False, "error": "feedback failed"}
        return {"ok": True, "id": item_id}

    # NOTE: عمداً هیچ متدِ post/send/dm/publish/pay وجود ندارد (propose-only ساختاری).
