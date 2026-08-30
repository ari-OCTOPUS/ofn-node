"""کارتِ راکد باید دیده شود و بشود از راکدی درش آورد.

رأیِ مالک ۲۰۲۶-۰۸-۰۵: «کارت‌های راکد گزینش هست کار نمی‌کند؛ آدم ببیند از
راکدی درش بیاورد.» تا آن روز `/api/lifecycle` فقط **عدد** می‌داد — ۲۹ کارتِ
راکد، قدیمی‌ترین ~۱۰ روز — و هیچ سطحی برای تصمیم وجود نداشت: تنها راه دکمهٔ
اینلاینِ تلگرام با توکنِ امضاشده بود و تحویلِ کارت خاموش است.

سه چیز این‌جا قفل می‌شود:
  ۱. `fold()` فهرست را **برمی‌گرداند** (قبلاً می‌ساخت و روی زمین می‌ریخت).
  ۲. نمای مینی‌اپ allowlist ِ صریح دارد — nonce/token/summary هرگز رد نمی‌شوند.
  ۳. `decide_rfc` واقعاً کارت را از STALLED بیرون می‌برد و ردیفی می‌سازد که
     `OCTOPUS-doctor-day` برمی‌دارد.

هیچ‌کدام به درختِ زنده دست نمی‌زنند: هر مورد ذخیرهٔ خودش را در tmp می‌سازد.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for _d in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "telegram_center")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import lifecycle_fold as lf            # noqa: E402
import miniapp_state as ms             # noqa: E402
from agi2027_control.ops_actions import OctopusOpsDB   # noqa: E402


def _store(now, **overrides):
    """یک کارتِ راکد + یک کارتِ تصمیم‌گرفته‌شده."""
    base = {
        "rfc:RFC-stale": {"kind": "rfc", "rfc_id": "RFC-stale", "summary": "متنِ محرمانه",
                          "owner": "6150431610", "nonce": "deadbeefdeadbeef",
                          "token_sha256": "cafebabecafebabe", "expires_at": str(now + 9999),
                          "delivery": "SENT", "decision": "SUBMITTED",
                          "created_ts": str(now - 864000), "updated_ts": str(now)},
        "rfc:RFC-done": {"kind": "rfc", "rfc_id": "RFC-done", "summary": "s2",
                         "owner": "6150431610", "nonce": "aa", "token_sha256": "bb",
                         "expires_at": str(now + 9999),
                         "delivery": "SENT", "decision": "DECIDED",
                         "created_ts": str(now - 3600), "updated_ts": str(now)},
    }
    base.update(overrides)
    return base


class StalledRig(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="stalled-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.state = self.tmp / "_ops" / "state"
        (self.state / "pulse").mkdir(parents=True)
        self.now = int(time.time())
        (self.state / "pulse" / "pending-cards.json").write_text(
            json.dumps(_store(self.now)), encoding="utf-8")
        # ⚠️ بدونِ این، `decide_rfc` به `_ops/state` ِ **زنده** می‌خورد.
        self._prev = os.environ.get("OCTOPUS_STATE_DIR")
        os.environ["OCTOPUS_STATE_DIR"] = str(self.state)
        self.addCleanup(self._restore)

    def _restore(self):
        if self._prev is None:
            os.environ.pop("OCTOPUS_STATE_DIR", None)
        else:
            os.environ["OCTOPUS_STATE_DIR"] = self._prev

    def _db(self):
        db = OctopusOpsDB(db_path=self.tmp / "ops.sqlite3")
        self.addCleanup(db.conn.close)
        return db

    def _fold(self):
        return lf.fold(str(self.state), now=float(self.now))


class FoldReturnsIdentity(StalledRig):
    def test_fold_returns_the_stalled_list(self):
        """پیش از این، فهرست ساخته می‌شد و **برنمی‌گشت**."""
        f = self._fold()
        self.assertIn("stalled_list", f, "fold هویتِ راکدها را برنمی‌گرداند")
        ids = [r.get("rfc_id") for r in f["stalled_list"]]
        self.assertEqual(ids, ["RFC-stale"], "فقط کارتِ راکد باید در فهرست باشد")

    def test_decided_card_is_not_in_the_list(self):
        f = self._fold()
        self.assertNotIn("RFC-done", [r.get("rfc_id") for r in f["stalled_list"]])

    def test_count_and_list_agree(self):
        """عددی که کارت را می‌سازد و فهرستی که دکمه می‌سازد نباید واگرا شوند."""
        f = self._fold()
        self.assertEqual(f["by_stage"]["STALLED"], len(f["stalled_list"]))

    def test_cap_is_announced_not_silent(self):
        big = {f"rfc:RFC-{i:03d}": {"kind": "rfc", "rfc_id": f"RFC-{i:03d}",
                                    "summary": "s", "owner": "1", "nonce": "n",
                                    "token_sha256": "t", "expires_at": str(self.now + 99),
                                    "delivery": "SENT", "decision": "SUBMITTED",
                                    "created_ts": str(self.now - 100 * i),
                                    "updated_ts": str(self.now)}
               for i in range(lf.STALLED_LIST_CAP + 7)}
        (self.state / "pulse" / "pending-cards.json").write_text(
            json.dumps(big), encoding="utf-8")
        f = self._fold()
        self.assertEqual(len(f["stalled_list"]), lf.STALLED_LIST_CAP)
        self.assertEqual(f["stalled_list_truncated"], 7,
                         "بریدنِ بی‌صدا از «همه را دیدی» غیرقابلِ تشخیص است")


class ProjectionIsContentFree(StalledRig):
    def test_only_three_fields_cross_the_boundary(self):
        rows = ms._lifecycle_stalled_rows(self._fold(), float(self.now))
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(set(r), {"rfc_id", "created_ts", "age_days"},
                             f"فیلدِ غیرمنتظره از مرز رد شد: {sorted(set(r))}")

    def test_credential_material_never_appears(self):
        """رکوردِ خام nonce و token_sha256 دارد — هیچ‌کدام نباید رد شوند."""
        blob = json.dumps(ms._lifecycle_stalled_rows(self._fold(), float(self.now)))
        for secret in ("deadbeefdeadbeef", "cafebabecafebabe", "محرمانه", "6150431610"):
            self.assertNotIn(secret, blob, f"{secret!r} از مرزِ چرخهٔ عمر رد شد")

    def test_age_is_computed_server_side(self):
        rows = ms._lifecycle_stalled_rows(self._fold(), float(self.now))
        self.assertAlmostEqual(rows[0]["age_days"], 10.0, delta=0.05,
                               msg="سن باید سمتِ سرور حساب شود، نه با ساعتِ دستگاه")

    def test_oldest_first(self):
        two = _store(self.now)
        two["rfc:RFC-new"] = dict(two["rfc:RFC-stale"], rfc_id="RFC-new",
                                  created_ts=str(self.now - 60))
        (self.state / "pulse" / "pending-cards.json").write_text(
            json.dumps(two), encoding="utf-8")
        rows = ms._lifecycle_stalled_rows(self._fold(), float(self.now))
        self.assertEqual([r["rfc_id"] for r in rows], ["RFC-stale", "RFC-new"],
                         "قدیمی‌ترین باید اول باشد — ترتیب خودش پیام است")


class GuardStaysNarrow(StalledRig):
    """استثنای `rfc_id` نباید دیوار را سست کرده باشد."""

    def test_the_exception_is_exactly_one_key(self):
        self.assertEqual(set(ms.LIFECYCLE_KEY_EXCEPTIONS), {"rfc_id"})

    def test_every_other_forbidden_key_still_raises(self):
        for bad in ("nonce", "token_sha256", "summary", "owner_id", "verdict",
                    "chat_id", "user", "secret", "expires_at"):
            with self.assertRaises(ValueError, msg=f"{bad} باید رد شود"):
                ms._lifecycle_enforce({bad: "x"})

    def test_exception_is_exact_match_not_substring(self):
        """`rfc_id_summary` و `owner_rfc_id` باید همچنان بیفتند."""
        for bad in ("rfc_id_summary", "owner_rfc_id", "rfc_id_token"):
            with self.assertRaises(ValueError, msg=f"{bad} از استثنا سوءاستفاده کرد"):
                ms._lifecycle_enforce({bad: "x"})

    def test_values_are_never_exempt(self):
        """کلیدِ مجاز با مقدارِ آلوده باز هم باید بیفتد."""
        with self.assertRaises(ValueError):
            ms._lifecycle_enforce({"rfc_id": "nonce=deadbeef"})


class DecisionActuallyUnstalls(StalledRig):
    def test_approve_moves_the_card_out_of_stalled(self):
        before = self._fold()
        self.assertEqual(before["by_stage"]["STALLED"], 1)
        res = self._db().decide_rfc({"rfc_id": "RFC-stale"}, "merge-approved")
        self.assertEqual(res.get("status"), "APPLIED", res)
        after = self._fold()
        self.assertEqual(after["by_stage"]["STALLED"], 0,
                         "کارت بعد از تصمیم باید از رکود بیرون بیاید")
        self.assertEqual(after["stalled_list"], [])

    def test_the_verdict_row_the_doctor_claims_exists(self):
        """بدونِ این ردیف، تصمیم یک no-op ِ بی‌صداست."""
        self._db().decide_rfc({"rfc_id": "RFC-stale"}, "merge-approved")
        led = self.state / "doctor" / "rfc-verdicts.db"
        self.assertTrue(led.exists(), "دفترِ حکم ساخته نشد")
        import sqlite3
        con = sqlite3.connect(str(led))
        try:
            row = con.execute("SELECT verdict,state FROM rfc_decision "
                              "WHERE rfc_id='RFC-stale'").fetchone()
        finally:
            con.close()
        self.assertEqual(row, ("merge-approved", "DECIDED"))

    def test_deny_is_a_distinct_verdict(self):
        self._db().decide_rfc({"rfc_id": "RFC-stale"}, "denied")
        import sqlite3
        con = sqlite3.connect(str(self.state / "doctor" / "rfc-verdicts.db"))
        try:
            v = con.execute("SELECT verdict FROM rfc_decision "
                            "WHERE rfc_id='RFC-stale'").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(v, "denied", "رد و پذیرش نباید یک ردیفِ یکسان بسازند")

    def test_second_decision_is_blocked_not_silently_ok(self):
        db = self._db()
        self.assertEqual(db.decide_rfc({"rfc_id": "RFC-stale"}, "merge-approved")["status"],
                         "APPLIED")
        again = db.decide_rfc({"rfc_id": "RFC-stale"}, "denied")
        self.assertEqual(again["status"], "BLOCKED")
        self.assertEqual(again["reason"], "already_decided")

    def test_unknown_card_is_blocked(self):
        r = self._db().decide_rfc({"rfc_id": "RFC-typo"}, "merge-approved")
        self.assertEqual((r["status"], r["reason"]), ("BLOCKED", "rfc_card_not_found"))

    def test_missing_id_is_blocked(self):
        r = self._db().decide_rfc({}, "merge-approved")
        self.assertEqual((r["status"], r["reason"]), ("BLOCKED", "missing_rfc_id"))

    def test_already_decided_card_cannot_be_re_decided(self):
        r = self._db().decide_rfc({"rfc_id": "RFC-done"}, "merge-approved")
        self.assertEqual(r["status"], "BLOCKED")

    def test_a_false_from_persist_is_never_reported_as_applied(self):
        """`persist_rfc_verdict` استثنا را می‌بلعد و False می‌دهد.

        اگر False را APPLIED گزارش کنیم، دقیقاً همان «✅ ِ تو هیچ نکرد» را
        ساخته‌ایم که کلِ این کار برای بستنش بود.
        """
        import outcomes.pending_card_recovery as pcr
        orig = pcr.persist_rfc_verdict
        pcr.persist_rfc_verdict = lambda **kw: False
        self.addCleanup(setattr, pcr, "persist_rfc_verdict", orig)
        r = self._db().decide_rfc({"rfc_id": "RFC-stale"}, "merge-approved")
        self.assertEqual(r["status"], "ERROR")
        self.assertFalse(r["ok"])


class ActionsAreAllowlisted(unittest.TestCase):
    def test_both_verbs_are_on_the_allowlist(self):
        from agi2027_control.ops_actions import ALLOWED_ACTIONS
        self.assertIn("rfc.approve", ALLOWED_ACTIONS)
        self.assertIn("rfc.deny", ALLOWED_ACTIONS)

    def test_the_dispatcher_actually_routes_them(self):
        """گرهِ AST: فعلِ allowlist-شده‌ای که در dispatch نیست = ۴۰۰ ِ خاموش."""
        import ast
        src = (_OPS / "agi2027_control" / "ops_actions.py").read_text(encoding="utf-8")
        routed = set()
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name):
                continue
            if node.left.id != "action":
                continue
            for c in node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    routed.add(c.value)
        from agi2027_control.ops_actions import ALLOWED_ACTIONS
        missing = sorted(set(ALLOWED_ACTIONS) - routed)
        self.assertEqual(missing, [],
                         f"در allowlist هست ولی dispatch ندارد: {missing}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
