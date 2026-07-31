#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capture — ‏Capture ِ یک‌ژسته‌ی DM (منشور رأی ۹–۱۰، لِین D موج ۲).

    متن/ویس/عکس/لینک → تشخیصِ نوع (کار/لید/ایده/هزینه/نوت) →
    بایگانی در vault طبقِ قانونِ اساسی → مسیریابی → تأییدیهٔ یک‌خطی

مرزها (مثل leg_tasks):
  · این ماژول **هیچ‌چیز نمی‌فرستد** — ack فقط متن است؛ ارسال با مرکز است.
  · هیچ دانلودی از تلگرام نمی‌کند — ویس با file_id/duration ثبت می‌شود و
    ack صادقانه می‌گوید متن‌سازی (transcription) هنوز نصب نیست. جعلِ
    transcript ممنوع.
  · طبقه‌بندِ پایه $0 و خالص است (جدولِ کلیدواژه به سبکِ intent.py)؛
    پالایشِ LLM فقط با ask_fn ِ تزریقی و پشتِ فلگِ OCTOPUS_TG_CAPTURE_LLM.
  · مسیرِ vault فقط از vault_root یا env ‏ORG_ROOT — هرگز literal ِ درختِ
    زنده. harness ِ تست‌ها ORG_ROOT را به vault ِ موقت پین می‌کند.
  · dedup ِ قانونِ اساسی §۹: قبل از نوشتن، message_id در محدودهٔ همان
    chat_id گشته می‌شود؛ بود ⇒ skip (پایپ‌لاین idempotent).

فلگ‌ها (هر دو default-off، خارج از PAPER_FULL_FLAGS):
  OCTOPUS_TG_CAPTURE      — مرکز فقط وقتی روشن است handle را صدا می‌زند
                             (و خودِ handle هم fail-closed چک می‌کند).
  OCTOPUS_TG_CAPTURE_LLM  — پالایشِ اختیاریِ LLM (tier محلی، هرگز پولی).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent

FLAG_CAPTURE = "OCTOPUS_TG_CAPTURE"
FLAG_CAPTURE_LLM = "OCTOPUS_TG_CAPTURE_LLM"

KINDS = ("task", "lead", "idea", "expense", "note")

RAW_SUBDIR = ("10 - Telegram processing", "Raw")

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def _flag_on(name: str) -> bool:
    return os.environ.get(name, "0") == "1"


# ── واژگانِ طبقه‌بندی (به سبکِ intent.py — خالص، بدون I/O) ────────────────────
_EXPENSE_KW = ("هزینه", "خرید", "پرداخت", "پول دادم", "پول", "فاکتور", "قبض")
_IDEA_KW = ("ایده",)
# فعل‌های امری/نشانه‌های کار — «باید» و «یادم بنداز» صریح‌ترین‌ها هستند.
_TASK = re.compile(
    r"یادم بنداز|یادم بینداز|یادآوری کن|فراموش نکن|\bباید\b|"
    r"\b(?:کن|بده|بزن|بگیر|بفرست|بخر|بنویس|بردار|بپرس)(?:م|ی|ید|یم)?\b")
_PHONE = re.compile(r"\+?\d[\d\-\s]{6,}\d")
_WHEN = re.compile(
    r"((?:پس‌فردا|پس فردا|فردا|امروز|امشب|شنبه|یکشنبه|دوشنبه|سه‌شنبه|"
    r"چهارشنبه|پنج‌شنبه|پنجشنبه|جمعه)(?:\s+(?:ساعت\s*)?[\d۰-۹]{1,2})?"
    r"|ساعت\s*[\d۰-۹]{1,2})")
_URL = re.compile(r"https?://\S+")

# نامِ پاها — همان واژگانِ intent._LEG_ALIASES؛ ابهام (۰ یا ۲+) ⇒ None.
_LEG_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lead", ("lead", "لید", "نقاش", "نقاشی")),
    ("ziman", ("ziman", "گالری", "gallery", "زیمان")),
    ("mining", ("mining", "ماینینگ")),
    ("crypto", ("crypto", "کریپتو", "etoro", "ایتورو")),
    ("accounting", ("accounting", "حسابداری", "اکانتینگ")),
    ("studio_pf", ("studio", "استودیو", "پروژه اف")),
    ("knowledge", ("knowledge", "دانش")),
    ("cartographer", ("cartographer", "نقشه‌بردار", "نقشه بردار")),
    ("system", ("سیستم", "system")),
)

_LEG_FA = {"lead": "نقاشی", "ziman": "زیمان", "mining": "ماینینگ",
           "crypto": "کریپتو", "accounting": "حسابداری",
           "studio_pf": "استودیو", "knowledge": "دانش",
           "cartographer": "نقشه‌بردار", "system": "سیستم"}

# پای شناخته → شناسنامهٔ پروژه (برای کلیدِ project ِ فرانت‌متر).
_LEG_PROJECT = {
    "lead": "03 - Projects/Lead-نقاشی/PROJECT",
    "ziman": "03 - Projects/Ziman Galerry/PROJECT",
    "mining": "03 - Projects/Mining/PROJECT",
    "crypto": "03 - Projects/Crypto - etoro/PROJECT",
    "accounting": "03 - Projects/Accounting/PROJECT",
    "studio_pf": "03 - Projects/اونلی فنز/PROJECT",
}


def _detect_leg(text: str) -> "str | None":
    low = str(text or "").lower()
    hits = []
    for key, needles in _LEG_ALIASES:
        for n in needles:
            if (n.lower() in low) if n.isascii() else (n in low):
                hits.append(key)
                break
    return hits[0] if len(hits) == 1 else None


def _find_when(text: str) -> "str | None":
    m = _WHEN.search(str(text or ""))
    return m.group(1).strip() if m else None


def _summary(text: str, media_kind: "str | None") -> str:
    first = str(text or "").strip().splitlines()[0].strip() if str(text or "").strip() else ""
    if not first and media_kind:
        first = f"[{media_kind}]"
    return (first or "capture")[:80]


def _llm_refine(out: dict, text: str, ask_fn) -> dict:
    """پالایشِ اختیاری — فقط فلگ+ask_fn؛ خطا/جوابِ بد ⇒ همان طبقه‌بندِ $0."""
    if not (_flag_on(FLAG_CAPTURE_LLM) and callable(ask_fn)):
        return out
    try:
        prompt = ("پیامِ مالک را طبقه‌بندی کن. فقط JSON بده: "
                  '{"kind": "task|lead|idea|expense|note", "leg": null|str, '
                  '"summary": str}\nپیام: ' + str(text or "")[:400])
        ans = str(ask_fn("tg_capture", prompt) or "")
        m = re.search(r"\{.*\}", ans, re.S)
        data = json.loads(m.group(0)) if m else {}
        if data.get("kind") in KINDS:
            out["kind"] = data["kind"]
        if data.get("leg") in _LEG_FA:
            out["leg"] = data["leg"]
        if isinstance(data.get("summary"), str) and data["summary"].strip():
            out["summary"] = data["summary"].strip()[:80]
    except Exception:  # noqa: BLE001 — پالایش هرگز مسیرِ $0 را نمی‌کشد
        pass
    return out


def classify(text: str, *, media_kind: "str | None" = None,
             ask_fn=None) -> dict:
    """متنِ آزاد → {kind, leg, when, summary(+phone)}. خالص و قطعی؛ $0."""
    raw = str(text or "").strip()
    norm = raw.translate(_EN)
    leg = _detect_leg(raw)
    when = _find_when(raw)
    phone_m = _PHONE.search(norm)
    phone = phone_m.group(0).strip() if phone_m else None

    if any(k in raw for k in _EXPENSE_KW):
        kind = "lead" if "لید" in raw else "expense"
    elif ("لید" in raw
          or (phone and ("مشتری" in raw or "نقاش" in raw or leg == "lead"))
          or ("مشتری" in raw and not _TASK.search(raw))):
        kind = "lead"
    elif any(k in raw for k in _IDEA_KW):
        kind = "idea"
    elif _TASK.search(raw):
        kind = "task"
    else:
        kind = "note"
    if kind == "lead" and leg is None:
        leg = "lead"                     # لید فقط تاپیکِ 🎨نقاشی (منشور §۵)

    out = {"kind": kind, "leg": leg, "when": when,
           "summary": _summary(raw, media_kind)}
    if phone:
        out["phone"] = phone
    return _llm_refine(out, raw, ask_fn)


# ── بایگانی در vault (قانونِ اساسی §۳/۵/۶/۹) ────────────────────────────────
def _vault_root(vault_root) -> Path:
    if vault_root:
        return Path(str(vault_root))
    env = os.environ.get("ORG_ROOT", "").strip()
    if env:
        return Path(env)
    raise ValueError("vault_root نامشخص: نه پارامتر، نه env ORG_ROOT")


def _slug(text: str) -> str:
    s = re.sub(r'[<>:"/\\|?*#\[\]\r\n]+', " ", str(text or ""))
    s = re.sub(r"\s+", " ", s).strip()[:40].rstrip(" .")
    return s or "capture"


def _find_duplicate(root: Path, message_id, chat_id) -> "Path | None":
    """§۹: ‏message_id در محدودهٔ همان chat_id — بود ⇒ skip (idempotent)."""
    if message_id is None:
        return None
    base = root / RAW_SUBDIR[0]
    if not base.exists():
        return None
    mid_line = f"message_id: {message_id}"
    cid_line = f"chat_id: {chat_id}"
    for p in base.rglob("*.md"):
        try:
            body = p.read_text("utf-8", errors="ignore")
        except OSError:
            continue
        if mid_line in body and cid_line in body:
            return p
    return None


def _template_hint(root: Path) -> str:
    """اسکلت از `_Templates/log.md` اگر بود (سطرِ راهنمای append-only)."""
    try:
        txt = (root / "_Templates" / "log.md").read_text("utf-8")
        for line in txt.splitlines():
            if line.startswith(">"):
                return line
    except OSError:
        pass
    return ""


def _note_text(kind_result: dict, raw_text: str, *, msg_meta: dict,
               day: str, root: Path) -> str:
    kind = kind_result.get("kind") or "note"
    leg = kind_result.get("leg")
    status = "idea" if kind == "idea" else "active"
    proj = _LEG_PROJECT.get(leg or "")
    lines = ["---",
             "type: telegram-log",
             f'project: "[[{proj}]]"' if proj else 'project: ""',
             f"status: {status}",
             "tags: [telegram]",
             f"created: {day}",
             f"updated: {day}",
             f"message_id: {msg_meta.get('message_id')}",
             f"chat_id: {msg_meta.get('chat_id')}"]
    if msg_meta.get("file_id"):
        lines.append(f"file_id: {msg_meta['file_id']}")
    if msg_meta.get("duration") is not None:
        lines.append(f"duration: {msg_meta['duration']}")
    lines.append("---")
    hint = _template_hint(root)
    body = ["", f"# {kind_result.get('summary') or 'capture'}", ""]
    if hint:
        body += [hint, ""]
    body += [str(raw_text or "").strip() or "(بدون متن)", "",
             f"- منبع: تلگرام · chat_id: {msg_meta.get('chat_id')} · "
             f"message_id: {msg_meta.get('message_id')}"
             + (f" · [{msg_meta['media']}]" if msg_meta.get("media") else ""),
             ""]
    return "\n".join(lines + body)


def file_to_vault(kind_result: dict, raw_text: str, *, msg_meta: dict,
                  now: "float | None" = None, vault_root=None) -> dict:
    """نوتِ خامِ capture — همیشه اول این نوشته می‌شود (Inbox-اول §۳).

    نام: `YYYY-MM-DD HHmm <slug>.md` (§۵ — capture ِ ماشینی)؛ نوشتن atomic
    ‏(tmp + os.replace). تکراری ⇒ {"dup": True} و هیچ فایلِ دومی."""
    root = _vault_root(vault_root)
    now = float(now if now is not None else time.time())
    dup = _find_duplicate(root, msg_meta.get("message_id"),
                          msg_meta.get("chat_id"))
    if dup is not None:
        return {"path": str(dup), "ack": "تکراری — قبلاً ثبت شده",
                "dup": True}
    ts = time.localtime(now)
    stamp = time.strftime("%Y-%m-%d %H%M", ts)
    day = time.strftime("%Y-%m-%d", ts)
    raw_dir = root.joinpath(*RAW_SUBDIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    name = f"{stamp} {_slug(kind_result.get('summary') or raw_text)}.md"
    p = raw_dir / name
    if p.exists():                       # همان دقیقه، همان slug — تصادمِ نادر
        p = raw_dir / (f"{stamp} {_slug(kind_result.get('summary') or raw_text)}"
                       f" m{msg_meta.get('message_id')}.md")
    tmp = p.with_suffix(".md.tmp")
    tmp.write_text(_note_text(kind_result, raw_text, msg_meta=msg_meta,
                              day=day, root=root), "utf-8")
    os.replace(tmp, p)
    return {"path": str(p), "ack": "ثبت شد ✅", "dup": False}


def _set_note_status_idea(note_path: str) -> None:
    """کارِ شخصیِ بی‌موتورِ یادآور: نوت با status: idea در Raw می‌ماند (§۴e)."""
    try:
        p = Path(note_path)
        txt = p.read_text("utf-8")
        txt = txt.replace("status: active", "status: idea", 1)
        tmp = p.with_suffix(".md.tmp")
        tmp.write_text(txt, "utf-8")
        os.replace(tmp, p)
    except OSError:
        pass


def _one_line(ack: str) -> str:
    a = re.sub(r"\s*\n\s*", " · ", str(ack or "").strip())
    return a[:120].translate(_FA)


# ── مسیریابی (درختِ تصمیمِ §۴) ──────────────────────────────────────────────
def route(kind_result: dict, raw_note_path: str, *, leg_tasks_mod=None,
          reminder_add_fn=None, lead_submit_fn=None,
          now: "float | None" = None) -> dict:
    """نوتِ خام نوشته شده؛ حالا شاخهٔ درختِ تصمیم + ‏ack ِ یک‌خطی.

    قراردادِ callbackهای تزریقی (لِین‌های خواهر بعداً سیم می‌کنند):
      reminder_add_fn(text: str, when: str|None) -> هرچیز؛ None ⇒ موتور نیست
      lead_submit_fn(payload: dict) -> هرچیز؛ payload حتماً
        channel="telegram_manual" دارد (consented_inbound — فایروال دست‌نخورده)
    """
    kind = kind_result.get("kind") or "note"
    leg = kind_result.get("leg")
    when = kind_result.get("when")
    summary = kind_result.get("summary") or ""

    if kind == "task" and leg:
        mod = leg_tasks_mod
        if mod is None:
            try:
                if str(_HERE) not in sys.path:
                    sys.path.insert(0, str(_HERE))
                import leg_tasks as mod  # noqa: PLC0415
            except Exception:  # noqa: BLE001
                mod = None
        if mod is not None:
            mod.add(leg, summary, now=now)
            ack = f"ثبت شد ✅ کار → پای {_LEG_FA.get(leg, leg)}"
            if when and callable(reminder_add_fn):
                reminder_add_fn(summary, when)
                ack += f" + یادآوری {when}"
            return {"routed": "leg-task", "ack": _one_line(ack)}
        _set_note_status_idea(raw_note_path)
        return {"routed": "raw-idea",
                "ack": _one_line(f"ثبت شد ✅ کار → پای {_LEG_FA.get(leg, leg)}"
                                 " (صفِ پا هنوز وصل نیست)")}

    if kind == "task":
        if callable(reminder_add_fn):
            reminder_add_fn(summary, when)
            ack = "ثبت شد ✅ کار شخصی + یادآوری " + (when or "بدون زمان")
            return {"routed": "reminder", "ack": _one_line(ack)}
        _set_note_status_idea(raw_note_path)
        return {"routed": "raw-idea",
                "ack": _one_line("ثبت شد ✅ کار شخصی — در Inbox تلگرام "
                                 "(یادآور هنوز وصل نیست)")}

    if kind == "lead":
        if callable(lead_submit_fn):
            lead_submit_fn({"channel": "telegram_manual",
                            "summary": summary,
                            "phone": kind_result.get("phone"),
                            "source_note": str(raw_note_path)})
            return {"routed": "lead-inbox",
                    "ack": _one_line("ثبت شد ✅ لید → تاپیک 🎨نقاشی")}
        return {"routed": "raw-lead",
                "ack": _one_line("ثبت شد ✅ لید — صفِ لید هنوز وصل نیست")}

    if kind == "expense":
        try:
            day = time.strftime("%Y-%m-%d", time.localtime(
                float(now if now is not None else time.time())))
            with Path(raw_note_path).open("a", encoding="utf-8") as f:
                f.write(f"- {day} هزینه: {summary}\n")
        except OSError:
            pass
        return {"routed": "expense-line",
                "ack": _one_line("ثبت شد ✅ هزینه → مرور هفتگی حسابداری")}

    if kind == "idea":
        return {"routed": "raw-note",
                "ack": _one_line("ثبت شد ✅ ایده → Inbox تلگرام")}
    return {"routed": "raw-note", "ack": _one_line("ثبت شد ✅ نوت")}


# ── نقطهٔ ورودِ سیم‌کشی ─────────────────────────────────────────────────────
def _media_kind(msg: dict, text: str) -> "str | None":
    if msg.get("voice"):
        return "voice"
    if msg.get("photo"):
        return "photo"
    if msg.get("document"):
        return "document"
    if msg.get("video"):
        return "video"
    for e in msg.get("entities") or []:
        if e.get("type") in ("url", "text_link"):
            return "link"
    if _URL.search(str(text or "")):
        return "link"
    return None


def handle(update_msg: dict, *, deps: "dict | None" = None) -> dict:
    """تنها ورودیِ لِینِ سیم‌کشی برای پیامِ DM ِ مالک.

    deps (همه اختیاری): now / vault_root / ask_fn / leg_tasks_mod /
    reminder_add_fn / lead_submit_fn. فلگ خاموش ⇒ دستِ‌نخورده (fail-closed).
    """
    deps = deps or {}
    if not _flag_on(FLAG_CAPTURE):
        return {"handled": False, "ack": ""}
    msg = dict(update_msg or {})
    text = str(msg.get("text") or msg.get("caption") or "")
    media = _media_kind(msg, text)
    meta = {"message_id": msg.get("message_id"),
            "chat_id": (msg.get("chat") or {}).get("id"),
            "media": media}

    if media == "voice":
        v = msg.get("voice") or {}
        meta["file_id"] = v.get("file_id")
        meta["duration"] = v.get("duration")
        kr = {"kind": "note", "leg": None, "when": None,
              "summary": ("[voice] " + text).strip()[:80]}
        filed = file_to_vault(kr, text, msg_meta=meta, now=deps.get("now"),
                              vault_root=deps.get("vault_root"))
        if filed.get("dup"):
            return {"handled": True, "dup": True, "kind": "note",
                    "path": filed["path"], "ack": _one_line(filed["ack"])}
        return {"handled": True, "kind": "note", "path": filed["path"],
                "routed": "raw-note",
                "ack": _one_line("ویس ثبت شد ✅ متن‌سازی هنوز نصب نیست")}

    kr = classify(text, media_kind=media, ask_fn=deps.get("ask_fn"))
    filed = file_to_vault(kr, text, msg_meta=meta, now=deps.get("now"),
                          vault_root=deps.get("vault_root"))
    if filed.get("dup"):
        return {"handled": True, "dup": True, "kind": kr["kind"],
                "path": filed["path"], "ack": _one_line(filed["ack"])}
    r = route(kr, filed["path"], leg_tasks_mod=deps.get("leg_tasks_mod"),
              reminder_add_fn=deps.get("reminder_add_fn"),
              lead_submit_fn=deps.get("lead_submit_fn"), now=deps.get("now"))
    return {"handled": True, "kind": kr["kind"], "path": filed["path"],
            "routed": r["routed"], "ack": r["ack"]}
