"""rate_card_builder — کارتِ نرخ از دادهٔ واقعی OCP (Lane Q2، رأی مالک Q6).

از بستهٔ bulk رجیستری قراردادهای NSW، قراردادهای خدمات نقاشی را بیرون می‌کشد
و توزیعِ ارزشِ قراردادها را به‌صورت کارت نرخ پیشنهادی می‌نویسد:
  data/painting_rate_card.json  با  approved_by_owner: false

قفل (رأی Q6): quote_engine تا approved_by_owner=true نشود کوتِ دارای قیمت
نمی‌فرستد. تأیید = مالک یک بار فایل را ویرایش می‌کند (یا فرمان --approve).
OCP مقدارِ قرارداد کل را دارد نه متراژ؛ پس کارت شامل باندهای ارزش +
نرخِ فرضیِ per-m² (بازهٔ محافظه‌کار بازار سیدنی، صریحاً برچسبِ assumption)
است تا موتور کوت بتواند از scope به رقم برسد. هیچ عددِ جعلی به‌عنوان
«دادهٔ OCP» برچسب نمی‌خورد — دو کلید جدا: ocp_derived و market_assumption.
"""
from __future__ import annotations

import gzip
import json
import statistics
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
DATA = Path.home() / ".local/share/ofn"
CARD_PATH = DATA / "painting_rate_card.json"


def build(releases: list[dict]) -> dict:
    """توزیعِ ارزشِ قراردادهای نقاشی از releases خام (اسکیمای OCDS: awards[].value.amount)."""
    try:
        from ofn.agents.nsw_ocp_harvest import is_painting_award
    except ImportError:  # اجرای مستقیم از همان پوشهٔ agents
        from nsw_ocp_harvest import is_painting_award
    vals = []
    for r in releases or []:
        try:
            if not is_painting_award(r):
                continue
            for award in r.get("awards", []) or []:
                try:
                    v = float(((award.get("value") or {}).get("amount")) or 0)
                except (TypeError, ValueError):
                    continue
                if v > 0:
                    vals.append(v)
        except Exception:  # noqa: BLE001
            continue
    if not vals:
        return {"error": "no-painting-contracts"}
    vals.sort()
    n = len(vals)
    card = {
        "version": "v1-proposed",
        "approved_by_owner": False,
        "note": "تأیید مالک لازم است (رأی Q4/Q6 2026-09-01). تا تأیید نشود "
                "هیچ کوتِ دارای قیمت ارسال نمی‌شود.",
        "built_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "NSW OCP bulk registry (contracts matching paint/coating)",
        "ocp_derived": {
            "n_contracts": n,
            "min_aud": round(vals[0], 2),
            "median_aud": round(statistics.median(vals), 2),
            "p25_aud": round(vals[n // 4], 2),
            "p75_aud": round(vals[(3 * n) // 4], 2),
            "max_aud": round(vals[-1], 2),
        },
        "market_assumption": {
            "_label": "ASSUMPTION — نه دادهٔ OCP؛ نرخِ بازهٔ بازار سیدنی تا تأیید مالک",
            "internal_per_m2_aud": [28, 45],
            "external_per_m2_aud": [35, 60],
            "ceiling_per_m2_aud": [80, 140],
            "min_job_callout_aud": 450,
            "quote_validity_days": 30,
        },
    }
    return card


def write_card(card: dict, path: Path = CARD_PATH) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(card, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")
    return {"written": str(path), "approved": card.get("approved_by_owner")}


def main() -> int:
    src = Path("/tmp/nsw2025.jsonl.gz")
    if not src.exists():
        print(json.dumps({"error": f"missing {src} — run nsw_ocp_harvest first"}))
        return 1
    releases = []
    with gzip.open(src, "rt") as f:
        for ln in f:
            try:
                releases.append(json.loads(ln))
            except Exception:  # noqa: BLE001
                continue
    card = build(releases)
    if "error" in card:
        print(json.dumps(card))
        return 1
    print(json.dumps(write_card(card), ensure_ascii=False))
    print(json.dumps(card["ocp_derived"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
