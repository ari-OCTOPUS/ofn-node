#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_proposal_metrics_honesty.py — C7 (گامِ ۱۷ ِ UNIFICATION-DESIGN-2026-08-03).

اندازه‌گیریِ ۲۰۲۶-۰۸-۰۳ روی درختِ زنده، `_ops/state/ORGANISM-STATE.json`:

    "proposal_metrics": {"proposals_delivered": 0, "proposal_outcomes": 0,
                         "proposals_sent": 0, "proposal_accept_rate": 0.0}

در برابرِ چرخهٔ عمرِ واقعی که `lifecycle_fold.fold()` می‌شمارد: ۴۱ کارتِ
تحویل‌شده، ۲۱ تصمیمِ مالک، و **صفر اثر**. علتش «باگ» نبود: `proposal_metrics()`
از یک لیستِ درون‌حافظه‌ای می‌خواند که هر ری‌استارت خالی‌اش می‌کند. منبعِ اشتباه.

این فایل چهار چیز را قفل می‌کند:

  ۱ **پلهٔ سایه واقعی است، نه توصیه.** حتی وقتی مالک منبع را عوض می‌کند، چرخهٔ
    اولِ بعد از ری‌استارت هنوز عددِ قدیمی را منتشر می‌کند و فقط قدیم/جدید را
    کنارِ هم می‌گذارد. دلیلش `goal_directed.measure()` است: `now[k] > oldest[k]`
    یعنی یک پرشِ ۰→۴۱ هر نیتِ بازِ ثبت‌شده را یک‌جا «moved» اعلام می‌کند.
  ۲ **`proposals_effected` صفرِ صریح است، نه کلیدِ غایب.** «صفر اثر» یافتهٔ اصلیِ
    این ممیزی است؛ نبودنِ کلید آن را دوباره نامرئی می‌کند.
  ۳ **منبعِ غایب ⇒ UNKNOWN، نه صفر.** ذخیرهٔ ناخوانا نباید به عددِ تمیز تبدیل شود.
  ۴ **بلوکِ منتشرشده بین دو چرخه پایدار است.** یک شمارندهٔ صعودی داخلِ این کلید،
    `self_knowledge._snapshot_hash` را هر تیک عوض می‌کند و مسیرِ
    `cached:no-change` را می‌کشد — پس شمارنده بیرون نمی‌رود.

ایزوله: هر فیکسچر یک `tempfile.mkdtemp` است و صراحتاً assert می‌شود که زیرِ
درختِ زنده نیست. `fold` فقط می‌خواند؛ بایتِ فایلِ کارت‌ها قبل/بعد سنجیده می‌شود.
"""
import ast
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("proposal-metrics-honesty")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lifecycle_fold as lf              # noqa: E402
import live_loop as ll                   # noqa: E402
import pending_card_recovery as pcr      # noqa: E402

LIVE_TREE = Path(os.environ.get("REAL_VAULT", r"F:\backup")).resolve()
FLAG = ll.LiveLoop.PM_SOURCE_FLAG

#: هفت کلیدی که پیش از C7 منتشر می‌شدند — قراردادِ حالتِ «off».
LEGACY_KEYS = {"proposals_delivered", "proposal_outcomes", "proposals_sent",
               "proposals_fake_delivered", "proposal_positive",
               "proposal_accept_rate", "proposal_value_aud"}

#: اعدادِ سنجیده‌شدهٔ ۰۸-۰۳ — فیکسچر عمداً همان شکل را بازمی‌سازد.
N_STALLED, N_DECIDED = 20, 21


# ─── فیکسچرها ────────────────────────────────────────────────────────────────
def _seed(n_stalled=N_STALLED, n_decided=N_DECIDED, state="RECONCILE_REQUIRED",
          receipt=""):
    """یک ذخیرهٔ حالتِ موقت با کارت و دفترِ حکم — هرگز زیرِ درختِ زنده."""
    sd = Path(tempfile.mkdtemp(prefix="pm-honesty-")) / "state"
    (sd / "pulse").mkdir(parents=True)
    cards = {}
    for i in range(n_stalled):
        cards["s%d" % i] = {"delivery": "SENT", "decision": "SUBMITTED",
                            "rfc_id": "RFC-S%d" % i,
                            "created_ts": "2026-07-26T00:00:00+00:00"}
    for i in range(n_decided):
        cards["d%d" % i] = {"delivery": "SENT", "decision": "DECIDED",
                            "rfc_id": "RFC-D%d" % i,
                            "created_ts": "2026-07-28T00:00:00+00:00"}
    (sd / "pulse" / "pending-cards.json").write_text(
        json.dumps(cards, ensure_ascii=False), "utf-8")
    con = pcr._rfc_con(sd)
    try:
        for i in range(n_decided):
            con.execute(
                "INSERT OR REPLACE INTO rfc_decision(rfc_id,verdict,revision,state,"
                "lease_owner,lease_until,receipt_id,operation_key,updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                ("RFC-D%d" % i, "approved", 1, state, None, None, receipt, None, 0))
        con.commit()
    finally:
        con.close()
    return sd


def _empty_state():
    sd = Path(tempfile.mkdtemp(prefix="pm-empty-")) / "state"
    sd.mkdir(parents=True)
    return sd


def _loop():
    """یک LiveLoopِ تازه بدونِ `__init__` — دقیقاً همان کاری که ری‌استارت می‌کند،
    و بدونِ لمسِ bus/انبار."""
    o = ll.LiveLoop.__new__(ll.LiveLoop)
    o._proposal_outcomes = []
    o._proposal_seen = set()
    return o


class _mode:
    """مقدارِ فلگ را برای یک بلوک ست می‌کند و بعد دقیقاً برمی‌گرداند."""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self.saved = os.environ.get(FLAG)
        if self.value is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = self.value
        return self

    def __exit__(self, *exc):
        if self.saved is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = self.saved
        return False


# ─── ۰: ایزوله ───────────────────────────────────────────────────────────────
def t_a_fixture_is_never_the_live_tree():
    """یک تستِ حالت که به `F:\\backup` بخورد، تست نیست — رویداد است."""
    for sd in (_seed(1, 1), _empty_state()):
        resolved = sd.resolve()
        assert LIVE_TREE not in resolved.parents and resolved != LIVE_TREE, \
            "فیکسچر زیرِ درختِ زنده ساخته شد: %s" % resolved


def t_b_state_dir_comes_from_env_not_from_the_repo():
    """`_pm_state_dir()` باید `OPS_DIR` را بخواند؛ وگرنه تستِ ایزوله بی‌معناست."""
    o = _loop()
    saved = os.environ.get("OPS_DIR")
    try:
        stray = Path(tempfile.mkdtemp(prefix="pm-opsdir-"))
        os.environ["OPS_DIR"] = str(stray)
        got = o._pm_state_dir()
        assert got == stray / "state", "OPS_DIR نادیده گرفته شد: %s" % got
    finally:
        if saved is None:
            os.environ.pop("OPS_DIR", None)
        else:
            os.environ["OPS_DIR"] = saved
    live = Path(os.environ["OPS_DIR"]).resolve()
    assert LIVE_TREE not in live.parents and live != LIVE_TREE, \
        "OPS_DIR ِ harness به درختِ زنده اشاره می‌کند: %s" % live


# ─── ۱: خودِ دروغ ────────────────────────────────────────────────────────────
def t_c_the_in_memory_source_reports_zero_against_a_real_backlog():
    """پایهٔ همهٔ ادعاها: منبعِ قدیمی صفر می‌دهد در حالی که ۴۱ کارت هست."""
    sd = _seed()
    got = lf.fold(sd)
    assert got["delivered"]["value"] == N_STALLED + N_DECIDED, got["delivered"]
    assert got["decided"]["value"] == N_DECIDED, got["decided"]
    assert got["effected"]["value"] == 0, got["effected"]
    with _mode("off"):
        legacy = _loop().proposal_metrics()
    assert legacy["proposals_delivered"] == 0, \
        "منبعِ درون‌حافظه‌ای باید صفر باشد وگرنه فیکسچر دروغ می‌گوید"
    assert legacy["proposal_outcomes"] == 0, legacy


def t_d_off_is_byte_identical_to_pre_c7():
    """رأیِ خروج: «off» دقیقاً هفت کلیدِ قبلی — نه کلیدِ تازه، نه I/O ِ تازه."""
    sd = _seed()
    with _mode("off"):
        out = _loop().proposal_metrics(_state_dir=sd)
    assert set(out) == LEGACY_KEYS, \
        "حالتِ off کلید اضافه/کم دارد: %s" % sorted(set(out) ^ LEGACY_KEYS)


# ─── ۲: پلهٔ سایه ────────────────────────────────────────────────────────────
def t_e_default_is_shadow_and_moves_no_published_number():
    """پیش‌فرض هیچ عددی را جابه‌جا نمی‌کند — فقط حقیقت را کنارش می‌گذارد."""
    sd = _seed()
    with _mode(None):
        out = _loop().proposal_metrics(_state_dir=sd)
    assert out["lifecycle"]["published"] == "shadow", out["lifecycle"]
    assert out["proposals_delivered"] == 0, "سایه عددِ منتشرشده را عوض کرد"
    assert out["proposal_outcomes"] == 0, "سایه عددِ منتشرشده را عوض کرد"
    cmp_ = out["lifecycle"]["compare"]
    assert cmp_["proposals_delivered"] == {"old": 0, "new": N_STALLED + N_DECIDED}, cmp_
    assert cmp_["proposal_outcomes"] == {"old": 0, "new": N_DECIDED}, cmp_
    assert cmp_["proposals_effected"] == {"old": None, "new": 0}, \
        "کلیدی که وجود نداشت نباید old=0 بگیرد: %s" % cmp_["proposals_effected"]


def t_f_owner_vote_still_pays_one_shadow_cycle_first():
    """سنجهٔ پذیرشِ اصلی: ۰→۴۱ و ۰→۲۱ — ولی **نه در چرخهٔ اول**."""
    sd = _seed()
    o = _loop()
    with _mode("lifecycle"):
        first = o.proposal_metrics(_state_dir=sd)
        second = o.proposal_metrics(_state_dir=sd)
    assert first["lifecycle"]["published"] == "shadow", \
        "چرخهٔ اول باید سایه باشد: %s" % first["lifecycle"]["published"]
    assert first["proposals_delivered"] == 0, \
        "چرخهٔ اول عدد را عوض کرد — پلهٔ سایه رد شد: %s" % first["proposals_delivered"]
    assert first["lifecycle"]["shadow_complete"] is False, first["lifecycle"]
    assert second["lifecycle"]["published"] == "lifecycle", second["lifecycle"]
    assert second["proposals_delivered"] == N_STALLED + N_DECIDED, \
        "0→41 اتفاق نیفتاد: %s" % second["proposals_delivered"]
    assert second["proposal_outcomes"] == N_DECIDED, \
        "0→21 اتفاق نیفتاد: %s" % second["proposal_outcomes"]


def t_g_a_fresh_process_pays_the_shadow_cycle_again():
    """پلهٔ سایه per-process است: ری‌استارتِ بعدی دوباره یک چرخه سایه می‌دهد،
    چون baselineِ `goal_directed` هم می‌تواند در همان فاصله بازنویسی شده باشد."""
    sd = _seed()
    with _mode("lifecycle"):
        a = _loop().proposal_metrics(_state_dir=sd)
        b = _loop().proposal_metrics(_state_dir=sd)
    assert a["lifecycle"]["published"] == "shadow", a["lifecycle"]
    assert b["lifecycle"]["published"] == "shadow", \
        "پروسهٔ تازه بدونِ سایه منتشر کرد: %s" % b["lifecycle"]["published"]


# ─── ۳: صفرِ صریح در برابرِ صفرِ پنهان ────────────────────────────────────────
def t_h_effected_is_surfaced_as_an_explicit_zero():
    """«صفر اثر» باید دیده شود، نه اینکه با نبودِ کلید نامرئی بماند."""
    sd = _seed()
    for mode in (None, "lifecycle"):
        with _mode(mode):
            out = _loop().proposal_metrics(_state_dir=sd)
        assert "proposals_effected" in out, \
            "کلیدِ proposals_effected در حالتِ %s غایب است" % mode
        assert out["proposals_effected"] == 0, out["proposals_effected"]


def t_i_applied_without_a_receipt_is_not_an_effect():
    """قرارِ C1: اثرِ بی‌رسید اثر نیست — و باید از همین کلید هم عبور کند."""
    no_receipt = _seed(n_stalled=0, n_decided=1, state="APPLIED", receipt="")
    with_receipt = _seed(n_stalled=0, n_decided=1, state="APPLIED", receipt="R-1")
    with _mode(None):
        a = _loop().proposal_metrics(_state_dir=no_receipt)
        b = _loop().proposal_metrics(_state_dir=with_receipt)
    assert a["proposals_effected"] == 0, \
        "APPLIED بدونِ رسید اثر شمرده شد: %s" % a["proposals_effected"]
    assert b["proposals_effected"] == 1, \
        "APPLIED با رسید اثر شمرده نشد: %s" % b["proposals_effected"]


def t_j_missing_source_is_unknown_not_zero():
    """ذخیرهٔ غایب ⇒ UNKNOWN. یک صفرِ تمیز این‌جا همان دروغِ اولیه است."""
    with _mode("lifecycle"):
        o = _loop()
        o.proposal_metrics(_state_dir=_empty_state())      # چرخهٔ سایه
        out = o.proposal_metrics(_state_dir=_empty_state())
    assert out["lifecycle"]["published"] == "unknown", out["lifecycle"]
    assert "proposals_effected" not in out, \
        "منبعِ ناخوانا یک صفرِ ساختگی ساخت: %s" % out.get("proposals_effected")
    assert out["proposals_delivered"] == 0 and out["proposal_outcomes"] == 0, \
        "با منبعِ ناخوانا نباید هیچ عددی جابه‌جا شود: %s" % out


def t_k_a_broken_fold_never_kills_the_tick():
    """منبعِ خراب باید UNKNOWN بدهد، نه استثنایی که `proposal_metrics` را ببلعد
    و کلید را از state حذف کند (که آن‌وقت merge_prev کهنه را back-fill می‌کند)."""
    def boom(_state_dir, *a, **kw):
        raise RuntimeError("nope")

    with _mode("lifecycle"):
        out = _loop().proposal_metrics(_fold=boom)
    assert out["lifecycle"]["published"] == "unknown", out["lifecycle"]
    assert out["lifecycle"]["reason"] == "RuntimeError", out["lifecycle"]
    assert LEGACY_KEYS <= set(out), "کلیدهای قدیمی گم شدند: %s" % sorted(out)


# ─── ۴: پایداریِ بلوکِ منتشرشده ──────────────────────────────────────────────
def t_l_published_block_is_stable_between_cycles():
    """اگر چیزی داخلِ این کلید هر تیک عوض شود، `_snapshot_hash` ِ خودشناسی هرگز
    `cached:no-change` نمی‌زند و هر چرخه یک کاوشِ عمیق می‌دود."""
    sd = _seed()
    with _mode(None):
        o = _loop()
        o.proposal_metrics(_state_dir=sd)
        second = o.proposal_metrics(_state_dir=sd)
        third = o.proposal_metrics(_state_dir=sd)
    dump = lambda d: json.dumps(d, ensure_ascii=False, sort_keys=True)   # noqa: E731
    assert dump(second["lifecycle"]) == dump(third["lifecycle"]), \
        "بلوک بین دو چرخه عوض شد:\n%s\n%s" % (dump(second["lifecycle"]),
                                              dump(third["lifecycle"]))
    assert "shadow_cycles" not in json.dumps(second, ensure_ascii=False), \
        "شمارندهٔ صعودی منتشر شد — hash ِ خودشناسی هر تیک عوض می‌شود"


def t_m_derived_keys_go_unknown_when_the_source_moves():
    """«۰٪ پذیرش از ۲۱ تصمیم» یک جملهٔ غلط است. عددِ مشتقِ کهنه ⇒ None."""
    sd = _seed()
    o = _loop()
    with _mode("lifecycle"):
        o.proposal_metrics(_state_dir=sd)
        out = o.proposal_metrics(_state_dir=sd)
    assert out["proposal_accept_rate"] is None, \
        "نرخِ پذیرشِ کهنه کنارِ ۲۱ تصمیم منتشر شد: %s" % out["proposal_accept_rate"]
    assert out["proposals_fake_delivered"] is None, out["proposals_fake_delivered"]
    assert out["lifecycle"]["keys_unknown"] == list(ll.LiveLoop.PM_DERIVED_KEYS), \
        out["lifecycle"]["keys_unknown"]


# ─── ۵: هزینه و اثرِ جانبی ───────────────────────────────────────────────────
def t_n_the_fold_writes_nothing_to_the_card_store():
    """تاشدگی خالص است. اگر بنویسد، شمارنده خودش را تغذیه می‌کند."""
    sd = _seed()
    cards = sd / "pulse" / "pending-cards.json"
    before = cards.read_bytes()
    with _mode("lifecycle"):
        o = _loop()
        o.proposal_metrics(_state_dir=sd)
        o.proposal_metrics(_state_dir=sd)
    assert cards.read_bytes() == before, "فایلِ کارت‌ها بایت‌یکسان نماند"


def t_o_the_lifecycle_read_is_memoised():
    """`_rfc_con()` روی هر باز شدن mkdir + CREATE TABLE + WAL می‌زند؛ این مسیر هر
    تیک می‌دود. بدونِ memo، همان اثرِ جانبی‌ای که C1 صریحاً هشدارش را داد."""
    calls = {"n": 0}
    real = lf.fold

    def counting(state_dir, *a, **kw):
        calls["n"] += 1
        return real(state_dir, *a, **kw)

    lf.fold = counting
    try:
        o = _loop()
        with _mode(None):
            o._pm_lifecycle()
            o._pm_lifecycle()
    finally:
        lf.fold = real
    assert calls["n"] == 1, "memo کار نکرد؛ fold %d بار خوانده شد" % calls["n"]


# ─── ۶: زنجیرهٔ نویسنده دست‌نخورده ──────────────────────────────────────────
def t_p_the_writer_chain_is_unchanged_and_singular():
    """C12 اجازهٔ نویسندهٔ دوم روی ORGANISM-STATE.json را نمی‌دهد — C7 هم
    نمی‌خواهدش. زنجیره همان است: live_loop → brain_worker → latch."""
    bw = (_OPS / "brain_worker.py").read_text("utf-8")
    assert "ctx.wired.live_loop.proposal_metrics()" in bw, \
        "زنجیرهٔ تغذیهٔ brain_worker عوض شده"
    assert 'block["proposal_metrics"] = _proposal_metrics' in bw, \
        "brain_worker دیگر همان کلید را در latch نمی‌گذارد"
    # ⚠️ نسخهٔ اولِ این گارد زیررشتهٔ `ORGANISM-STATE` را در کلِ فایل می‌گرفت و
    # روی **کامنتِ خودم** قرمز شد (و روی یک کامنتِ از-قبل-موجود در خطِ ۴۸۹).
    # همان درسِ ثبت‌شده: grep کامنت را هم می‌شمارد. پس AST، و فقط رشته‌های واقعی.
    tree = ast.parse((_OPS / "live_loop.py").read_text("utf-8"))
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert not any("ORGANISM-STATE" in s for s in literals), \
        "live_loop نامِ فایلِ حالت را به‌عنوانِ رشتهٔ واقعی گرفت — بوی نویسندهٔ دوم"
    writes = {"write_text", "write_bytes", "mkdir", "unlink", "rmtree", "touch",
              "rename", "makedirs", "remove", "dump", "connect", "open"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not (node.name == "proposal_metrics" or node.name.startswith("_pm_")):
            continue
        used = {getattr(c.func, "attr", None) or getattr(c.func, "id", None)
                for c in ast.walk(node) if isinstance(c, ast.Call)}
        bad = used & writes
        assert not bad, "مسیرِ %s می‌نویسد: %s" % (node.name, sorted(bad))


def t_q_goal_baseline_sees_no_movement_in_shadow():
    """دقیقاً کلیدهایی که `goal_directed._baseline_metrics()` می‌خواند — در سایه
    هیچ‌کدام تکان نمی‌خورند، پس `measure()` موفقیتِ جعلی نمی‌سازد."""
    sd = _seed()
    with _mode(None):
        out = _loop().proposal_metrics(_state_dir=sd)
    for key in ("proposals_delivered", "proposal_outcomes", "proposal_value_aud"):
        assert (out.get(key) or 0) == 0, \
            "کلیدِ رأی‌دهندهٔ goal_directed در سایه حرکت کرد: %s=%s" % (key, out.get(key))


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print("\n%s test_proposal_metrics_honesty: %d/%d"
          % ("✅" if not failed else "❌", len(checks) - failed, len(checks)))
    sys.exit(1 if failed else 0)
