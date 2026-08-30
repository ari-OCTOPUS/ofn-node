"""report.py — گزارش انسان‌خوان + bundle ماشین‌خوان.

بند ۱۵: خروجی‌ها در reports/ (انسان‌خوان) و artifacts/ (ماشین‌خوان).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(path: Path, data: str) -> None:
    """نوشتن اتمیک: temp + rename. اگر corrupt شد، فایل قبلی سالم می‌ماند."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp-", suffix=path.suffix
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def export_bundle(
    result: dict,
    output_dir: Path,
    *,
    label: str = "world-discovery-latest",
    now: Optional[datetime] = None,
) -> dict:
    """نوشتن bundle ماشین‌خوان به‌صورت اتمیک.

    فایل: <output_dir>/<label>.json
    خروجی: {path, schema, written_at, sha256}
    """
    now = now or datetime.now(timezone.utc)
    output_dir = Path(output_dir)
    out_path = output_dir / f"{label}.json"

    bundle = {
        "schema": "world-discovery.bundle.v1",
        "written_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "result": result,
    }
    text = json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True)
    _atomic_write(out_path, text)

    import hashlib
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "path": str(out_path),
        "schema": "world-discovery.bundle.v1",
        "written_at": bundle["written_at"],
        "sha256": sha,
        "bytes": len(text.encode("utf-8")),
    }


def load_bundle_check(path: Path) -> dict:
    """بارگذاری و اعتبارسنجی bundle. اگر corrupt بود → fail closed."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"corrupt artifact: {e}") from e
    if data.get("schema") != "world-discovery.bundle.v1":
        raise ValueError(f"unknown schema: {data.get('schema')}")
    return data


def write_human_report(
    *,
    direction: dict,
    metrics: dict,
    candidates: list[dict],
    top_discovery: Optional[dict],
    competitor_matrix: dict,
    asymmetry_hypotheses: list[dict],
    experiment: Optional[dict],
    owner_action_cards: list[dict],
    final_status: str,
    output_dir: Path,
    now: Optional[datetime] = None,
) -> str:
    """نوشتن گزارش انسان‌خوان Markdown. برمی‌گرداند path."""
    now = now or datetime.now(timezone.utc)
    output_dir = Path(output_dir)
    fname = f"WORLD-DISCOVERY-EXECUTION-REPORT-{now.strftime('%Y-%m-%d')}.md"
    out_path = output_dir / fname

    lines: list[str] = []
    lines.append(f"# WORLD-DISCOVERY EXECUTION REPORT — {now.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append(f"> [FACT] وضعیت نهایی مأموریت: **{final_status}**")
    lines.append("")
    lines.append("## جهت مالک")
    lines.append(f"- دامنه: {direction.get('domain')}")
    lines.append(f"- جغرافیا: {direction.get('geography')}")
    lines.append(f"- افق: {direction.get('horizon_days')} روز")
    lines.append(f"- رقبا: {', '.join(direction.get('competitors', []))}")
    lines.append(f"- سطح عمل: {direction.get('action_level')}")
    lines.append(f"- حداقل شاهد: {direction.get('min_sources')} منبع مستقل")
    lines.append("")
    lines.append("## سنجه‌های مأموریت")
    lines.append("| سنجه | مقدار |")
    lines.append("|---|---:|")
    for k, v in metrics.items():
        lines.append(f"| {k} | {v} |")
    inv_msg = "✅ همه ۰" if all(
        metrics.get(inv, 0) == 0
        for inv in ("external_effect_count", "spend_amount",
                    "privacy_violation_count", "unsupported_claim_count")
    ) else "❌ نقض شده"
    lines.append("")
    lines.append(f"**سنجه‌های سخت (external/spend/privacy/unsupported):** {inv_msg}")
    lines.append("")

    lines.append(f"## کاندیداها ({len(candidates)})")
    for i, c in enumerate(candidates[:10], 1):
        lines.append(
            f"{i}. [{c.get('raw_kind')}] {c.get('claim', '')[:120]} "
            f"(independent={c.get('independent_sources')}, "
            f"date={c.get('has_date')})"
        )
    lines.append("")

    if top_discovery:
        lines.append("## کشف برتر")
        lines.append(f"- **ID:** {top_discovery.get('discovery_id')}")
        lines.append(f"- **ادعا:** {top_discovery.get('claim')}")
        lines.append(f"- **چرا مهم:** {top_discovery.get('why_it_matters')}")
        lines.append(f"- **وضعیت:** {top_discovery.get('status')}")
        lines.append(f"- **novelty:** {top_discovery.get('novelty', {}).get('decision')}")
        lines.append(f"- **falsifier:** {top_discovery.get('falsifier')}")
        lines.append(f"- **آزمایش بعدی:** {top_discovery.get('next_experiment')}")
        lines.append(f"- **owner_gate:** {top_discovery.get('owner_gate')}")
        lines.append("")
        ev = top_discovery.get("evidence", [])
        lines.append(f"### شواهد ({len(ev)} منبع)")
        for s in ev[:10]:
            lines.append(
                f"- [{s.get('tier')}] {s.get('title', '')[:80]} — "
                f"`{s.get('url', '')[:80]}` ({s.get('source_date', '?')})"
            )
        lines.append("")

    lines.append("## ماتریس رقابت")
    rows = competitor_matrix.get("rows", [])
    if rows:
        lines.append("| شرکت | نقاط قوت | نقاط ضعف | شاهد واقعی |")
        lines.append("|---|---|---|---|")
        for r in rows:
            st = "; ".join(r.get("strengths", []))[:60]
            we = "; ".join(r.get("weaknesses", []))[:60]
            ev = "✅" if r.get("real_use_evidence") else "❌"
            lines.append(f"| {r.get('company')} | {st} | {we} | {ev} |")
    else:
        lines.append("_ماتریس خالی_")
    lines.append("")

    lines.append(f"## فرضیه‌های مزیت نامتقارن ({len(asymmetry_hypotheses)})")
    for h in asymmetry_hypotheses[:8]:
        lines.append(f"- **{h.get('asymmetry_id')}**: {h.get('opportunity', '')[:140]}")
        lines.append(f"  - شاهد لازم: {h.get('evidence_needed', '')[:120]}")
    lines.append("")

    if experiment:
        lines.append("## آزمایش پیشنهادی")
        lines.append(f"- **ID:** {experiment.get('experiment_id')}")
        lines.append(f"- **سطح:** {experiment.get('level')}")
        lines.append(f"- **فرضیه:** {experiment.get('hypothesis')}")
        lines.append(f"- **سنجه:** {experiment.get('observable_metric')}")
        lines.append(f"- **هدف:** {experiment.get('target')}")
        lines.append(f"- **falsifier:** {experiment.get('falsifier')}")
        lines.append(f"- **deadline:** {experiment.get('deadline')}")
        lines.append(f"- **cost ceiling:** {experiment.get('cost_ceiling')}")
        lines.append("")

    if owner_action_cards:
        lines.append(f"## Owner Action Cards ({len(owner_action_cards)})")
        lines.append("> همه در وضعیت BLOCKED_BY_OWNER. هیچ ارسالی بدون رأی تازه نیست.")
        for c in owner_action_cards:
            lines.append(f"- **{c.get('action_id')}**: {c.get('exact_action')}")
            lines.append(f"  - expires: {c.get('expires_at')}")
            lines.append(f"  - default: {c.get('default_without_approval')}")
        lines.append("")

    lines.append("---")
    lines.append("> [FACT] این گزارش اطلاعات است، نه مجوز. هیچ‌چیز در آن به‌عنوان "
                 "مجوز خرج/ارسال/deploy تلقی نمی‌شود.")

    text = "\n".join(lines)
    _atomic_write(out_path, text)
    return str(out_path)
