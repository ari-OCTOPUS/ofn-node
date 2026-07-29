#!/usr/bin/env python3
"""تستِ پروبِ رانشِ فلگ.

معیارِ اصلی (ابطال‌پذیریِ ساختاری): یک فلگ را در فایل عوض کن و snapshot را
دست نزن → `count` باید دقیقاً ۱ شود. اگر این تست سبز نشد، خودِ پروب دروغ می‌گوید.

اجرا هم با `python test_flag_drift.py` کار می‌کند هم با pytest.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flag_drift as fd  # noqa: E402


CRLF = "\r\n"


def _write_flags(path: Path, pairs, extra_lines=()):
    body = [f'@set "{k}={v}"' for k, v in pairs] + list(extra_lines)
    path.write_bytes((CRLF.join(body) + CRLF).encode("utf-8"))


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_last_definition_wins_and_duplicate_is_counted(self):
        f = self.tmp / "f.cmd"
        _write_flags(f, [("OCTOPUS_X", "0"), ("OCTOPUS_Y", "1"), ("OCTOPUS_X", "1")])
        flags, stats = fd.parse_flags_file(f)
        self.assertEqual(flags["OCTOPUS_X"], "1", "معناشناسیِ cmd: آخرین برنده است")
        self.assertIn("OCTOPUS_X", stats["duplicates"])
        self.assertEqual(stats["duplicates"]["OCTOPUS_X"], 2)

    def test_comments_are_ignored(self):
        f = self.tmp / "f.cmd"
        _write_flags(f, [("OCTOPUS_A", "1")],
                     ['rem @set "OCTOPUS_B=1"', ':: @set "OCTOPUS_C=1"'])
        flags, _ = fd.parse_flags_file(f)
        self.assertIn("OCTOPUS_A", flags)
        self.assertNotIn("OCTOPUS_B", flags)
        self.assertNotIn("OCTOPUS_C", flags)

    def test_bare_and_inline_set_forms(self):
        f = self.tmp / "f.cmd"
        f.write_bytes((CRLF.join([
            "set OCTOPUS_BARE=7",
            'if not defined OCTOPUS_INLINE set "OCTOPUS_INLINE=9"',
        ]) + CRLF).encode("utf-8"))
        flags, _ = fd.parse_flags_file(f)
        self.assertEqual(flags["OCTOPUS_BARE"], "7")
        self.assertEqual(flags["OCTOPUS_INLINE"], "9")

    def test_hygiene_counts_lone_lf(self):
        f = self.tmp / "f.cmd"
        f.write_bytes(b'@set "OCTOPUS_A=1"\r\n@set "OCTOPUS_B=1"\n')
        _flags, stats = fd.parse_flags_file(f)
        self.assertEqual(stats["crlf"], 1)
        self.assertEqual(stats["lone_lf"], 1, "LFِ تنها باید دیده شود — cmd را می‌شکند")


class SecretTests(unittest.TestCase):
    def test_secret_name_detection_is_conservative(self):
        for name in ("FUGU_API_KEY", "OCTOPUS_CB_SECRET", "TELEGRAM_BOT_TOKEN",
                     "SOME_PASSWORD", "X_CRED", "OWNER_AUTH_X"):
            self.assertTrue(fd.is_secret_name(name), name)
        for name in ("OCTOPUS_TG_TOPIC_REPLY", "PAID_HTTP_TIMEOUT_S",
                     "OCTOPUS_WIRE_COHERENCE"):
            self.assertFalse(fd.is_secret_name(name), name)

    def test_secret_values_never_appear_in_snapshot_or_probe(self):
        tmp = Path(tempfile.mkdtemp())
        f, s = tmp / "f.cmd", tmp / "snap.json"
        _write_flags(f, [("FUGU_API_KEY", "sk-live-DO-NOT-LEAK"),
                         ("OCTOPUS_TG_TOPIC_REPLY", "1")])
        fd.snapshot(f, s, env={"FUGU_API_KEY": "sk-live-DO-NOT-LEAK",
                               "OCTOPUS_TG_TOPIC_REPLY": "1"})
        blob = s.read_text(encoding="utf-8")
        self.assertNotIn("sk-live-DO-NOT-LEAK", blob)
        self.assertIn(fd.REDACTED, blob)

        _write_flags(f, [("FUGU_API_KEY", "sk-live-ROTATED"),
                         ("OCTOPUS_TG_TOPIC_REPLY", "1")])
        res = fd.probe(f, s)
        self.assertNotIn("sk-live-ROTATED", json.dumps(res, ensure_ascii=False))
        self.assertNotIn("sk-live-DO-NOT-LEAK", json.dumps(res, ensure_ascii=False))
        self.assertIn("FUGU_API_KEY", res["secrets_not_compared"])


class DriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.f = self.tmp / "OCTOPUS-flags.cmd"
        self.s = self.tmp / "flags-loaded.json"

    def test_no_snapshot_never_reports_green(self):
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        res = fd.probe(self.f, self.s)
        self.assertEqual(res["status"], "no_snapshot")
        self.assertEqual(res["count"], 0)
        self.assertIn("hint", res)

    def test_snapshot_matching_file_reports_zero_drift(self):
        _write_flags(self.f, [("OCTOPUS_A", "1"), ("OCTOPUS_B", "0")])
        fd.snapshot(self.f, self.s, env={"OCTOPUS_A": "1", "OCTOPUS_B": "0"})
        res = fd.probe(self.f, self.s)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["count"], 0, res.get("drifted"))

    def test_THE_INVARIANT_arm_without_restart_yields_exactly_one_drift(self):
        """قلبِ ماجرا: فلگ در فایل عوض شد، پروسه ری‌استارت نشد → دقیقاً ۱."""
        _write_flags(self.f, [("OCTOPUS_TG_TOPIC_REPLY", "0"), ("OCTOPUS_B", "1")])
        fd.snapshot(self.f, self.s,
                    env={"OCTOPUS_TG_TOPIC_REPLY": "0", "OCTOPUS_B": "1"})
        # مالک فلگ را مسلح می‌کند و ری‌استارت نمی‌کند — سناریوی واقعیِ ۲۷ جولای
        _write_flags(self.f, [("OCTOPUS_TG_TOPIC_REPLY", "1"), ("OCTOPUS_B", "1")])
        res = fd.probe(self.f, self.s)
        self.assertEqual(res["count"], 1, res.get("drifted"))
        d = res["drifted"][0]
        self.assertEqual(d["name"], "OCTOPUS_TG_TOPIC_REPLY")
        self.assertEqual((d["loaded"], d["armed"], d["kind"]), ("0", "1", "changed"))
        self.assertTrue(res["file_changed_since_snapshot"])

    def test_added_and_removed_are_distinguished(self):
        _write_flags(self.f, [("OCTOPUS_OLD", "1")])
        fd.snapshot(self.f, self.s, env={"OCTOPUS_OLD": "1"})
        _write_flags(self.f, [("OCTOPUS_NEW", "1")])
        res = fd.probe(self.f, self.s)
        kinds = {d["name"]: d["kind"] for d in res["drifted"]}
        self.assertEqual(kinds.get("OCTOPUS_NEW"), "added")
        self.assertEqual(kinds.get("OCTOPUS_OLD"), "removed")

    def test_untracked_env_keys_are_ignored(self):
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        fd.snapshot(self.f, self.s, env={"OCTOPUS_A": "1", "PATH": "/usr/bin",
                                         "USERNAME": "x"})
        res = fd.probe(self.f, self.s)
        self.assertEqual(res["count"], 0)

    def test_probe_is_fail_soft_on_missing_file(self):
        res = fd.probe(self.tmp / "nope.cmd", self.s)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["drifted"], [])

    def test_render_never_raises_for_any_status(self):
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        for res in (fd.probe(self.f, self.s),
                    fd.probe(self.tmp / "nope.cmd", self.s)):
            self.assertIsInstance(fd.render(res), str)
        fd.snapshot(self.f, self.s, env={"OCTOPUS_A": "0"})
        self.assertIsInstance(fd.render(fd.probe(self.f, self.s)), str)


class RealVaultShapeTests(unittest.TestCase):
    """اگر فایلِ واقعیِ فلگ کنارِ ماژول بود، شکلش را هم چک کن — ولی نبودش
    نباید سوئیت را قرمز کند (تستِ محیط‌وابسته هرگز گیتِ اصلی نیست)."""

    def test_real_flags_file_parses_if_present(self):
        real = Path(__file__).resolve().parents[1] / "OCTOPUS-flags.cmd"
        if not real.exists():
            self.skipTest("OCTOPUS-flags.cmd در این درخت نیست")
        flags, stats = fd.parse_flags_file(real)
        self.assertGreater(stats["defined"], 20)
        self.assertEqual(stats["lone_lf"], 0,
                         "فایلِ .cmd نباید LFِ تنها داشته باشد (گاتچای ابزارِ Edit)")


class PerProcessTests(unittest.TestCase):
    """۲۰۲۶-۰۷-۲۹ — سیم‌کشی به boot. سه ناوردی که بدونشان پروب بی‌ارزش است."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.f = self.tmp / "OCTOPUS-flags.cmd"

    def test_two_processes_do_not_clobber_each_other(self):
        """قلبِ per-process: organism ِ کهنه نباید پشتِ center ِ تازه پنهان شود."""
        _write_flags(self.f, [("OCTOPUS_A", "0")])
        fd.snapshot_boot("organism", self.f, self.tmp, env={"OCTOPUS_A": "0"})
        _write_flags(self.f, [("OCTOPUS_A", "1")])      # مالک مسلح می‌کند
        fd.snapshot_boot("center", self.f, self.tmp, env={"OCTOPUS_A": "1"})

        res = fd.probe_all(self.f, self.tmp)
        by = {p["proc"]: p for p in res["procs"]}
        self.assertEqual(set(by), {"organism", "center"}, "هر دو باید دیده شوند")
        self.assertEqual(by["organism"]["count"], 1, "organism کدِ کهنه دارد")
        self.assertEqual(by["center"]["count"], 0, "center تازه بوت شده")
        self.assertEqual(res["stale_procs"], 1)
        self.assertIn("organism", fd.render_all(res))

    def test_env_only_var_is_not_drift(self):
        """کلیدهای .env هرگز در فایلِ فلگ نیستند — شمردنشان = پروبِ همیشه‌قرمز."""
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        fd.snapshot_boot("organism", self.f, self.tmp, env={
            "OCTOPUS_A": "1",
            "TELEGRAM_ALLOWED_CHAT_IDS": "123",   # از .env می‌آید، نه از .cmd
            "TELEGRAM_OWNER_CHAT_ID": "456",
        })
        res = fd.probe_all(self.f, self.tmp)
        self.assertEqual(res["count"], 0, res.get("drifted"))

    def test_real_drift_still_caught_next_to_env_only_vars(self):
        """جهشِ عمدی: مبادا فیکسِ بالا پروب را کور کرده باشد."""
        _write_flags(self.f, [("OCTOPUS_A", "0")])
        fd.snapshot_boot("organism", self.f, self.tmp,
                         env={"OCTOPUS_A": "0", "TELEGRAM_ALLOWED_CHAT_IDS": "1"})
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        res = fd.probe_all(self.f, self.tmp)
        self.assertEqual(res["count"], 1, res.get("drifted"))
        self.assertEqual(res["drifted"][0]["name"], "OCTOPUS_A")
        self.assertEqual(res["drifted"][0]["proc"], "organism")

    def test_deleted_flag_is_still_reported_as_removed(self):
        """فلگی که *بود* و حذف شد، رانش است — دامنه نباید این را ببلعد."""
        _write_flags(self.f, [("OCTOPUS_GONE", "1")])
        fd.snapshot_boot("organism", self.f, self.tmp, env={"OCTOPUS_GONE": "1"})
        _write_flags(self.f, [("OCTOPUS_OTHER", "1")])
        res = fd.probe_all(self.f, self.tmp)
        kinds = {d["name"]: d["kind"] for d in res["drifted"]}
        self.assertEqual(kinds.get("OCTOPUS_GONE"), "removed")
        self.assertEqual(kinds.get("OCTOPUS_OTHER"), "added")

    def test_probe_all_without_snapshots_never_reports_green(self):
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        res = fd.probe_all(self.f, self.tmp)
        self.assertEqual(res["status"], "no_snapshot")
        self.assertEqual(res["count"], 0)
        self.assertIsInstance(fd.render_all(res), str)

    def test_snapshot_boot_is_absolutely_fail_soft(self):
        """در مسیرِ بوتِ ارگانیسمِ زنده است — حق ندارد چیزی را بکشد."""
        self.assertIsNone(
            fd.snapshot_boot("x", self.tmp / "does-not-exist.cmd", self.tmp))

    def test_proc_slug_cannot_escape_state_dir(self):
        p = fd.snapshot_path_for("../../evil", self.tmp)
        self.assertEqual(p.parent.resolve(), self.tmp.resolve())

    def test_secret_values_never_leak_through_per_process_layer(self):
        _write_flags(self.f, [("FUGU_API_KEY", "sk-live-DO-NOT-LEAK")])
        fd.snapshot_boot("organism", self.f, self.tmp,
                         env={"FUGU_API_KEY": "sk-live-DO-NOT-LEAK"})
        blob = json.dumps(fd.probe_all(self.f, self.tmp), ensure_ascii=False)
        blob += fd.render_all(fd.probe_all(self.f, self.tmp))
        blob += (self.tmp / "flags-loaded-organism.json").read_text(encoding="utf-8")
        self.assertNotIn("sk-live-DO-NOT-LEAK", blob)


class BootCallSiteTests(unittest.TestCase):
    """گاردِ ضدِ یتیمی — **متنِ منبعِ** نقاطِ بوت را می‌سنجد، نه شکلِ ماژول را.

    درسِ ثبت‌شده (mining_os، ۲۰۲۶-۰۷-۲۸): بسته‌ای با ۳۲ تستِ سبز، صفر صداکننده
    داشت؛ تستِ درون-بسته هرگز نمی‌پرسد «کسی صدایم می‌زند؟». اگر کسی این
    فراخوان‌ها را بردارد، این تست قرمز می‌شود — نه اینکه بی‌صدا بمیرد.
    """

    SITES = {
        "organism.py": "organism",
        "telegram_center/center.py": "center",
        "cortex/cortex.py": "cortex",
        "live/server.py": "live",
    }

    def test_every_entrypoint_snapshots_its_own_env_at_boot(self):
        root = Path(__file__).resolve().parents[1]
        missing = []
        for rel, proc in self.SITES.items():
            p = root / rel
            self.assertTrue(p.exists(), f"نقطهٔ بوت غایب است: {rel}")
            src = p.read_text(encoding="utf-8", errors="replace")
            if f'snapshot_boot("{proc}")' not in src:
                missing.append(rel)
        self.assertEqual(missing, [],
                         "این نقاطِ بوت دیگر snapshot نمی‌گیرند → پروبِ رانش کور می‌شود")

    def test_flags_card_uses_the_per_process_view(self):
        """اگر کارتِ /flags به probeِ تک‌فایلی برگردد، مالک دوباره یک پروسه را
        به‌جای همه می‌بیند — همان سبزِ دروغ."""
        src = (Path(__file__).resolve().parents[1] / "telegram_center"
               / "introspect_cmd.py").read_text(encoding="utf-8", errors="replace")
        self.assertIn("probe_all", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
