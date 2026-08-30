"""تولید/تازه‌سازیِ manifest مرزِ اعتماد (R13/C-013 — شورای دوم).

خروجی: config/trust-boundary.json — digest هر فایل TCB (CODE_TCB_FILES) +
digest پاکتِ NO-GO (R0a: تستِ ۹گانه نباید توسط ایجنت/سامانه بازنویس‌پذیر باشد).

پس از هر تغییرِ مجازِ TCB (با رأی مالک) این اسکریپت را دوباره اجرا کن و
manifest را به امضای مالک بده:

    cd 4d_system && py scripts/generate_trust_boundary.py
    # امضا (دستِ مالک یا ایجنتِ صریحاً تفویض‌شده، مثل رویهٔ D1):
    openssl pkeyutl -sign -inkey ~/.octopus-signing/octopus-owner-ed25519-private.pem \
        -rawin -in config/trust-boundary.json \
        -out config/trust-boundary.json.sig

وریفای عمومی (بدون کلید خصوصی):
    openssl pkeyutl -verify -pubin \
        -inkey ../_ops/owner-signing/octopus-owner-ed25519-public.pem \
        -rawin -in config/trust-boundary.json -sigfile config/trust-boundary.json.sig

فعال‌سازیِ اجرا (بعد از امضا، با رأی مالک): OCTOPUS_TCB_MANIFEST_ENFORCE=1
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SYSTEM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SYSTEM_ROOT))

from brain.guardrails import CODE_TCB_FILES, CODE_TCB_DIR_NAMES  # noqa: E402

SCHEMA = "octopus-trust-boundary/1"
NO_GO_REL = "../_ops/tests/test_no_go_envelope.py"  # نسبت به SYSTEM_ROOT (R0a)


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def main() -> int:
    files: dict[str, str] = {}
    missing: list[str] = []
    for rel in sorted(CODE_TCB_FILES):
        digest = sha256_file(SYSTEM_ROOT / rel)
        if digest is None:
            missing.append(rel)
        else:
            files[rel] = f"sha256:{digest}"

    no_go = SYSTEM_ROOT / NO_GO_REL
    no_go_digest = sha256_file(no_go)

    manifest = {
        "schema": SCHEMA,
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "scripts/generate_trust_boundary.py (R13 debt-sweep 2026-08-16)",
        "owner_binding": {
            "authority": "owner (Armin)",
            "decision_record": "owner delegation 2026-08-16: «همه چیو اجرا کن کامل — اجازه تصمیم‌گیری داری»",
            "public_key": "_ops/owner-signing/octopus-owner-ed25519-public.pem",
            "algorithm": "ed25519",
            "sig_file": "config/trust-boundary.json.sig",
        },
        "tcb": {
            "files": files,
            "dirs": sorted(CODE_TCB_DIR_NAMES),
            "extra_rules": [
                "هر __init__.py همیشه محافظت‌شده (اجرا در زمانِ import)",
                "هر مسیرِ خارج از SYSTEM_ROOT محافظت‌شده (شاملِ پوشهٔ مرجعِ 4D)",
                "REFERENCE_DIR که به ریشه یا جدِّ آن resolve شود نامعتبر است (C-013)",
            ],
        },
        "no_go_envelope": {
            "file": NO_GO_REL,
            "sha256": f"sha256:{no_go_digest}" if no_go_digest else None,
            "ownership": "owner-only — بازنویسی/حذف توسط ایجنت یا سامانه ممنوع (R0a)",
        },
        "enforcement": {
            "flag": "OCTOPUS_TCB_MANIFEST_ENFORCE",
            "default": "0 (سایه‌ای)",
            "enabled_semantics": "ناهمخوانی digest / امضای نامعتبر / manifest غایب ⇒ ok=False ⇒ توقفِ حفاظتی",
        },
    }

    out = SYSTEM_ROOT / "config" / "trust-boundary.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False,
                              sort_keys=False) + "\n", encoding="utf-8")

    print(f"نوشته شد: {out.relative_to(SYSTEM_ROOT)}")
    print(f"  فایل‌های TCB با digest: {len(files)}")
    if missing:
        print(f"  ⚠️ مفقود: {missing}")
    print(f"  پاکت NO-GO: {NO_GO_REL} → "
          f"{'sha256 ✓' if no_go_digest else 'مفقود!'}")
    print("قدم بعدی (دستِ مالک): امضا با کلید Ed25519 — فرمان در سربرگ همین فایل.")
    return 0 if not missing and no_go_digest else 1


if __name__ == "__main__":
    raise SystemExit(main())
