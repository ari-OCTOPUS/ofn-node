#!/usr/bin/env python3
"""leg.py — Phase 4 · L-0: چارچوبِ پا (workerِ ایزوله، harnessِ مشترک).

ایزولاسیونِ Worker (INV-17، IsolationModel.md): هر پا یک task_packetِ حداقلی می‌گیرد —
read-allowlist فقط به نوت‌های پروژهٔ خودش (هرگز wildcard، هرگز کلِ vault)، ابزارِ scoped،
بودجهٔ سخت، spawn=0، secrets=[] (همیشه خالی). خروجیِ پا = یک proposalِ بررسی‌پذیر، نه
نوشتن در source-of-truth (AgentInstructions.md · INV-10). هیچ اثرِ برگشت‌ناپذیری بدونِ
human-append (INV-01 / TINV-7) شلیک نمی‌شود.

money_link الزامی (INV-14): پای بدونِ money_linkِ حل‌شده = incubating (هرگز زیرِ organ_gate
بودجه‌گیری نمی‌کند). هر پا زیرِ organ_gate بودجه دارد (T2 پک) وقتی active باشد.

propose-only: پا فقط draft/quote/گزارش تولید می‌کند؛ هرگز send/publish/pay/trade نمی‌کند.
هر اثرِ بیرونی → از کانالِ تلگرامِ P3 (human-append، is_human=1).

PII/دادهٔ مشتری محلی می‌ماند، هرگز به هیچ LLMِ بیرونی نمی‌رود (D-26، Master Painting).
additive: هیچ ماژولِ موجودی تغییر نمی‌کند. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

# دسترسی به _ops/ (opslib + organ_gate + attribution)
_HERE = Path(__file__).resolve().parent              # _ops/legs
_OPS = _HERE.parent                                    # _ops
_BUDGET = _OPS / "budget"
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_BUDGET) not in sys.path:
    sys.path.insert(0, str(_BUDGET))
import opslib        # noqa: E402


# ─── task_packet — capability-scoped، minimal (IsolationModel.md) ───────────────
# هرگز wildcard در allowlist. هرگز secrets غیرخالی. این قراردادِ structural است که
# در __init__ verify می‌شود (fail-closed: پا ساخته نمی‌شود اگر نقض کند).

@dataclass(frozen=True)
class TaskPacket:
    """بستهٔ حداقلی که یک پا می‌بیند. هر فیلد = یک capability-bound."""
    leg_id: str                                       # هویتِ پا (مثلاً "lead-naghshi")
    organ: str                                        # ارگانِ بودجه (در budgets.yaml)
    read_allowlist: tuple[str, ...]                   # IDهای مشخصِ نوت‌ها؛ هرگز "*"
    tools: tuple[str, ...] = ()                       # ابزارِ scoped (پیش‌فرض: هیچ)
    budget_aud: float = 0.0                           # سقفِ hardِ این task
    spawn: int = 0                                    # INV-17: همیشه ۰
    secrets: tuple = field(default_factory=tuple)     # همیشه خالی (verified)

    def __post_init__(self):
        # verify ساختاری (structural، نه behavioral — INV-17/AP-14)
        if not self.leg_id or not self.organ:
            raise ValueError("leg_id و organ الزامی‌اند")
        if any(w == "*" or w == "" for w in self.read_allowlist):
            raise ValueError("wildcard/خالی در read_allowlist ممنوع (IsolationModel D2)")
        if not self.read_allowlist:
            raise ValueError("read_allowlist خالی ممنوع — پا حداقل یک نوت می‌بیند")
        if self.spawn != 0:
            raise ValueError("spawn≠0 ممنوع (INV-17: worker تا proposal محدود است)")
        if self.secrets:
            raise ValueError("secrets غیرخالی ممنوع (D1: اعتبارنامه از مرز عبور نمی‌کند)")
        if self.budget_aud < 0:
            raise ValueError("budget_aud منفی ممنوع")

    def can_read(self, note_id: str) -> bool:
        """چکِ capability: آیا این پا اجازهٔ خواندنِ این note_id را دارد؟ دقیقاً matching."""
        return note_id in self.read_allowlist


# ─── Proposal — تنها خروجیِ مجازِ پا (D3: structural output confinement) ─────────
@dataclass
class Proposal:
    """یک پیشنهادِ بررسی‌پذیر. پا نمی‌تواند source-of-truth را بنویسد؛ فقط این را تولید می‌کند.
    provenance: actor/leg_id/hash (D5 — approval یک eventِ جداگانهٔ انسانی است که پا نمی‌تواند جعل کند)."""
    proposal_id: str
    leg_id: str
    kind: str                  # "draft_quote" / "report" / "draft_message"
    payload: dict
    hlc: tuple = (0, 0)        # HLC-stamp طبقِ P1 (leg از bus نمی‌خواند، مالک stamp می‌زند یا ۰)

    def to_dict(self) -> dict:
        h = self._hash()
        return {"proposal_id": self.proposal_id, "leg_id": self.leg_id,
                "kind": self.kind, "payload": self.payload,
                "hlc": list(self.hlc), "hash": h}

    def _hash(self) -> str:
        import hashlib
        canon = json.dumps({"proposal_id": self.proposal_id, "leg_id": self.leg_id,
                            "kind": self.kind, "payload": self.payload,
                            "hlc": list(self.hlc)}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]


# ─── Leg — کلاسِ پایهٔ worker ───────────────────────────────────────────────────
class Leg:
    """پایهٔ workerِ ایزوله. task_packet را لود می‌کند، بریفِ allowlistedش را می‌خواند،
    proposal تولید می‌کند. زیرِ organ_gate می‌رود (وقتی active). propose-only."""

    def __init__(self, packet: TaskPacket, organ_table: dict | None = None):
        self.packet = packet
        # organ_table قابل‌تزریق (تست بدونِ budgets.yaml واقعی). None = opslib.organ_table
        self._organ_table = organ_table
        # money_link (INV-14): پای بدونِ organِ حل‌شده = incubating
        self._money_link = self._resolve_money_link()
        self._proposals_emitted: list[Proposal] = []

    # -- money_link (INV-14) ----------------------------------------------------
    def _resolve_money_link(self) -> str:
        """وضعیتِ money_link: 'active' (organ موجود) یا 'incubating' (نبود).
        پای incubating هرگز organ_gate.reserve نمی‌کند — فقط proposal."""
        organs = self._organ_table if self._organ_table is not None else _safe_organ_table()
        if self.packet.organ in organs:
            return "active"
        return "incubating"

    @property
    def money_link(self) -> str:
        return self._money_link

    # -- ایزولاسیونِ خواندن (D2) -------------------------------------------------
    def read_brief(self, note_id: str, fs_get=None) -> str | None:
        """خواندنِ یک نوت از allowlist. اگر note_id در allowlist نباشد → None (fail-closed،
        نه exception که پا را بکشد — فقط رد). fs_get قابل‌تزریق (تست بدونِ دیسک).
        PII هرگز به LLM نمی‌رود — این متد فقط متن برمی‌گرداند، فراخوانِ آن مسئولِ مرز است."""
        if not self.packet.can_read(note_id):
            return None                                    # خارجِ allowlist = رد
        if fs_get is not None:
            return fs_get(note_id)
        # پیش‌فرض: خواندن از مسیرِ نوت (نسبی به vault root). fail-soft: نبود = None.
        try:
            p = opslib.STATE_DIR.parent.parent / note_id   # _ops/state → vault
            if p.exists():
                return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        return None

    # -- organ_gate (T2 پک) — فقط وقتی active ---------------------------------
    def reserve_budget(self, est_aud: float, task: str = "") -> dict:
        """رزروِ بودجه زیرِ organ_gate. پای incubating → deny (fail-closed).
        est_aud → est_usd با نرخِ FX. زیرِ سقفِ packet.budget_aud هم چک می‌شود."""
        if self._money_link != "active":
            return {"allow": False, "reason": f"incubating (no money_link for {self.packet.organ})"}
        if est_aud > self.packet.budget_aud > 0:           # سقفِ hardِ task_packet (0 = نامحدودِ ارگانیسم)
            return {"allow": False, "reason": f"over-task-budget(AU${est_aud}>{self.packet.budget_aud})"}
        try:
            import organ_gate                              # noqa: WPS433 — lazy
        except Exception as e:                             # noqa: BLE001
            return {"allow": False, "reason": f"organ_gate-unavailable:{e}"}
        fx_inv = 1.0 / max(_safe_fx(), 0.0001)             # AUD→USD
        return organ_gate.reserve(self.packet.organ, est_aud * fx_inv, task=task)

    def settle_budget(self, est_aud: float, actual_aud: float, task: str = "") -> dict:
        """settle بعد از کار. پای incubating → no-op."""
        if self._money_link != "active":
            return {"ok": False, "reason": "incubating"}
        try:
            import organ_gate                              # noqa: WPS433
        except Exception:                                  # noqa: BLE001
            return {"ok": False, "reason": "organ_gate-unavailable"}
        fx_inv = 1.0 / max(_safe_fx(), 0.0001)
        return organ_gate.settle(self.packet.organ, est_aud * fx_inv, actual_aud * fx_inv, task=task)

    def release_budget(self, est_aud: float, task: str = "") -> dict:
        """بازپس‌گیریِ رزروِ شکست‌خورده. پای incubating → no-op."""
        if self._money_link != "active":
            return {"ok": False, "reason": "incubating"}
        try:
            import organ_gate                              # noqa: WPS433
        except Exception:                                  # noqa: BLE001
            return {"ok": False, "reason": "organ_gate-unavailable"}
        fx_inv = 1.0 / max(_safe_fx(), 0.0001)
        return organ_gate.release(self.packet.organ, est_aud * fx_inv, task=task)

    # -- تولیدِ proposal (D3 — تنها خروجیِ مجاز) --------------------------------
    def emit_proposal(self, kind: str, payload: dict, hlc: tuple = (0, 0)) -> Proposal:
        """تولیدِ یک proposal. هیچ متدِ send/publish/pay در Leg نیست (propose-only).
        leg_id و provenance رویش مهر می‌خورد. approval = eventِ جداگانهٔ انسانی (D5)."""
        p = Proposal(proposal_id=f"P-{uuid.uuid4().hex[:12]}", leg_id=self.packet.leg_id,
                     kind=kind, payload=dict(payload), hlc=tuple(hlc))
        self._proposals_emitted.append(p)
        return p

    @property
    def proposals(self) -> list[Proposal]:
        return list(self._proposals_emitted)

    # -- متدهای ممنوع (propose-only — صریح برای خواننده/تست) --------------------
    # توابعِ send/publish/pay/trade عمداً وجود ندارند. هر اثرِ بیرونی از کانالِ P3
    # (human-append) می‌آید، نه از پا. این یک structural constraint است (INV-17).

    def status(self) -> dict:
        """snapshot فقط‌خواندنی از وضعیتِ پا."""
        return {"leg_id": self.packet.leg_id, "organ": self.packet.organ,
                "money_link": self._money_link,
                "read_allowlist": list(self.packet.read_allowlist),
                "tools": list(self.packet.tools), "budget_aud": self.packet.budget_aud,
                "spawn": self.packet.spawn, "secrets_count": len(self.packet.secrets),
                "proposals_emitted": len(self._proposals_emitted)}


# ─── helpersِ fail-soft (تست‌پذیر، بدونِ وابستگیِ import-time) ──────────────────
def _safe_organ_table() -> dict:
    try:
        return opslib.organ_table()
    except Exception:                                      # noqa: BLE001
        return {}


def _safe_fx() -> float:
    """AUD per USD (برای تبدیلِ est_aud→est_usd). fail-soft: 1.5 (تقریبی AU)."""
    try:
        fx, _ = opslib.fx_aud_per_usd()
        return float(fx) or 1.5
    except Exception:                                      # noqa: BLE001
        return 1.5
