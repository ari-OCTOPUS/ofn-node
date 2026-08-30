"""shadow.py — گیتِ propose-only سرتاسری (G11).

تصمیمِ ثبت‌شدهٔ مالک (Strategy-DecisionLog.md): سیستمِ مارکتینگِ چند-ایجنتی تا
رسیدنِ ۱۰–۳۰ فروشِ واقعی در حالتِ **shadow** می‌ماند. یعنی هر اکشنِ روبه‌بیرون
فقط proposal می‌سازد و **هرگز اجرا نمی‌شود**.

این ماژول چهار لایه را به هم می‌بندد:
  • command_registry → ریسک/حالتِ فرمان
  • authz            → نقشِ حاکمیتِ کاربر (owner/admin/viewer/agent)
  • governance       → چرخهٔ propose→decide با گیتِ RED
  • store(ledger)    → ثبتِ تغییرناپذیر

قواعدِ سخت (fail-closed):
  • فرمانِ ناشناخته → رد.
  • حالتِ auto (GREEN) = خواندنی؛ proposal نمی‌سازد و چیزی اجرا نمی‌کند.
  • حالت‌های propose/approval/red_gate → فقط proposal؛ هیچ side-effect.
  • can_execute تا وقتی shadow روشن است **همیشه False** است — حتی با decisionِ
    approved. خاموش‌کردنِ shadow فقط با نقشِ owner ممکن است.
این ماژول خودش هیچ ارسال/انتشار/خرجی انجام نمی‌دهد؛ فقط گیت و پروپوزال است.
"""
from __future__ import annotations

from typing import Optional

from . import governance
from .command_registry import CommandRegistry

_SHADOW_FLAG = "ziman_shadow"     # کلیدِ store.flags؛ نبود = روشن (پیش‌فرضِ امن)


class ShadowGate:
    def __init__(self, store, registry: Optional[CommandRegistry] = None,
                 authz=None):
        self.store = store
        self.registry = registry or CommandRegistry.load()
        self.authz = authz

    # ── حالتِ shadow ────────────────────────────────────────────────────────
    def is_shadow_on(self) -> bool:
        """پیش‌فرضِ امن: اگر پرچم تنظیم نشده باشد، shadow روشن است."""
        return self.store.get_flag(_SHADOW_FLAG, "on") != "off"

    def set_shadow(self, on: bool, actor_role: str) -> dict:
        """خاموش/روشن‌کردنِ shadow — فقط owner. غیرِ owner → PermissionError."""
        if (actor_role or "").strip().lower() != "owner":
            self.store.append_event(
                kind="shadow_denied", project="ziman",
                detail=f"role={actor_role} tried set_shadow({on})", actor=actor_role)
            raise PermissionError("only owner (SahebZiman) may change shadow mode")
        self.store.set_flag(_SHADOW_FLAG, "off" if not on else "on")
        self.store.append_event(
            kind="shadow_set", project="ziman",
            detail=f"shadow={'on' if on else 'off'}", actor=actor_role)
        return {"shadow_on": self.is_shadow_on()}

    def _role(self, actor_chat_id: Optional[int], actor_role: Optional[str]) -> str:
        if actor_role:
            return actor_role.strip().lower()
        if self.authz is not None and actor_chat_id is not None:
            return self.authz.ziman_role_for_chat(actor_chat_id)
        return "agent"   # فراخوانِ برنامه‌ای بدونِ زمینهٔ کاربر → ایجنت (approve ممنوع)

    # ── مسیرِ اصلی: هر اکشنِ روبه‌بیرون از اینجا می‌گذرد ─────────────────────
    def submit(self, command: str, detail: str, actor_chat_id: Optional[int] = None,
               actor_role: Optional[str] = None, project: str = "ziman") -> dict:
        """یک فرمان را طبقه‌بندی می‌کند و در صورتِ نیاز proposal می‌سازد.

        خروجی همیشه شاملِ executed=False است (این گیت هرگز اجرا نمی‌کند).

        نکتهٔ طراحی: اینجا عمداً `registry.role_allowed` اعمال نمی‌شود. submit مسیرِ
        *پیشنهاد* است و در سیستمِ propose-only خودِ ایجنت (که در فیلدِ roles نیست)
        باید بتواند اکشن‌های YELLOW/ORANGE/RED را برای تأییدِ مالک پیشنهاد دهد —
        وگرنه خودمختاریِ propose-only می‌شکند. فیلدِ `roles` رجیستری *فراخوانیِ
        تعاملیِ فرمان* را گیت می‌کند (در adapterها با owner_only)، و تصمیم‌گیری با
        can_decide (NC-3: ایجنت هرگز approve نمی‌کند). info['roles'] در خروجی می‌آید
        تا adapter بتواند در صورتِ نیاز فراخوانیِ تعاملی را گیت کند.
        """
        info = self.registry.classify(command)
        role = self._role(actor_chat_id, actor_role)
        base = {"command": info["command"], "risk": info["risk"],
                "mode": info["mode"], "role": role, "executed": False,
                "allowed_roles": info["roles"]}

        if not info["known"]:
            return {**base, "status": "denied",
                    "reason": f"unknown command {command!r} (fail-closed)"}

        if info["mode"] == "auto":     # GREEN خواندنی — نه proposal، نه اجرا
            return {**base, "status": "read_only",
                    "reason": "GREEN read command; no proposal, no side-effect"}

        # propose/approval/red_gate → فقط proposal
        p = governance.propose(self.store, kind=info["command"].lstrip("/"),
                               project=project, detail=detail,
                               risk=info["risk"], proposed_by=role)
        return {**base, "status": "proposed", "proposal_id": p["proposal_id"],
                "ref": p.get("ref"),
                "reason": ("awaiting owner approval (RED)" if info["risk"] == "RED"
                           else f"proposed ({info['risk']}); awaiting decision")}

    # ── گیتِ اجرا — قلبِ propose-only ────────────────────────────────────────
    def can_execute(self, ref_or_proposal_id: str) -> dict:
        """آیا این proposal اجازهٔ اجرا دارد؟ تا shadow روشن است، هرگز.

        حتی با shadow خاموش، فقط proposalِ approved اجازه می‌گیرد (fail-closed).
        این تابع خودش اجرا نمی‌کند؛ فقط مجوز می‌دهد.
        """
        if self.is_shadow_on():
            return {"execute": False,
                    "reason": "shadow mode ON — propose-only until 10–30 real sales"}
        p = (self.store.get_proposal_by_ref(ref_or_proposal_id)
             or self.store.get_proposal(ref_or_proposal_id))
        if not p:
            return {"execute": False, "reason": "unknown proposal (fail-closed)"}
        if p.get("status") != "approved":
            return {"execute": False,
                    "reason": f"proposal not approved (status={p.get('status')})"}
        return {"execute": True, "reason": "approved and shadow off",
                "decision_id": p.get("decision_id"), "risk": p.get("risk")}

    def status(self) -> dict:
        pend = self.store.list_proposals(status="pending")
        return {"shadow_on": self.is_shadow_on(),
                "pending_proposals": len(pend),
                "ledger_ok": self.store.verify_ledger().get("ok")}
