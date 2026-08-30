"""DA-5 جزء ۱ — شناسنامهٔ پنج‌پروسه‌ای ارگانیسم (organism manifest، قدم صفر).

فقط-خواندن. هیچ enforce/فلگ/خرید/تغییر رفتاری. خروجی:
_ops/audit/organism-manifest.json — هر فکت با observed_at.

چرا: trust-boundary.json فعلی ۱۴ فایلِ observe-onlyِ مغز 4d را هش می‌کند؛
پنج/شش پروسهٔ زندهٔ _ops که واقعاً اثر می‌سازند (send/pay/write) بیرونش‌اند.
این اسکریپت ادعا را با وضعیت واقعی پروسه‌ها می‌سنجد (self-identification =
سنجش ادعا در برابر واقعیت، نه صدور خودگواهی).

فیلدها (DA-5): pid · port · entry_files+sha256 · effective_flags (last-wins) ·
scheduled_tasks · effect_paths (اعلانی) · drift.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent   # F:/backup
OPS = VAULT / "_ops"
OUT = OPS / "audit" / "organism-manifest.json"

# نقش‌های ادعاشده (STATE §1) — drift همین‌ها را با مشاهده می‌سنجد
DECLARED_MEMBERS = ["organism", "center", "gateway", "live", "cortex"]

# مسیرهای اثرِ هر عضو — اعلانی (اعلام ≙ واقعیت نیست؛ مکانیزه‌شدنش در DA-4 PEP)
EFFECT_PATHS = {
    "organism": ["write:state", "send:telegram(via center)", "pay:no"],
    "center":   ["send:telegram(direct)", "write:tg-state", "pay:no"],
    "gateway":  ["http:local(8774)", "write:no", "pay:no"],
    "live":     ["http:local(8773)", "write:no", "pay:no"],
    "cortex":   ["write:outputs", "llm:paid(via router)", "pay:budget-capped"],
    "unknown":  ["UNDECLARED — must fail admission in future manifest"],
}


def _run(cmd: list[str], timeout=60) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return r.stdout or ""
    except Exception:  # noqa: BLE001
        return ""


def _sha256(p: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(65536), b""):
                h.update(c)
        return h.hexdigest()
    except OSError:
        return None


def _processes() -> list[dict]:
    """python.exe زنده‌ها با CommandLine از CIM (فقط-خواندن)."""
    out = _run(["powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                "Select-Object ProcessId,CreationDate,CommandLine | "
                "ConvertTo-Json -Compress"])
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        procs = []
        for p in data or []:
            procs.append({
                "pid": p.get("ProcessId"),
                "started": str(p.get("CreationDate") or "")[:19],
                "cmdline": str(p.get("CommandLine") or "")[:300],
            })
        return procs
    except (ValueError, TypeError):
        return []


def _ports() -> dict[int, list[int]]:
    """pid → listening ports از netstat (فقط-خواندن)."""
    out = _run(["netstat", "-ano", "-p", "TCP"])
    m: dict[int, list[int]] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[3] == "LISTENING":
            try:
                port = int(parts[1].rsplit(":", 1)[1])
                pid = int(parts[4])
                m.setdefault(pid, []).append(port)
            except (ValueError, IndexError):
                continue
    return m


def _role_of(cmdline: str) -> str:
    """نقش از محتوای cmdline — خاص‌ترها اول (مسیرِ gateway شامل
    «telegram_center» است؛ ترتیب تطبیق مهم)."""
    c = (cmdline or "").lower().replace("\\", "/")
    for token, role in (("gateway", "gateway"), ("organism.py", "organism"),
                        ("cortex", "cortex"), ("live/server", "live"),
                        ("live.py", "live"), ("telegram_center", "center"),
                        ("doctor", "doctor(aux)"), ("observatory", "observatory")):
        if token in c:
            return role
    for member in DECLARED_MEMBERS:
        if member in c:
            return member
    return "unknown"


def _entry_file(cmdline: str) -> str | None:
    """فایل ورودی .py از cmdline — مطلق یا نسبی (نسبی نسبت به vault/OPS حل می‌شود)."""
    tokens = re.findall(r'([A-Za-z]:\\[^\s"\']+\.py|[^\s"\']+\.py)', cmdline or "")
    for t in tokens:
        p = Path(t)
        if p.is_absolute() and p.exists():
            return str(p)
        for base in (VAULT, OPS, VAULT / "4d_system"):
            cand = base / t
            if cand.exists():
                return str(cand)
    return tokens[0] if tokens else None


def _effective_flags_last_wins() -> dict[str, str]:
    """بازپارسِ flags.cmd با قاعدهٔ «آخرین تعریف برنده» (همان موتور flag_drift)."""
    sys.path.insert(0, str(OPS))
    try:
        import flag_drift
        flags, _ = flag_drift.parse_flags_file(OPS / "OCTOPUS-flags.cmd")
        return dict(flags)
    except Exception as e:  # noqa: BLE001
        return {"_error": f"{type(e).__name__}: {e}"}


def main() -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    procs = _processes()
    ports = _ports()
    flags = _effective_flags_last_wins()

    members = []
    for p in procs:
        role = _role_of(p["cmdline"])
        entry = _entry_file(p["cmdline"])
        members.append({
            "role": role,
            "pid": p["pid"],
            "started": p["started"],
            "ports_listening": sorted(ports.get(p["pid"], [])),
            "entry_file": entry,
            "entry_sha256": _sha256(Path(entry)) if entry else None,
            "effect_paths": EFFECT_PATHS.get(role, EFFECT_PATHS["unknown"]),
            "cmdline": p["cmdline"],
        })

    tasks = _run(["powershell", "-NoProfile", "-Command",
                  "Get-ScheduledTask -TaskName '*Observator*','*OCTOPUS*' -ErrorAction "
                  "SilentlyContinue | ForEach-Object { $_.TaskName + '=' + $_.State }"])

    observed_roles = {m["role"] for m in members}
    manifest = {
        "schema": "octopus-organism-manifest/0",
        "observed_at": now,
        "declared_members": DECLARED_MEMBERS,
        "members_observed": members,
        "flags_effective_last_wins": flags,
        "flags_count": len(flags),
        "scheduled_tasks": [t for t in tasks.splitlines() if t.strip()],
        "drift": {
            "declared_not_observed": [r for r in DECLARED_MEMBERS
                                      if r not in observed_roles],
            "observed_not_declared": sorted(
                r for r in observed_roles - set(DECLARED_MEMBERS) if r != "unknown"),
            "unknown_cmdline_members": sum(1 for m in members if m["role"] == "unknown"),
            "note": "ادعا در برابر مشاهده — هر مقدار نونال = شکافِ شناسنامه",
        },
        "next_steps_with_owner_vote": [
            "امضای این manifest (همان کلید Ed25519) بعد از تصویب دامنه",
            "وصل drift به AEB (generate_aeb.py)",
            "تبدیل effect_paths اعلانی به قرارداد ۱۵-فیلدی DA-4",
        ],
        "read_only": True,
    }
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"نوشته شد: {OUT.name}")
    print(f"اعضای مشاهده‌شده: {len(members)} (ادعاشده: {len(DECLARED_MEMBERS)})")
    for m in members:
        print(f"  {m['role']:13} pid={m['pid']} ports={m['ports_listening']} "
              f"entry={'✓' if m['entry_sha256'] else '✗'}")
    d = manifest["drift"]
    print(f"drift: missing={d['declared_not_observed']} "
          f"extra={d['observed_not_declared']} unknown={d['unknown_cmdline_members']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
