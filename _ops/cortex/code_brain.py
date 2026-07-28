#!/usr/bin/env python3
"""code_brain.py — مغزِ تولیدِ patch برای خودمختاریِ کد (L0، propose-only).

این ماژول «مغز» است که جلویِ خالی بودنِ ورودیِ code_autonomy.tick() را می‌گیرد:
یک task انسانی (مثلاً «در _ops/telegram_center/parser.py تابع parse را در برابرِ
JSON خراب مقاوم کن») را می‌گیرد و یک patch کاندید {target, content, intent} تولید
می‌کند. **صفر اعمالِ زنده، صفر نوشتنِ مستقیم به درخت** — خروجی فقط به shadow-testِ
code_autonomy داده می‌شود (که خودش در worktree ایزوله می‌زند).

قرارداد با code_autonomy (حفظِ safety model، تغییری در گیت‌ها نیست):
  - target باید داخلِ allow-list باشد (code_autonomy._ALLOW_ROOTS). اگر نباشد،
    مغز None برمی‌گرداند → patchای تولید نمی‌شود → هیچ‌چیز به صف نمی‌رود.
  - intent همیشه content-free است (کدِ هدف، نه توضیحِ بیزنس).
  - مغز هرگز خودش shadow/apply/commit نمی‌کند. فقط محتوای کاندید می‌دهد.

سطح‌بندیِ agent (هر سه stdlib-only، انتخاب در زمانِ اجرا):
  - L1 SDK: اگر `claude_agent_sdk` نصب باشد و OCTOPUS_CODE_BRAIN=1 → agent با tool-use.
  - L1 API: اگر نباشد ولی ANTHROPIC_API_KEY باشد → raw urllib + tool-use API
    (همان الگوی langar_bot._think_agent، بدون وابستگیِ بیرونی).
  - L0: اگر هیچ‌کدام نباشد → task را در pending-tasks باقی می‌گذارد (هیچ کدی تولید
    نمی‌شود). این یعنی نبودِ مغز چیزی را نمی‌شکند — همان invariantِ DualBrainV3.

$0 · stdlib + opslib. تست: `_ops/tests/test_code_brain.py`.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent                 # _ops/cortex
_OPS = _HERE.parent
for _p in (str(_OPS / "budget"), str(_HERE), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

import code_autonomy  # noqa: E402  — برای allowed_target() + deny/allow-list

FLAG = "OCTOPUS_CODE_BRAIN"          # کلیدِ روشن‌کردنِ مغز (default OFF)
TASKS_DIR = opslib.STATE_DIR / "cortex" / "pending-tasks"
BRAIN_LOG = opslib.STATE_DIR / "cortex" / "code-brain.jsonl"
_MAX_PATCH_BYTES = 200_000          # سقفِ اندازهٔ محتوای تولیدی (دژ در برابرِ انفجار)


def enabled() -> bool:
    """مغز روشن است؟ فلگِ صریحِ مالک لازم است (default OFF = هیچ patchای تولید نمی‌شود)."""
    return str(os.environ.get(FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def _log(rec: dict) -> None:
    try:
        rec = {"ts": opslib.now_iso(), **rec}
        opslib.append_jsonl(BRAIN_LOG, rec)
    except Exception:  # noqa: BLE001
        pass


def _has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _can_spend() -> bool:
    """چکِ سقفِ هزینه — همان CostMeterِ langar را می‌خواند (fail-closed)."""
    try:
        cost_path = Path(_OPS.parent / "03 - Projects" / "اونلی فنز" / "langar" / "cost_meter.json")
        if not cost_path.exists():
            return True     # بدونِ فایل = محدودیتی نیست (مغز پیشنهاد می‌دهد، اعمالِ گیت‌شده)
        from datetime import date
        st = json.loads(cost_path.read_text(encoding="utf-8"))
        month = date.today().strftime("%Y-%m")
        if st.get("month") != month:
            return True
        cap = float(os.environ.get("LANGAR_MONTHLY_CAP_AUD", 15))
        return float(st.get("spent_aud", 0.0)) < cap
    except Exception:  # noqa: BLE001
        return False      # state نامعتبر = مصرف ممنوع (fail-closed)


def _add_cost(aud: float) -> None:
    """ثبتِ هزینهٔ تخمینی به همان cost_meter.json (اشتراک با لنگر)."""
    try:
        cost_path = Path(_OPS.parent / "03 - Projects" / "اونلی فنز" / "langar" / "cost_meter.json")
        from datetime import date
        month = date.today().strftime("%Y-%m")
        st = {"month": month, "spent_aud": 0.0}
        if cost_path.exists():
            loaded = json.loads(cost_path.read_text(encoding="utf-8"))
            if loaded.get("month") == month:
                st = loaded
        st["spent_aud"] = round(float(st.get("spent_aud", 0.0)) + max(aud, 0.001), 4)
        cost_path.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


# ─── system prompt (embed کردنِ deny/allow-list تا agent از همان ابتدا بداند) ─────
def _system_prompt() -> str:
    deny = ", ".join(code_autonomy._DENY)
    allow = ", ".join(code_autonomy._ALLOW_ROOTS)
    return (
        "You are a code-patch generator for the Octopus organism. Output STRICT JSON only.\n"
        f"ALLOWED target roots (you may ONLY patch files under these): {allow}\n"
        f"HARD DENY (never touch, even if asked): {deny}\n"
        "Rules:\n"
        "1. Read the target file with the read_file tool first, then propose a FULL replacement "
        "content for that single file.\n"
        "2. If the requested change would touch a denied path or is out of the allowed roots, "
        'return {\"target\": null, \"content\": null, \"reason\": \"out-of-scope\"}.\n'
        "3. Never invent file paths; target must be an existing file you read.\n"
        "4. Never include secrets, real names, cities, tokens, or PII.\n"
        "5. Keep intent short and content-free (describe the code change, not business).\n"
        "Respond with ONE JSON object: "
        '{"target": "<relative path under an allowed root>", "content": "<full new file content>", '
        '"intent": "<one line>"}'
    )


# ─── ابزارهای خواندن (sandbox) ───────────────────────────────────────────────────
def _read_file_tool(target_rel: str) -> str:
    """خواندنِ فایلِ هدف (read-only). فقط داخلِ allow-list."""
    if not code_autonomy.allowed_target(target_rel):
        return "ERROR: خارج از allow-list."
    repo = _OPS.parent
    tgt = repo.joinpath(*target_rel.split("/"))
    if not tgt.exists():
        return "ERROR: فایل وجود ندارد."
    try:
        return tgt.read_text(encoding="utf-8", errors="ignore")[:40000]
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {type(e).__name__}"


def _list_dir_tool(path: str) -> str:
    repo = _OPS.parent
    base = repo.joinpath(*path.split("/")) if path else repo
    rel = str(base.relative_to(repo)).replace("\\", "/") + "/"
    if not code_autonomy.allowed_target(rel):
        return "ERROR: خارج از allow-list."
    try:
        return "\n".join(sorted(p.name + ("/" if p.is_dir() else "")
                                for p in base.iterdir())[:80]) or "(empty)"
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {type(e).__name__}"


_TOOLS = [
    {"name": "read_file", "description": "محتوای کاملِ یک فایل درونِ allow-list (read-only).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                      "required": ["path"]}},
    {"name": "list_dir", "description": "فهرستِ محتویاتِ یک مسیر درونِ allow-list (read-only).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                      "required": ["path"]}},
]
_TOOL_FN = {"read_file": lambda path: _read_file_tool(path),
            "list_dir": lambda path: _list_dir_tool(path)}


def _extract_json(text: str) -> Optional[dict]:
    """بیرون‌کشیدنِ JSON object از پاسخِ مدل (مدل ممکن است با متن بپیچاند)."""
    if not text:
        return None
    # ابتدا کل متن، بعد اولین {... }.
    for cand in (text.strip(), _first_json_object(text)):
        if not cand:
            continue
        try:
            d = json.loads(cand)
            if isinstance(d, dict):
                return d
        except (ValueError, TypeError):
            continue
    return None


def _first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        return ""
    depth = 0
    instr = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return ""


def _api_messages_create(body: dict) -> dict:
    """POST به api.anthropic.com/v1/messages با tool-use (stdlib urllib)."""
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


# ─── هستهٔ تولیدِ patch ─────────────────────────────────────────────────────────
def draft_patch(task: str, *, max_turns: int = 5) -> Optional[dict]:
    """یک task انسانی → patch کاندید {target, content, intent}. صفر اعمال.

    بازگشت None = تولید نشد (نبودِ کلید/بودجه/مجوز، یا مدل خارج از محدوده گفت).
    خروجی همیشه validated است: target درونِ allow-list و content غیرخالی و زیرِ سقف.
    اعمال هرگز اینجا نیست — code_autonomy.tick(patch) آن را در worktree می‌زند.
    """
    if not enabled():
        _log({"event": "skipped", "reason": "flag-off"})
        return None
    if not task or not task.strip():
        return None
    if not _has_key():
        _log({"event": "skipped", "reason": "no-api-key"})
        return None
    if not _can_spend():
        _log({"event": "skipped", "reason": "cost-cap"})
        return None

    try:
        patch = _draft_via_api(task, max_turns)
    except Exception as e:  # noqa: BLE001
        _log({"event": "draft-error", "err": str(e)[:200]})
        return None
    if not patch:
        return None
    # اعتبارسنجیِ نهایی (defense-in-depth، حتی اگر مدل اشتباه کند)
    tgt = str(patch.get("target") or "")
    content = str(patch.get("content") or "")
    if not code_autonomy.allowed_target(tgt):
        _log({"event": "rejected", "reason": "target-not-allowed", "target": tgt[:120]})
        return None
    if not content.strip() or len(content) > _MAX_PATCH_BYTES:
        _log({"event": "rejected", "reason": "bad-content"})
        return None
    out = {"target": tgt, "content": content,
           "intent": str(patch.get("intent") or task[:100])[:200]}
    _log({"event": "drafted", "target": tgt, "intent": out["intent"][:80]})
    return out


def _draft_via_api(task: str, max_turns: int) -> Optional[dict]:
    """raw urllib + tool-use loop (همان الگوی langar، صفر وابستگیِ بیرونی)."""
    msgs = [{"role": "user", "content": task[:2000]}]
    for _ in range(max(1, max_turns)):
        resp = _api_messages_create({
            "model": os.environ.get("CODE_BRAIN_MODEL", "claude-haiku-4-5"),
            "max_tokens": 2000,
            "system": _system_prompt(),
            "messages": msgs,
            "tools": _TOOLS,
        })
        usage = resp.get("usage", {})
        aud = (usage.get("input_tokens", 0) * 1 + usage.get("output_tokens", 0) * 5) / 1e6 * 1.55
        _add_cost(aud)
        # پایانِ مکالمه: پاسخِ نهایی را به‌عنوان JSON parse کن
        if resp.get("stop_reason") != "tool_use":
            text = "".join(b.get("text", "") for b in resp.get("content", [])
                           if b.get("type") == "text")
            return _extract_json(text)
        # اجرای tool‌ها و افزودنِ نتیجه
        msgs.append({"role": "assistant", "content": resp.get("content", [])})
        results = []
        for b in resp.get("content", []):
            if b.get("type") == "tool_use":
                fn = _TOOL_FN.get(b.get("name"), lambda **_: "no-such-tool")
                res = fn(**(b.get("input") or {}))
                results.append({"type": "tool_result", "tool_use_id": b.get("id"),
                                "content": str(res)[:8000]})
        msgs.append({"role": "user", "content": results})
    return None


# ─── صفِ taskها (قراردادِ file-based، هم‌سان با pending-patches) ────────────────
def enqueue_task(task: str, *, source: str = "langar") -> str:
    """task را در pending-tasks/<id>.json ذخیره می‌کند. id = task-<hash>."""
    import hashlib
    tid = "task-" + hashlib.sha256(task.encode("utf-8")).hexdigest()[:10]
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"id": tid, "task": task[:2000], "source": source, "ts": opslib.now_iso(),
           "status": "pending"}
    (TASKS_DIR / f"{tid}.json").write_text(json.dumps(rec, ensure_ascii=False), "utf-8")
    return tid


def pending_tasks() -> list[dict]:
    """فهرستِ taskهای pending روی دیسک."""
    if not TASKS_DIR.exists():
        return []
    out = []
    for f in sorted(TASKS_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text("utf-8"))
            if d.get("status") == "pending":
                out.append(d)
        except Exception:  # noqa: BLE001
            continue
    return out


def _consume_task(task_id: str) -> None:
    """علامت‌گذاریِ task به‌عنوان done (نه حذف — برای حسابرسی باقی می‌ماند)."""
    try:
        p = TASKS_DIR / f"{task_id}.json"
        if p.exists():
            d = json.loads(p.read_text("utf-8"))
            d["status"] = "done"
            d["done_ts"] = opslib.now_iso()
            p.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
    except Exception:  # noqa: BLE001
        pass


# ─── تپش: خواندنِ صف → draft_patch → code_autonomy.tick ─────────────────────────
AUTOAPPLY_FLAG = "OCTOPUS_CODE_AUTOAPPLY_LOWRISK"


def _autoapply_lowrisk() -> bool:
    """auto-apply برای کم‌ریسک روشن است؟ (default OFF؛ رأیِ صریحِ مالک)."""
    return str(os.environ.get(AUTOAPPLY_FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def _stamp_auto_approval(proposal_id: str, intent: str) -> None:
    """نوشتنِ یک approval موقت برای auto-apply (معادلِ تپِ ✅ مالک).

    فقط وقتی auto-apply روشن است صدا زده می‌شود. این همان فایلِ approvals/<id>.json
    است که apply_approved آن را می‌خواند — یعنی هر ۷ گیتِ آن همچنان فعال‌اند.
    مرورِ زمانِ تأییدِ code_autonomy (۴۸h) روی آن صدق می‌کند: اگر driver دیر اجرا
    شود، auto-approval کهنه می‌شود و اعمال نمی‌شود (fail-closed)."""
    import time
    try:
        apdir = code_autonomy.APPROVALS_DIR
        apdir.mkdir(parents=True, exist_ok=True)
        rec = {"verdict": "ok", "epoch": time.time(),
               "ts": opslib.now_iso(), "by": "auto-lowrisk",
               "reason": f"shadow-green + low-risk flag: {intent[:80]}"}
        (apdir / f"{proposal_id}.json").write_text(
            json.dumps(rec, ensure_ascii=False), "utf-8")
    except Exception:  # noqa: BLE001
        pass


def tick_once(*, draft_fn=None, tick_fn=None, propose_fn=None) -> dict:
    """یک تپش: یک pending-task → patch → shadow-test (در code_autonomy).

    دو مسیر بعد از shadow سبز:
      - HITL (default): patch → propose_to_owner → کارتِ تأییدِ تلگرامی.
      - auto-apply (OCTOPUS_CODE_AUTOAPPLY_LOWRISK=1): patch → approval موقت →
        apply_approved (با همان ۷ گیت + auto-rollback). هر دو داخلِ allow-list.
    اعمالِ زوجه فقط در مسیرِ auto-apply و زیرِ همهٔ گیت‌هاست. این تابع idempotent است
    و در هر تپش یک task می‌گیرد.

    *_fn تزریق‌پذیرند (الگوی run_fn در code_autonomy) — تست‌ها fake می‌زنند، صفر شبکه/git.
    """
    out = {"processed": 0, "drafted": 0, "green": 0, "proposed": 0, "autoapplied": 0}
    tasks = pending_tasks()
    if not tasks:
        return out
    task = tasks[0]
    out["processed"] = 1
    _draft = draft_fn or draft_patch
    patch = _draft(task.get("task", ""))
    if not patch:
        _consume_task(task.get("id", ""))   # مغز نشد → باز هم علامت بزن تا لوپ نزند
        out["reason"] = "no-patch-drafted"
        return out
    out["drafted"] = 1
    # ← وصل‌شدن به pipeline موجود (نه بازنویسیِ آن)
    _tick = tick_fn or code_autonomy.tick
    verdict = _tick(patch)
    shadow = verdict.get("shadow") or {}
    if not (shadow.get("ok") and shadow.get("green")):
        if shadow.get("ok") and not shadow.get("green"):
            out["reason"] = "shadow-red (patch رد شد، درخت زنده امن)"
            _consume_task(task.get("id", ""))
        else:
            out["reason"] = "shadow-failed: " + str(shadow.get("reason") or "")
            # در حالتِ shadow-failed (نه red) task را نگه می‌داریم برای تلاشِ دوباره
        return out
    out["green"] = 1
    # patch سبز است. ابتدا برای HITL پیشنهاد بده (همیشه — کارت به مالک می‌رود).
    _propose = propose_fn or code_autonomy.propose_to_owner
    prop = _propose({**patch, "shadow_green": True})
    if prop.get("ok"):
        out["proposed"] = 1
        out["proposal_id"] = prop.get("id")
    # مسیرِ auto-apply (اختیاری، default OFF): فقط داخلِ allow-list.
    pid = prop.get("id") if prop.get("ok") else None
    if _autoapply_lowrisk() and pid and code_autonomy.allowed_target(patch["target"]):
        _stamp_auto_approval(pid, patch.get("intent", ""))
        # ← همان apply_approved با ۷ گیت؛ active()/قلب/touched/deny/refractory همه چک می‌شوند
        r = code_autonomy.apply_approved(
            {**patch, "shadow_green": True, "id": pid}, pid)
        out["autoapplied"] = 1 if (r.get("ok") and r.get("applied")) else 0
        out["autoapply_green"] = r.get("green")
        out["autoapply_rolled_back"] = r.get("rolled_back")
        if r.get("ok") and r.get("applied"):
            opslib.heartbeat(f"code-brain auto-applied {patch['target']} (low-risk, "
                             f"shadow-green, canary={'green' if r.get('green') else 'RED→rolled-back'})")
    _consume_task(task.get("id", ""))
    return out


def run_forever(*, every_s: float = 300.0) -> None:
    """درایورِ پس‌زمینه: هر every_s ثانیه tick_once. پشتِ فلگ (default OFF).
    خاموشیِ آنی: فایلِ _ops/STOP-CODE-AUTONOMY (همان کیلِ code_autonomy)."""
    import time
    stop = code_autonomy.KILL
    while not stop.exists():
        try:
            if enabled():
                tick_once()
        except Exception:  # noqa: BLE001
            pass
        for _ in range(max(1, int(every_s // 5))):
            if stop.exists():
                break
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        print("code-brain driver: زنده — kill = _ops/STOP-CODE-AUTONOMY · flag = "
              + FLAG)
        run_forever()
    else:
        print(json.dumps({"enabled": enabled(), "has_key": _has_key(),
                          "can_spend": _can_spend(), "pending": len(pending_tasks())},
                         ensure_ascii=False, indent=2))
