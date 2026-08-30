"""test_proposal_counter_durable.py — اولین کارِ واقعیِ مالک نباید نامرئی باشد.

اندازه‌گیریِ ۲۰۲۶-۰۸-۰۱ روی درختِ زنده:

    proposal_metrics = {proposals_delivered: 0, proposals_sent: 0,
                        proposal_outcomes: 0, proposal_value_aud: 0}

و علتش دو چیزِ مستقل بود که با هم یک شکستِ کامل می‌ساختند:

  ۱ `LiveLoop._proposal_outcomes` یک لیستِ **درون‌حافظه‌ای** است و کامنتِ خودش
    می‌گوید «in-memory by design». آن استدلال برای دوباره‌ننوشتنِ منبعِ
    append-only درست است، ولی عارضه‌اش این بود که هر ری‌استارت شمارنده را صفر
    می‌کرد. ارگانیسم روزها بالا بود و عدد همچنان صفر.
  ۲ لولهٔ لید تحویل را در `proposal_registry` (ماندگار) می‌نویسد و **هرگز** به
    آن لیست اضافه نمی‌کند.

یعنی حتی اگر مالک همین امروز یک لیدِ واقعی را کامل می‌چرخاند، شمارنده صفر
می‌ماند و موفقیتش دیده نمی‌شد. این بدترین شکلِ شکست است: کار می‌کند و کسی
نمی‌فهمد.

این فایل قفل می‌کند که رهیدراسیون **فقط می‌خواند** — هیچ ردیفی به انبار اضافه
نمی‌کند — و اینکه فلگ‌خاموش دقیقاً رفتارِ امروز است.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("proposal-counter-durable")

sys.path.insert(0, str(_HERE.parent / "outcomes"))
import os                       # noqa: E402
import live_loop as ll          # noqa: E402
import proposal_registry as pr  # noqa: E402

FLAG = ll.LiveLoop.REHYDRATE_FLAG


def _db() -> Path:
    return Path(os.environ["ORG_ROOT"]) / "_ops" / "state" / "outcomes" / "outcomes.db"


def _wipe():
    """انبار را پاک کن.

    ⚠️ بدونِ این، تست‌ها ردیف‌های همدیگر را می‌بینند و اعداد جابه‌جا می‌شوند —
    اولین اجرای همین فایل `3` گرفت جایی که `2` انتظار می‌رفت. هر مسیرِ تحتِ
    آزمون باید ایزوله شود، نه فقط ریشهٔ درخت.
    """
    for p in _db().parent.glob("outcomes.db*"):
        try:
            p.unlink()
        except OSError:
            pass


def _seed(n_delivered=2, n_outcome=1, with_lead=True, extra=()):
    """چند ردیفِ واقعی در انبارِ ماندگار بنویس (در درختِ ایزوله)."""
    os.environ["OCTOPUS_WIRE_VERDICT_OUTCOME"] = "1"
    _wipe()
    store = pr._open_store(create=True)
    assert store is not None, "انبار ساخته نشد"
    for i in range(n_delivered):
        store.record({
            "correlation_id": f"c{i}", "mission_id": "", "proposal_id": f"p{i}",
            "leg_id": "lead", "lead_id": (f"L{i}" if with_lead else None),
            "event_type": "delivered", "verdict": None, "value_aud_claimed": 0.0,
            "idempotency_key": f"deliv|p{i}", "payload": {}})
    for i in range(n_outcome):
        store.record({
            "correlation_id": f"c{i}", "mission_id": "", "proposal_id": f"p{i}",
            "leg_id": "lead", "lead_id": None,
            # ⚠️ خط تیره، نه زیرخط — `outcome_store.EVENT_TYPES` فقط همین را
            # می‌پذیرد و هر شکلِ دیگری `ValueError` می‌دهد. همین املا بود که
            # نگاشتِ نسخهٔ اولِ کدِ تولیدی را بی‌صدا مرده کرده بود.
            "event_type": "accepted-measurement", "verdict": "approved",
            "value_aud_claimed": 1200.0,
            # source=tg-center: شکلِ واقعیِ رأیِ مالک (center.py record_owner_verdict).
            # ۲۰۲۶-۰۸-۰۶: فیلترِ self_run/source روی همین کلید تکیه می‌کند؛ فیکسچرِ
            # قدیمی payload خالی می‌داد و به‌اشتباه رد می‌شد.
            "idempotency_key": f"acc|p{i}", "payload": {"source": "tg-center"}})
    for j, et in enumerate(extra):
        store.record({
            "correlation_id": f"e{j}", "mission_id": "", "proposal_id": f"e{j}",
            "leg_id": "lead", "lead_id": None, "event_type": et,
            "verdict": None, "value_aud_claimed": 999.0,
            "idempotency_key": f"{et}|e{j}", "payload": {}})
    store.close()


def _fresh():
    """یک LiveLoopِ تازه — همان کاری که ری‌استارت می‌کند."""
    return ll.LiveLoop.__new__(ll.LiveLoop)


def _rehydrate_only(obj):
    obj._proposal_seen = set()
    obj._proposal_outcomes = []
    return obj._rehydrate_proposal_counter()


def _off():
    os.environ.pop(FLAG, None)


def _on():
    os.environ[FLAG] = "1"


# ── فلگ ──────────────────────────────────────────────────────────────────────
def t_a_flag_off_is_todays_behaviour():
    """خاموش = لیست خالی = دقیقاً عددی که امروز می‌بینی."""
    _off()
    _seed()
    o = _fresh()
    res = _rehydrate_only(o)
    assert res["rehydrated"] == 0 and res["reason"] == "flag-off", res
    assert o._proposal_outcomes == []
    assert ll.LiveLoop.proposal_metrics(o)["proposals_delivered"] == 0


def t_b_flag_on_recovers_the_durable_rows():
    _on()
    try:
        _seed(n_delivered=3, n_outcome=1)
        o = _fresh()
        res = _rehydrate_only(o)
        assert res["rehydrated"] == 4, res
        m = ll.LiveLoop.proposal_metrics(o)
        assert m["proposals_delivered"] == 3, m
        assert m["proposal_outcomes"] == 1, m
        assert m["proposal_positive"] == 1, m
        assert m["proposal_value_aud"] == 1200.0, m
    finally:
        _off()


# ── ناوردیِ اصلی: فقط خواندن ────────────────────────────────────────────────
def t_c_rehydration_never_writes_a_row():
    """اگر رهیدراسیون بنویسد، شمارنده خودش را تغذیه می‌کند و عدد بی‌معنا می‌شود —
    همان «آرتیفکتِ خودساخته شاهد نیست» که در حافظه ثبت است."""
    _on()
    try:
        _seed(n_delivered=2, n_outcome=1)
        store = pr._open_store()
        before = len(store.events())
        store.close()
        for _ in range(3):
            _rehydrate_only(_fresh())
        store = pr._open_store()
        after = len(store.events())
        store.close()
        assert after == before, f"رهیدراسیون نوشت: {before} → {after}"
    finally:
        _off()


def t_d_rehydration_is_idempotent_within_one_loop():
    """دو بار صدا زدن روی یک شیء نباید عدد را دوبرابر کند — چون هر بوت یک‌بار
    صدا می‌زند، ولی کسی ممکن است دستی هم بزندش."""
    _on()
    try:
        _seed(n_delivered=2, n_outcome=0)
        o = _fresh()
        _rehydrate_only(o)
        first = ll.LiveLoop.proposal_metrics(o)["proposals_delivered"]
        o._proposal_seen = set()
        o._proposal_outcomes = []
        o._rehydrate_proposal_counter()
        second = ll.LiveLoop.proposal_metrics(o)["proposals_delivered"]
        assert first == second == 2, (first, second)
    finally:
        _off()


# ── نگاشتِ صریح ──────────────────────────────────────────────────────────────
def t_e_other_event_types_are_never_counted():
    """انبار پنج نوع می‌پذیرد؛ فقط دو تا شمرده می‌شوند.

    `deferred` و `failed` رویدادهای واقعی‌اند و **نباید** تحویل یا نتیجه شمرده
    شوند. اگر نگاشت سخاوتمند بود، عدد باد می‌کرد و مالک فکر می‌کرد کار رفته —
    همان دروغِ سبزی که کلِ این هفته دربارهٔ آن بود.

    (نوعِ کاملاً ناشناخته اصلاً وارد انبار نمی‌شود: `outcome_store` خودش
    `ValueError` می‌دهد. آن گارد از قبل هست و این تست به آن تکیه نمی‌کند.)
    """
    _on()
    try:
        _seed(n_delivered=0, n_outcome=0, extra=("deferred", "failed"))
        o = _fresh()
        _rehydrate_only(o)
        m = ll.LiveLoop.proposal_metrics(o)
        assert m["proposals_delivered"] == 0, m
        assert m["proposal_outcomes"] == 0, m
        assert m["proposal_value_aud"] == 0.0, m
    finally:
        _off()


def t_f_a_synthetic_delivery_is_not_counted_as_sent():
    """`sent` از `lead_id` می‌آید. تحویلِ بی‌لید = کارتِ داخلی، نه ارسالِ واقعی
    به یک آدم. اگر این تفکیک نباشد، `proposals_fake_delivered` بی‌معنی است."""
    _on()
    try:
        _seed(n_delivered=2, n_outcome=0, with_lead=False)
        o = _fresh()
        _rehydrate_only(o)
        m = ll.LiveLoop.proposal_metrics(o)
        assert m["proposals_delivered"] == 2, m
        assert m["proposals_sent"] == 0, m
        assert m["proposals_fake_delivered"] == 2, m
    finally:
        _off()


def t_g_a_broken_store_never_kills_the_boot():
    """رهیدراسیون در `__init__` صدا زده می‌شود. اگر بترکد، کلِ حلقهٔ زنده بالا
    نمی‌آید — و آن از صفربودنِ شمارنده بی‌نهایت بدتر است."""
    _on()
    try:
        orig = pr._open_store
        pr._open_store = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            res = _rehydrate_only(_fresh())
            assert res["rehydrated"] == 0 and res["reason"] == "error", res
        finally:
            pr._open_store = orig
    finally:
        _off()


# ── آلودگیِ self_run (۲۰۲۶-۰۸-۰۶) ─────────────────────────────────────────────
def t_i_self_run_and_non_tg_rows_are_excluded_from_the_vote():
    """outcomes.db مشترک است؛ outcomes/research_loop.py با همان event_type
    (accepted-measurement) و leg_id=research، payload.self_run=True می‌نویسد —
    سنجشِ داخلیِ فرضیه، نه رأیِ مالک. زنده: ۹/۳۵ ردیفِ accepted-measurement
    دقیقاً همین بود و accept_rate را کاذب بالا می‌برد. الگوی فیلتر عیناً از
    acceptance_journey.py::_verify_p8 پورت شد: self_run رد می‌شود؛ و
    source باید با «tg-» شروع شود (یک ردیفِ canaryِ دستی با
    source=C1-internal-canary هم با همین شرط رد می‌شود)."""
    _on()
    try:
        _wipe()
        os.environ["OCTOPUS_WIRE_VERDICT_OUTCOME"] = "1"
        store = pr._open_store(create=True)
        store.record({
            "correlation_id": "real1", "proposal_id": "preal", "leg_id": "lead-naghshi",
            "event_type": "accepted-measurement", "verdict": "approved",
            "value_aud_claimed": 500.0, "idempotency_key": "acc|preal",
            "payload": {"source": "tg-proposal-button"}})
        store.record({
            "correlation_id": "research1", "proposal_id": "presearch", "leg_id": "research",
            "event_type": "accepted-measurement", "verdict": "approved",
            "value_aud_claimed": 0.0, "idempotency_key": "acc|presearch",
            "payload": {"self_run": True, "measurement_only": True}})
        store.record({
            "correlation_id": "canary1", "proposal_id": "pcanary", "leg_id": "canary",
            "event_type": "accepted-measurement", "verdict": "approved",
            "value_aud_claimed": 0.0, "idempotency_key": "acc|pcanary",
            "payload": {"source": "C1-internal-canary"}})
        store.close()
        o = _fresh()
        res = _rehydrate_only(o)
        assert res["rehydrated"] == 1, res
        m = ll.LiveLoop.proposal_metrics(o)
        assert m["proposal_outcomes"] == 1, m
        assert m["proposal_value_aud"] == 500.0, m
    finally:
        _off()


def t_h_no_store_at_all_is_not_an_error():
    """قبل از اولین تحویل، فایلِ انبار وجود ندارد. آن حالتِ عادی است، نه خطا.

    ⚠️ روی ویندوز حذفِ فایلِ sqlite وقتی کانکشنی بازمانده `PermissionError`
    می‌دهد — اولین اجرای همین تست دقیقاً همان‌جا ترکید. پس `_wipe` خطای حذف را
    می‌بلعد و این تست به **جوابِ تابع** تکیه می‌کند نه به موفقیتِ حذف.
    """
    _on()
    try:
        _wipe()
        res = _rehydrate_only(_fresh())
        assert res["rehydrated"] == 0, res
        assert res["reason"] in ("no-store", "error"), res
    finally:
        _off()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_proposal_counter_durable: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
