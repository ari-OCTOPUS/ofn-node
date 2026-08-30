#!/usr/bin/env python3
"""validator — artifact ِ ورودی سالم است؟ و شاهدش واقعاً کافی است؟

دو کارِ جدا که یکی گرفتنشان خطرناک است:

  `validate_artifact`   شکل، نسخه، شناسه، hash. شکستش ⇒ BLOCK.
  `evidence_summary`    شمارشِ **مستقلِ** شاهد. اعتماد نمی‌کنیم به عددی که خودِ
                        artifact دربارهٔ خودش گزارش کرده.

دومی مهم‌تر است: اگر `metrics.triangulated_discovery_count` را باور کنیم، یک
artifact ِ دستکاری‌شده می‌تواند بگوید «۵ منبعِ مستقل دارم» و ما validated
حسابش کنیم. پس منابع از خودِ `evidence_urls`/`independent_sources` شمرده
می‌شوند، با نرمال‌سازیِ دامنه.

$0 · stdlib · تابعِ خالص · صفر I/O.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from .contracts import (KNOWN_BUNDLE_SCHEMAS, KNOWN_RESULT_SCHEMAS,
                       SOURCE_STATUSES, content_hash, unwrap)

# ⚠️ فلگ روی کلِ الگو، نه `(?i)` وسطِ آن: پایتون ۳٫۱۱+ فلگِ سراسریِ غیرِ ابتدایی
# را `PatternError` می‌دهد — و چون این الگو در مسیرِ **حذفِ راز** است، یک
# استثنای import-time یعنی هیچ redaction ای اجرا نمی‌شود. بی‌صدا هم نبود
# (کرش کرد)، ولی اگر یک `except` بالادست می‌بود، می‌شد.
_SECRETISH = re.compile(
    r"sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_\-]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:api[_-]?key|secret|password|passwd|bearer)\b\s*[:=]\s*\S{8,}",
    re.I)
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<!\d)(\+?\d[\d\s\-()]{8,}\d)(?!\d)")


def validate_artifact(artifact) -> dict:
    """{ok, errors, warnings, result, status}. هر ابهام ⇒ ok=False."""
    errors, warnings = [], []
    if not isinstance(artifact, dict):
        return {"ok": False, "errors": ["not-a-dict"], "warnings": [],
                "result": {}, "status": None}

    top = artifact.get("schema")
    if top not in KNOWN_BUNDLE_SCHEMAS and top not in KNOWN_RESULT_SCHEMAS:
        # نسخهٔ ناشناخته = BLOCK، نه «شاید سازگار». سازگاریِ حدسی همان چیزی
        # است که یک تغییرِ بی‌صدا در بالادست را به رفتارِ غلط تبدیل می‌کند.
        errors.append(f"unknown-schema:{top!r}")

    result = unwrap(artifact)
    if not result:
        errors.append("no-result-object")
        return {"ok": False, "errors": errors, "warnings": warnings,
                "result": {}, "status": None}

    if result.get("schema") not in KNOWN_RESULT_SCHEMAS:
        errors.append(f"unknown-result-schema:{result.get('schema')!r}")

    status = result.get("status")
    if status not in SOURCE_STATUSES:
        errors.append(f"unknown-status:{status!r}")

    if not str(result.get("discovered_at") or "").strip():
        warnings.append("no-discovered_at")

    # شناسه: bundle خودش `artifact_id` ندارد، پس از hash ساخته می‌شود — ولی
    # اگر روزی داشت و با محتوا نخواند، BLOCK.
    declared_id = artifact.get("artifact_id") or result.get("artifact_id")
    computed = content_hash(result)
    if declared_id and str(declared_id) != computed:
        errors.append("artifact-hash-mismatch")

    d = result.get("discovery")
    if status == "DISCOVERY_VALIDATED" and not isinstance(d, dict):
        errors.append("validated-status-without-discovery-object")
    if status != "DISCOVERY_VALIDATED" and isinstance(d, dict) and d:
        warnings.append("non-validated-status-carries-discovery-object")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "result": result, "status": status,
            "artifact_id": declared_id or computed,
            "content_hash": computed}


def _domain(u: str) -> str:
    try:
        h = (urlsplit(str(u)).hostname or "").lower()
    except ValueError:
        return ""
    return h[4:] if h.startswith("www.") else h


def evidence_summary(result: dict) -> dict:
    """شمارشِ **مستقل** — عددِ خودگزارشیِ artifact خوانده ولی باور نمی‌شود.

    خروجی هر دو را می‌دهد تا اختلاف قابلِ دیدن باشد؛ حکم فقط با شمارشِ خودمان."""
    d = result.get("discovery") if isinstance(result.get("discovery"), dict) else {}
    urls = []
    for key in ("evidence_urls", "sources", "confirming_sources"):
        v = d.get(key)
        if isinstance(v, list):
            urls.extend(str(x) for x in v)
    domains = {dd for dd in (_domain(u) for u in urls) if dd}
    self_reported = None
    try:
        m = result.get("metrics") or {}
        self_reported = int(m.get("triangulated_discovery_count"))
    except (TypeError, ValueError):
        self_reported = None
    fals = d.get("falsifier") or d.get("falsifier_statement")
    return {"evidence_count": len(urls),
            "independent_source_count": len(domains),
            "domains": sorted(domains),
            "self_reported_triangulated": self_reported,
            "falsifier_present": bool(str(fals or "").strip())}


def experiment_of(result: dict) -> "dict | None":
    """آزمایش را از artifact بردار — **اگر واقعاً باشد**.

    artifact ِ واقعیِ ۲۰۲۶-۰۷-۳۰ کلیدِ `experiment` **ندارد** (چون
    `experiments_designed=0`) در حالی که مانیفست مستندش کرده. پس نبودش حالتِ
    عادی است، نه خطا — و `None` برمی‌گردد نه `{}`، تا صداکننده «نبود» را از
    «خالی» تفکیک کند."""
    for key in ("experiment", "designed_experiment", "next_experiment"):
        v = result.get(key)
        if isinstance(v, dict) and v:
            return v
    exps = result.get("experiments")
    if isinstance(exps, list) and exps and isinstance(exps[0], dict):
        return exps[0]
    return None


def scan_sensitive(text: str) -> dict:
    """راز و PII در متنِ خروجی. **قبل** از هر draft صدا زده می‌شود."""
    t = str(text or "")
    return {"secrets": bool(_SECRETISH.search(t)),
            "emails": _EMAIL.findall(t)[:5],
            "phones": [p for p in _PHONE.findall(t)][:5]}


def redact(text: str) -> str:
    """حذفِ راز و PII. عمداً **پیش از** ساختِ draft، نه بعدش."""
    t = str(text or "")
    t = _SECRETISH.sub("[REDACTED-SECRET]", t)
    t = _EMAIL.sub("[REDACTED-EMAIL]", t)
    t = _PHONE.sub("[REDACTED-PHONE]", t)
    return t
