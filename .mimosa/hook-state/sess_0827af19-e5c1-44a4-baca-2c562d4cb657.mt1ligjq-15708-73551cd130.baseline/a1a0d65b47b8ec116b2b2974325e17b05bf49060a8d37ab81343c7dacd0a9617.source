#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""life_economy.py — لایهٔ اقتصاد داروینی (فاز ۶ MEGA-FINISH-ALL-v1).

جداستی عمدی: `life_currency.py` (B1) تخصیصِ سهبعدی است و دست نمیخورد؛ این ماژول
(B2) روی آن لایهٔ rent/credit/sleep/retire/defense/چهار خزانه/ضدبازی میسازد.

قواعد قفلشده:
  - درآمد فقط از رویدادِ دارای `independent_evidence_ref`؛ خودگزارشی = صفر (ضدبازی).
  - credit <= 0 → SLEEP؛ هر ۱۰ ضربان status=OFF.
  - N چرخهٔ متوالی SLEEP → RETIRE (نه delete؛ هویت/دفاع/شواهد میمانند).
  - انتقال SURVIVAL → DISCOVERY ممنوع (رسیدِ رد).
  - هر رویداد یک رسیدِ append-only با before/after دارد؛ replay بازسازی میکند.
  - budget_after هرگز منفی نمیشود (اجاره فقط از credit مثبت کسر میشود).

همهٔ خروجیها MEASURED؛ هیچ VERIFIED. stdlib-only · fail-soft.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "life-economy.v1"
GRADE = "MEASURED"

VAULTS = ("SURVIVAL", "MAINTENANCE", "DISCOVERY", "HUMAN_VALUE")
ALLOWED_REWARD_TYPES = ("prediction_correct", "novelty_admitted", "defect_fixed",
                        "capability_replayed", "human_value")


@dataclass(frozen=True)
class EconomyConfig:
    rent_per_beat: float = 1.0
    initial_credit: float = 10.0
    sleep_threshold: float = 0.0      # credit <= threshold → SLEEP
    retire_after_sleep_cycles: int = 3
    off_every_n_beats: int = 10
    reward_units: dict = field(default_factory=lambda: {
        "prediction_correct": 2.0, "novelty_admitted": 5.0,
        "defect_fixed": 3.0, "capability_replayed": 4.0, "human_value": 6.0})


class LifeEconomy:
    def __init__(self, state_dir: Path | None = None,
                 cfg: EconomyConfig = EconomyConfig()):
        if state_dir is None:
            state_dir = Path(__file__).resolve().parent.parent / "state" / "pulse"
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.state_dir / "life-economy-events.jsonl"
        self.latest_path = self.state_dir / "life-economy-latest.json"
        self.cfg = cfg
        self.organs: dict[str, dict] = {}
        self.vaults: dict[str, float] = {v: 0.0 for v in VAULTS}

    # ── ثبت رسید (append-only) ──────────────────────────────────────────────
    def _receipt(self, event: dict) -> dict:
        row = {"schema": SCHEMA, "grade": GRADE, "ts": time.time(),
               "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S"), **event}
        row["event_hash"] = hashlib.sha256(
            json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:24]
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def _organ(self, organ_id: str, create: bool = True) -> dict | None:
        o = self.organs.get(organ_id)
        if o is None and create:
            o = {"id": organ_id, "status": "ACTIVE", "credits": self.cfg.initial_credit,
                 "energy": self.cfg.initial_credit, "sleep_cycles": 0,
                 "defense": [], "retired_at": None, "lineage": [organ_id]}
            self.organs[organ_id] = o
        return o

    # ── چرخهٔ حیات ──────────────────────────────────────────────────────────
    def beat(self, beat_id: int, organ_ids: list[str] | None = None) -> list:
        """یک ضربان: اجاره از اعضای ACTIVE با credit مثبت؛ خواب؛ خروجی OFF هر ۱۰ ضربان."""
        receipts = []
        ids = organ_ids or list(self.organs)
        for oid in ids:
            o = self._organ(oid)
            if o is None or o["status"] == "RETIRED":
                continue
            before = float(o["credits"])
            if o["status"] == "ACTIVE" and before > self.cfg.sleep_threshold:
                rent = min(self.cfg.rent_per_beat, before)
                o["credits"] = round(before - rent, 4)
                self.vaults["SURVIVAL"] = round(self.vaults["SURVIVAL"] + rent, 4)
                o["sleep_cycles"] = 0
                status = "ACTIVE"
            else:
                o["status"] = "SLEEP"
                o["sleep_cycles"] = int(o.get("sleep_cycles") or 0) + 1
                status = "SLEEP"
            if o["sleep_cycles"] >= self.cfg.retire_after_sleep_cycles:
                o["status"] = "RETIRED"
                o["retired_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                status = "RETIRED"   # نه delete؛ هویت/دفاع/شواهد میمانند
            r = self._receipt({
                "event_id": str(uuid.uuid4())[:12], "event_type": "rent",
                "organ_id": oid, "beat_id": int(beat_id),
                "status": status, "credit_before": before, "credit_after": float(o["credits"]),
                "independent_evidence_ref": "rent-ledger", "vault": "SURVIVAL",
                "actor": "life-economy", "rollback_ref": ""})
            if status == "SLEEP" and int(beat_id) % self.cfg.off_every_n_beats == 0:
                off = self._receipt({
                    "event_id": str(uuid.uuid4())[:12], "event_type": "heartbeat-off",
                    "organ_id": oid, "beat_id": int(beat_id), "status": "OFF",
                    "credit_before": float(o["credits"]), "credit_after": float(o["credits"]),
                    "independent_evidence_ref": "life-economy", "vault": "SURVIVAL",
                    "actor": "life-economy", "rollback_ref": ""})
                receipts.append(off)
            receipts.append(r)
        return receipts

    def reward(self, organ_id: str, reward_type: str, *, evidence_ref: str = "",
               amount: float | None = None) -> dict:
        """درآمد فقط با رسیدِ مستقل؛ خودگزارشی = رد و صفر credit."""
        before = float((self._organ(organ_id) or {}).get("credits") or 0.0)
        if reward_type not in ALLOWED_REWARD_TYPES:
            return self._receipt({
                "event_id": str(uuid.uuid4())[:12], "event_type": "reward-rejected",
                "organ_id": organ_id, "reason": "unknown-reward-type",
                "credit_before": before, "credit_after": before, "vault": "NONE",
                "independent_evidence_ref": evidence_ref, "actor": "life-economy"})
        if not evidence_ref:
            return self._receipt({
                "event_id": str(uuid.uuid4())[:12], "event_type": "reward-rejected",
                "organ_id": organ_id, "reason": "self-report-no-independent-evidence",
                "credit_before": before, "credit_after": before, "vault": "NONE",
                "independent_evidence_ref": "", "actor": "life-economy"})
        amt = amount if amount is not None else float(self.cfg.reward_units.get(reward_type, 0))
        o = self._organ(organ_id)
        o["credits"] = round(before + amt, 4)
        vault = {"prediction_correct": "SURVIVAL", "novelty_admitted": "DISCOVERY",
                 "defect_fixed": "MAINTENANCE", "capability_replayed": "SURVIVAL",
                 "human_value": "HUMAN_VALUE"}[reward_type]
        self.vaults[vault] = round(self.vaults[vault] + amt, 4)
        return self._receipt({
            "event_id": str(uuid.uuid4())[:12], "event_type": f"reward-{reward_type}",
            "organ_id": organ_id, "credit_before": before, "credit_after": float(o["credits"]),
            "amount": amt, "vault": vault, "independent_evidence_ref": evidence_ref,
            "actor": "life-economy", "rollback_ref": ""})

    def self_report(self, organ_id: str, amount: float) -> dict:
        """تلاش برای گرفتن credit با خودگزارشی — همیشه رد (ضدبازی)."""
        return self.reward(organ_id, "prediction_correct", evidence_ref="", amount=amount)

    def defense(self, organ_id: str, text: str) -> dict:
        """دفاعِ versioned پیش از بازنشستگی. دفاع نمیتواند معیار را عوض کند."""
        o = self._organ(organ_id)
        version = len(o.get("defense") or []) + 1
        o.setdefault("defense", []).append({"version": version, "text": str(text)[:500],
                                            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        return self._receipt({
            "event_id": str(uuid.uuid4())[:12], "event_type": "defense-recorded",
            "organ_id": organ_id, "defense_version": version,
            "credit_before": float(o["credits"]), "credit_after": float(o["credits"]),
            "vault": "SURVIVAL", "independent_evidence_ref": "life-economy",
            "actor": "life-economy"})

    def transfer(self, from_vault: str, to_vault: str, amount: float) -> dict:
        """انتقال بین خزانهها. SURVIVAL → DISCOVERY همیشه رد میشود."""
        if from_vault == "SURVIVAL" and to_vault == "DISCOVERY":
            return self._receipt({
                "event_id": str(uuid.uuid4())[:12], "event_type": "transfer-denied",
                "reason": "SURVIVAL-to-DISCOVERY-forbidden", "from_vault": from_vault,
                "to_vault": to_vault, "amount": float(amount), "vault": "NONE",
                "independent_evidence_ref": "constitution", "actor": "life-economy"})
        if amount <= 0 or self.vaults.get(from_vault, 0.0) < amount:
            return self._receipt({
                "event_id": str(uuid.uuid4())[:12], "event_type": "transfer-denied",
                "reason": "insufficient-or-invalid", "from_vault": from_vault,
                "to_vault": to_vault, "amount": float(amount), "vault": "NONE",
                "independent_evidence_ref": "life-economy", "actor": "life-economy"})
        self.vaults[from_vault] = round(self.vaults[from_vault] - amount, 4)
        self.vaults[to_vault] = round(self.vaults[to_vault] + amount, 4)
        return self._receipt({
            "event_id": str(uuid.uuid4())[:12], "event_type": "transfer-ok",
            "from_vault": from_vault, "to_vault": to_vault, "amount": float(amount),
            "vault": from_vault, "independent_evidence_ref": "life-economy",
            "actor": "life-economy", "credit_before": 0.0, "credit_after": 0.0})

    def replay(self) -> dict:
        """بازسازی موجودیها از ردیفهای append-only و مقایسه با آخرین نوشته."""
        credits: dict[str, float] = {}
        vaults = {v: 0.0 for v in VAULTS}
        off_seen = 0
        for line in self.events_path.read_text("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            et = e.get("event_type")
            if et == "rent":
                oid = e.get("organ_id")
                credits[oid] = float(e.get("credit_after") or 0.0)
                vaults["SURVIVAL"] += float(e.get("credit_before", 0) or 0) - float(
                    e.get("credit_after", 0) or 0)
            elif et and et.startswith("reward-") and not et.endswith("rejected"):
                oid = e.get("organ_id")
                credits[oid] = float(e.get("credit_after") or 0.0)
                vaults[e.get("vault") or "NONE"] += float(e.get("amount") or 0.0)
            elif et == "heartbeat-off":
                off_seen += 1
            elif et == "transfer-ok":
                vaults[e.get("from_vault") or ""] -= float(e.get("amount") or 0.0)
                vaults[e.get("to_vault") or ""] += float(e.get("amount") or 0.0)
        try:
            latest = json.loads(self.latest_path.read_text("utf-8"))
            last_organs = latest.get("organs") or {}
            consistent = all(
                abs(float((last_organs.get(k) or {}).get("credits", 0)) - float(v)) < 1e-6
                for k, v in credits.items())
            consistent = consistent and all(
                abs(float((latest.get("vaults") or {}).get(k, 0)) - float(v)) < 1e-6
                for k, v in vaults.items())
        except Exception:  # noqa: BLE001
            consistent = False
        return {"schema": SCHEMA, "grade": GRADE, "replay_ok": consistent,
                "credits_replayed": credits, "vaults_replayed": vaults,
                "off_heartbeats": off_seen}

    def snapshot(self) -> dict:
        state = {"schema": SCHEMA, "grade": GRADE, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "organs": self.organs, "vaults": self.vaults,
                 "receipts": sum(1 for _ in self.events_path.open(encoding="utf-8"))}
        tmp = self.latest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), "utf-8")
        import os
        os.replace(tmp, self.latest_path)
        return state

    def run_sim(self, beats: int = 12, seed: str = "sim-fixed") -> dict:
        """شبیهسازی قطعی در زیرشاخهٔ ایزوله (فایل رویدادِ runtime را آلوده نمیکند)."""
        sub = self.state_dir / f"sim-{seed}"
        sim = LifeEconomy(state_dir=sub, cfg=self.cfg)
        random_marker = hashlib.sha256(seed.encode()).hexdigest()[:8]
        for oid in ("organism", "work_pump"):
            o = sim._organ(oid)
            o["credits"] = 20.0 if oid == "organism" else 3.0
        out = []
        out.append(sim.defense("work_pump", f"defense-v1 ({random_marker})"))
        out.append(sim.self_report("organism", 99.0))                      # رد میشود
        out.append(sim.reward("organism", "prediction_correct",
                              evidence_ref=f"pred-ledger:{random_marker}"))  # +2
        out.append(sim.transfer("SURVIVAL", "DISCOVERY", 5.0))            # رد میشود
        for b in range(1, beats + 1):
            out += sim.beat(b, ["organism", "work_pump"])
        state = sim.snapshot()
        return {"seed": seed, "beats": beats, "events": len(out), "state": state,
                "replay": sim.replay(), "state_dir": str(sub)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--seed", default="fixed")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--state-dir", default=str(
        Path(__file__).resolve().parent.parent / "state" / "pulse"))
    args = ap.parse_args()
    eco = LifeEconomy(Path(args.state_dir))
    if args.sim:
        r = eco.run_sim(seed=args.seed)
        print(json.dumps(r, ensure_ascii=False, indent=1))
    elif args.replay:
        print(json.dumps(eco.replay(), ensure_ascii=False, indent=1))
    else:
        ap.print_help()
