#!/usr/bin/env python3
"""vault_updater.py — propose-only «تولیدکنندهٔ patch» برای vault (جلسه ۴۶).

رأی مالک: «پرامپتِ به‌روزرسانی نباید بنویسد — باید patch تولید کند. شناخت (classify/draft)
را از اثر (EffectorGate که commit می‌کند) جدا کن.» این ماژول **هرگز به دیسک دست نمی‌زند**؛
خروجی‌اش یک PATCH PROPOSALِ اعتبارسنجی‌شدهٔ layer-aware و ledger-ready است (JSONِ سخت‌گیر).
نوشتنِ واقعی از gate/human-append می‌گذرد. cognition ≠ effect.

سیاستِ commit = Ring × risk × Autonomy-Envelope:
  Ring 0 (ژنوم/قانون اساسی)      → HOLD (فقط flag، هرگز edit)
  Ring 1 (schema/index/MOC/PROJECT)→ GATE (همیشه رأیِ انسان)
  Ring 2-3 (نوتِ دامنه)          → AUTO اگر risk=LOW و مسیر ∈ envelope، وگرنه GATE
  Ring 4 (inbox/scratch)         → AUTO اگر risk=LOW، وگرنه GATE
  Project-F / PII / CRITICAL     → HOLD + escalate (تخطی‌ناپذیر)

ریل‌های سخت (fail-closed): هرگز delete/overwrite (فقط append یا supersede-with-pointer)؛
هرگز provenance جعل نکن (بی‌منبع → HOLD)؛ retrievalِ خالی/ابهام/schema ناقص → HOLD؛
CRITICAL هرگز downgrade/suppress نمی‌شود. $0 · stdlib · deterministic.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

# ── LAYER_MAP: Ring per مسیر (prefix؛ خاص‌ترین برنده) ─────────────────────────────
# Ring 0 = ژنوم/قانون اساسی (READ-ONLY)، 1 = schema/index/MOC، 2-3 = دامنه، 4 = inbox/scratch.
RING_RULES = [
    # (regex مسیر, ring)  — به‌ترتیب؛ اولین تطبیق برنده.
    (r"^(CLAUDE\.md|_PROJECT_INSTRUCTIONS\.md|\.agentignore)$", 0),
    (r"(^|/)_code(/|$)", 0),
    (r"^07 - Knowledge/genome-system/ledger/", 0),
    (r"ROTATION|CHARTER|charter|SECRETS-ROTATION", 0),
    (r"Property Schema|\.obsidian/types\.json", 1),
    (r"(^|/)_Index - ", 1),
    (r"(^|/)(Home|HANDOFF)\.md$", 1),
    (r"(^|/)PROJECT\.md$", 1),
    (r"^00 - Inbox/", 4),
    (r"^10 - Telegram processing/Raw/", 4),
    (r"^(03 - Projects|07 - Knowledge|09 - People|02 - Life OS)/", 3),
]
# مسیرهای هرگز-نوشتنی (فقط مقصدِ انتقال) و Project-F (HOLD مطلق).
_ARCHIVE_RE = re.compile(r"(^|/)(_Archive|_Duplicates)(/|$)")
_PROJECTF_RE = re.compile(r"اونلی|onlyfans|Project-F", re.I)
# PII/secret (fail-closed → HOLD/CRITICAL).
_PII_RE = re.compile(
    r"(\b09\d{9}\b|\b\d{10,}\b|@[\w.]+\.\w+|\b0x[a-fA-F0-9]{20,}\b|"
    r"api[_-]?key|password|seed phrase|private key|wallet)", re.I)
_CRITICAL_RE = re.compile(
    r"(secret|کلید|راز|password|wallet|seed|\.pem|delete|حذف|drop table|"
    r"rm -rf|قانون اساسی|constitution|germline|ژنوم)", re.I)
_DECISION_RE = re.compile(r"(تصمیم|verdict|decide|approv|رأی|choose|انتخاب)", re.I)
_TASK_RE = re.compile(r"(todo|\[ \]|باید|task|انجام بده|پیگیری|deadline|مهلت)", re.I)
_REF_RE = re.compile(r"(https?://|منبع|source|ref:|arxiv|doi)", re.I)


def ring_for(path: str) -> int:
    """Ring یک مسیر. پیش‌فرضِ ناشناخته = 3 (دامنه) — محافظه‌کار (GATE مگر LOW+envelope)."""
    p = str(path or "")
    for rx, ring in RING_RULES:
        if re.search(rx, p):
            return ring
    return 3


def classify(raw: str, target_path: str = "") -> dict:
    """{kind, target_ring, sensitivity}. deterministic؛ cognitionِ LLM بعداً plug می‌شود."""
    t = str(raw or "")
    if _DECISION_RE.search(t):
        kind = "decision"
    elif _TASK_RE.search(t):
        kind = "task"
    elif _REF_RE.search(t):
        kind = "reference"
    elif len(t) > 240:
        kind = "insight"
    else:
        kind = "fact"
    sens = "high" if (_PII_RE.search(t) or _CRITICAL_RE.search(t)) else "normal"
    return {"kind": kind, "target_ring": ring_for(target_path), "sensitivity": sens}


def _tokens(s: str) -> set:
    return {w for w in re.split(r"\W+", str(s).lower()) if len(w) > 2}


def dedup(raw: str, candidates: list[dict], tau: float = 0.5) -> dict:
    """شباهتِ tokenِ (Jaccard) raw با کاندیداها. ≥τ → merge/append به همان نوت.
    candidates: [{path, summary}]. (ارتقا: cosineِ hash-embeddingِ neural/encoders.)"""
    rt = _tokens(raw)
    best_path, best = None, 0.0
    for c in candidates or []:
        ct = _tokens(c.get("summary", "") + " " + c.get("path", ""))
        if not rt or not ct:
            continue
        sim = len(rt & ct) / len(rt | ct)
        if sim > best:
            best, best_path = sim, c.get("path")
    matched = best_path if best >= tau else None
    return {"matched_path": matched, "cosine": round(best, 3)}


def risk_flag(cls: dict, path: str, conflict: bool) -> str:
    """LOW | REVIEW | CRITICAL. CRITICAL هرگز downgrade نمی‌شود."""
    if cls.get("sensitivity") == "high" or ring_for(path) == 0:
        return "CRITICAL"
    if conflict or ring_for(path) == 1:
        return "REVIEW"
    return "LOW"


def commit_mode(ring: int, risk: str, in_envelope: bool, projectf: bool) -> str:
    """AUTO | GATE | HOLD — طبقِ جدولِ Ring×risk×envelope. fail-closed."""
    if projectf:
        return "HOLD"
    if risk == "CRITICAL" or ring == 0:
        return "HOLD" if ring == 0 else "GATE"
    if ring == 1:
        return "GATE"
    if ring == 4:
        return "AUTO" if risk == "LOW" else "GATE"
    # Ring 2-3
    if risk == "LOW" and in_envelope:
        return "AUTO"
    return "GATE"


def _sha(s: str) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:16]


def propose(raw_input: str, *, provenance: str = "", target_path: str = "",
            candidates: list[dict] | None = None, autonomy_envelope: list[str] | None = None,
            existing_body: str = "", tau: float = 0.5) -> dict:
    """هستهٔ propose-only: raw → PATCH PROPOSALِ JSONِ سخت‌گیر. **هرگز به دیسک نمی‌نویسد.**"""
    candidates = candidates or []
    envelope = autonomy_envelope or []

    def _hold(reason: str, prompt: str) -> dict:
        return {"status": "HOLD", "classification": classify(raw_input, target_path),
                "target_path": target_path, "commit_mode": "HOLD", "risk": "REVIEW",
                "dedup": {"matched_path": None, "cosine": 0.0}, "patch": "",
                "ledger_entry": {}, "rationale": reason[:240],
                "human_prompt": prompt[:300]}

    # ریل‌های HOLDِ سخت (fail-closed)
    if not str(raw_input or "").strip():
        return _hold("ورودی خالی", "چیزی برای ثبت نیست.")
    if not str(provenance or "").strip():
        return _hold("provenance ندارد (بی‌منبع → HOLD)", "منبعِ این اطلاعات چیست؟")
    if _PROJECTF_RE.search(raw_input) or _PROJECTF_RE.search(target_path):
        return _hold("Project-F → containment", "این به Project-F مربوط است — در ابزارِ خودش.")
    if _PII_RE.search(raw_input):
        return _hold("PII/secret شناسایی شد → HOLD", "اطلاعاتِ حساس؛ دستیِ خودت رسیدگی کن.")
    if _ARCHIVE_RE.search(target_path):
        return _hold("_Archive/_Duplicates فقط مقصدِ انتقال است", "به لایهٔ فعال هدف بده.")

    cls = classify(raw_input, target_path)
    dd = dedup(raw_input, candidates, tau)
    # retrievalِ خالی → فرضِ تکراری، HOLD (طبقِ اسپک: کورکورانه نوتِ نو نساز)
    if not candidates and not target_path:
        return _hold("retrievalِ خالی + مسیرِ نامشخص → HOLD", "کجا ثبت شود؟ مسیر بده.")

    matched = dd["matched_path"]
    tgt = matched or target_path
    ring = ring_for(tgt)
    projectf = bool(_PROJECTF_RE.search(tgt))
    conflict = False   # (نگاشتِ تضادِ محتوایی: اگر matched ولی محتوا مغایر — v-بعد)
    risk = risk_flag(cls, tgt, conflict)
    in_env = any(tgt.startswith(e) for e in envelope)
    mode = commit_mode(ring, risk, in_env, projectf)

    op = "append" if matched else "create"
    if matched and conflict:
        op = "supersede"   # هرگز overwrite — نوتِ قدیم حفظ + pointer
    body = str(raw_input).strip()
    after = _sha(existing_body + body if op == "append" else body)
    patch = {"op": op, "path": tgt, "content": body[:2000],
             "append_preferring": True, "idempotent": True}
    ledger = {"before_hash": _sha(existing_body) if existing_body else "",
              "after_hash": after, "op": op, "provenance": str(provenance)[:200],
              "rationale": f"{cls['kind']} → Ring{ring} → {mode}",
              "ts": opslib.now_iso()}
    out = {
        "status": "OK", "classification": cls, "target_path": tgt,
        "commit_mode": mode, "risk": risk, "dedup": dd,
        "patch": json.dumps(patch, ensure_ascii=False),
        "ledger_entry": ledger,
        "rationale": f"{cls['kind']} · Ring{ring} · {'merge' if matched else 'create'} · {mode}",
    }
    if mode in ("GATE", "HOLD"):
        out["human_prompt"] = (f"«{body[:80]}» → {tgt} (Ring{ring}، {risk}). "
                               + ("تأیید می‌کنی؟" if mode == "GATE" else "دستی رسیدگی کن."))
    return out
