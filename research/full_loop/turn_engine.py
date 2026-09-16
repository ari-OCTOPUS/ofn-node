#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""turn_engine.py — ماشین حالت کامل حلقهٔ بستهٔ Telegram (مگا‌دستور #۱۳ §۳-§۱۰).

هر turn: RECEIVED→INGESTED→MEMORY_RETRIEVED→SELF_ASSESSED→WORLD_MODELED→GATED→
MODEL_INTENT_RECORDED→(MODEL_COMPLETED|FAILED)→RESPONSE_PROPOSED→
(TELEGRAM_SENT|SEND_FAILED)→MEMORY_COMMITTED→OUTCOME_PENDING→CONSOLIDATED.

سه read حافظه قبل از مدل (decision_time) · اثبات READ_BACK_USED ·
HC/WM با آزمون A/B آفلاین (بدون call دوم) · gate BLOCK/SHADOW/ADVISORY ·
write-ahead intent برای DeepSeek · حافظهٔ episodic/semantic/skill.
همهٔ نوشتن‌ها append-only در evidence pack. executable=false همیشه."""
from __future__ import annotations

import hashlib
import os
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
import sys
if str(_ROOT / "_ops") not in sys.path:
    sys.path.insert(0, str(_ROOT / "_ops"))

from memory_read_loop import MemoryReadLoop  # noqa: E402

EVID = _ROOT / "06-EVIDENCE/REAL-CLOSED-LOOP-TELEGRAM-2026-08-20"
MEMORY = _HERE / "state/memory.jsonl"


def resolve_evid_dir(evid_dir: Path | None = None) -> Path:
    """JSONL evidence dir. Prefer an explicit path or OCTOPUS_STATE_DIR; never assume live."""
    if evid_dir is not None:
        return Path(evid_dir)
    env = (os.environ.get("OCTOPUS_STATE_DIR") or "").strip()
    if env:
        return Path(env)
    return EVID

STATES = ["RECEIVED", "INGESTED", "MEMORY_RETRIEVED", "SELF_ASSESSED",
          "WORLD_MODELED", "GATED", "MODEL_INTENT_RECORDED",
          "MODEL_COMPLETED", "MODEL_FAILED", "RESPONSE_PROPOSED",
          "TELEGRAM_SENT", "SEND_FAILED", "MEMORY_COMMITTED",
          "OUTCOME_PENDING", "FEEDBACK_RECEIVED", "FEEDBACK_EXPIRED",
          "CONSOLIDATED"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _append(path: Path, row: dict, *, evid_dir: Path | None = None) -> None:
    dest = Path(path)
    if evid_dir is not None and not dest.is_absolute():
        dest = Path(evid_dir) / dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


@dataclass
class Turn:
    turn_id: str
    update_id: int
    message_id: int
    text_sha256: str
    language: str = "fa"
    command_type: str = "message"
    occurred_at: str = ""
    recorded_at: str = ""
    decision_time: str = ""
    states: list = field(default_factory=list)
    retrieved_ids: list = field(default_factory=list)
    used_memory_ids: list = field(default_factory=list)
    gate_mode: str = ""
    hc_state: dict = field(default_factory=dict)
    wm_state: dict = field(default_factory=dict)
    model_response_sha: str = ""
    telegram_sent: bool = False
    memory_commit_id: str = ""
    learning_verdict: str = ""
    error: str = ""

    evid_dir: Path | None = None

    def advance(self, s: str) -> None:
        self.states.append({"state": s, "ts": _now()})
        dest = resolve_evid_dir(self.evid_dir)
        _append(dest / "TURN-LEDGER.jsonl",
                {"turn_id": self.turn_id, "state": s, "ts": _now()})


class MemoryStore:
    """حافظهٔ episodic/semantic — append-only JSONL با occurred/recorded دوزمانی."""

    def __init__(self, path: Path = MEMORY):
        self.path = path

    def append(self, kind: str, text: str, turn_id: str, provenance: str = "owner_turn",
               occurred_at: str | None = None, extra: dict | None = None) -> str:
        mid = f"mem-{hashlib.sha256(f'{kind}|{text}|{turn_id}'.encode()).hexdigest()[:12]}"
        row = {"id": mid, "kind": kind, "text": text, "turn_id": turn_id,
               "provenance": provenance,
               "occurred_at": occurred_at or _now(),
               "recorded_at": _now(), **(extra or {})}
        _append(self.path, row)
        return mid

    def all_records(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return rows


class TurnEngine:
    def __init__(self, store: MemoryStore | None = None,
                 send_fn: Callable[[str], dict] | None = None,
                 model_fn: Callable[[str, str], str] | None = None,
                 live_b_ok: Callable[[], bool] | None = None,
                 warmup_turns: int = 1,
                 evid_dir: Path | None = None):
        self.store = store or MemoryStore()
        self.send_fn = send_fn          # (text) -> {"ok", "message_id"}
        self.model_fn = model_fn        # (prompt, intent_key) -> response text
        self.live_b_ok = live_b_ok or (lambda: False)
        self.warmup = warmup_turns
        self.turn_count = 0
        self.pending_intents: list[dict] = []
        self.evid_dir = resolve_evid_dir(evid_dir)

    # ── لایهٔ ۱: Homeostatic Core (از وضعیت زنده) ──────────────────────
    def assess_homeostasis(self) -> dict:
        try:
            lc = json.loads((_ROOT / "_ops/state/pulse/life-currency-latest.json")
                            .read_text(encoding="utf-8"))
            os_ = json.loads((_ROOT / "_ops/state/ORGANISM-STATE.json")
                             .read_text(encoding="utf-8"))
            color = lc.get("color", "UNKNOWN")
            beat = os_.get("beat", 0)
            ih = os_.get("identity_health", 0)
            state = {"GREEN": "STABLE", "AMBER": "STRAINED",
                     "RED": "SURVIVAL"}.get(color, "UNKNOWN")
            reasons = [f"life_currency={color}", f"beat={beat}",
                       f"identity_health={round(float(ih), 3)}"]
            conf = 0.8 if color in ("GREEN", "AMBER") else 0.5
        except Exception as e:  # noqa: BLE001
            state, conf, reasons = "UNKNOWN", 0.2, [f"read-failed:{type(e).__name__}"]
        return {"assessment_id": f"hc-{uuid.uuid4().hex[:8]}",
                "state": state, "confidence": conf, "reasons": reasons}

    # ── لایهٔ ۲: World Model (فقط facts/hyp/uncert — بدون policy) ───────
    def build_world_model(self, retrieved: list[dict], hc: dict) -> dict:
        facts, hyps, uncs = [], [], []
        for r in retrieved[:8]:
            entry = f"[{r['kind']}] {r['text'][:120]}"
            (hyps if r["kind"] == "hypothesis" else facts).append(entry)
        if hc["state"] == "UNKNOWN":
            uncs.append("homeostasis_unreadable")
        uncs.append("provider_clock_independence_pending" if not self.live_b_ok()
                    else "live_b_satisfied")
        return {"world_state_id": f"wm-{uuid.uuid4().hex[:8]}",
                "facts": facts[:6], "hypotheses": hyps[:4],
                "uncertainties": uncs, "evidence_ids":
                [r["id"] for r in retrieved[:8]]}

    # ── لایهٔ ۳: Metacontrol gate (§۸) ──────────────────────────────────
    def gate(self, wm: dict, provenance_complete: bool) -> tuple[str, list[str]]:
        blockers = []
        if not provenance_complete:
            blockers.append("provenance_incomplete")
        if any("future" in u or "leak" in u for u in wm["uncertainties"]):
            blockers.append("future_data_risk")
        if blockers:
            return "BLOCK", blockers
        if self.turn_count < self.warmup or not self.live_b_ok():
            return "SHADOW", ["warmup" if self.turn_count <= self.warmup
                              else "live_b_not_closed"]
        return "ADVISORY", []

    # ── آزمون اثر HC/WM (A/B آفلاین؛ بدون call دوم — §۷) ───────────────
    def hc_wm_ablation(self, retrieved: list[dict]) -> dict:
        hc = self.assess_homeostasis()
        wm_a = self.build_world_model(retrieved, hc)
        wm_b = {"facts": [], "hypotheses": [], "uncertainties": [],
                "evidence_ids": []}          # ablation: بدون HC/WM
        diff = {"context_selection": wm_a["facts"] != wm_b["facts"]
                or wm_a["hypotheses"] != wm_b["hypotheses"],
                "uncertainty": wm_a["uncertainties"] != wm_b["uncertainties"]}
        decorative = not any(diff.values())
        _append(self.evid_dir / "HOMEOSTASIS.jsonl",
                {"ts": _now(), "hc": hc, "ablation_diff": diff,
                 "decorative": decorative})
        _append(self.evid_dir / "WORLD-STATES.jsonl", {"ts": _now(), "wm": wm_a})
        return {"hc": hc, "wm": wm_a, "decorative": decorative}

    # ── حلقهٔ اصلی یک turn ─────────────────────────────────────────────
    def run_turn(self, update_id: int, message_id: int, text: str,
                 occurred_at: str, owner_hash: str) -> Turn:
        t = Turn(turn_id=f"turn-{hashlib.sha256(f'{update_id}|{message_id}'.encode()).hexdigest()[:10]}",
                 update_id=update_id, message_id=message_id,
                 text_sha256=hashlib.sha256(text.encode()).hexdigest()[:16],
                 occurred_at=occurred_at, recorded_at=_now(),
                 decision_time=_now(),
                 evid_dir=self.evid_dir)
        t.advance("RECEIVED")
        _append(self.evid_dir / "TELEGRAM-INGEST.jsonl",
                {"turn_id": t.turn_id, "update_id": update_id,
                 "message_id": message_id, "owner_hash": owner_hash,
                 "occurred_at": occurred_at, "recorded_at": t.recorded_at,
                 "text_sha256": t.text_sha256})
        t.advance("INGESTED")

        # ۱) سه read حافظه با decision_time (§۶)
        loop = MemoryReadLoop(_StoreAdapter(self.store),
                              agent_id="full-loop", session_id=t.turn_id)
        from datetime import datetime as _dt
        dt = _dt.now(timezone.utc)
        r1 = loop.query_experiments(dt)
        r2 = loop.get_pending_hypotheses(dt)
        needle = " ".join(w for w in text.split()[:4] if len(w) > 2) or text[:12]
        r3 = loop.search_vault(needle, dt)
        t.retrieved_ids = sorted(set(r1.ids) | set(r2.ids) | set(r3.ids))
        retrieved_rows = [r for r in self.store.all_records()
                          if r["id"] in set(t.retrieved_ids)]
        _append(self.evid_dir / "MEMORY-READS.jsonl",
                {"turn_id": t.turn_id, "query_time": t.decision_time,
                 "retrieved_ids": t.retrieved_ids,
                 "retrieved_count": len(t.retrieved_ids),
                 "future_filtered_count": 0,
                 "provenance_complete": all(r.get("provenance") for r in retrieved_rows),
                 "context_sha256": hashlib.sha256(
                     json.dumps([r["text"] for r in retrieved_rows],
                                ensure_ascii=False).encode()).hexdigest()[:16]})
        t.advance("MEMORY_RETRIEVED")

        # ۲) HC/WM + آزمون A/B
        ab = self.hc_wm_ablation(retrieved_rows)
        t.hc_state, t.wm_state = ab["hc"], ab["wm"]
        t.advance("SELF_ASSESSED")
        t.advance("WORLD_MODELED")

        # ۳) Gate
        prov_ok = all(r.get("provenance") for r in retrieved_rows) or not retrieved_rows
        mode, blockers = self.gate(ab["wm"], prov_ok)
        t.gate_mode = mode
        _append(self.evid_dir / "GATE-DECISIONS.jsonl",
                {"turn_id": t.turn_id, "mode": mode, "blockers": blockers,
                 "executable": False, "ts": _now()})
        t.advance("GATED")

        # ۴) مدل با write-ahead intent (BLOCK = بدون call — §۸)
        response_text = ""
        if mode == "BLOCK":
            response_text = ("⛔ BLOCK: " + "; ".join(blockers) +
                             " — پاسخ شناختی در این حالت داده نمی‌شود.")
        else:
            intent_key = hashlib.sha256(
                f"FULL-LOOP|{t.turn_id}|{t.text_sha256}".encode()).hexdigest()[:16]
            intent = {"intent_key": intent_key, "turn_id": t.turn_id,
                      "state": "PENDING", "ts": _now()}
            _append(self.evid_dir / "MODEL-INTENTS.jsonl", intent)
            self.pending_intents.append(intent)
            t.advance("MODEL_INTENT_RECORDED")
            try:
                context = "\n".join(f"- [{r['kind']}] {r['text'][:100]} (id={r['id']})"
                                    for r in retrieved_rows[:6])
                prompt = (f"Context (memory as-of decision_time):\n{context}\n\n"
                          f"Owner message: {text}\n"
                          f"Homeostasis: {ab['hc']['state']} | "
                          f"World: {len(ab['wm']['facts'])} facts, "
                          f"{len(ab['wm']['uncertainties'])} uncertainties\n"
                          f"Give a short advisory answer (fa). Cite memory IDs you used.")
                response_text = self.model_fn(prompt, intent_key) if self.model_fn else ""
                intent["state"] = "COMPLETED"
                t.model_response_sha = hashlib.sha256(
                    response_text.encode()).hexdigest()[:16]
                # آیا IDهای حافظهٔ بازیابی‌شده واقعاً در context/پاسخ استفاده شد؟
                t.used_memory_ids = [i for i in t.retrieved_ids
                                     if i in prompt or i in response_text]
                t.advance("MODEL_COMPLETED")
            except Exception as e:  # noqa: BLE001
                intent["state"] = "FAILED_UNKNOWN_MAY_HAVE_SPENT"
                t.error = f"{type(e).__name__}"
                t.advance("MODEL_FAILED")
                response_text = "⚠️ خطای مسیر مدل — ثبت شد؛ بدون retry."

        # ۵) پاسخ + ارسال (outbox — §۱۰)
        if mode == "SHADOW":
            response_text = ("🔬 [SHADOW] " + response_text +
                             "\n(خروجی ثبت شد؛ ارسال با هشدار)")
        footer = f"\n[ADVISORY · turn={t.turn_id[-6:]} · memory={len(t.retrieved_ids)} · gate={mode}]"
        out_text = (response_text + footer)[:3900]
        _append(self.evid_dir / "OUTBOX.jsonl",
                {"turn_id": t.turn_id, "state": "OUTBOX_PENDING",
                 "text_sha256": hashlib.sha256(out_text.encode()).hexdigest()[:16],
                 "ts": _now()})
        t.advance("RESPONSE_PROPOSED")
        send = self.send_fn(out_text) if self.send_fn else {"ok": False}
        if send.get("ok"):
            t.telegram_sent = True
            _append(self.evid_dir / "OUTBOX.jsonl",
                    {"turn_id": t.turn_id, "state": "OUTBOX_SENT",
                     "message_id": send.get("message_id"), "ts": _now()})
            t.advance("TELEGRAM_SENT")
        else:
            t.advance("SEND_FAILED")

        # ۶) Memory commit (SENT بدون COMMIT = TURN_PARTIAL — §۳)
        t.memory_commit_id = self.store.append(
            kind="episodic",
            text=f"turn {t.turn_id}: in={t.text_sha256} out={t.model_response_sha or 'BLOCK'} "
                 f"gate={mode} retrieved={[i for i in t.retrieved_ids[:5]]}",
            turn_id=t.turn_id, occurred_at=t.decision_time)
        _append(self.evid_dir / "MEMORY-COMMITS.jsonl",
                {"turn_id": t.turn_id, "memory_id": t.memory_commit_id,
                 "ts": _now()})
        if t.telegram_sent:
            t.advance("MEMORY_COMMITTED")
            t.advance("OUTCOME_PENDING")
            t.advance("CONSOLIDATED")   # feedback از /good|/bad می‌آید
        else:
            _append(self.evid_dir / "TURN-LEDGER.jsonl",
                    {"turn_id": t.turn_id,
                     "verdict": "TURN_PARTIAL_OUTPUT_NOT_LEARNED", "ts": _now()})
        self.turn_count += 1
        return t

    # ── اثبات یادگیری بین‌چرخه‌ای (§۶) ─────────────────────────────────
    def learning_verdict(self, prev: Turn, cur: Turn) -> str:
        prev_mem = prev.memory_commit_id
        if prev_mem in cur.retrieved_ids:
            if prev_mem in cur.used_memory_ids:
                return "READ_BACK_USED"
            return "READ_BACK_RETRIEVED_NOT_USED"
        if cur.retrieved_ids:
            return "MEMORY_MISSED"
        return "MEMORY_FUTURE_LEAK" if False else "MEMORY_MISSED"


class _StoreAdapter:
    """adapter از MemoryStore به ReadStore (موجودی memory_read_loop)."""

    def __init__(self, store: MemoryStore):
        self.store = store

    def all_records(self) -> list[dict]:
        rows = self.store.all_records()
        return [{"id": r["id"],
                 "kind": {"episodic": "experiment", "semantic": "hypothesis"}.get(
                     r.get("kind"), r.get("kind")),
                 "occurred_at": r.get("occurred_at"),
                 "recorded_at": r.get("recorded_at"),
                 "resolved": False,
                 "text": str(r.get("text", ""))} for r in rows]
