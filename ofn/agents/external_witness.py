"""external_witness — شاهد دوم: سنجهٔ حیاتی از بیرونِ مرز خود (SPEC §2).

ریشهٔ درد ۲۰۲۶-۰۹-۰۲: سیستم دربارهٔ خودش گزارش می‌داد و همان را باور می‌کرد
(self-model سبز، سندِ قفل عددِ نخوانده، گیت سبزِ بی‌رأی). این ماژول برای هر
ادعای حیاتی دو منبع می‌خواند و **اختلاف خودش خروجی است** — هرگز حل نمی‌کند؛
حل اختلاف تصمیم است و تصمیم مال مالک است.

سه سطح شاهد (جایگزین برچسب‌های موقت REPORTED/UNVERIFIED):
  WITNESS_A  بیرون‌شاهد مستقل (ماشین دوم، GitHub API، رسید بانک/SMTP)
  WITNESS_B  فرمان تکرارپذیر ثبت شد ولی روی همین ماشین اجرا شد
  WITNESS_C  فقط ادعای داخلی

هیچ سندی نباید «VERIFIED» را بدون سطح شاهد بنویسد — WAL الان WITNESS_A است
(خوانش روی board-182). لجر: STATE_DIR/legs/claims-ledger.jsonl — فقط append،
هر خط line_sha256 (الگوی ofn/doctor/receipts، بازاستفاده از canonical_json).

دو تشخیص:
  STALE_CLAIM  ادعای ثبت‌شده بیش از N روز بازاندازه‌گیری نشده (F-09)
  SILENT_FLIP  مقدار عوض شده ولی هیچ ruling_idای برایش نیست — مهم‌ترین
               آلارم سیستم: یعنی یک مسیر نوشتنِ ناشناخته وجود دارد

ممنوع: هر نوشتن به غیر از لجر خودش · هر ارسال (این ماژول هیچ مسیر
شبکه‌ای جز GETِ فقط-خواندن GitHub ندارد) · بازنویسی لجر یا اسناد.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parents[1]))
import opslib  # noqa: E402

SCHEMA = "octopus.external-witness.v1"
LEDGER = opslib.STATE_DIR / "legs" / "claims-ledger.jsonl"
FLAG_CLAIMS = _HERE.parents[1] / "docs" / "runbooks" / "FLAG-CLAIMS.json"

GITHUB_API = "https://api.github.com/repos/ari-OCTOPUS/ofn-node/commits/main"

# کادنس بازاندازه‌گیری (روز) — بیشتر از این = STALE_CLAIM
REMEASURE_CADENCE_DAYS = 7


from enum import Enum  # noqa: E402


class WitnessLevel(str, Enum):
    WITNESS_A = "WITNESS_A"
    WITNESS_B = "WITNESS_B"
    WITNESS_C = "WITNESS_C"


# ── لجر: append-only با line_sha256 ─────────────────────────────────────────

def canonical_json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def append_claim(claim: dict, ledger: Path | None = None) -> dict:
    """فقط append. هر خط شامل line_sha256 روی فرم کانونی است."""
    line = dict(claim)
    line.setdefault("recorded_at", opslib.now_iso())
    body = canonical_json(line)
    line["line_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    p = ledger or LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:  # تنها نوشتنِ مجاز این ماژول
        fh.write(canonical_json(line) + "\n")
    return line


def read_ledger(ledger: Path | None = None) -> list[dict]:
    p = ledger or LEDGER
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        out.append(json.loads(ln))
    return out


def verify_ledger(ledger: Path | None = None) -> list[str]:
    """بازمحاسبهٔ line_sha256 هر خط؛ خروجی = فهرست خطوط دست‌کاری‌شده."""
    p = ledger or LEDGER
    bad = []
    for i, ln in enumerate(read_ledger(p)):
        rec = dict(ln)
        got = rec.pop("line_sha256", None)
        if got != hashlib.sha256(
                canonical_json(rec).encode("utf-8")).hexdigest():
            bad.append(str(i))
    return bad


# ── درایورهای بیرون‌شاهد (تنها شبکهٔ مجاز: GET فقط-خواندن) ──────────────────

def fetch_github_main_sha(timeout: int = 15) -> tuple[str | None, str]:
    """GitHub API عمومی. خطا = ('', دلیل) — UNKNOWN، نه حدس."""
    req = urllib.request.Request(
        GITHUB_API, headers={"Accept": "application/vnd.github+json",
                             "User-Agent": "octopus-external-witness"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            sha = json.loads(r.read().decode("utf-8")).get("sha")
            return sha, "github-api"
    except Exception as e:  # noqa: BLE001
        return None, f"err:{type(e).__name__}"


def read_local_git_head(git_dir: Path) -> tuple[str | None, str]:
    """git rev-parse روی دیسک (درون‌شاهد، ولی زمینِ متفاوت از API)."""
    import subprocess
    try:
        p = subprocess.run(
            ["git", "-C", str(git_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15)
        if p.returncode != 0:
            return None, f"rc={p.returncode}"
        return p.stdout.strip(), "git-rev-parse"
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"err:{type(e).__name__}"


# ── cross-check های شش‌ادعایی (جدول §2.2) ──────────────────────────────────

def default_repo_dir() -> Path:
    """مسیر مخزن در هر دو چیدمان (دیباگ 2026-09-04):
    لپ‌تاپ F:\\ofn-node\\ofn\\agents → parents[2]/ofn-node ·
    بورد ~/ofn/ofn/agents → parents[1]. اولویت: env OFN_REPO_ROOT،
    سپس نخستین نامزدی که .git دارد (فایلِ worktree یا پوشه)."""
    import os
    env = os.environ.get("OFN_REPO_ROOT")
    cands = ([Path(env)] if env else []) + [
        _HERE.parents[2] / "ofn-node",   # لپ‌تاپ
        _HERE.parents[1],                # بورد
    ]
    for c in cands:
        if (c / ".git").exists():
            return c
    return cands[-1]


def check_main_head(git_dir: Path | None = None) -> dict:
    """ادعا: main HEAD — درون: git محلی · بیرون: GitHub API."""
    g = git_dir or default_repo_dir()
    local, src_l = read_local_git_head(g)
    remote, src_r = fetch_github_main_sha()
    claim = {"claim": "main_head", "local": local, "remote": remote}
    if local is None or remote is None:
        claim.update(verdict="UNKNOWN", detail=f"{src_l} / {src_r}")
    elif local == remote:
        claim.update(verdict="MATCH", witness=WitnessLevel.WITNESS_A.value)
    else:
        claim.update(verdict="DIVERGED",
                     detail=f"local={str(local)[:8]} remote={str(remote)[:8]}",
                     witness=WitnessLevel.WITNESS_A.value)
    return claim


def check_flag_claims(now: float | None = None) -> list[dict]:
    """FLAG-CLAIMS.json در برابر واقعیتِ خواندنی از همین درخت.

    سند غلط است، نه فایل — اختلاف فقط ثبت می‌شود."""
    if not FLAG_CLAIMS.exists():
        return [{"claim": "flag_claims", "verdict": "UNPROBED",
                 "detail": "registry absent on this host"}]
    import datetime as dt
    now = now if now is not None else dt.datetime.now(dt.timezone.utc).timestamp()
    out = []
    data = json.loads(FLAG_CLAIMS.read_text(encoding="utf-8"))
    for c in data.get("claims", []):
        entry = {"claim": f"flag:{c['name']}", "documented": c.get("value"),
                 "measured_at": c.get("measured_at"),
                 "command": c.get("command")}
        ts = c.get("measured_at", "")
        try:
            age_days = (now - dt.datetime.strptime(
                ts, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=dt.timezone.utc).timestamp()) / 86400
            entry["age_days"] = round(age_days, 1)
            if age_days > REMEASURE_CADENCE_DAYS:
                entry["verdict"] = "STALE_CLAIM"
        except ValueError:
            entry["verdict"] = "UNKNOWN"
            entry["detail"] = "unparseable measured_at"
        out.append(entry)
    return out


def detect_silent_flip(ledger: Path | None = None) -> list[dict]:
    """تغییر مقدارِ claim بدون ruling_id در خط جدید = مسیر نوشتن ناشناخته."""
    flips = []
    last: dict[str, dict] = {}
    for rec in read_ledger(ledger):
        name = rec.get("claim")
        if not isinstance(name, str):
            continue
        if name in last:
            if last[name].get("value") != rec.get("value") \
                    and not rec.get("ruling_id"):
                flips.append({
                    "claim": name,
                    "from": last[name].get("value"),
                    "to": rec.get("value"),
                    "recorded_at": rec.get("recorded_at"),
                    "verdict": "SILENT_FLIP",
                })
        last[name] = rec
    return flips


# ── اجرا ────────────────────────────────────────────────────────────────────

def run(ledger: Path | None = None, now: float | None = None) -> dict:
    checks = [check_main_head()] + check_flag_claims(now)
    flips = detect_silent_flip(ledger)
    report = {
        "schema": SCHEMA,
        "generated_at": opslib.now_iso(),
        "checks": checks,
        "silent_flips": flips,
        "tampered_ledger_lines": verify_ledger(ledger),
        "banner": (
            f"{sum(1 for c in checks if c.get('verdict') == 'MATCH')} match · "
            f"{sum(1 for c in checks if c.get('verdict') not in ('MATCH',))} "
            "attention — conflicts are recorded, never resolved"),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    report = run()
    print(json.dumps(report, ensure_ascii=False))
    # ثبت ادعاهای این دور در لجر (فقط append) — مگر اینکه --no-ledger آمده باشد
    if not (argv and "--no-ledger" in argv):
        for c in report["checks"]:
            append_claim({
                "claim": c.get("claim"),
                "value": c.get("local") or c.get("documented"),
                "verdict": c.get("verdict"),
                "witness": c.get("witness", WitnessLevel.WITNESS_C.value),
            })
    return 0


if __name__ == "__main__":
    sys.exit(main())
