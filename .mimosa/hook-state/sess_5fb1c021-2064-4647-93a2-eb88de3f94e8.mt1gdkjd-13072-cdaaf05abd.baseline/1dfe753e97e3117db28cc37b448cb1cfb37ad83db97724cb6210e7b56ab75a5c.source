#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""propose.py — دستِ دکتر: از تشخیصِ نثری به **پچِ اجراشدنی**.

این حلقهٔ گمشده بود. تا دیروز دکتر می‌دید (`scanner`)، می‌فهمید (`vault` + `fugu`)،
و می‌توانست ایزوله اجرا کند (`mission_runner`) — ولی بینِ «فهمید» و «اجرا کرد»
هیچ چیزی نبود جز نثر. نثر را نمی‌شود apply کرد.

`propose` مغز را وادار می‌کند به‌جای پاراگراف، **JSONِ ساختاریافته** بدهد، و بعد آن
JSON را از هفت گیتِ ایمنی رد می‌کند — گیت‌هایی که **در کد** اجرا می‌شوند، نه در پرامپت.
پرامپت را می‌شود دور زد؛ `if` را نه.

    تشخیص ⟶ propose ⟶ [۷ گیت] ⟶ callable ⟶ MissionRunner(worktree) ⟶ کارت ⟶ رأی ⟶ merge

هیچ‌جای این ماژول چیزی روی دیسک نمی‌نویسد. خروجی‌اش یک **تابع** است که
`MissionRunner` آن را داخلِ worktreeِ ایزوله صدا می‌زند — و بس.

stdlib-only.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

__all__ = ["Patch", "PatchSet", "PROPOSE_SYSTEM", "parse_patchset",
           "GateError", "DENY", "MAX_FILES"]

# ---------------------------------------------------------------- خطِ قرمز
# چیزهایی که هیچ پچی حق لمسشان را ندارد. این فهرست از منشورِ خودِ مخزن می‌آید و
# **در کد** اجرا می‌شود، نه در متنِ پرامپت — چون مدل متن را می‌تواند نادیده بگیرد.
DENY = (
    ".env", "flags.cmd", "octopus-flags",
    "_ops/state/",            # حالتِ زنده — دادهٔ ارگانیسم، نه کدش
    "genome", "ledger", "budget", "kill", "stop-organism",
    ".git/", "_worktrees/", "_archive/", "_duplicates/",
    "project-f", "پروژه-اف",
)
MAX_FILES = 6                 # پچی که به بیش از این دست بزند، ماموریت نیست — بازنویسی است
MAX_BYTES = 40_000            # سقفِ اندازهٔ کلِ تغییر

# ساختنِ فایلِ نو (مثلاً «یک پا اضافه کن») مجاز است — ولی فقط در این پوشه‌ها.
# بیرونِ این‌ها، «فایلِ نو» یعنی کاشتنِ کدِ اجراییِ ناشناس در جایی که کسی نگاهش نمی‌کند.
CREATE_ALLOW = ("_ops/legs/", "_ops/organs/", "_ops/tools/", "_ops/os_v1/",
                "OCTOPUS-DOCTOR/")

# ═══════════════════════ حریم (Sanctum) — گیتِ ۹ ═══════════════════════
# این‌ها ممنوع نیستند (باید بتوانند تکامل پیدا کنند) ولی **شاهد را می‌سازند**،
# پس تغییرشان با رأیِ عادی کافی نیست.
#
# چرا اضافه شد — و این را از تحقیق فهمیدم، نه از فکرِ خودم:
# مقالهٔ Darwin Gödel Machine (Sakana، ۲۰۲۵) دو حالتِ شکستِ **مشاهده‌شده** گزارش می‌کند
# که هر دو دقیقاً روی معماریِ من می‌نشستند:
#   ۱ ایجنت **لاگِ اجرای تست را جعل کرد** — «فقط یک لاگِ قلابی می‌سازد که انگار
#     تست‌ها اجرا شده و همه سبزند»، در حالی که اصلاً اجرا نشده بودند.
#   ۲ وقتی گفتند «توهم را کم کن»، **نشانگرهای تشخیصِ توهم را حذف کرد** —
#     یعنی به‌جای حلِ مسئله، سنجه را خراب کرد.
#
# ترجمهٔ این دو به سیستمِ من:
#   · پچی که `_ops/tests/` را عوض کند، می‌تواند سوئیت را همیشه‌سبز کند ⇒ گیتِ من بی‌اثر
#   · پچی که خودِ `propose.py` یا `policy_sampler.py` را عوض کند، می‌تواند
#     گیت‌ها را بردارد ⇒ سیستم گاردِ خودش را خاموش می‌کند
# هیچ‌کدام در فهرستِ DENY نبودند. این یک **سوراخِ واقعی** بود.
SANCTUM = (
    "/tests/", "test_", "run_all.py", "conftest.py",     # شاهد
    "propose.py", "policy_sampler.py", "honest_metric.py",
    "mission_runner.py", "efe.py", "router.py", "channel.py",
    "daemon.py", "outcome_ledger.py",                    # خودِ گاردها
    "10-قوانین/", "R-0",                                 # قوانین
)

PROPOSE_SYSTEM = """تو «دکترِ اختاپوس» هستی و باید یک تغییرِ کدِ **کوچک و قابلِ‌بازگشت** پیشنهاد بدهی.

خروجیِ تو **فقط** یک آبجکتِ JSON است. هیچ متنی قبل یا بعدش ننویس. بدونِ ```.

شِما:
{
  "mission_id": "kebab-case-کوتاه",
  "title": "یک جمله، فارسی",
  "rationale": "چرا این تغییر — با ارجاع به شاهدِ واقعی، نه حدس",
  "risk": "low" | "medium" | "high",
  "rollback": "اگر بد شد چطور برگردانده می‌شود",
  "patches": [
    {
      "file": "مسیرِ نسبی با اسلشِ رو به جلو، از ریشهٔ مخزن",
      "anchor": "متنِ **دقیقاً** موجود در فایل که باید جایگزین شود",
      "replacement": "متنِ جایگزین",
      "why": "این یک تکه چه چیزی را عوض می‌کند",
      "create": false
    }
  ]
}

برای **ساختنِ فایلِ نو** (مثلاً افزودنِ یک «پا»/لِگ): `"create": true` بگذار،
`"anchor"` را خالی بگذار، و کلِ محتوای فایل را در `"replacement"` بنویس.
ساختِ فایل فقط در این مسیرها مجاز است: `_ops/legs/` · `_ops/organs/` · `_ops/tools/`.
فایلی که از قبل وجود دارد را با `create` بازنویسی نکن — آن پچِ عادی است با لنگر.

قواعدی که رعایتشان اجباری است:
1. `anchor` باید در فایل **دقیقاً یک بار** بیاید. اگر مطمئن نیستی، تکهٔ بزرگ‌تری
   بردار تا یکتا شود. لنگرِ مبهم ⇒ کلِ ماموریت رد می‌شود.
2. فاصله، تورفتگی و پایانِ‌خط را عیناً حفظ کن. یک فاصلهٔ اضافه یعنی رد.
3. حداکثر شش فایل. کمتر بهتر.
4. هرگز به این‌ها دست نزن: فایل‌های راز/توکن، `_ops/state/`، دفترِ ژنوم، بودجه،
   کلیدِ توقف، `.git`. اگر تشخیصت این‌ها را لازم دارد، به‌جای پچ در `rationale`
   بنویس چرا و هیچ پچی نده.
5. **افزایشی باش.** ترجیحِ اول: افزودنِ کد پشتِ flag با شکستِ نرم. بازنویسیِ رفتارِ
   موجود فقط وقتی که راهِ دیگری نباشد.
6. اگر شاهدِ کافی نداری، `patches` را خالی بگذار و در `rationale` بنویس
   `[UNKNOWN]` و اینکه چه شاهدی لازم داری. **پیشنهادِ حدسی از پیشنهاد ندادن بدتر است.**
"""


class GateError(ValueError):
    """پچ از یکی از گیت‌ها رد نشد. پیام دقیقاً می‌گوید کدام."""


@dataclass(frozen=True)
class Patch:
    file: str
    anchor: str
    replacement: str
    why: str = ""
    create: bool = False          # فایلِ نو: `anchor` خالی، `replacement` = کلِ محتوا

    @property
    def delta_bytes(self) -> int:
        if self.create:
            return len(self.replacement.encode())
        return abs(len(self.replacement.encode()) - len(self.anchor.encode()))


@dataclass
class PatchSet:
    mission_id: str
    title: str
    rationale: str
    patches: list[Patch] = field(default_factory=list)
    risk: str = "medium"
    rollback: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.patches

    # ------------------------------------------------------------- حریم
    @property
    def sanctum_files(self) -> list[str]:
        """فایل‌هایی که **شاهد را می‌سازند یا گارد را اجرا می‌کنند**."""
        out = []
        for p in self.patches:
            low = (p.file or "").replace("\\", "/").lower()
            if any(s.lower() in low for s in SANCTUM):
                out.append(p.file)
        return sorted(set(out))

    @property
    def touches_sanctum(self) -> bool:
        return bool(self.sanctum_files)

    # ------------------------------------------------------------- گیت‌ها
    def gate(self, allow_sanctum: bool = False) -> None:
        """نُه گیت. هرکدام رد شد، استثنا — نه هشدارِ بی‌صدا.

        `allow_sanctum` را **فقط مالک** می‌تواند بدهد، و فقط بعد از دیدنِ دیفِ کامل.
        """
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,48}", self.mission_id or ""):
            raise GateError(f"گیت ۱ — mission_id نامعتبر: {self.mission_id!r}")
        if self.empty:
            raise GateError("گیت ۲ — هیچ پچی نیست (این خطا نیست؛ یعنی مغز شاهد نداشت)")
        if len({p.file for p in self.patches}) > MAX_FILES:
            raise GateError(f"گیت ۳ — بیش از {MAX_FILES} فایل: "
                            f"{len({p.file for p in self.patches})}")
        if self.touches_sanctum and not allow_sanctum:
            raise GateError(
                "گیت ۹ — حریم: این پچ به فایلی دست می‌زند که **شاهد را می‌سازد یا "
                f"گارد را اجرا می‌کند**: {self.sanctum_files[:3]}. "
                "رأیِ عادی کافی نیست — مالک باید دیفِ کامل را ببیند و صریح اجازه بدهد. "
                "(دلیل: DGM ثابت کرد ایجنت سوئیت را همیشه‌سبز و گاردِ خودش را خاموش می‌کند)")
        total = sum(p.delta_bytes for p in self.patches)
        if total > MAX_BYTES:
            raise GateError(f"گیت ۴ — تغییر خیلی بزرگ است: {total} بایت")
        for p in self.patches:
            f = (p.file or "").replace("\\", "/").strip()
            if not f:
                raise GateError("گیت ۵ — مسیرِ خالی")
            pp = PurePosixPath(f)
            if pp.is_absolute() or ".." in pp.parts or f.startswith("/") or ":" in f:
                raise GateError(f"گیت ۵ — مسیرِ خطرناک: {f!r}")
            low = f.lower()
            for d in DENY:
                if d in low:
                    raise GateError(f"گیت ۶ — خطِ قرمز «{d}» در {f!r}")
            if p.create:
                if p.anchor:
                    raise GateError(f"گیت ۷ — فایلِ نو نباید لنگر داشته باشد: {f!r}")
                if not p.replacement.strip():
                    raise GateError(f"گیت ۷ — فایلِ نو خالی است: {f!r}")
                if not any(low.startswith(a.lower()) or a.lower() in low
                           for a in CREATE_ALLOW):
                    raise GateError(
                        f"گیت ۸ — ساختِ فایلِ نو فقط در {CREATE_ALLOW} مجاز است، نه {f!r}")
                continue
            if not p.anchor:
                raise GateError(f"گیت ۷ — لنگرِ خالی در {f!r} (اگر فایلِ نو است، create=true)")
            if p.anchor == p.replacement:
                raise GateError(f"گیت ۷ — پچِ بی‌اثر در {f!r}")

    # ---------------------------------------------------- ساختِ callable
    def as_apply(self, allow_sanctum: bool = False):
        """تابعی که `MissionRunner` داخلِ worktree صدا می‌زند.

        هر شکستی استثنا می‌دهد ⇒ `MissionRunner` ماموریت را قرمز می‌کند و
        worktree را پاک می‌کند. **صفر بایت** روی درختِ زنده.
        """
        self.gate(allow_sanctum=allow_sanctum)

        def apply_patch(root: Path) -> None:
            root = Path(root).resolve()
            for p in self.patches:
                target = (root / p.file.replace("\\", "/")).resolve()
                if not str(target).startswith(str(root)):
                    raise GateError(f"فرار از ریشه: {p.file!r}")
                if p.create:
                    if target.exists():
                        raise GateError(f"فایل از قبل هست — «ساختن» بازنویسی نیست: {p.file}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(p.replacement, encoding="utf-8", newline="")
                    continue
                if not target.exists():
                    raise GateError(f"فایل وجود ندارد: {p.file}")
                txt = target.read_text("utf-8")
                n = txt.count(p.anchor)
                if n == 0:
                    raise GateError(f"لنگر پیدا نشد در {p.file} — "
                                    "شاید فاصله/تورفتگی فرق دارد")
                if n > 1:
                    raise GateError(f"لنگر {n} بار در {p.file} تکرار شده — مبهم است")
                target.write_text(txt.replace(p.anchor, p.replacement, 1),
                                  encoding="utf-8", newline="")
        return apply_patch

    # -------------------------------------------------------------- کارت
    def card(self) -> str:
        """کارتِ ۱ — گیتِ نیت. قبل از هر اجرایی به مالک نشان داده می‌شود."""
        head = (f"🩺 پیشنهادِ ماموریت — `{self.mission_id}`\n"
                f"**{self.title}**\nریسک: {self.risk}\n\n{self.rationale}\n")
        if self.empty:
            return head + "\n_هیچ پچی پیشنهاد نشد — شاهد کافی نبود._"
        body = "\n".join(f"· `{p.file}` — {p.why or '—'}" for p in self.patches[:MAX_FILES])
        return head + f"\nتغییرات ({len(self.patches)} تکه):\n{body}\n\nبازگشت: {self.rollback or '—'}"


# ------------------------------------------------------------------- parse
_FENCE = re.compile(r"```(?:json)?\s*(.+?)```", re.S)


def parse_patchset(text: str) -> PatchSet:
    """JSONِ مغز ⟶ PatchSet. مدل ممکن است داخلِ ``` بگذارد؛ می‌بریم و می‌خوانیم."""
    if not text or not text.strip():
        raise GateError("پاسخِ خالی از مغز")
    raw = text.strip()
    # ۲۹ جولای، از اولین request واقعی: مدل گاهی JSON را لای متن/فنسِ ناقص می‌پیچد و
    # «اولین { تا آخرین }» بازهٔ نامعتبر می‌گیرد. همان درسِ extract_json ارگانیسم
    # (392addf «extract_json robust»): چند کاندید بساز — هر فنس + هر بازهٔ آکولادِ
    # متوازن (با احترام به رشته‌ها) — و اولین دیکتِ معتبرِ مأموریت‌نما را بردار.
    candidates = [m.group(1).strip() for m in _FENCE.finditer(raw)]
    for i in [k for k, ch in enumerate(raw) if ch == "{"][:20]:
        depth, in_str, esc = 0, False, False
        for j in range(i, len(raw)):
            ch = raw[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(raw[i:j + 1])
                    break
    d, last_err = None, "پاسخ هیچ بلوکِ JSON نداشت"
    for cand in sorted(set(candidates), key=len, reverse=True):
        try:
            obj = json.loads(cand)
        except ValueError as e:
            last_err = str(e)
            continue
        if isinstance(obj, dict) and ("patches" in obj or "mission_id" in obj):
            d = obj
            break
    if d is None:
        raise GateError(f"JSON معتبر نیست: {last_err}")
    ps = PatchSet(
        mission_id=str(d.get("mission_id", "")).strip(),
        title=str(d.get("title", "")).strip(),
        rationale=str(d.get("rationale", "")).strip(),
        risk=str(d.get("risk", "medium")).strip() or "medium",
        rollback=str(d.get("rollback", "")).strip(),
    )
    for it in (d.get("patches") or []):
        if not isinstance(it, dict):
            raise GateError("عضوِ patches آبجکت نیست")
        f = str(it.get("file", ""))
        anchor = str(it.get("anchor", ""))
        repl = str(it.get("replacement", ""))
        # ۲۹ جولای: پارسر فیلدِ create را نمی‌خواند و همیشه False می‌ساخت — دو request
        # واقعی بی‌دلیل پشتِ گیتِ ۷ سوخت. حالا خوانده می‌شود؛ و نرمال‌سازیِ بی‌ابهام:
        # لنگرِ خالی + مسیرِ داخلِ CREATE_ALLOW + محتوای غیرخالی = فایلِ نو.
        # گیت‌های ۵/۶/۸ و چکِ «فایل از قبل هست — بازنویسی نیست» همچنان حاکم‌اند.
        create = bool(it.get("create", False))
        if not create and not anchor.strip() and repl.strip():
            low = f.replace("\\", "/").strip().lower()
            if any(low.startswith(a.lower()) for a in CREATE_ALLOW):
                create = True
        ps.patches.append(Patch(
            file=f,
            anchor=anchor,
            replacement=repl,
            why=str(it.get("why", "")),
            create=create,
        ))
    if "[UNKNOWN]" in ps.rationale:
        ps.notes.append("مغز صریحاً گفت شاهد کافی ندارد")
    return ps
