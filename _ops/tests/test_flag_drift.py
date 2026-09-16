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
import time
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
                     "SOME_PASSWORD", "X_CRED", "OWNER_AUTH_X",
                     "OCTOPUS_BOARD_CP_BEARER", "X_BEARER", "BEARER", "Bearer",
                     "AUTHORIZATION", "Authorization"):
            self.assertTrue(fd.is_secret_name(name), name)
        for name in ("OCTOPUS_TG_TOPIC_REPLY", "PAID_HTTP_TIMEOUT_S",
                     "OCTOPUS_WIRE_COHERENCE"):
            self.assertFalse(fd.is_secret_name(name), name)

    def test_bearer_name_redacts_snapshot_value(self):
        tmp = Path(tempfile.mkdtemp())
        flags = tmp / "f.cmd"
        snap = tmp / "snap.json"
        _write_flags(flags, [("OCTOPUS_BOARD_CP_BEARER", "FAKEVALUE_NOT_A_SECRET"),
                             ("OCTOPUS_TG_TOPIC_REPLY", "1")])
        fd.snapshot(flags, snap, env={
            "OCTOPUS_BOARD_CP_BEARER": "FAKEVALUE_NOT_A_SECRET",
            "OCTOPUS_TG_TOPIC_REPLY": "1",
        })
        blob = snap.read_text(encoding="utf-8")
        self.assertNotIn("FAKEVALUE_NOT_A_SECRET", blob)
        self.assertIn(fd.REDACTED, blob)
        self.assertIn("OCTOPUS_BOARD_CP_BEARER", blob)

    def test_chat_ids_are_treated_as_secrets(self):
        """۲۰۲۶-۰۷-۲۹: snapshotِ boot مقدارِ TELEGRAM_OWNER_CHAT_ID را خام
        می‌نوشت — هیچ توکنِ رازی نامش را نمی‌گرفت."""
        for name in ("TELEGRAM_OWNER_CHAT_ID", "TG_CENTER_CHAT_ID",
                     "TELEGRAM_ALLOWED_CHAT_IDS", "OCTOPUS_OWNER_ID"):
            self.assertTrue(fd.is_secret_name(name), name)
        # ولی نه هر چیزی که «ID» دارد — وگرنه فلگ‌های بی‌ضرر هم redact می‌شوند
        for name in ("OCTOPUS_WIRE_IDENTITY_EQ", "OCTOPUS_WIRE_IDEAS"):
            self.assertFalse(fd.is_secret_name(name), name)

    def test_miniapp_url_is_treated_as_a_secret(self):
        """VQ-CAPABILITY-URL-LEAK-001 (۲۰۲۶-۰۸-۰۳، برشِ ۳): OCTOPUS_MINIAPP_URL
        حاملِ اعتبار است (هر کسی داشته باشدش به تونلِ خصوصی می‌رسد) ولی هیچ
        توکنِ رازِ قبلی نامش را نمی‌گرفت — snapshot ِ boot خام می‌نوشتش."""
        self.assertTrue(fd.is_secret_name("OCTOPUS_MINIAPP_URL"))
        # ولی هر چیزی که فقط "URL" دارد نه — الگو دقیقاً MINIAPP_URL است
        for name in ("OCTOPUS_WEBHOOK_URL", "OCTOPUS_BASE_URL"):
            self.assertFalse(fd.is_secret_name(name), name)

    def test_snapshot_boot_never_writes_a_chat_id(self):
        """گاردِ end-to-end: مقدارِ شناسهٔ چت نباید در فایلِ روی دیسک باشد."""
        tmp = Path(tempfile.mkdtemp())
        f = tmp / "OCTOPUS-flags.cmd"
        _write_flags(f, [("OCTOPUS_A", "1")])
        fd.snapshot_boot("organism", f, tmp, env={
            "OCTOPUS_A": "1", "TELEGRAM_OWNER_CHAT_ID": "6150431610"})
        blob = (tmp / "flags-loaded-organism.json").read_text(encoding="utf-8")
        self.assertNotIn("6150431610", blob)
        self.assertIn(fd.REDACTED, blob)

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
    """Tracked declaration evidence remains testable when live-local flags are absent."""

    def test_real_flags_file_or_tracked_manifest_is_structurally_valid(self):
        ops = Path(__file__).resolve().parents[1]
        real = ops / "OCTOPUS-flags.cmd"
        if real.exists():
            flags, stats = fd.parse_flags_file(real)
            self.assertGreater(stats["defined"], 20)
            self.assertEqual(stats["lone_lf"], 0,
                             "فایلِ .cmd نباید LFِ تنها داشته باشد (گاتچای ابزارِ Edit)")
            return
        manifest = ops / "FLAG-NAMES-MANIFEST.txt"
        self.assertTrue(manifest.exists(), "نه flags.cmd هست نه manifest نام‌ها")
        names = [line.strip() for line in manifest.read_text("utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        self.assertGreater(len(names), 20)
        self.assertEqual(names, sorted(set(names)))
        self.assertTrue(all(name.startswith(("OCTOPUS_", "CORTEX_", "CHRONO_"))
                            for name in names))


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

    def test_legacy_snapshot_without_file_flags_keeps_old_behaviour(self):
        """شکافِ پوششی که راستی‌آزمایی گرفت: شاخهٔ سازگاریِ عقب‌رو فقط با
        خواندنِ کد ادعا شده بود، نه با اجرا."""
        _write_flags(self.f, [("OCTOPUS_A", "1")])
        fd.snapshot_boot("organism", self.f, self.tmp,
                         env={"OCTOPUS_A": "1", "OCTOPUS_ENVONLY": "1"})
        sp = self.tmp / "flags-loaded-organism.json"
        d = json.loads(sp.read_text(encoding="utf-8"))
        del d["file_flags"]                       # snapshotِ نسخهٔ قدیم
        sp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        res = fd.probe_all(self.f, self.tmp)
        kinds = {x["name"]: x["kind"] for x in res["drifted"]}
        self.assertEqual(kinds.get("OCTOPUS_ENVONLY"), "removed",
                         "بدونِ file_flags باید رفتارِ سابق (شمردنِ env-only) بماند")

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

    def test_card_is_rtl_safe(self):
        """۲۰۲۶-۰۷-۲۹ — از مشاهدهٔ کارتِ واقعی در گروه: نسخهٔ اول
        «center · بوت 0.1h پیش: 0» می‌ساخت و تلگرام آن را
        «center · 0.1h بوت پیش: 0» نشان می‌داد. عددِ لاتینِ برهنه داخلِ جملهٔ
        فارسی با bidi جابه‌جا می‌شود — هیچ تستی این را نمی‌گرفت چون
        رشته «درست» بود، فقط رندرش غلط بود."""
        _write_flags(self.f, [("OCTOPUS_A", "0")])
        fd.snapshot_boot("organism", self.f, self.tmp, env={"OCTOPUS_A": "0"})
        _write_flags(self.f, [("OCTOPUS_A", "1")])       # یک رانشِ واقعی
        for card in (fd.render_all(fd.probe_all(self.f, self.tmp)),
                     fd.render_all(fd.probe_all(self.f, self.tmp / "nope"))):
            self.assertIsInstance(card, str)
        card = fd.render_all(fd.probe_all(self.f, self.tmp))
        self.assertNotRegex(card, r"[0-9]",
                            "رقمِ لاتین در کارتِ فارسی = جابه‌جاییِ bidi")
        self.assertIn("⁦organism⁩", card,
                      "نامِ لاتین باید ایزولهٔ جهت داشته باشد")
        self.assertTrue(card.startswith("‏"),
                        "کارت باید با RLM شروع شود تا جهتِ پاراگراف قطعی باشد")

    def test_fa_num_and_age_helpers(self):
        self.assertEqual(fd.fa_num(4), "۴")
        self.assertEqual(fd.fa_num("0.1"), "۰٫۱")
        self.assertIn("دقیقه", fd._age_fa(time.time() - 300))
        self.assertIn("ساعت", fd._age_fa(time.time() - 7200))
        self.assertEqual(fd._age_fa("خراب"), "")      # fail-soft

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

    # (ب) ۲۰۲۶-۰۷-۲۹ — راستی‌آزماییِ متخاصم گرفت: snapshot قبل از گاردِ
    # تک‌نمونه/wired صدا زده می‌شد، پس پروسه‌ای که بلافاصله خارج می‌شود هم
    # boot_ts تازه می‌زد و snapshotِ پروسهٔ واقعی را بازنویسی می‌کرد. سناریوی
    # عینی: RUN-TG-CENTER.bat حلقهٔ ۱۰ثانیه‌ای است؛ بدونِ توکن هر ۱۰ ثانیه یک
    # «تازه بوت شدم» نوشته می‌شد در حالی که هیچ centerی زنده نبود.
    GUARDS = {
        "organism.py": "organism=START",
        "cortex/cortex.py": "cortex=START",
        "live/server.py": "live-cockpit=START",
        "telegram_center/center.py": "STOP-TG-CENTER هست",
    }

    def test_snapshot_is_taken_only_after_the_liveness_guard(self):
        root = Path(__file__).resolve().parents[1]
        late = []
        for rel, guard in self.GUARDS.items():
            src = (root / rel).read_text(encoding="utf-8", errors="replace")
            g, s = src.find(guard), src.find("snapshot_boot")
            self.assertGreaterEqual(g, 0, f"لنگرِ گارد در {rel} نیست")
            self.assertGreaterEqual(s, 0, f"snapshot_boot در {rel} نیست")
            if s < g:
                late.append(rel)
        self.assertEqual(late, [], "snapshot قبل از گاردِ زنده‌بودن گرفته می‌شود "
                                   "→ پروسهٔ در حالِ خروج هم boot_ts تازه می‌زند")

    def test_center_main_block_is_last_so_late_defs_bind(self):
        """(الف) در center.py بلوکِ __main__ وسطِ فایل بود و run_forever تا STOP
        بلاک می‌کند، پس `def _introspect` که بعدش می‌آمد هرگز تعریف نمی‌شد و
        /flags در پروسهٔ زنده NameError می‌داد — در حالی که تست‌ها (که import
        می‌کنند) سبز بودند. الگوی «تستِ سبز روی مسیرِ مرده»."""
        src = (Path(__file__).resolve().parents[1] / "telegram_center"
               / "center.py").read_text(encoding="utf-8", errors="replace")
        i_main = src.find('if __name__ == "__main__":')
        self.assertGreaterEqual(i_main, 0)
        after = src[i_main:]
        stray = [ln for ln in after.splitlines()
                 if ln.startswith("def ") or ln.startswith("class ")]
        self.assertEqual(stray, [], "این تعریف‌ها بعد از بلوکِ __main__ آمده‌اند "
                                    "و در پروسهٔ زنده هرگز bind نمی‌شوند")

    def test_flags_card_uses_the_per_process_view(self):
        """اگر کارتِ /flags به probeِ تک‌فایلی برگردد، مالک دوباره یک پروسه را
        به‌جای همه می‌بیند — همان سبزِ دروغ."""
        src = (Path(__file__).resolve().parents[1] / "telegram_center"
               / "introspect_cmd.py").read_text(encoding="utf-8", errors="replace")
        self.assertIn("probe_all", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
