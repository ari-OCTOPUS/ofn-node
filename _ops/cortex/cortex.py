#!/usr/bin/env python3
"""cortex.py — مغزِ مرکزیِ کنترل‌گر: پروسهٔ جدا روی 127.0.0.1:8772 (رأی مالک).

هر چرخه (ریتم از قلبِ سایه — «قلب به همهٔ ساختار وصل است»):
  1) sweep: آگاهیِ همهٔ اعضا از state-fileهای خودشان (read-only) → coherence
  2) alignment: مرتب‌سازیِ **کران‌دارِ** نقشهٔ کارِ $0 (رأی مالک: هرگز پول/merge/حذف)
  3) think: یک فکرِ کوتاه با مغزِ محلی ($0) → ژورنالِ append-only (حافظهٔ ماندگار —
     با خاموش/روشن از بین نمی‌رود)
  4) state ماشین‌خوان + HTTP برای کابین/پنل/هر عضو («به همه جا API»)

جدایی: crash بدن روی مغز اثر ندارد و برعکس. STOP-CORTEX = خوابِ مغز؛
STOP-ORGANISM = مغز فقط تماشا می‌کند (هیچ نوشتنِ نقشه). STOP معمار = خروجِ کامل.
bind انحصاریِ 8772 = قفلِ تک‌نمونه (الگوی organism).
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE))
import opslib        # noqa: E402
import registry      # noqa: E402
import model_router  # noqa: E402

PORT = int(os.environ.get("CORTEX_PORT", "8772"))
CORTEX_DIR = opslib.STATE_DIR / "cortex"
STATE_PATH = CORTEX_DIR / "cortex-state.json"
JOURNAL_PATH = CORTEX_DIR / "journal.jsonl"
STOP_CORTEX = opslib.OPS / "STOP-CORTEX"
THINK_EVERY_N = int(os.environ.get("CORTEX_THINK_EVERY_N", "5"))
IMPROVE_EVERY_N = int(os.environ.get("CORTEX_IMPROVE_EVERY_N", "10"))
DEFAULT_PERIOD_S = float(os.environ.get("CORTEX_PERIOD_S", "120"))


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def heart_rhythm_period() -> tuple[float, str]:
    """ریتمِ چرخهٔ مغز از قلبِ سایه: period مغز = clamp(۲×periodِ قلب، ۶۰..۶۰۰).
    قلب تند بتپد مغز هم تندتر جارو می‌کند؛ قلبِ در استراحت = مغزِ آرام."""
    shadow = _read_json(opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json")
    p = shadow.get("period_s")
    if not p:
        return DEFAULT_PERIOD_S, "بدونِ قلب — ریتمِ پیش‌فرض"
    period = max(60.0, min(600.0, 2.0 * float(p)))
    return period, f"×۲ قلبِ سایه ({p}s)"


def align_work_plan(sweep: dict) -> dict:
    """اختیارِ مصوب: مرتب‌سازیِ کران‌دارِ کارِ $0. کران‌ها (تست‌شده):
    فقط templateهای paid=False · فقط ترتیب + every_s در [۰.۵×..۲×]ِ پیش‌فرض ·
    هرگز add/remove/kind-change · نبودِ plan → هیچ. خروجی: گزارشِ diff."""
    if opslib.STOP_ORGANISM.exists():
        return {"changed": False, "reason": "بدن STOP است — مغز فقط تماشا می‌کند"}
    plan_path = opslib.STATE_DIR / "pulse" / "work-plan.json"
    plan = _read_json(plan_path)
    if plan.get("schema") != "work-plan.v1" or not plan.get("templates"):
        return {"changed": False, "reason": "plan غایب — pump هنوز seed نکرده"}
    defaults = {"health": 21600, "gap_report": 43200}
    free = [t for t in plan["templates"] if not t.get("paid")]
    paid = [t for t in plan["templates"] if t.get("paid")]
    stale = set(sweep.get("stale_members") or [])
    coherence = float(sweep.get("coherence", 1.0))
    changed = []
    # قاعدهٔ ۱: coherence پایین → health تندتر (تا کفِ ۰.۵×)؛ بالا → به پیش‌فرض برگرد
    for t in free:
        base = defaults.get(t["kind"], t.get("every_s", 43200))
        target = base * (0.5 if coherence < 0.5 else 1.0)
        target = max(base * 0.5, min(base * 2.0, target))
        if abs(t.get("every_s", base) - target) > 1:
            t["every_s"] = int(target)
            changed.append(f"{t['kind']}.every_s→{int(target)}")
    # قاعدهٔ ۲: عضوِ کهنهٔ مدرسه → gap_report جلوی صف؛ وگرنه health اول
    order = ["gap_report", "health"] if "school" in stale else ["health", "gap_report"]
    free_sorted = sorted(free, key=lambda t: order.index(t["kind"])
                         if t["kind"] in order else 99)
    if [t["kind"] for t in free_sorted] != [t["kind"] for t in free]:
        changed.append("reorder:" + ">".join(t["kind"] for t in free_sorted))
    new_templates = free_sorted + paid          # paid دست‌نخورده، تهِ صف
    if not changed:
        return {"changed": False, "reason": "هم‌راستا بود"}
    plan["templates"] = new_templates
    plan["aligned_by"] = "cortex"
    plan["aligned_ts"] = opslib.now_iso()
    try:
        with opslib.LockedJson(plan_path) as lj:
            lj.write(plan)
    except Exception as e:  # noqa: BLE001
        return {"changed": False, "reason": f"write-failed: {e}"}
    return {"changed": True, "diff": changed}


def think(sweep: dict, cycle: int) -> str:
    """فکرِ کوتاهِ ژورنال‌شده — مغزِ محلی اگر بالا بود؛ وگرنه خلاصهٔ قطعی.
    فقط عددها و idها به مدل می‌رود — هیچ secret/PII."""
    summary = (f"coherence={sweep['coherence']} · "
               f"stale={','.join(sweep['stale_members']) or 'هیچ'} · "
               f"اعضا={sweep['n']}")
    r = model_router.ask(
        "think",
        f"وضعیتِ مجموعه: {summary}. یک جملهٔ کوتاه: الان مهم‌ترین کارِ مجموعه چیست؟",
        max_tokens=90)
    if r.get("ok"):
        return f"[{r.get('tier')}] {r['text']}"
    return f"[det] {summary}"


def self_improve(cycle: int) -> dict | None:
    """هر IMPROVE_EVERY_N چرخه: حلقهٔ خودارتقایی — ممیزیِ خود + پیشنهادهای دسته‌بندی‌شده.
    propose-only (رأی مالک/قانون)؛ $0؛ fail-soft. خروجی برای state/کابین."""
    try:
        import improve
        d = improve.run(write=True)
        return {"maturity_pct": d.get("maturity_pct"),
                "n_proposals": d.get("n_proposals"),
                "top": [t.get("title") for t in (d.get("top") or [])[:3]]}
    except Exception as e:  # noqa: BLE001 — خودارتقا نباید مغز را بکشد
        opslib.alert([f"cortex self_improve error: {type(e).__name__}: {e}"])
        return None


def self_model_refresh(cycle: int) -> dict | None:
    """هر IMPROVE_EVERY_N چرخه (لایهٔ فراشناختی جلسه ۴۶): نقشهٔ سورسِ خود را تازه کن —
    «کدِ خودش رو بخونه و درک کنه». $0، read-only، fail-soft."""
    try:
        import self_model
        return self_model.run_and_persist()
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex self_model error: {type(e).__name__}: {e}"])
        return None


def part_loops_run(cycle: int) -> dict | None:
    """لوپِ یادگیری+خود-تغییرِ هر بخش (جلسه ۴۶، «برای هر بخش لوپ طرح کن»).
    هر بخش observe→learn→propose؛ propose-only. $0، fail-soft."""
    try:
        import part_loops
        d = part_loops.run_all(beat=cycle)
        bad = [p["name"] for p in d.get("parts", []) if p["status"] in ("🔴", "🟡")]
        return {"n_parts": len(d.get("parts", [])),
                "n_proposals": d.get("n_proposals", 0), "attention": bad[:5]}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex part_loops error: {type(e).__name__}: {e}"])
        return None


def business_brain_run(cycle: int) -> dict | None:
    """مغزِ دومِ عملیاتِ کسب‌وکار (جلسه ۴۶): Lead-نقاشی + Project-F لوپِ درآمدیِ خودشان.
    propose-only؛ Project-F content-free. $0، fail-soft."""
    try:
        import business_brain
        d = business_brain.run_all(beat=cycle)
        return {"n_projects": len(d.get("projects", [])),
                "n_proposals": d.get("n_proposals", 0)}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex business_brain error: {type(e).__name__}: {e}"])
        return None


def stress_tick(cycle: int) -> dict | None:
    """هومئوستاتِ استرس/ترس هر چرخه (رأی مالک): علائمِ حیاتیِ زیرسیستم‌ها.
    ترس → auto_approve.self_test مکث می‌کند (fail-closed). $0، fail-soft."""
    try:
        import stress
        a = stress.persist()
        return {"level": a["level"], "organism_stress": a["organism_stress"],
                "in_fear": a["in_fear"]}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex stress error: {type(e).__name__}: {e}"])
        return None


def run_cycle(cycle: int) -> dict:
    sweep = registry.sweep()
    alignment = align_work_plan(sweep)
    stress_summary = stress_tick(cycle)
    thought = think(sweep, cycle) if (cycle % THINK_EVERY_N == 0) else None
    model_summary = (self_model_refresh(cycle)
                     if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    parts_summary = (part_loops_run(cycle)
                     if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    business_summary = (business_brain_run(cycle)
                        if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    improve_summary = (self_improve(cycle)
                       if (IMPROVE_EVERY_N > 0 and cycle % IMPROVE_EVERY_N == 0) else None)
    period, rhythm_src = heart_rhythm_period()
    state = {
        "ts": opslib.now_iso(), "cycle": cycle,
        "coherence": sweep["coherence"],
        "stale_members": sweep["stale_members"],
        "members": sweep["members"],
        "alignment": alignment,
        "rhythm": {"period_s": period, "source": rhythm_src},
        "brains": {"keys": model_router.keys_present(),
                   "paid_gate": model_router.paid_gate()[1],
                   "local_model": os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")},
        **({"thought": thought} if thought else {}),
        **({"self_improve": improve_summary} if improve_summary else {}),
        **({"self_model": model_summary} if model_summary else {}),
        **({"part_loops": parts_summary} if parts_summary else {}),
        **({"business_brain": business_summary} if business_summary else {}),
        **({"stress": stress_summary} if stress_summary else {}),
        "schema": "cortex-state.v1",
    }
    CORTEX_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with opslib.LockedJson(STATE_PATH) as lj:
            lj.write(state)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex state write failed: {e}"])
    rec = {"ts": state["ts"], "cycle": cycle,
           "coherence": sweep["coherence"],
           "aligned": alignment.get("changed", False),
           **({"diff": alignment.get("diff")} if alignment.get("changed") else {}),
           **({"thought": thought} if thought else {})}
    try:
        opslib.append_jsonl(JOURNAL_PATH, rec)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"cortex journal failed: {e}"])
    return state


class _Srv(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/cortex":
            self._send(200, STATE_PATH.read_bytes() if STATE_PATH.exists() else b"{}")
            return
        if self.path.startswith("/api/journal"):
            lines = []
            try:
                if JOURNAL_PATH.exists():
                    lines = JOURNAL_PATH.read_text("utf-8").splitlines()[-20:]
            except OSError:
                pass
            self._send(200, ("[" + ",".join(lines) + "]").encode("utf-8"))
            return
        if self.path == "/":
            st = _read_json(STATE_PATH)
            html = ("<!doctype html><html dir='rtl' lang='fa'><meta charset='utf-8'>"
                    "<title>Cortex</title><body style='font-family:Tahoma;padding:2em'>"
                    "<h2>🧠 مغزِ مرکزی</h2>"
                    f"<pre style='direction:ltr;text-align:left'>"
                    f"{json.dumps(st, ensure_ascii=False, indent=2)}</pre>"
                    "<p>API: /api/cortex · /api/journal · POST /ask</p></body></html>")
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        self._send(404, b"{}")

    def do_POST(self):  # noqa: N802
        if self.path != "/ask":
            self._send(404, b"{}")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            task = str(body.get("task", "daily"))[:40]
            prompt = str(body.get("prompt", ""))[:4000]
            out = model_router.ask(task, prompt,
                                   max_tokens=int(body.get("max_tokens", 300)))
            self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"))
        except Exception as e:  # noqa: BLE001
            self._send(500, json.dumps({"ok": False, "reason": str(e)},
                                       ensure_ascii=False).encode("utf-8"))

    def log_message(self, *a):
        pass


def main() -> int:
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    try:
        srv = _Srv(("127.0.0.1", PORT), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except OSError:
        print(f"cortex: نمونهٔ دیگری روی {PORT} زنده است — خروجِ تمیز.")
        return 0
    print(f"cortex: زنده روی http://127.0.0.1:{PORT} — kill تمیز: فایل _ops/STOP-CORTEX")
    opslib.heartbeat(f"cortex=START port={PORT}")
    cycle = 0
    while True:
        if STOP_CORTEX.exists() or opslib.halted() == "STOP(architect)":
            opslib.heartbeat("cortex=HALT (STOP) — خروجِ تمیز")
            return 0
        cycle += 1
        try:
            run_cycle(cycle)
        except Exception as e:  # noqa: BLE001 — خطای خاموش ممنوع، مرگِ حلقه هم ممنوع
            opslib.alert([f"cortex cycle error: {type(e).__name__}: {e}"])
        period, _ = heart_rhythm_period()
        time.sleep(period)


if __name__ == "__main__":
    sys.exit(main())
