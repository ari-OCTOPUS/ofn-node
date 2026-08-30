"""test_arbiter_consensus_rule — «اجماع» با یک متحرک و دو ثابت، دروغ است.

گامِ ۱۰ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C11).

سنجشِ زندهٔ ۰۸-۰۳ که این قاعده را لازم کرد: داور `driver="consensus"`،
`n_present=3` و `color=GREEN` منتشر می‌کرد، در حالی که از سه قلب:

  · cardiac      یک ثابتِ ریاضی بود (۴۲.۴۲۶۴s از ۰۷-۲۸؛ mass روی کفِ ۱.۰ پین است
                 چون فقط از organهای بودجه و attribution.confirmed رشد می‌کند که ۰ است)
  · control_law  ۵.۵ ساعت دقیقاً ۶۰.۰ می‌داد، و هر ~۲۲۰s نوشته ولی هر تیک خوانده
                 می‌شد — چهار تیک از پنج، یک اسنپ‌شاتِ نگه‌داشته‌شده رأیِ زنده شمرده می‌شد
  · rhythm       تنها متحرک؛ ۱۰۰٪ حرکتِ اجماع فقط نویزِ ۱/f همین یکی بود

قاعده: **حضور رأی نیست؛ حرکت رأی است.** وقتی `n_moving <= 1`، مقدارِ `driver`
حق ندارد `consensus` باشد.

قراردادِ رشته پیش از فرود با AST شمرده شد: تنها مصرف‌کننده
`OCTOPUS-DOCTOR/doctor/scanner.py` است که فقط `.startswith("brake")` را تست
می‌کند، و هیچ‌جای درخت `== "consensus"` مقایسه نمی‌شود. پس تغییر امن است.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("arbiter-consensus-rule")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from heart import pulse_arbiter as pa   # noqa: E402


def _v(name, period, mode, braking=False, color="GREEN"):
    return pa._vote(name, period, braking, 1.0, color=color, mode=mode)


def t_one_mover_is_solo_not_consensus():
    """بارِ اصلی: یک متحرک + دو ثابت ⇒ `solo:<name>`، هرگز `consensus`."""
    out = pa.arbitrate([_v("cardiac", 42.43, "CONSTANT"),
                        _v("control_law", 60.0, "HELD"),
                        _v("rhythm", 70.4, "LIVE")])
    assert out["driver"] == "solo:rhythm", f"باید solo:rhythm باشد، شد {out['driver']!r}"
    assert out["driver"] != "consensus"
    assert out["n_present"] == 3, out
    assert out["n_moving"] == 1, out
    assert out["n_held"] == 1 and out["n_constant"] == 1, out


def t_two_movers_is_still_consensus():
    """جفتِ لازم: با دو متحرکِ واقعی، «اجماع» دوباره معنا دارد."""
    out = pa.arbitrate([_v("cardiac", 42.43, "CONSTANT"),
                        _v("control_law", 60.0, "LIVE"),
                        _v("rhythm", 70.4, "LIVE")])
    assert out["driver"] == "consensus", f"با دو متحرک باید اجماع باشد، شد {out['driver']!r}"
    assert out["n_moving"] == 2, out


def t_zero_movers_is_frozen_never_consensus():
    """جهشِ سند: ریتم را ثابت کن ⇒ n_moving=0 و driver **نباید** consensus باشد."""
    out = pa.arbitrate([_v("cardiac", 42.43, "CONSTANT"),
                        _v("control_law", 60.0, "HELD"),
                        _v("rhythm", 70.4, "CONSTANT")])
    assert out["n_moving"] == 0, out
    assert out["driver"] != "consensus", f"با صفر متحرک اجماع اعلام شد: {out['driver']!r}"
    assert out["driver"] == "frozen", out["driver"]


def t_brake_still_wins_over_the_new_rule():
    """رگرسیون: ترمز غالب است و پیشوندِ `brake:` دست‌نخورده می‌ماند.

    `scanner.py` روی همین `.startswith("brake")` تکیه دارد؛ اگر قاعدهٔ تازه آن را
    بشکند، یک هشدارِ واقعیِ دکتر بی‌صدا ناپدید می‌شود.
    """
    out = pa.arbitrate([_v("cardiac", 42.43, "CONSTANT", braking=True, color="AMBER"),
                        _v("rhythm", 70.4, "LIVE")])
    assert out["driver"].startswith("brake"), out["driver"]
    assert "cardiac" in out["driver"], out["driver"]


def t_counts_are_exhaustive():
    """هر رأیِ حاضر دقیقاً در یکی از چهار سطل بیفتد — وگرنه شمارش دروغ می‌گوید."""
    votes = [_v("cardiac", 42.43, "CONSTANT"),
             _v("control_law", 60.0, "HELD"),
             _v("rhythm", 70.4, "LIVE")]
    out = pa.arbitrate(votes)
    total = (out["n_moving"] + out["n_held"] + out["n_constant"]
             + out["n_unknown_mode"])
    assert total == out["n_present"], f"{total} != n_present {out['n_present']}"


def t_unknown_mode_does_not_count_as_moving():
    """«نمی‌دانم» نباید به‌عنوان حرفِ تازه شمرده شود."""
    out = pa.arbitrate([_v("cardiac", 42.43, "UNKNOWN"),
                        _v("control_law", 60.0, "UNKNOWN"),
                        _v("rhythm", 70.4, "LIVE")])
    assert out["n_moving"] == 1, out
    assert out["n_unknown_mode"] == 2, out
    assert out["driver"] == "solo:rhythm", out["driver"]


def t_vote_carries_the_three_new_fields():
    v = _v("x", 60.0, "HELD")
    for key in ("mode", "dof", "last_change_ts"):
        assert key in v, f"رأی فیلدِ {key} را ندارد"
    assert pa._vote("y", 1.0, False, 1.0, mode="nonsense")["mode"] == "UNKNOWN", \
        "حالتِ نامعتبر باید به UNKNOWN بیفتد، نه اینکه عبور کند"


def t_cardiac_is_stamped_constant_while_mass_is_pinned():
    """تمبرِ ساختاری: mass روی کف ⇒ CONSTANT، بدونِ نیاز به تاریخچه."""
    snap = {"enabled": True, "bio_rhythm": {"period_s": 42.4264, "mass": 1.0,
                                            "pace": "mice"},
            "budget": {"depleted": False}, "baroreflex_factor": 1.0}
    v = pa._cardiac_vote(snap)
    assert v["mode"] == "CONSTANT", f"mass پین‌شده باید CONSTANT بدهد، شد {v['mode']}"
    assert v["dof"] == 1, v
    moved = dict(snap)
    moved["bio_rhythm"] = dict(snap["bio_rhythm"], mass=4.0, period_s=30.0)
    v2 = pa._cardiac_vote(moved)
    assert v2["mode"] == "LIVE", f"mass ِ رشدکرده باید LIVE بدهد، شد {v2['mode']}"


def t_control_law_is_stamped_held_when_the_snapshot_is_old():
    """ظرفی که کندتر نوشته می‌شود از آنکه خوانده شود، HELD است نه LIVE."""
    import provenance as prov
    old = prov.parse_ts("2026-08-03T00:00:00")
    rec_old = {"ts": "2026-08-03T00:00:00", "period_s": 60.0, "telemetry": {"gates": {}}}
    v = pa._control_vote(rec_old)
    assert v["mode"] in ("HELD", "UNKNOWN"), f"اسنپ‌شاتِ کهنه LIVE شمرده شد: {v['mode']}"
    assert old is not None


def t_no_production_consumer_branches_on_the_driver_string():
    """گاردِ قرارداد: هیچ کدِ **تولیدی** نباید روی برابری با «consensus» شاخه بزند.

    `driver` یک قراردادِ رشته‌ای است. `scanner.py` فقط `.startswith("brake")` را
    می‌سنجد که امن است، ولی هر مصرف‌کننده‌ای که `== "consensus"` بنویسد با این
    تغییر بی‌صدا رفتارش عوض می‌شود.

    تست‌ها عمداً مستثنا هستند: تستی که قرارداد را assert می‌کند سالم است (و یکی
    هست — `test_pulse_arbiter.py::t_consensus_acceleration` با سه رأیِ LIVE، جایی
    که اجماع واقعاً درست است). خطر، شاخه‌زدنِ کدِ تولیدی است نه ادعای تست.

    نکتهٔ روش: نسخهٔ اولِ همین گارد تست‌ها را هم می‌شمرد و قرمز شد — و همان قرمز
    نشان داد گرپِ دستیِ من پیش‌تر سقف خورده بود و فهرست را ناقص دیده بودم.
    """
    import subprocess
    r = subprocess.run(["git", "grep", "-n", '== "consensus"', "--", "*.py"],
                       cwd=str(_OPS.parent), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    hits = []
    for ln in (r.stdout or "").splitlines():
        path = ln.split(":", 1)[0].replace("\\", "/")
        if "/tests/" in path or path.startswith(("4d_system/", "PRE-0/", "03 - Projects/")):
            continue
        hits.append(ln)
    assert not hits, f"مصرف‌کنندهٔ تولیدیِ برابری با «consensus» پیدا شد: {hits[:3]}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_arbiter_consensus_rule: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
