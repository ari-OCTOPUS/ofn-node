"""Owner onboarding panel -- local-only, stdlib, zero cost, zero external calls.

Serves a short "get to know you" form at http://127.0.0.1:<PORT>/. First
visit shows the form; answers are saved (atomic write) to OWNER-PROFILE.json
plus an append-only markdown log in _ops/state/. Later visits recognize the
saved profile and show a summary instead of a blank form.
"""
from __future__ import annotations

import html
import json
import os
import re
import socket
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

STATE_DIR = Path(__file__).resolve().parents[1] / "state"
PROFILE_JSON = STATE_DIR / "OWNER-PROFILE.json"
PROFILE_LOG = STATE_DIR / "OWNER-PROFILE-LOG.md"
PORT = int(os.environ.get("PANEL_PORT", "8790"))

# Read-only project dashboard: scans every PROJECT.md note in the vault.
# Excluded dirs mirror .agentignore (never read: .git/_code/_Archive/_Duplicates/
# secrets-export) plus tooling noise (.claude -- catches stale worktree copies).
VAULT_ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {".git", "_code", "_Archive", "_Duplicates", "secrets-export",
                 ".claude", "node_modules", "__pycache__", ".obsidian", "_Templates"}
STATUS_COLOR = {
    "active": ("#e2f3e6", "#1f6d3a"),
    "idea": ("#e6eefb", "#2a5599"),
    "paused": ("#faf1de", "#8a5a10"),
    "done": ("#eeece5", "#5f5d55"),
    "archived": ("#eeece5", "#8a887f"),
}

# (key, label, kind, options)  kind in {text, textarea, radio, checkbox}
QUESTIONS = [
    ("name", "چی صدات کنم؟", "text", None),
    ("role", "یک خط بگو الان بیشترِ وقتت پیِ چیه؟", "text", None),
    ("focus", "این روزها کدوم پروژه‌ها اولویت دارن؟", "checkbox",
     ["نقاشی (Lead)", "Ziman Gallery", "Mining", "Crypto", "Accounting",
      "اونلی فنز", "هیپنوتیزم و خودآگاهی", "خودِ architect / ارگانیسم"]),
    ("tone", "دوست داری باهات چطوری حرف بزنم؟", "radio",
     ["خیلی مختصر و مستقیم", "معمولی، مثل الان", "با توضیح بیشتر، قدم‌به‌قدم"]),
    ("autonomy", "چقدر دوست داری خودش دست به کار بشه؟", "radio",
     ["فقط بگو، دست به هیچی نزن", "پیشنهاد بده، تایید با من", "توی کارای کوچیک خودش انجام بده"]),
    ("risk", "با پول و بودجه چقدر محتاط باشه؟", "radio",
     ["خیلی محتاط", "متعادل", "می‌تونه ریسک حساب‌شده بکنه"]),
    ("best_time", "بهترین وقت روز برای گزارش/خلاصه دادن بهت کِیه؟", "text", None),
    ("avoid", "چیزی هست که هرگز نباید بدون اجازه‌ات انجام بده؟", "textarea", None),
    ("goal", "در یک جمله، هدف بزرگ‌تر از ساختن این سیستم چیه؟", "textarea", None),
]

STYLE = """
  body{margin:0;padding:2.5rem 1rem;background:#f5f3ee;font-family:Vazirmatn,Tahoma,Arial,sans-serif;
       color:#242320;display:flex;justify-content:center;line-height:1.8}
  .card{max-width:560px;width:100%;background:#fff;border-radius:14px;padding:2rem 2.2rem;
        box-shadow:0 1px 3px rgba(0,0,0,.08)}
  h1{font-size:20px;font-weight:600;margin:0 0 .3rem}
  p.sub{color:#77746c;margin:0 0 1.6rem;font-size:14px}
  .q{margin-bottom:1.4rem}
  label.qlabel{display:block;font-size:14px;font-weight:600;margin-bottom:.5rem}
  input[type=text],textarea{width:100%;box-sizing:border-box;padding:.6rem .7rem;border:1px solid #ddd9cf;
        border-radius:8px;font-family:inherit;font-size:14px;background:#fbfaf7}
  textarea{min-height:64px;resize:vertical}
  .opts{display:flex;flex-wrap:wrap;gap:.5rem}
  .opt{border:1px solid #ddd9cf;border-radius:20px;padding:.4rem .9rem;font-size:13px;cursor:pointer;
       background:#fbfaf7;user-select:none}
  .opt input{margin-left:.4rem}
  button{background:#242320;color:#fff;border:none;border-radius:8px;padding:.75rem 1.6rem;
         font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
  button:hover{background:#403e38}
  table{width:100%;border-collapse:collapse;font-size:14px;margin:1rem 0}
  td{padding:.5rem 0;border-bottom:1px solid #eee;vertical-align:top}
  td.k{color:#77746c;width:40%}
  a{color:#4a6fa5}
  .note{font-size:12px;color:#9a978d;margin-top:1.4rem}
  .nav{display:flex;gap:1rem;margin-bottom:1.4rem;font-size:13px}
  .nav a{color:#77746c;text-decoration:none}
  .nav a:hover{color:#242320}
  .plist{display:flex;flex-direction:column;gap:.7rem}
  .pcard{border:1px solid #eee;border-radius:10px;padding:.9rem 1rem}
  .prow{display:flex;justify-content:space-between;align-items:center;gap:.5rem}
  .ptitle{font-weight:600;font-size:15px}
  .pill{font-size:12px;padding:.2rem .6rem;border-radius:20px;white-space:nowrap}
  .pmeta{font-size:12px;color:#9a978d;margin:.3rem 0 0}
  .pfocus{font-size:13px;color:#4a4844;margin:.4rem 0 0}
"""


def _page(body: str, title: str = "پنل آشنایی") -> bytes:
    nav = ('<div class="nav"><a href="/">پروفایل</a><a href="/projects">پروژه‌ها</a>'
           '<a href="/lead">لید</a><a href="/organism">ارگانیسم</a></div>')
    return (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        f"<title>{title}</title><style>{STYLE}</style></head>"
        f'<body><div class="card">{nav}{body}</div></body></html>'
    ).encode("utf-8")


def _load_profile() -> dict | None:
    if PROFILE_JSON.exists():
        try:
            return json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


_SAVE_LOCK = threading.Lock()


def _save_profile(answers: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with _SAVE_LOCK:
        existing = _load_profile() or {}
        history = existing.get("history", [])
        if existing.get("answers"):
            history.append({"answers": existing["answers"], "saved_at": existing.get("updated_at")})
        profile = {
            "answers": answers,
            "created_at": existing.get("created_at", now),
            "updated_at": now,
            "history": history[-20:],
        }
        tmp = PROFILE_JSON.with_suffix(".tmp")
        tmp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(PROFILE_JSON)
        with open(PROFILE_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"\n## {now}\n")
            for key, label, _kind, _opts in QUESTIONS:
                val = answers.get(key, "")
                if isinstance(val, list):
                    val = "، ".join(val)
                fh.write(f"- **{label}**: {val or '—'}\n")


def _parse_scalar(raw: str):
    v = raw.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    if v.startswith("[["):
        return v
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
    return v


def _parse_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    fm: dict = {}
    body = text
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body = "\n".join(lines[i + 1:])
                break
            if ":" in lines[i]:
                key, _, val = lines[i].partition(":")
                fm[key.strip()] = _parse_scalar(val)
    return fm, body


def _extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            t = s[2:].strip()
            if t.startswith("پروژه:"):
                t = t.split(":", 1)[1].strip()
            return t
    return fallback


_WIKILINK_PIPE = re.compile(r"\[\[[^\]|]+\|([^\]]+)\]\]")
_WIKILINK_PLAIN = re.compile(r"\[\[([^\]]+)\]\]")


def _clean_bullet(s: str) -> str:
    s = _WIKILINK_PIPE.sub(r"\1", s)
    s = _WIKILINK_PLAIN.sub(lambda m: m.group(1).rsplit("/", 1)[-1], s)
    return s.replace("**", "")


def _clip(s: str, n: int = 160) -> str:
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(" ")
    if sp > 40:
        cut = cut[:sp]
    return cut + "…"


def _extract_bullet(body: str, heading: str, prefer: str = "") -> str:
    in_section = False
    bullets = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            if in_section:
                break
            in_section = s[3:].strip() == heading
            continue
        if in_section and s.startswith("- "):
            b = s[2:].strip()
            if b and b != "—":
                bullets.append(b)
    if not bullets:
        return ""
    if prefer:
        for b in bullets:
            if b.startswith(prefer):
                return _clip(_clean_bullet(b))
    return _clip(_clean_bullet(bullets[-1]))


def _count_open_actions(body: str) -> int:
    in_section = False
    n = 0
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            if in_section:
                break
            in_section = s[3:].strip() == "Next actions"
            continue
        if in_section and s.startswith("- [ ]"):
            rest = s[5:].strip()
            if rest and rest != "—":
                n += 1
    return n


def _scan_projects() -> list[dict]:
    items = []
    paths = []
    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]  # هرگز وارد مسیر ممنوع نشو
        if "PROJECT.md" in files:
            paths.append(Path(root) / "PROJECT.md")
    for p in paths:
        try:
            fm, body = _parse_note(p)
        except OSError:
            continue
        items.append({
            "path": str(p.relative_to(VAULT_ROOT)).replace("\\", "/"),
            "title": _extract_title(body, p.parent.name),
            "kind": fm.get("kind", "project"),
            "status": fm.get("status", "?"),
            "updated": fm.get("updated", "—"),
            "focus": _extract_bullet(body, "Active Context", prefer="تمرکز فعلی"),
            "open_actions": _count_open_actions(body),
        })
    order = {"active": 0, "idea": 1, "paused": 2, "done": 3, "archived": 4}
    items.sort(key=lambda x: (order.get(x["status"], 5), x["title"]))
    return items


def _read_state_json(name: str) -> dict:
    p = STATE_DIR / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _age_fa(ts_iso: str) -> str:
    try:
        t = datetime.fromisoformat(ts_iso)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        mins = int((datetime.now(timezone.utc) - t).total_seconds() // 60)
    except (ValueError, TypeError):
        return "؟"
    if mins < 1:
        return "همین الان"
    if mins < 60:
        return f"{mins} دقیقه پیش"
    if mins < 60 * 24:
        return f"{mins // 60} ساعت پیش"
    return f"{mins // (60 * 24)} روز پیش"


def render_organism() -> bytes:
    prof = _load_profile() or {}
    name = (prof.get("answers") or {}).get("name", "")
    hello = f"سلام {html.escape(name)} — " if name else ""
    st = _read_state_json("ORGANISM-STATE.json")
    if not st:
        body = (
            "<h1>ارگانیسم</h1>"
            f'<p class="sub">{hello}هنوز روشن نشده — هیچ state‌ای در <code>_ops/state/</code> نیست.</p>'
            '<p>برای روشن‌کردن (سایه، $۰): دابل‌کلیک روی <code>F:\\backup\\_ops\\RUN-ORGANISM.bat</code></p>'
            '<p class="note">توقف تمیز: ساختن فایل <code>_ops\\STOP-ORGANISM</code> و یک تیک صبر.</p>'
        )
        return _page(body, title="ارگانیسم")
    ts = str(st.get("ts", ""))
    age = _age_fa(ts)
    stale = "🟢 زنده" if ("دقیقه" in age or age == "همین الان") else "🟠 کهنه"
    month = st.get("month") or {}
    today = st.get("today") or {}
    rows = [
        ("آخرین تیک", f"{stale} · {age}"),
        ("شروع", str(st.get("started", "—"))[:19].replace("T", " ")),
        ("خرج ماه (متر سایه)", f"AU${month.get('aud', 0):.2f}" if isinstance(month.get("aud"), (int, float)) else "—"),
        ("خرج امروز", f"US${today.get('usd', 0):.4f}" if isinstance(today.get("usd"), (int, float)) else "—"),
        ("متر مشکوک صفر", str(st.get("suspect_zero_total", "—"))),
        ("تعارض تلمتری", str(len(st.get("conflicts") or [])) if isinstance(st.get("conflicts"), list) else "—"),
        ("فشار epoch", str((st.get("pressure") or {}).get("pressure", "—"))),
        ("epoch بعدی (دقیقه)", str(st.get("next_epoch_minutes", "—"))),
        ("σ تکثیر", str(st.get("sigma", "pre-replication"))),
        ("halted / frozen", f"{st.get('halted') or '—'} / {st.get('frozen') or '—'}"),
    ]
    if st.get("last_error"):
        rows.append(("آخرین خطا", html.escape(str(st["last_error"])[:200])))
    table = "".join(f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in rows)
    body = (
        "<h1>ارگانیسم — وضعیت زنده</h1>"
        f'<p class="sub">{hello}همه‌چیز سایه و $۰؛ بودجهٔ زنده پشت گیت دوقفلهٔ خودت.</p>'
        f"<table>{table}</table>"
        '<p><a href="http://127.0.0.1:8771/">سرور وضعیت خود ارگانیسم (8771)</a></p>'
        '<p class="note">این صفحه فقط فایل‌های state را می‌خواند — هیچ چیزی را تغییر نمی‌دهد.</p>'
    )
    return _page(body, title="ارگانیسم")


def render_projects(items: list[dict]) -> bytes:
    n_active = sum(1 for it in items if it["status"] == "active")
    total_open = sum(it["open_actions"] for it in items)
    cards = []
    for it in items:
        bg, fg = STATUS_COLOR.get(it["status"], ("#eeece5", "#5f5d55"))
        focus_html = f'<p class="pfocus">{html.escape(it["focus"])}</p>' if it["focus"] else ""
        actions = f' · {it["open_actions"]} اقدام باز' if it["open_actions"] else ""
        cards.append(
            '<div class="pcard">'
            f'<div class="prow"><span class="ptitle">{html.escape(it["title"])}</span>'
            f'<span class="pill" style="background:{bg};color:{fg}">{html.escape(it["status"])}</span></div>'
            f'<p class="pmeta">{html.escape(it["kind"])} · به‌روزرسانی {html.escape(str(it["updated"]))}{actions}</p>'
            f"{focus_html}"
            "</div>"
        )
    body = (
        "<h1>پروژه‌ها</h1>"
        f'<p class="sub">{n_active} فعال از {len(items)} پروژه · {total_open} اقدام باز روی میز</p>'
        f'<div class="plist">{"".join(cards)}</div>'
    )
    return _page(body, title="پروژه‌ها")


def _render_field(key: str, label: str, kind: str, options: list | None, existing: dict | None) -> str:
    cur = existing.get(key) if existing else None
    if kind == "text":
        v = html.escape(cur) if isinstance(cur, str) else ""
        req = " required" if key == "name" else ""
        return (f'<div class="q"><label class="qlabel">{label}</label>'
                f'<input type="text" name="{key}" value="{v}"{req}></div>')
    if kind == "textarea":
        v = html.escape(cur) if isinstance(cur, str) else ""
        return (f'<div class="q"><label class="qlabel">{label}</label>'
                f'<textarea name="{key}">{v}</textarea></div>')
    if kind == "radio":
        cur_list = [cur] if isinstance(cur, str) else []
        opts = "".join(
            f'<label class="opt"><input type="radio" name="{key}" value="{html.escape(o)}"'
            f'{" checked" if o in cur_list else ""}> {o}</label>'
            for o in options
        )
        return f'<div class="q"><label class="qlabel">{label}</label><div class="opts">{opts}</div></div>'
    if kind == "checkbox":
        cur_list = cur if isinstance(cur, list) else []
        opts = "".join(
            f'<label class="opt"><input type="checkbox" name="{key}" value="{html.escape(o)}"'
            f'{" checked" if o in cur_list else ""}> {o}</label>'
            for o in options
        )
        return f'<div class="q"><label class="qlabel">{label}</label><div class="opts">{opts}</div></div>'
    return ""


def render_form(existing: dict | None = None) -> bytes:
    fields = "".join(_render_field(k, lbl, kind, opts, existing) for k, lbl, kind, opts in QUESTIONS)
    heading = "ویرایش پاسخ‌ها" if existing else "بذار بشناسمت"
    sub = ("هر وقت خواستی می‌تونی دوباره برگردی و عوضش کنی."
           if existing else
           "چندتا سوال کوتاه — جواب‌ها فقط روی همین لپ‌تاپ ذخیره می‌شه، جایی نمی‌ره.")
    body = (
        f"<h1>{heading}</h1><p class=\"sub\">{sub}</p>"
        f'<form method="post" action="/submit">{fields}'
        f'<button type="submit">ذخیره کن</button></form>'
        f'<p class="note">ذخیره محلی · بدون اینترنت · بدون هیچ سرویس بیرونی</p>'
    )
    return _page(body)


def render_welcome(profile: dict) -> bytes:
    answers = profile.get("answers", {})
    name = answers.get("name") or "دوست"
    row_parts = []
    for key, label, _kind, _opts in QUESTIONS:
        v = answers.get(key)
        if isinstance(v, list):
            shown = "، ".join(v) if v else "—"
        else:
            shown = html.escape(v) if v else "—"
        row_parts.append(f'<tr><td class="k">{label}</td><td>{shown}</td></tr>')
    updated = str(profile.get("updated_at", "—"))[:19].replace("T", " ")
    body = (
        f"<h1>خوش برگشتی، {html.escape(name)}</h1>"
        f'<p class="sub">آخرین به‌روزرسانی: {updated}</p>'
        f'<table>{"".join(row_parts)}</table>'
        f'<p><a href="/edit">ویرایش پاسخ‌ها</a></p>'
        f'<p class="note">این پروفایل را ارگانیسم/سیستم‌های دیگر همین vault هم می‌توانند بخوانند (فقط‌خواندنی).</p>'
    )
    return _page(body)


def render_saved() -> bytes:
    body = (
        "<h1>ذخیره شد</h1>"
        '<p class="sub">جواب‌هات ثبت شد. دفعه بعد که این صفحه رو باز کنی، می‌شناستت.</p>'
        '<p><a href="/">برگشت</a></p>'
    )
    return _page(body)


# ─── B3: فرمِ لید → mint LEAD-YYYYMMDD-NNN + رویدادِ PROPOSAL (فقط propose؛ CONFIRM دستِ reconcile) ───
LEAD_CELLS = [("lead.doer", "نقاشی (Lead)"), ("ziman.doer", "Ziman"), ("crypto.doer", "Crypto")]


def submit_lead(lead_name: str, lead_desc: str, expected_aud: str, cell: str) -> dict:
    """ورودیِ انسانیِ لید → attribution.propose (mint id + PROPOSAL). هیچ CONFIRM/پول/fitness.
    fail-closed: ورودیِ نامعتبر یا خطای ثبت → {ok:False, error}؛ هرگز نیمه‌ثبت."""
    name = (lead_name or "").strip()
    if not name:
        return {"ok": False, "error": "نام/کارِ لید لازم است"}
    try:
        exp = float(str(expected_aud).strip() or "0")
    except ValueError:
        return {"ok": False, "error": "ارزشِ تخمینی باید عدد باشد (AUD)"}
    if exp < 0:
        return {"ok": False, "error": "ارزشِ تخمینی منفی نمی‌شود"}
    if cell not in {c for c, _ in LEAD_CELLS}:
        cell = "lead.doer"
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "budget"))
        import attribution  # lazy: خطای import پنل را نمی‌شکند (fail-closed فقط برای مسیرِ لید)
        desc = name if not (lead_desc or "").strip() else f"{name} — {lead_desc.strip()}"
        rec = attribution.propose(cell, exp, lead=desc)
        return {"ok": True, "attribution_id": rec["payload"]["attribution_id"], "cell": cell}
    except Exception as e:  # noqa: BLE001 — پیام امن (بدون echo راز)، هیچ نیمه‌ثبت
        return {"ok": False, "error": f"ثبت نشد: {type(e).__name__}"}


def render_lead_form(error: str = "") -> bytes:
    cells = "".join(
        f'<label class="opt"><input type="radio" name="cell" value="{c}"'
        f'{" checked" if i == 0 else ""}> {lbl}</label>'
        for i, (c, lbl) in enumerate(LEAD_CELLS))
    err = f'<p class="sub" style="color:#a33">{html.escape(error)}</p>' if error else ""
    body = (
        "<h1>لید جدید</h1>"
        '<p class="sub">لید را وارد کن؛ سیستم یک کدِ یکتا (LEAD-…) می‌سازد که روی کوت/فاکتور می‌نویسی. '
        'فقط ثبتِ فرصت است (PROPOSAL) — هیچ پولی اینجا تأیید نمی‌شود.</p>'
        f"{err}"
        '<form method="post" action="/lead">'
        '<div class="q"><label class="qlabel">نام/کارِ لید</label>'
        '<input type="text" name="lead_name" required></div>'
        '<div class="q"><label class="qlabel">توضیح کوتاه (اختیاری)</label>'
        '<textarea name="lead_desc"></textarea></div>'
        '<div class="q"><label class="qlabel">ارزشِ تخمینی (AUD)</label>'
        '<input type="text" name="expected_aud" value="0"></div>'
        f'<div class="q"><label class="qlabel">کدام پا اعتبار می‌گیرد؟</label>'
        f'<div class="opts">{cells}</div></div>'
        '<button type="submit">ثبتِ لید (mint کد)</button></form>'
        '<p class="note">کد فقط carrier است؛ تأییدِ پول بعداً از reconcile با CSVِ بانک/حسابداری می‌آید — '
        'سیستم هرگز خودش پول را تأیید نمی‌کند.</p>'
    )
    return _page(body, title="لید جدید")


def render_lead_done(aid: str, cell: str) -> bytes:
    body = (
        "<h1>لید ثبت شد ✅</h1>"
        '<p class="sub">کدِ carrier ساخته شد. این را روی کوت/فاکتور بنویس:</p>'
        '<p style="font-size:22px;font-weight:700;letter-spacing:1px;direction:ltr;text-align:center;'
        f'background:#f0efe9;border-radius:10px;padding:1rem">{html.escape(aid)}</p>'
        f'<p class="sub">پا: {html.escape(cell)} · وضعیت: PROPOSAL (هنوز واردِ fitness نشده)</p>'
        '<p><a href="/lead">لید دیگر</a> · <a href="/">خانه</a></p>'
        '<p class="note">وقتی پول نشست: ردیفِ CSV با همین کد در <code>_ops/reconcile</code> بگذار → '
        'reconcile آن را در پنجرهٔ ۷ روز CONFIRMED می‌کند.</p>'
    )
    return _page(body, title="لید ثبت شد")


class _ExclusivePanelServer(ThreadingHTTPServer):
    """تلهٔ شناختهٔ ویندوز (جلسه ۱۹): http.server با SO_REUSEADDR پیش‌فرض double-bind
    ساکت می‌سازد — bind را انحصاری می‌کنیم تا دو نمونهٔ پنل هرگز هم‌زمان بالا نیایند."""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, payload: bytes, status: int = 200, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.rstrip("/") or "/"
        if path == "/favicon.ico":
            self._send(b"", status=204)
            return
        if path == "/profile":
            self._send(json.dumps(_load_profile() or {}, ensure_ascii=False).encode("utf-8"),
                       ctype="application/json; charset=utf-8")
            return
        if path == "/edit":
            prof = _load_profile()
            self._send(render_form(prof.get("answers") if prof else None))
            return
        if path == "/projects":
            self._send(render_projects(_scan_projects()))
            return
        if path == "/lead":
            self._send(render_lead_form())
            return
        if path == "/organism":
            self._send(render_organism())
            return
        profile = _load_profile()
        if profile and profile.get("answers"):
            self._send(render_welcome(profile))
        else:
            self._send(render_form())

    def do_POST(self):
        path = self.path.rstrip("/") or "/"
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        parsed = parse_qs(raw)
        if path == "/lead":
            res = submit_lead(parsed.get("lead_name", [""])[0], parsed.get("lead_desc", [""])[0],
                              parsed.get("expected_aud", ["0"])[0], parsed.get("cell", ["lead.doer"])[0])
            self._send(render_lead_done(res["attribution_id"], res["cell"]) if res["ok"]
                       else render_lead_form(res["error"]))
            return
        if path != "/submit":
            self._send(b"not found", status=404)
            return
        answers = {}
        for key, _label, kind, _opts in QUESTIONS:
            if kind == "checkbox":
                answers[key] = parsed.get(key, [])
            else:
                answers[key] = parsed.get(key, [""])[0].strip()
        if not answers.get("name"):
            prof = _load_profile()
            self._send(render_form(prof.get("answers") if prof else None))
            return
        _save_profile(answers)
        self._send(render_saved())


def main() -> None:
    try:
        server = _ExclusivePanelServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        print(f"نتونستم روی پورت {PORT} بالا بیام (شاید از قبل روشنه): {e}")
        sys.exit(1)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"پنل روشنه: {url}  (برای توقف: Ctrl+C)")
    if os.environ.get("PANEL_AUTOOPEN") == "1":
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
