#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_callback_scanner — موتورِ نحویِ اسکنِ callback_data/دیسپچر، مشترک میانِ
test_tg_callback_emitter_parity.py و هر تستِ دیگری که به همین قرارداد نیاز دارد.

تاریخچه: نسخهٔ اول (۲۰۲۶-۰۸ آغازین) این منطق را مستقیم در فایلِ تست، فقط برای
۴ فایلِ hardcode‌شده (center.py / approval_channel.py / tool_request.py /
test_cycle.py) اجرا می‌کرد. باگِ wiring.py (۲۰۲۶-۰۸-۰۶، `brain_digest_beat`
دکمه‌ای با callback_data="mn:ap" ساخت که فقط center.py هندلرش را می‌شناخت،
درحالی‌که این کارت از کانالِ approval_channel می‌رود) نشان داد چهار فایل کافی
نیست — هر فایلی در _ops می‌تواند emitter باشد. این ماژول همان مکانیزمِ AST را
نگه می‌دارد (نه grep؛ نه شمردنِ کامنت) و آن را به **کلِ درختِ _ops** تعمیم می‌دهد.

سه پرسش جدا:
  1) `emitted_verbs(path)`      — کجا یک callback_data واقعاً ساخته می‌شود؟
  2) `handled_verbs(path)`      — یک روتر (center.py/approval_channel.py) چه
                                   verbهایی را واقعاً dispatch می‌کند؟
  3) `producing_bots(path)`     — کارتِ ساخته‌شده در این فایل از کدام بات(ها)
                                   می‌رود — پس باید روی دیسپچرِ **همان** بات(ها)
                                   بررسی شود؟

پرسشِ سوم چیزیست که این فایل روی آن اضافه می‌کند. بخشِ «چطور» پایینِ فایل است.
"""
from __future__ import annotations

import ast
import re
from collections import deque
from pathlib import Path

# کدِ زیرِ تست = همان درختی که این فایل داخلش زندگی می‌کند (harness.py هم همین
# قاعده را دارد: SELF_OPS = .../_ops، نه REAL_VAULT).
_HERE = Path(__file__).resolve().parent
OPS = _HERE.parent

SKIP_DIRS = {"tests", "__pycache__", "_Archive", "_agent_reports", ".pytest_cache"}

# ── دو روتر ─────────────────────────────────────────────────────────────────
CENTER = OPS / "telegram_center" / "center.py"          # @intergrade2725_Bot
APPROVAL = OPS / "budget" / "approval_channel.py"        # @Robo2725_bot (ارگانیسم)

# ── انکرهای اضافیِ باتِ ارگانیسم ────────────────────────────────────────────
# approval_channel.py تنها فایلی نیست که کارتش قطعاً از بات ارگانیسم می‌رود.
# دو شاهدِ AST-پذیر و مستقیم داریم که فایل بدونِ حدس، بدونِ hardcode کردنِ اسمِ
# فایل، به همین بات بسته می‌شود:
#   الف) `from approval_channel import TelegramApprovalChannel` — خودِ کلاسِ
#        کانالِ ارگانیسم را وارد می‌کند (wiring.py، approval_channel_merge.py).
#   ب) پارامتری دقیقاً به‌نامِ `approval_channel` می‌گیرد و نگه می‌دارد — الگوی
#      `LiveLoop.__init__(..., approval_channel=None, ...)` → `self.channel = approval_channel`.
# این‌ها را «انکر» می‌نامیم چون خودشان verb می‌سازند (wiring.py) یا مستقیماً به
# چیزی که verb می‌سازد وصل‌اند (live_loop.py) — و از هرکدام دقیقاً **یک گام**
# import مستقیم را هم approval-family می‌شماریم (پایین را ببین: چرا یک گام، نه
# بازگشتیِ نامحدود).
WIRING = OPS / "wiring.py"
APPROVAL_MERGE = OPS / "budget" / "approval_channel_merge.py"
LIVE_LOOP = OPS / "live_loop.py"

_KNOWN_APPROVAL_IMPORT_ANCHORS = (WIRING, APPROVAL_MERGE)   # شاهدِ (الف)
_KNOWN_APPROVAL_PARAM_ANCHORS = (LIVE_LOOP,)                  # شاهدِ (ب)

_VERB = re.compile(r"^([A-Za-z][A-Za-z0-9_]{0,15}):")


def iter_py_files():
    """هر .py زیرِ _ops، به‌جز پوشه‌های سیستمی/آرشیو/کش. جایگزینِ لیستِ ۴تاییِ قدیم."""
    for f in sorted(OPS.rglob("*.py")):
        if any(p in f.parts for p in SKIP_DIRS):
            continue
        yield f


_parse_cache: dict = {}


def _parse(path: Path):
    """AST-treeِ یک فایل، با کش (بر پایهٔ path) — این ماژول در یک اجرا چند بار
    روی همان فایل صدا زده می‌شود (emitted_verbs/handled_verbs/import_edges/
    signalها)؛ بدونِ کش، هر بار کلِ درختِ _ops دوباره parse می‌شود. کش فقط
    نتیجهٔ parse را نگه می‌دارد، هیچ منطقی عوض نمی‌شود."""
    if path in _parse_cache:
        return _parse_cache[path]
    try:
        tree = ast.parse(Path(path).read_text("utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        tree = None
    _parse_cache[path] = tree
    return tree


_emitted_cache: dict = {}
_handled_cache: dict = {}


# ── (۱) emitted_verbs ────────────────────────────────────────────────────────
def emitted_verbs(path: Path) -> set:
    """verbهایی که در `callback_data` **ساخته** می‌شوند — از AST، نه grep.

    دو شکل پوشش داده می‌شود: رشتهٔ ثابت (`"tr:list"`) و f-string
    (`f"tr:y:{rid}"`) که در AST یک `JoinedStr` با اولین جزءِ ثابت است.

    دکمه‌های `url` عمداً **دیده نمی‌شوند** — این تابع فقط دنبالِ کلیدِ لفظیِ
    `"callback_data"` می‌گردد، هرگز `"url"`. دکمهٔ url هرگز به هیچ دیسپچرِ
    بات نمی‌رسد (خودِ تلگرام، سمتِ کلاینت، چتِ بات دیگر را باز می‌کند) — نکتهٔ
    ۲۰۲۶-۰۸-۰۶ که در wiring.py:brain_digest_beat و
    test_organ_dialogue.py:t_brain_digest_beat_keyboard_has_no_dead_cross_bot_button
    مستند است. پس نیازی به فیلترِ صریح نیست: نبودِ کلید یعنی بیرون از دامنه."""
    if path in _emitted_cache:
        return _emitted_cache[path]
    out = set()
    tree = _parse(path)
    if tree is None:
        _emitted_cache[path] = out
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if not (isinstance(k, ast.Constant) and k.value == "callback_data"):
                    continue
                lit = None
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    lit = v.value
                elif isinstance(v, ast.JoinedStr) and v.values:
                    first = v.values[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        lit = first.value
                if lit:
                    m = _VERB.match(lit)
                    if m:
                        out.add(m.group(1))
    _emitted_cache[path] = out
    return out


def all_emitters() -> dict:
    """{path: {verb, ...}} برای هر فایلی که واقعاً چیزی emit می‌کند."""
    out = {}
    for f in iter_py_files():
        v = emitted_verbs(f)
        if v:
            out[f] = v
    return out


# ── (۲) handled_verbs ────────────────────────────────────────────────────────
def _module_level_string_collections(tree: ast.Module) -> dict:
    """`NAME = ("a","b")` / `[...]` / `{...}` در سطحِ ماژول → {NAME: {"a","b"}}.

    فقط تکلیفِ ساده (یک target، یک literal) شمرده می‌شود؛ اگر NAME چند بار روی
    چیزهای متفاوت assign شود یا هر عضو رشته نباشد، رد می‌شود (بدونِ حدس)."""
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, (ast.Tuple, ast.List, ast.Set))):
            vals = set()
            ok = True
            for e in node.value.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    vals.add(e.value)
                else:
                    ok = False
                    break
            if ok and vals:
                out[node.targets[0].id] = vals
    return out


def handled_verbs(path: Path) -> set:
    """verbهایی که روتر **می‌شناسد** — مقایسه‌های `verb == "x"` / `in {...}` /
    `parts[0] == "x"`، همه از AST.

    ⚠️ عمداً مجموعه‌های سطحِ ماژول (مثلِ `_MUTATING = frozenset({"app","tr"})`)
    **شمرده نمی‌شوند** مگر همان NAME واقعاً در یک مقایسهٔ verb-ایست به‌کار رفته
    باشد (یعنی خودِ شاخهٔ dispatch به آن ارجاع بدهد). نسخهٔ اول می‌شمرد و گارد
    بی‌دندان شد: برداشتنِ کاملِ شاخهٔ `verb == "tr"` از center هیچ تستی را
    قرمز نکرد، چون نامِ `tr` از همان مجموعهٔ عضویت برداشته می‌شد. عضویت در یک
    لیستِ «این verb جهش‌زاست» یعنی **دسته‌بندی**، نه **رسیدگی**. فقط شاخهٔ
    dispatch حساب است — این‌جا یعنی مقایسه باید مستقیماً روی `verb`/`v`/`kind`/
    `parts[0]`/`p[0]` باشد؛ ارجاع به یک NAME فقط وقتی حساب می‌شود که خودش طرفِ
    راستِ **همین** مقایسه باشد (مثلِ `parts[0] not in _VERDICTS` در
    center.py:_handle_callback — دروازهٔ واقعیِ ok/no/later، نه دسته‌بندیِ صرف)."""
    if path in _handled_cache:
        return _handled_cache[path]
    out = set()
    tree = _parse(path)
    if tree is None:
        _handled_cache[path] = out
        return out
    module_literals = _module_level_string_collections(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            left = node.left
            is_verbish = (
                (isinstance(left, ast.Name) and left.id in ("verb", "v", "kind"))
                or (isinstance(left, ast.Subscript)
                    and isinstance(left.value, ast.Name)
                    and left.value.id in ("parts", "p"))
            )
            if not is_verbish:
                continue
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                    out.add(comp.value)
                elif isinstance(comp, (ast.Set, ast.Tuple, ast.List)):
                    for e in comp.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            out.add(e.value)
                elif isinstance(comp, ast.Name) and comp.id in module_literals:
                    out |= module_literals[comp.id]
    _handled_cache[path] = out
    return out


# ── (۳) producing_bots ───────────────────────────────────────────────────────
# «این فایل کارتی می‌سازد — از کدام بات فرستاده می‌شود؟» import را dataflow
# نمی‌کند (این یک AST-scanner است، نه یک اجراکننده)، پس این پرسش را با
# **گراف importِ درون‌ـ_ops** جواب می‌دهیم: اگر روترِ R، ماژولِ M را (مستقیم یا
# با چند گامِ محدود) import می‌کند، فرض این است که R خودش کارتِ M را می‌سازد و با
# کلاینتِ خودش می‌فرستد — پس دیسپچرِ خودِ R باید verbهای M را بشناسد.
#
# این فرض شکننده است (importِ X لزوماً یعنی «کارتِ X را می‌فرستم»، نه فقط
# «تابعی از X صدا می‌زنم») — و در طیِ ساختِ این اسکنر دوبار واقعاً شکست:
#   • center.py «approval_channel» را import می‌کند (برای چک‌کردنِ state، نه
#     فرستادن) → اگر همین یک import کافی بود، **کل** approval-family به
#     center می‌چسبید (۲۰۱ فایل، شاملِ decision_gate/capability_registry که
#     واقعاً فقط centerاند). قاعدهٔ ۱ (پایین) همین را می‌بندد.
#   • quote_cmd.py (خودش centerـفمیلی) یک تابع از wiring.py صدا می‌زند (بی‌ربط
#     به ساختِ کارت) → اگر بازگشتیِ نامحدود بود، wiring.py (که خودش approval
#     است) از centerهم «قابلِ‌دیدن» می‌شد و SHARED غلط می‌داد. قاعدهٔ ۲ همین را
#     می‌بندد (approval-anchor‌ها را برای BFSِ center مسدود می‌کنیم).
#
# پس این BFS **نامتقارن و محافظه‌کارانه** است، نه یک closure عمومی:
#
#   قاعدهٔ ۱ — سمتِ center: BFS از {center.py} رو به جلو، بی‌سقفِ عمق، ولی از
#   هر گرهی که فن‌اوت بزرگ دارد (> FANOUT_THRESHOLD import) دیگر جلو نمی‌رود
#   مگر خودش anchor باشد؛ و هرگز وارد گره‌های approval-anchor نمی‌شود. این حدِ
#   فن‌اوت دقیقاً برای این است: center.py خودش (۹۲ import) روترِ واقعیست، پس
#   بی‌قیدوشرط گسترش می‌یابد؛ ولی فایل‌های میانیِ حجیم (که معمولاً utility اند،
#   نه card-builder) دیگر رله نمی‌شوند. زنجیرهٔ سه‌گامیِ
#   center → owner_console.telegram_adapter → conversation → views (هر سه
#   نازک: ۲-۳ import) دقیقاً به همین دلیل درست resolve می‌شود.
#
#   قاعدهٔ ۲ — سمتِ approval: هیچ BFSِ بازگشتی از approval_channel.py نیست
#   (خودش too-hub است: نزدیکِ همهٔ _ops را transitively می‌بیند). فقط **یک گام**
#   importِ مستقیم از هرکدام از انکرها (approval_channel.py، wiring.py،
#   approval_channel_merge.py) به‌علاوهٔ خودِ فایل‌های param-anchor
#   (live_loop.py). این همان چیزیست که deferral_rebuild.py/lead_pipeline.py
#   را resolve می‌کند (هر دو مستقیماً از wiring.py وارد می‌شوند) بدونِ باز
#   کردنِ راه به بقیهٔ ۱۱۹ importِ wiring.py.
#
# نتیجه برای هر emitter: "center" / "approval" / "shared" (هر دو) /
# "unknown" (هیچ‌کدام — رفتارِ محافظه‌کارانه: مثلِ shared سنجیده شود، چون
# ندانستن نباید هرگز به معنیِ رد شدن باشد).

FANOUT_THRESHOLD = 15

_edges_cache: dict = {}


def import_edges(path: Path) -> set:
    """هر importِ این فایل، به‌شکلِ `(qualified_or_None, leaf_stem)`.

    `qualified` وقتی پر است که بشود مسیر را صریح resolve کرد (مثلِ
    `from owner_console import telegram_adapter` → "owner_console.telegram_adapter")
    — برای شکستنِ ابهامِ stemهای هم‌نام (مثلِ دو فایلِ telegram_adapter.py)."""
    if path in _edges_cache:
        return _edges_cache[path]
    tree = _parse(path)
    out = set()
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    parts = a.name.split(".")
                    out.add((a.name if len(parts) > 1 else None, parts[-1]))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                modparts = mod.split(".") if mod else []
                if modparts:
                    out.add((None, modparts[-1]))
                for a in node.names:
                    qual = (mod + "." + a.name) if mod else None
                    out.add((qual, a.name))
    _edges_cache[path] = out
    return out


def build_stem_map() -> dict:
    """{file_stem: [path, ...]} برای همهٔ فایل‌های _ops (برای resolveِ import)."""
    stem_map: dict = {}
    for f in iter_py_files():
        stem_map.setdefault(f.stem, []).append(f)
    return stem_map


def _resolve_import(qual, stem, from_path: Path, stem_map: dict):
    cands = stem_map.get(stem)
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    same_dir = [c for c in cands if c.parent == from_path.parent]
    if len(same_dir) == 1:
        return same_dir[0]
    if qual:
        qparts = qual.split(".")
        for c in cands:
            rel_parts = list(c.relative_to(OPS).with_suffix("").parts)
            if rel_parts[-len(qparts):] == qparts:
                return c
    return None   # ابهامِ حل‌نشده → حدس نمی‌زنیم


def _has_approval_param_signal(path: Path) -> bool:
    """پارامتری دقیقاً به‌نامِ `approval_channel` در تعریفِ تابع/متد — شاهدِ (ب)."""
    tree = _parse(path)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            allargs = list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
            if any(a.arg == "approval_channel" for a in allargs):
                return True
    return False


def _has_approval_import_signal(path: Path) -> bool:
    """import مستقیمِ `TelegramApprovalChannel` — شاهدِ (الف).

    telegram_center/* عمداً معاف است: center.py خودش `approval_channel` را
    import می‌کند (برای cross-reference، نه فرستادن) و اگر این‌جا شمرده شود،
    خودِ center یک approval-anchor می‌شود و همه‌چیز به هم می‌چسبد (دقیقاً
    شکستِ اولی که در کامنتِ بالا ثبت شد)."""
    if "telegram_center" in path.parts:
        return False
    return "TelegramApprovalChannel" in {s for _, s in import_edges(path)}


def _bfs(anchors: set, stem_map: dict, *, bounded_fanout: bool,
         blocked_nodes: frozenset = frozenset(), block_dirs: tuple = ()) -> set:
    visited = set(anchors)
    q = deque(anchors)
    while q:
        cur = q.popleft()
        is_anchor = cur in anchors
        edges = import_edges(cur)
        if bounded_fanout and not is_anchor and len(edges) > FANOUT_THRESHOLD:
            continue   # هاب فراتر از انکر: دیگر رله نمی‌شود (قاعدهٔ ۱)
        for qual, stem in edges:
            tgt = _resolve_import(qual, stem, cur, stem_map)
            if tgt is None or tgt in visited:
                continue
            if tgt in blocked_nodes or any(bd in tgt.parts for bd in block_dirs):
                continue
            visited.add(tgt)
            if bounded_fanout:
                q.append(tgt)
            # bounded_fanout=False یعنی «فقط یک گام» (قاعدهٔ ۲) — q هرگز پر
            # نمی‌شود، پس حلقه بعد از انکرهای اولیه تمام می‌شود.
    return visited


def producing_bots(stem_map: dict | None = None) -> dict:
    """{path: frozenset تویِ {"center","approval"}} برای هر فایلِ _ops.

    frozenset خالی = نه از center نه از approval قابلِ‌ردیابی (unknown)."""
    if stem_map is None:
        stem_map = build_stem_map()

    approval_anchors = {APPROVAL}
    for f in _KNOWN_APPROVAL_IMPORT_ANCHORS:
        if f.exists():
            approval_anchors.add(f)
    for f in iter_py_files():
        if f == APPROVAL or f == CENTER:
            continue
        if _has_approval_import_signal(f):
            approval_anchors.add(f)

    s_center = _bfs({CENTER}, stem_map, bounded_fanout=True,
                     blocked_nodes=frozenset(approval_anchors))
    s_approval = _bfs(approval_anchors, stem_map, bounded_fanout=False,
                       blocked_nodes=frozenset({CENTER}),
                       block_dirs=("telegram_center",))
    for f in _KNOWN_APPROVAL_PARAM_ANCHORS:
        if f.exists():
            s_approval.add(f)

    result = {}
    for f in iter_py_files():
        bots = set()
        if f in s_center:
            bots.add("center")
        if f in s_approval:
            bots.add("approval")
        result[f] = frozenset(bots)
    return result


_importers_index_cache = None


def _importers_index(stem_map: dict) -> dict:
    """{path: {path_that_imports_it, ...}} — یک‌بار برای کلِ درخت ساخته می‌شود
    (به‌جای اسکنِ کاملِ درخت به‌ازایِ هر فراخوانیِ has_any_importer)."""
    global _importers_index_cache
    if _importers_index_cache is not None:
        return _importers_index_cache
    idx: dict = {}
    for f in iter_py_files():
        for qual, stem in import_edges(f):
            tgt = _resolve_import(qual, stem, f, stem_map)
            if tgt is not None and tgt != f:
                idx.setdefault(tgt, set()).add(f)
    _importers_index_cache = idx
    return idx


def has_any_importer(path: Path, stem_map: dict | None = None) -> bool:
    """آیا فایلِ دیگری در _ops این فایل را import می‌کند؟ False = orphan/not-wired
    (مثلِ approval_channel_merge.py که خودش می‌گوید «Zero live callers»؛ یا
    owner_console که STATUS="IMPLEMENTED_NOT_WIRED" دارد ولی از طریقِ
    telegram_adapter واقعاً وصل است، پس orphan نیست).

    کاربرد: ماژولِ بی‌importer اگر verb ای emit کند، هیچ باتِ زنده‌ای واقعاً آن
    کارت را نمی‌فرستد (کد اصلاً اجرا نمی‌شود) — پس own-router-check برایش
    بی‌معناست، نه سکوت درباره‌اش."""
    if stem_map is None:
        stem_map = build_stem_map()
    return bool(_importers_index(stem_map).get(path))
