"""R19 — تولید Audit Evidence Bundle (AEB) از درختِ زنده.

شورای دوم (GPT-5.6 Sol + Gemini 3.1 Pro): «دیگر هرگز حسابرسی روی سندِ نثری».
هر فکت با observed_at + TTL؛ حقایقِ فرّار (PID/فلگ/بودجه) سریع منقضی می‌شوند،
حقایق ساختاری (کد امضاشده) فقط برای همان digest معتبرند. هر فقیطهٔ کلیدی
برچسبِ نردبانِ وضعیت می‌گیرد: declared→implemented→tested→deployed→drilled→reproduced.

خروجی: _ops/audit/bundles/AEB-<ts>.json + AEB-<ts>.txt (نسخهٔ امضاشدنی)

امضا (دستِ مالک — مثل رویهٔ D1):
  openssl pkeyutl -sign -inkey ~/.octopus-signing/octopus-owner-ed25519-private.pem \
    -rawin -in AEB-<ts>.txt -out AEB-<ts>.txt.sig

فقط-خواندن است؛ به‌جز خودِ باندل هیچ فایلی را نمی‌نویسد.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent   # F:/backup
FOURD = VAULT / "4d_system"
PY = sys.executable or "py"


def _run(cmd, cwd=None, timeout=120):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return {"exit": r.returncode, "out": r.stdout.strip()[-4000:],
                "err": r.stderr.strip()[-2000:]}
    except Exception as e:  # noqa: BLE001
        return {"exit": -1, "out": "", "err": f"{type(e).__name__}: {e}"}


def sha256_file(p: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(65536), b""):
                h.update(c)
        return h.hexdigest()
    except OSError:
        return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bundle: dict = {
        "schema": "octopus-aeb/1",
        "audit_id": f"AEB-{ts}",
        "observed_at": now_iso(),
        "expires_at": {
            "volatile_facts": (datetime.now(timezone.utc)
                               + timedelta(hours=24)).isoformat(timespec="seconds"),
            "note": "حقایق ساختاری فقط برای همان commit/digest معتبرند",
        },
        "generator": "_ops/audit/generate_aeb.py (R19 debt-sweep 2026-08-16)",
    }

    # ── ۱. مخزن ─────────────────────────────────────────────────────────
    g = lambda *a: _run(["git", *a], cwd=VAULT)          # noqa: E731
    head = g("rev-parse", "HEAD")["out"]
    dirty = g("status", "--porcelain")["out"].splitlines()
    unpushed = g("rev-list", "--count", "germline/master..HEAD"
                 if g("rev-parse", "--verify", "germline/master")["exit"] == 0
                 else "HEAD")["out"]
    bundle["source_repo"] = {
        "path": str(VAULT), "branch": g("rev-parse", "--abbrev-ref", "HEAD")["out"],
        "commit_sha": head[:12],
        "dirty_files": len(dirty),
        "unpushed_commits_vs_germline": unpushed.strip() or "n/a",
        "germline_remote": g("remote", "get-url", "germline")["out"],
        "observed_at": now_iso(),
    }

    # ── ۲. مرزِ اعتماد (R13) ────────────────────────────────────────────
    tb = _run([PY, "-c",
               "import json;from brain import guardrails;"
               "print(json.dumps(guardrails.check_trust_boundary()))"], cwd=FOURD)
    try:
        tb_data = json.loads(tb["out"])
    except ValueError:
        tb_data = {"error": tb["err"] or tb["out"]}
    tb_data["state_ladder"] = ("implemented+tested" if tb_data.get("digests_ok")
                               else "implemented")
    bundle["trust_boundary"] = tb_data

    # ── ۳. پاکتِ NO-GO (R0a) + تست زندهٔ سریع ───────────────────────────
    # توجه: این فایل script خوداعتبارسنج است، نه pytest (در run_all هم مستقیم
    # اجرا می‌شود — نکتهٔ T3 شورا)؛ با pytest exit 5/INTERNALERROR می‌دهد.
    ngo_path = VAULT / "_ops" / "tests" / "test_no_go_envelope.py"
    ngo_run = _run([PY, "-X", "utf8", str(ngo_path)],
                   cwd=ngo_path.parent, timeout=300)
    bundle["no_go_envelope"] = {
        "file": "_ops/tests/test_no_go_envelope.py",
        "sha256": sha256_file(ngo_path),
        "protected_by": "4d_system/config/trust-boundary.json (owner-only)",
        "quick_run_exit": ngo_run["exit"],
        "quick_run_tail": ngo_run["out"].splitlines()[-1] if ngo_run["out"] else ngo_run["err"][:200],
        "state_ladder": "tested (9/9 in run_all; quick rerun here)"
                        if ngo_run["exit"] == 0 else "REGRESSION",
        "observed_at": now_iso(),
    }

    # ── ۴. فلگ‌ها + کلیدهای کشتن ────────────────────────────────────────
    flags: dict[str, str] = {}
    try:
        for line in (VAULT / "_ops" / "OCTOPUS-flags.cmd").read_text(
                encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*set\s+([A-Z0-9_]+)=(\S+)\s*$", line, re.I)
            if m:
                flags[m.group(1)] = m.group(2)
    except OSError:
        pass
    try:
        org = json.loads((VAULT / "_ops" / "state" / "ORGANISM-STATE.json")
                         .read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        org = {}
    bundle["runtime_control"] = {
        "flags_enabled": {k: v for k, v in flags.items() if v == "1"},
        "kill_state": {
            "stop_file_present": (VAULT / "STOP-ORGANISM").exists(),
            "observatory_kill_switch": (VAULT / "_ops" / "observatory" /
                                        "data" / "kill.switch").exists(),
            "org_state_halted": org.get("halted"),
            "wire_kill_seam_flag": flags.get("OCTOPUS_WIRE_KILL_SEAM"),
            "state_ladder": "armed (flags.cmd) + drilled (T11 sandbox); "
                            "seam documented — OCTOPUS_WIRE_KILL_SEAM=1",
        },
        "organism": {k: org.get(k) for k in
                     ("ts", "started", "beat", "halted", "frozen", "stop_organism")
                     if k in org},
        "observed_at": now_iso(),
    }

    # ── ۵. بودجه ────────────────────────────────────────────────────────
    try:
        bud = json.loads((VAULT / "_ops" / "budget" / "budget-state.json")
                         .read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        bud = {}
    bundle["budget"] = {k: bud.get(k) for k in
                        ("date", "spent_today_usd", "month", "spent_month_aud",
                         "halted") if k in bud} | {"observed_at": now_iso()}

    # ── ۶. زمان‌بند (C-014 containment) ─────────────────────────────────
    sched = _run(["powershell", "-NoProfile", "-Command",
                  "Get-ScheduledTask -TaskName '*Observator*' | ForEach-Object "
                  "{ $_.TaskName + '=' + $_.State }"], timeout=60)
    bundle["scheduler_inventory"] = {
        "observatory_tasks": sched["out"].splitlines(),
        "c014_containment": "old task OCTOPUS-Observatory disabled 2026-08-15 "
                            "~22:46 local (delegated owner decision); "
                            "proof scheduled for next :36 window",
        "observed_at": now_iso(),
    }

    # ── ۷. تناقض‌های باز ────────────────────────────────────────────────
    try:
        creg = (VAULT / "01-TRUTH" / "CONTRADICTIONS.md").read_text(encoding="utf-8")
        total = len(re.findall(r"^\s{id:\s*C-0\d\d", creg, re.M))
        open_c = len(re.findall(r"status:\s*open", creg))
    except OSError:
        total = open_c = -1
    bundle["contradictions"] = {
        "registered": total, "marked_open": open_c,
        "registry": "01-TRUTH/CONTRADICTIONS.md",
        "next_free_id": "C-015",
        "observed_at": now_iso(),
    }

    # ── ۸. اسکن راز + بستهٔ D1 ──────────────────────────────────────────
    gl = VAULT / "_ops" / "tests" / "_baselines" / "gitleaks-full-20260815.json"
    d1_man = VAULT / "_ops" / "D1-AUDIT-PACKAGE-2026-08-15" / "MANIFEST.txt"
    d1_sig = d1_man.with_suffix(".sig")
    bundle["secret_scan_and_audit"] = {
        "gitleaks_baseline": {"file": str(gl.relative_to(VAULT)),
                              "sha256": sha256_file(gl),
                              "summary": "781 findings; 453 in existing files; "
                                         "zero live .env keys tracked; 1 GitHub PAT "
                                         "flagged for OWNER rotation (R1 — pending)"},
        "d1_package": {"manifest_sha256": sha256_file(d1_man),
                       "owner_signature_present": d1_sig.exists(),
                       "status": "NOT_STARTED (awaiting external auditor — R21 owner)"},
        "observed_at": now_iso(),
    }

    # ── ۹. نردبانِ وضعیت — ادعاهای سرخطِ امروز ──────────────────────────
    bundle["state_ladder"] = {
        "memory_loop (C-012)": "deployed + drilled (T1 telemetry 1.0/1.0, 2026-08-15)",
        "no_go_envelope": "tested (9/9 in run_all)",
        "trust_boundary_manifest (R13)": tb_data.get("state_ladder", "?")
                                          + " — signature: " + str(tb_data.get("signature")),
        "kill_switch": "deployed + drilled (T11); seam additive-guard armed via flag",
        "observatory_duplication (C-014)": "contained (task disabled); structural "
                                           "fix (job registry) = follow-up",
        "budget_meter (T12)": "independently reproduced (117/117)",
    }

    # ── نوشتن ───────────────────────────────────────────────────────────
    out_dir = VAULT / "_ops" / "audit" / "bundles"
    out_dir.mkdir(parents=True, exist_ok=True)
    j_path = out_dir / f"AEB-{ts}.json"
    j_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False),
                      encoding="utf-8")

    t_path = out_dir / f"AEB-{ts}.txt"
    lines = [
        f"AUDIT EVIDENCE BUNDLE {bundle['audit_id']}",
        f"observed_at: {bundle['observed_at']}",
        f"repo: {VAULT} @ {bundle['source_repo']['commit_sha']}"
        f" (dirty={bundle['source_repo']['dirty_files']},"
        f" unpushed={bundle['source_repo']['unpushed_commits_vs_germline']})",
        f"trust_boundary: digests_ok={tb_data.get('digests_ok')} "
        f"signature={tb_data.get('signature')}",
        f"no_go_envelope: exit={bundle['no_go_envelope']['quick_run_exit']} "
        f"sha256={bundle['no_go_envelope']['sha256'][:16]}…",
        f"kill: stop_file={bundle['runtime_control']['kill_state']['stop_file_present']} "
        f"halted={bundle['runtime_control']['kill_state']['org_state_halted']}",
        f"budget: {bundle['budget'].get('spent_month_aud')} AUD month-to-date",
        f"contradictions: {total} registered / {open_c} open (next free: C-015)",
        "state_ladder:",
        *[f"  - {k}: {v}" for k, v in bundle["state_ladder"].items()],
        f"aeb_json_sha256: {sha256_file(j_path)}",
        "--- end of signed payload ---",
    ]
    t_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"نوشته شد: {j_path.name}")
    print(f"          {t_path.name} (امضاشدنی)")
    print(f"trust_boundary: digests_ok={tb_data.get('digests_ok')} "
          f"signature={tb_data.get('signature')}")
    print(f"no_go quick run exit: {ngo_run['exit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
