#!/usr/bin/env python3
"""self_scan — آنچه ارگانیسم دربارهٔ **خودش** نمی‌داند.

جایگاه در میانِ ابزارهای موجود (هیچ‌کدام دوباره‌کاری نمی‌شود)
────────────────────────────────────────────────────────────
    orphan_scan.py          «کدام ماژول به هیچ‌چیز وصل نیست؟»   (سطحِ ماژول)
    doctor/self_knowledge   «حالم چطور است و ریشه‌اش چیست؟»      (LLM، تشخیصی)
    coherence.py            «آیا ادعاهایم ابطال‌پذیرند؟»          (صداقت)
    capability_registry     «چه چیزی می‌توانم به مالک نشان دهم؟»
    flag_drift.py           «مسلح در برابرِ بارگذاری‌شده»
    tg_send_audit.py        «پیام‌ها به کجا می‌روند؟»
    dark_capabilities.py    «کدام قابلیت کد دارد و در هر پروسه نمی‌دود؟»

    self_scan.py  ← این‌جا: **پنج شکافی که هیچ‌کدامِ بالا نمی‌بیند**

⚠️ همپوشانیِ صادقانه با `dark_capabilities` (۲۰۲۶-۰۸-۰۱): پرسشِ F ِ این فایل
(«مسلح ولی بی‌خواننده») همان پرسشِ `orphan_armed` آن‌جاست و هر دو امروز عددِ
یکسان می‌دهند — که خودش شاهدِ متقاطع است، نه دوباره‌کاری. تفاوتِ واقعی این است
که آن‌جا حکم از snapshotِ بوتِ **هر پروسه** می‌آید، پس حالتِ «در center روشن،
در organism خاموش» را می‌بیند و این‌جا نمی‌شود دید؛ و دروازه را از پارامترِ
تنظیمی جدا می‌کند. اگر روزی اعدادشان واگرا شدند، یکی از دو اسکنر شکسته است.

پنج پرسشِ این ماژول
───────────────────
 F  فلگ‌های تاریک   کدام فلگ در فایل مسلح است ولی هیچ خطِ کدی نمی‌خواندش؟
                     و کدام فلگ در کد خوانده می‌شود ولی هرگز تعریف نشده؟
 S  حالتِ یتیم       کدام فایلِ state روی دیسک هست که هیچ ماژولی نامش را نمی‌برد؟
                     و کدام فقط **یک** ارجاع دارد (امضایِ «نوشته می‌شود، خوانده نه»)؟
 T  ماژولِ بی‌تست    کدام ماژول هیچ فایلِ تستی به آن اشاره نمی‌کند؟
 M  نشانهٔ ناتمام    TODO / FIXME / جای‌نگه‌دار که در کدِ زنده جا مانده.
 Y  نمادِ مرده       تابع/کلاسِ عمومی که هیچ فایلِ دیگری نامش را نمی‌برد.

چرا **نمرهٔ واحد** نمی‌دهد
──────────────────────────
یک عددِ مرکب («۸۷٪ خودآگاه») پنهان می‌کند که کدام بررسی چیزی پیدا نکرد چون
تمیز است و کدام‌یک چون خراب است. همان بیماریِ ادعایِ ابطال‌ناپذیر. پس شمارشِ
خام، به تفکیک، و هر یافته با «چه چیزی ابطالش می‌کند».

ناوردی‌ها: فقط‌خواندنی · stdlib · fail-soft · هرگز خارج از `_ops` را نمی‌خواند
(مسیرهای PII/Identity ساختاراً ممنوع‌اند، §۰ قاعدهٔ ۷).

اجرا:
    python _ops/self_scan.py                # کارتِ انسانی
    python _ops/self_scan.py --json
    python _ops/self_scan.py --only flags   # flags|state|tests|markers|symbols
"""
from __future__ import annotations

import ast
import json
import re
import sys
import time
from pathlib import Path

SCHEMA = "self-scan.v1"
CARD_TITLE = "خودشناسی — نقاطِ کور"

# ساختاراً ممنوع. حتی اگر کسی مسیر بدهد، این‌ها رد می‌شوند.
_FORBIDDEN_PARTS = ("08 - Partner (PII)", "Identity", ".git", "__pycache__",
                    "_code", "node_modules", ".venv")
_SKIP_DIRS = ("_Archive", "_Duplicates", ".pytest_cache",
              ".claude", "worktrees")  # ⚠️ ۰۸-۰۱: `.claude` = ۵.۵ GB و ۶۷k فایل در ۱۸ worktree (۹۶٪ رونوشت)

_FLAG_RE = re.compile(r"\b((?:OCTOPUS|PAID|FUGU|TELEGRAM)_[A-Z0-9_]{2,})\b")
_STATE_SUFFIXES = (".json", ".jsonl", ".db", ".txt", ".md", ".cursor", ".lock")
_MARKER_RE = re.compile(
    r"(?:^|\s|#)(TODO|FIXME|XXX|HACK|TBD|NOTIMPL|PLACEHOLDER)\b", re.I)
_PERSIAN_MARKER_RE = re.compile(r"(جای‌?نگه‌?دار|بعداً پر شود|هنوز پیاده نشده)")


def _safe(p: Path) -> bool:
    parts = set(p.parts)
    if any(f in parts for f in _FORBIDDEN_PARTS):
        return False
    return not any(d in parts for d in _SKIP_DIRS)


def py_files(root: Path, include_tests=True):
    for f in sorted(root.rglob("*.py")):
        if not _safe(f):
            continue
        if not include_tests and (f.name.startswith("test_") or "tests" in f.parts):
            continue
        yield f


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


class Corpus:
    """درخت را **یک‌بار** می‌خواند و **یک‌بار** پارس می‌کند.

    نسخهٔ اول هر بررسی درخت را از نو می‌خواند: پنج بررسی = پنج خواندنِ کامل،
    و `scan_symbols` جداگانه دوباره پارس می‌کرد. روی درختی که `wiring.py`ِ
    ۱۸۵ کیلوبایتی دارد این هزینهٔ واقعی است، و بدتر: هر بررسی می‌توانست
    **تصویرِ متفاوتی** از درخت ببیند اگر فایلی وسطِ اسکن عوض می‌شد — یعنی
    گزارشی که با خودش ناسازگار است. حالا هر پنج بررسی روی یک snapshot کار
    می‌کنند: هم سریع‌تر، هم درونی‌سازگار.
    """

    __slots__ = ("root", "_paths", "_text", "_tree", "_words", "_names",
                 "reads", "parses")

    _WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    # ترتیبِ alternation عمدی است: `jsonl` **قبل** از `json`. نسخهٔ اول
    # برعکس بود و هر `x.jsonl` را «x.json» ایندکس می‌کرد — یعنی هر فایلِ
    # jsonlِ state بی‌سروصدا «یتیم» گزارش می‌شد. تست گرفتش، نه چشم.
    _NAME_RE = re.compile(r"[\w\-.]+\.(?:jsonl|json|db|txt|md|cursor|lock)\b")

    def __init__(self, root: Path):
        self.root = Path(root)
        self._paths = [f for f in sorted(self.root.rglob("*.py")) if _safe(f)]
        self._text: dict = {}
        self._tree: dict = {}
        self._words: dict | None = None
        self._names: dict | None = None
        self.reads = 0
        self.parses = 0

    # ── ایندکسِ معکوس ─────────────────────────────────────────────────────
    # نسخهٔ اول برای هر نماد، **همهٔ** فایل‌ها را regex می‌زد: O(نماد × فایل ×
    # بایت). با ~۴۰۰ نمادِ عمومی و ۳۰۰ فایل یعنی صدها مگابایت اسکنِ تکراری.
    # حالا یک پاسِ regex روی هر فایل یک ایندکسِ معکوس می‌سازد و هر جست‌وجو
    # O(1) می‌شود. همان جواب، مرتبهٔ متفاوت.

    def _build_index(self):
        self._words, self._names = {}, {}
        for f in self._paths:
            txt = self.text(f)
            for w in set(self._WORD_RE.findall(txt)):
                self._words.setdefault(w, set()).add(f)
            for n in set(self._NAME_RE.findall(txt)):
                self._names.setdefault(n, set()).add(f)

    def files_with_word(self, word: str) -> set:
        if self._words is None:
            self._build_index()
        return self._words.get(word, set())

    def files_with_filename(self, name: str) -> set:
        if self._names is None:
            self._build_index()
        return self._names.get(name, set())

    def paths(self, include_tests=True):
        if include_tests:
            return list(self._paths)
        return [f for f in self._paths
                if not (f.name.startswith("test_") or "tests" in f.parts)]

    def text(self, p: Path) -> str:
        key = str(p)
        if key not in self._text:
            self._text[key] = _read(p)
            self.reads += 1
        return self._text[key]

    def tree(self, p: Path):
        key = str(p)
        if key not in self._tree:
            self.parses += 1
            try:
                self._tree[key] = ast.parse(self.text(p))
            except SyntaxError:
                self._tree[key] = None
        return self._tree[key]

    def items(self, include_tests=True):
        for f in self.paths(include_tests):
            yield f, self.text(f)

    @property
    def stats(self) -> dict:
        return {"files": len(self._paths), "reads": self.reads,
                "parses": self.parses,
                "bytes": sum(len(t) for t in self._text.values())}


def _corpus(root, corpus):
    return corpus if isinstance(corpus, Corpus) else Corpus(root)


def _env_defaults(tree) -> dict:
    """`os.environ.get("X", "1")` → {"X": "1"}. پیش‌فرضِ حاکم، نه حدس."""
    out = {}
    if tree is None:
        return out
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("get", "getenv")):
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        name = node.args[0].value
        if not isinstance(name, str) or not _FLAG_RE.fullmatch(name):
            continue
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            out[name] = node.args[1].value
        else:
            out.setdefault(name, "")
    return out


# ══════════════════════════════════════════════════════════════════════════
#  F — فلگ‌های تاریک
# ══════════════════════════════════════════════════════════════════════════

def scan_flags(root: Path, corpus=None) -> dict:
    """دو جهتِ تاریکی، و هرکدام معنایِ کاملاً متفاوتی دارد.

    · `armed_unread`  در فایل هست، هیچ کدی نمی‌خواندش → یا کدش حذف شده یا
                      نامش غلط تایپ شده. در هر دو حالت **بی‌اثرِ خاموش**.
    · `read_unarmed`  کد می‌خواندش، در فایل نیست → پیش‌فرضِ کد حاکم است و
                      مالک هرگز رأیی نداده. **بی‌اثرِ نامرئی** — بدتر.
    """
    flags_file = root / "OCTOPUS-flags.cmd"
    armed = {}
    parse_err = None
    if flags_file.exists():
        try:
            # پارسر از **کنارِ خودِ این ماژول** import می‌شود، نه از درختِ
            # اسکن‌شونده. نسخهٔ اول از `root` می‌خواندش و در تست باعث شد
            # `flag_drift.py` داخلِ درختِ آزمایشی کپی شود و نمادهای خودش
            # به‌عنوانِ «مردهٔ» آن درخت گزارش شوند — یعنی ابزار، ورودیِ خودش
            # را آلوده می‌کرد.
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import flag_drift as _fd            # همان پارسر، یک منبعِ حقیقت
            armed, _stats = _fd.parse_flags_file(flags_file)
            armed = {k: v for k, v in armed.items() if _FLAG_RE.fullmatch(k)}
        except Exception as exc:                # noqa: BLE001
            parse_err = f"{type(exc).__name__}: {exc}"
    cor = _corpus(root, corpus)
    in_code: dict[str, list] = {}
    defaults: dict[str, list] = {}
    for f, txt in cor.items():
        for name in set(_FLAG_RE.findall(txt)):
            in_code.setdefault(name, []).append(f.name)
        # پیش‌فرضی که در نبودِ فلگ **واقعاً حاکم است**. بدونِ این، «فلگ تعریف
        # نشده» یک اخطارِ انتزاعی است؛ با این، تبدیل می‌شود به «این رفتار همین
        # حالا روشن/خاموش است و تو رأی نداده‌ای».
        for name, dflt in _env_defaults(cor.tree(f)).items():
            defaults.setdefault(name, []).append({"module": f.name, "default": dflt})
    # رازها عمداً در `.env` زندگی می‌کنند نه در flags.cmd. شمردنشان به‌عنوانِ
    # «تعریف‌نشده» یک مثبتِ کاذبِ پرسروصداست — اولین اجرا `OCTOPUS_CB_SECRET` و
    # `TELEGRAM_BOT_TOKEN` را به‌اشتباه گزارش کرد.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from flag_drift import is_secret_name as _is_secret
    except Exception:  # noqa: BLE001
        def _is_secret(n):
            return any(t in n.upper() for t in ("SECRET", "TOKEN", "KEY", "PASS"))

    armed_unread = sorted(n for n in set(armed) - set(in_code)
                          if not _is_secret(n))
    read_unarmed = sorted(n for n in set(in_code) - set(armed)
                          if not _is_secret(n))
    secrets_skipped = sorted(n for n in set(armed) ^ set(in_code) if _is_secret(n))
    return {
        "flags_file_found": flags_file.exists(),
        "parse_error": parse_err,
        "armed": len(armed), "referenced_in_code": len(in_code),
        "matched": len(set(armed) & set(in_code)),
        "armed_unread": armed_unread,
        "read_unarmed": [{"flag": n, "modules": sorted(set(in_code[n]))[:4]}
                         for n in read_unarmed],
        "secrets_skipped": secrets_skipped,
        # فقط برای فلگ‌های تعریف‌نشده: «این رفتار همین حالا با این مقدار
        # کار می‌کند و تو رأیی نداده‌ای».
        "defaults": {n: defaults[n] for n in read_unarmed if n in defaults},
        "falsified_by": "اگر کدی نامِ فلگ را بسازد (concat یا getattr) این "
                        "ممیزی آن را نمی‌بیند — پس صفر بودن اثبات نیست. "
                        "و روی یک درختِ ناقص، `armed_unread` بی‌معناست: "
                        "«خواننده‌ای ندارد» با «فایلش اسکن نشده» یکی می‌شود.",
    }


# ══════════════════════════════════════════════════════════════════════════
#  S — حالتِ یتیم
# ══════════════════════════════════════════════════════════════════════════

def scan_state(root: Path, corpus=None) -> dict:
    """امضایِ «نوشته می‌شود، خوانده نمی‌شود».

    ایستا نمی‌شود مطمئن گفت چه کسی می‌خواند و چه کسی می‌نویسد. ولی **شمارشِ
    ارجاع** یک سیگنالِ تیز می‌دهد:
      · صفر ارجاع  → هیچ ماژولی حتی نامش را نمی‌برد. یتیمِ قطعی.
      · یک ارجاع   → فقط نویسنده‌اش می‌شناسدش. مصرف‌کننده ندارد.
                     (`tg-send-log.jsonl` دقیقاً همین بود تا امشب.)
    """
    state_dir = root / "state"
    files = []
    if state_dir.exists():
        for f in sorted(state_dir.rglob("*")):
            if f.is_file() and _safe(f) and f.suffix in _STATE_SUFFIXES:
                files.append(f)
    cor = _corpus(root, corpus)
    prod = set(cor.paths(include_tests=False))
    now = time.time()
    rows = []
    for f in files:
        name = f.name
        refs = sorted({q.name for q in cor.files_with_filename(name) & prod})
        try:
            st = f.stat()
            age_h = round((now - st.st_mtime) / 3600.0, 1)
            size = st.st_size
        except OSError:
            age_h, size = None, None
        rows.append({"file": str(f.relative_to(state_dir)), "refs": len(refs),
                     "by": refs[:4], "age_h": age_h, "bytes": size})
    orphan = [r for r in rows if r["refs"] == 0]
    single = [r for r in rows if r["refs"] == 1]
    return {
        "state_dir_found": state_dir.exists(),
        "files": len(rows),
        "orphan": sorted(orphan, key=lambda r: -(r["bytes"] or 0))[:30],
        "orphan_count": len(orphan),
        "single_referencer": sorted(single, key=lambda r: -(r["bytes"] or 0))[:30],
        "single_count": len(single),
        "falsified_by": "ارجاع با نامِ ساخته‌شده (f-string یا join) دیده نمی‌شود؛ "
                        "پس «یتیم» یعنی «نامش هیچ‌جا نیامده»، نه «قطعاً بی‌مصرف».",
    }


# ══════════════════════════════════════════════════════════════════════════
#  T — ماژولِ بی‌تست
# ══════════════════════════════════════════════════════════════════════════

def scan_tests(root: Path, corpus=None) -> dict:
    cor = _corpus(root, corpus)
    tests = [f for f in cor.paths() if f.name.startswith("test_")]
    test_corpus = " \n".join(cor.text(t) for t in tests)
    mods = [f for f in cor.paths(include_tests=False)
            if f.name != "__init__.py"]
    untested = []
    for m in mods:
        stem = m.stem
        if re.search(rf"\b(?:import|from)\s+{re.escape(stem)}\b", test_corpus):
            continue
        if re.search(rf"\b{re.escape(stem)}\b", test_corpus):
            continue
        untested.append({"module": str(m.relative_to(root)),
                         "lines": cor.text(m).count("\n") + 1,
                         "fan_in": len(cor.files_with_word(stem)
                                       & set(cor.paths(include_tests=False)) - {m})})
    untested.sort(key=lambda r: -r["lines"])
    return {
        "test_files": len(tests), "modules": len(mods),
        "untested_count": len(untested),
        "covered_rate": round(1 - len(untested) / len(mods), 3) if mods else None,
        "untested": untested[:30],
        "falsified_by": "«اشاره‌شده در یک تست» با «تست‌شده» یکی نیست — این عدد "
                        "سقفِ خوش‌بینانه است، نه پوشش.",
    }


# ══════════════════════════════════════════════════════════════════════════
#  M — نشانهٔ ناتمام
# ══════════════════════════════════════════════════════════════════════════

def scan_markers(root: Path, corpus=None) -> dict:
    cor = _corpus(root, corpus)
    hits = []
    for f, txt in cor.items(include_tests=False):
        for i, line in enumerate(txt.splitlines(), 1):
            m = _MARKER_RE.search(line) or _PERSIAN_MARKER_RE.search(line)
            if not m:
                continue
            # `# noqa` و ارجاعِ توضیحی به خودِ کلمه شمرده نمی‌شود
            if "noqa" in line or "_MARKER_RE" in line:
                continue
            hits.append({"file": str(f.relative_to(root)), "line": i,
                         "marker": m.group(1) if m.groups() else m.group(0),
                         "snippet": line.strip()[:90]})
    by_marker: dict[str, int] = {}
    for h in hits:
        k = str(h["marker"]).upper()
        by_marker[k] = by_marker.get(k, 0) + 1
    return {"count": len(hits), "by_marker": dict(sorted(by_marker.items())),
            "hits": hits[:40]}


# ══════════════════════════════════════════════════════════════════════════
#  Y — نمادِ مرده
# ══════════════════════════════════════════════════════════════════════════

def scan_symbols(root: Path, min_lines=6, corpus=None) -> dict:
    """تابع/کلاسِ عمومی که هیچ فایلِ **دیگری** نامش را نمی‌برد.

    مکملِ `orphan_scan`: آن‌جا یک نامِ استفاده‌شده کلِ ماژول را «وصل» می‌کند،
    پس ۹۰٪ مردهٔ داخلِ یک ماژولِ زنده نامرئی می‌ماند. این‌جا دیده می‌شود.
    محافظه‌کارانه: dunder، `_private`، و توابعِ کوتاه کنار گذاشته می‌شوند.
    """
    cor = _corpus(root, corpus)
    dead = []
    for f, src in cor.items():
        if f.name.startswith("test_"):
            continue
        tree = cor.tree(f)
        if tree is None:
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                continue
            name = node.name
            if name.startswith("_") or name.startswith("test"):
                continue
            span = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
            if span < min_lines:
                continue
            used = bool(cor.files_with_word(name) - {f})
            if not used:
                dead.append({"file": str(f.relative_to(root)), "symbol": name,
                             "line": node.lineno, "lines": span})
    dead.sort(key=lambda r: -r["lines"])
    return {"count": len(dead), "dead": dead[:30],
            "falsified_by": "فراخوانیِ پویا (getattr/registry/رشته) دیده نمی‌شود؛ "
                            "هر مورد باید دستی تأیید شود، نه دسته‌جمعی حذف."}


# ══════════════════════════════════════════════════════════════════════════

_CHECKS = {"flags": scan_flags, "state": scan_state, "tests": scan_tests,
           "markers": scan_markers, "symbols": scan_symbols}


def run(root=None, only=None) -> dict:
    root = Path(root) if root else Path(__file__).resolve().parent
    cor = Corpus(root)
    out = {"schema": SCHEMA, "root": str(root), "checks": {}, "errors": {}}
    for key, fn in _CHECKS.items():
        if only and key != only:
            continue
        try:
            out["checks"][key] = fn(root, corpus=cor)
        except Exception as exc:  # noqa: BLE001 — یک بررسیِ شکسته بقیه را نمی‌کشد
            out["errors"][key] = f"{type(exc).__name__}: {exc}"
    c = out["checks"]
    out["headline"] = {
        "dark_flags_armed_unread": len(c.get("flags", {}).get("armed_unread", [])),
        "dark_flags_read_unarmed": len(c.get("flags", {}).get("read_unarmed", [])),
        "orphan_state": c.get("state", {}).get("orphan_count"),
        "write_only_state": c.get("state", {}).get("single_count"),
        "untested_modules": c.get("tests", {}).get("untested_count"),
        "unfinished_markers": c.get("markers", {}).get("count"),
        "dead_symbols": c.get("symbols", {}).get("count"),
        "checks_failed": len(out["errors"]),
    }
    out["corpus"] = cor.stats
    # عمداً هیچ نمرهٔ مرکبی ساخته نمی‌شود — §بالای فایل.
    return out


def card(root=None) -> str:
    r = run(root)
    h = r["headline"]
    f = r["checks"].get("flags", {})
    s = r["checks"].get("state", {})
    t = r["checks"].get("tests", {})
    lines = [
        "🪞 خودشناسی — چیزهایی که دربارهٔ خودم نمی‌دانستم",
        "",
        f"🏳 فلگ  مسلح‌ولی‌بی‌خواننده {h['dark_flags_armed_unread']}   "
        f"خوانده‌ولی‌تعریف‌نشده {h['dark_flags_read_unarmed']}   "
        f"(از {f.get('armed', 0)} مسلح، {f.get('referenced_in_code', 0)} در کد)",
        f"🗃 state  یتیم {h['orphan_state']}   تک‌ارجاع {h['write_only_state']}   "
        f"(از {s.get('files', 0)} فایل)",
        f"🧪 تست   بی‌تست {h['untested_modules']} از {t.get('modules', 0)} ماژول "
        f"(پوششِ اسمی {t.get('covered_rate')})",
        f"🚧 ناتمام {h['unfinished_markers']}   ☠️ نمادِ مرده {h['dead_symbols']}",
    ]
    if h["checks_failed"]:
        lines.append(f"🚩 {h['checks_failed']} بررسی خطا داد: "
                     + ", ".join(r["errors"]))
    top = (f.get("read_unarmed") or [])[:5]
    if top:
        lines += ["", "خوانده‌شده ولی هرگز تعریف‌نشده (پیش‌فرضِ کد حاکم است، "
                      "رأیِ مالک وجود ندارد):"]
        lines += [f"   · {x['flag']}  ← {', '.join(x['modules'])}" for x in top]
    orph = (s.get("single_referencer") or [])[:4]
    if orph:
        lines += ["", "فقط نویسنده‌اش می‌شناسدش (مصرف‌کننده ندارد):"]
        lines += [f"   · {x['file']}  ({x['bytes']} بایت، تنها ارجاع: "
                  f"{', '.join(x['by'])})" for x in orph]
    lines += ["", "هیچ نمرهٔ واحدی ساخته نمی‌شود: یک عدد پنهان می‌کند کدام بررسی",
              "چیزی پیدا نکرد چون تمیز است و کدام چون خراب است."]
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        if i + 1 < len(argv):
            only = argv[i + 1]
    root = next((a for a in argv if not a.startswith("--")
                 and a not in _CHECKS), None)
    if "--json" in argv:
        print(json.dumps(run(root, only), ensure_ascii=False, indent=2))
    else:
        print(card(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
