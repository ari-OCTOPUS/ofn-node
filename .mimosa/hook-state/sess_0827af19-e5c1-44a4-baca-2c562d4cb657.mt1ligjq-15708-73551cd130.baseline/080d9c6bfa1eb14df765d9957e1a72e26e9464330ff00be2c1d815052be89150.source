"""
coordinator/dual_notifier.py
==============================
پیام تلگرام یکپارچه از هر دو ربات.
"""
import sys, json, time, requests
from pathlib import Path
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, str(Path(__file__).parent))
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, CONFLUENCE_THRESHOLD, WATCH_THRESHOLD

try:
    from confluence_scorer import ConfluenceResult
except ImportError:
    ConfluenceResult = object   # type: ignore


ACTION_EMOJI = {
    "MINE+BUY":  "🚨⛏️💰",
    "MINE":      "⛏️",
    "BUY":       "💰",
    "RUN_NODE":  "🖥️",
    "WATCH":     "👀",
    "NO_ACTION": "❌",
}

QUADRANT_STARS = {
    "DEPLOY":          "⭐⭐⭐⭐⭐",
    "ACCUMULATE":      "⭐⭐⭐⭐",
    "NEUTRAL":         "⭐⭐⭐",
    "WAIT":            "⭐⭐",
    "MACRO_ONLY_BULL": "⭐⭐⭐",
    "MACRO_ONLY_BEAR": "⭐",
    "SOCIAL_ONLY_HOT": "⭐⭐⭐",
    "TRAP":            "⚠️",
    "UNKNOWN":         "❓",
    "MACRO_ONLY":      "⭐⭐",
}


def _macro_line(result: ConfluenceResult) -> str:
    score = 0
    btc   = "?"
    # از اولین result macro می‌گیریم
    return ""


def build_message(results: List, meta: dict) -> str:
    now     = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cycle   = (meta.get("cycle_ts") or "")[:16]
    nulled  = meta.get("cycle_nulled", True)
    macro   = meta.get("macro", {})
    cq      = macro.get("macro_cq_score", "?")
    btc_t   = macro.get("btc_trend", "?")

    macro_icon = {"DISTRIBUTING": "🔴", "NEUTRAL": "🟡", "ACCUMULATING": "🟢"}.get(btc_t, "⚪")

    lines = [
        "🤝 *DUAL-BOT CONFLUENCE*",
        f"🕐 {now}  |  QA cycle: `{cycle}`",
        f"{macro_icon} BTC macro: *{btc_t}* (CQ={cq})"
        + (" — ⛔ CYCLE NULLED" if nulled else ""),
        "━━━━━━━━━━━━━━━━━━━━━",
    ]

    # جدا کن: action darbiarim, watch, no_action
    signals  = [r for r in results if r.action not in ("NO_ACTION", "WATCH")]
    watches  = [r for r in results if r.action == "WATCH"]
    no_acts  = [r for r in results if r.action == "NO_ACTION"]

    # ── Accumulate signals ──────────────────────────────────────────────────
    if signals:
        for r in sorted(signals, key=lambda x: -x.confluence):
            emoji  = ACTION_EMOJI.get(r.action, "❓")
            stars  = QUADRANT_STARS.get(r.sentinel_quadrant, "")
            lines += [
                f"\n{emoji} *{r.symbol}* — {r.action}",
                f"  Confluence: `{r.confluence:.2f}` / 1.00",
                f"  QA: score=`{r.final_score:.1f}` edge=`{','.join(r.edge_present) or 'none'}`",
                f"  Sentinel: {stars} `{r.sentinel_quadrant}` kelly=`{r.sentinel_kelly:.2f}`",
            ]
            if r.sentinel_social is not None:
                lines.append(
                    f"  Signal: social=`{r.sentinel_social:+.2f}` macro=`{r.sentinel_macro:+.2f}`")
            lines.append(f"  → _{r.action_reason}_")
            if r.veto_layers:
                lines.append(f"  QA veto layers: `{'  '.join(r.veto_layers)}`")
    else:
        lines.append("\n❌ *NO ACCUMULATE SIGNAL THIS CYCLE*")

    # ── Watch list ─────────────────────────────────────────────────────────
    if watches:
        lines.append("\n👀 *WATCH* (approaching threshold):")
        for r in sorted(watches, key=lambda x: -x.confluence):
            lines.append(
                f"  • {r.symbol}: confluence=`{r.confluence:.2f}` "
                f"| {r.sentinel_quadrant} | {r.action_reason}")

    # ── Reviewed ──────────────────────────────────────────────────────────
    all_syms = [r.symbol for r in results]
    lines += [
        "\n━━━━━━━━━━━━━━━━━━━━━",
        f"Reviewed: `{' · '.join(all_syms)}`",
        f"📊 `{len(signals)}` signal | `{len(watches)}` watch | `{len(no_acts)}` skip",
        "_PAPER MODE — no real capital deployed_",
    ]

    return "\n".join(lines)


def send(results: List, meta: dict) -> bool:
    """پیام را به تلگرام می‌فرستد. True اگه موفق."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[DualNotifier] No Telegram credentials — printing only")
        msg = build_message(results, meta)
        print("\n" + "─" * 60)
        print(msg)
        print("─" * 60 + "\n")
        return False

    msg = build_message(results, meta)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       msg,
            "parse_mode": "Markdown",
        }, timeout=15)
        if r.ok:
            print("[DualNotifier] ✓ Telegram sent")
            return True
        else:
            print(f"[DualNotifier] Telegram error: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"[DualNotifier] Request failed: {e}")
        return False


def save_decisions(results: List, meta: dict, path) -> None:
    """نتایج را در decisions.jsonl ذخیره می‌کند."""
    from dataclasses import asdict
    record = {
        "ts":       datetime.now(timezone.utc).isoformat(),
        "cycle_ts": meta.get("cycle_ts", ""),
        "macro":    meta.get("macro", {}),
        "decisions": [
            {
                "symbol":       r.symbol,
                "action":       r.action,
                "confluence":   r.confluence,
                "qa_contrib":   r.qa_contrib,
                "sentinel_contrib": r.sentinel_contrib,
                "sentinel_quadrant": r.sentinel_quadrant,
                "sentinel_kelly": r.sentinel_kelly,
                "gates_passed": r.gates_passed,
                "gate_failures": r.gate_failures,
                "edge_present": r.edge_present,
                "final_score":  r.final_score,
            }
            for r in results
        ]
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[DualNotifier] decisions logged → {path}")
