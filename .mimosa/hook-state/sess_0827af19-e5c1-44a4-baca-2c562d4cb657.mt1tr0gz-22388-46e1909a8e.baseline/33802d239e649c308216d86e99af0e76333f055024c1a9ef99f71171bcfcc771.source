#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_live_state_guard.py — گاردِ برشِ ۰ را می‌سنجد.

ادعایی که این فایل نگه می‌دارد: **سوییت صفر بایت زیرِ `_ops/state` ِ زنده عوض نکند.**

نکتهٔ طراحیِ ایمنی — چرا ریشه در تست جابه‌جا می‌شود:
    بردارهای مخرب (`unlink`، `truncate`، `replace`) را فقط وقتی می‌شود کامل سنجید
    که هدف **واقعاً وجود داشته باشد**. اگر همان‌ها را روی `F:\\backup\\_ops\\state`
    بسنجیم، هر جهشِ موفق (یعنی گاردِ شکسته) یک فایلِ زندهٔ واقعی را پاک می‌کند —
    یعنی جهش‌آزمودنِ گارد خودش خطرِ همان چیزی می‌شود که گارد جلویش را می‌گیرد.
    پس `REAL_VAULT` به یک درختِ موقت می‌رود و گارد **همان کدِ واقعی** را روی آن
    اجرا می‌کند؛ و اینکه ریشهٔ پیش‌فرض واقعاً درختِ زنده است، جداگانه و بدونِ هیچ
    نوشتنی assert می‌شود (`t_default_root_is_the_live_tree`).
"""
from __future__ import annotations

import os
import socket
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import live_state_guard as G  # noqa: E402


class GuardCase(unittest.TestCase):
    def setUp(self):
        self._env = {k: os.environ.get(k) for k in ("REAL_VAULT", "OCTOPUS_TEST_ISOLATION_LOG")}
        self._tmp = tempfile.mkdtemp(prefix="guard-root-")
        os.environ["REAL_VAULT"] = self._tmp
        os.environ.pop("OCTOPUS_TEST_ISOLATION_LOG", None)   # ثبتِ بیرونی در تست لازم نیست
        self.state = Path(self._tmp) / "_ops" / "state"
        self.state.mkdir(parents=True, exist_ok=True)
        G.disarm()
        G.reset()
        G.arm("block")

    def tearDown(self):
        G.disarm()
        G.reset()
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        # حفاظتِ ریشهٔ **واقعی** را برگردان: اگر این فایل زیرِ runner ِ ایزوله بدود،
        # پروسه بعد از این تست باید همچنان درختِ زنده را محافظت کند.
        if (os.environ.get("OCTOPUS_TEST_LIVE_STATE_GUARD") or "").strip():
            G.arm()

    # ── ۱. هر بردارِ نوشتن مسدود می‌شود ───────────────────────────────────────
    def t_every_write_vector_raises(self):
        f = self.state / "victim.txt"
        G.disarm(); f.write_text("original", "utf-8"); G.arm("block")
        d = self.state / "sub"
        G.disarm(); d.mkdir(exist_ok=True); G.arm("block")

        vectors = {
            "open-w":        lambda: open(f, "w"),
            "open-a":        lambda: open(f, "a"),
            "open-r+":       lambda: open(f, "r+"),
            "path-write":    lambda: f.write_text("mutated", "utf-8"),
            "path-bytes":    lambda: f.write_bytes(b"mutated"),
            "os.open":       lambda: os.open(str(f), os.O_WRONLY),
            "os.replace":    lambda: os.replace(str(f), str(f) + ".moved"),
            "os.rename":     lambda: os.rename(str(f), str(f) + ".moved"),
            "os.remove":     lambda: os.remove(str(f)),
            "os.unlink":     lambda: os.unlink(str(f)),
            "path-unlink":   lambda: f.unlink(),
            "os.rmdir":      lambda: os.rmdir(str(d)),
            "os.mkdir-new":  lambda: os.mkdir(str(self.state / "brand-new")),
            "os.makedirs":   lambda: os.makedirs(str(self.state / "a" / "b")),
            "os.truncate":   lambda: os.truncate(str(f), 0),
            "sqlite-rw":     lambda: sqlite3.connect(str(self.state / "new.db")),
        }
        for name, fn in vectors.items():
            with self.subTest(vector=name):
                with self.assertRaises(G.LiveStateWriteError, msg=f"{name} مسدود نشد"):
                    fn()
        # و مهم‌تر از استثنا: **جهان عوض نشده**
        self.assertEqual(f.read_text("utf-8"), "original", "محتوای فایل عوض شد")
        self.assertTrue(d.is_dir(), "پوشه حذف شد")
        self.assertFalse((self.state / "brand-new").exists())
        self.assertFalse((self.state / "new.db").exists())

    # ── ۲. خواندن هرگز مسدود نمی‌شود ─────────────────────────────────────────
    def t_reads_are_never_blocked(self):
        f = self.state / "readable.txt"
        G.disarm(); f.write_text("payload", "utf-8"); G.arm("block")
        self.assertEqual(open(f, "r").read(), "payload")
        self.assertEqual(f.read_text("utf-8"), "payload")
        db = self.state / "ro.db"
        G.disarm(); sqlite3.connect(str(db)).close(); G.arm("block")
        uri = "file:" + str(db).replace("\\", "/") + "?mode=ro"
        sqlite3.connect(uri, uri=True).close()          # نباید استثنا بدهد

    # ── ۳. بیرونِ ریشه آزاد است (state ِ خودِ worktree قربانی نشود) ────────────
    def t_paths_outside_the_root_are_untouched(self):
        other = Path(tempfile.mkdtemp(prefix="not-live-")) / "x.txt"
        other.write_text("ok", "utf-8")                 # نباید استثنا بدهد
        self.assertEqual(other.read_text("utf-8"), "ok")
        self.assertIsNone(G._inside(other))

    # ── ۴. عبور با `..` — اول resolve، بعد قضاوت ─────────────────────────────
    def t_traversal_cannot_escape_the_check(self):
        # شکلِ **واقعیِ** فرار: مسیری که لفظاً با ریشه شروع نمی‌شود ولی به داخلِ آن
        # resolve می‌شود. (نسخهٔ اولِ این تست `state/../state/x` بود — که چون رشته‌اش
        # همچنان با `state\` شروع می‌شد، حتی گاردِ بی‌abspath هم می‌گرفتش؛ جهش‌آزمایی
        # نشان داد آن تست کور بود، نه گارد.)
        escape = self.state.parent / "other" / ".." / "state" / "sneak.txt"
        self.assertFalse(os.path.normcase(str(escape)).startswith(
            os.path.normcase(str(self.state)) + os.sep),
            "فیکسچر باید مسیری باشد که با زیررشته گرفته **نمی‌شود**")
        with self.assertRaises(G.LiveStateWriteError):
            open(escape, "w")
        self.assertFalse((self.state / "sneak.txt").exists())
        # و شکلِ سادهٔ درون-ریشه هم همچنان گرفته شود
        with self.assertRaises(G.LiveStateWriteError):
            open(self.state / ".." / "state" / "plain.txt", "w")
        self.assertFalse((self.state / "plain.txt").exists())

    # ── ۵. صفر-بایتی از جهش تفکیک می‌شود ────────────────────────────────────
    def t_zero_byte_ops_are_recorded_but_not_blocked(self):
        d = self.state / "already"
        G.disarm(); d.mkdir(exist_ok=True); G.reset(); G.arm("block")
        d.mkdir(parents=True, exist_ok=True)            # هست ⇒ صفر بایت ⇒ عبور
        (self.state / "ghost.txt").unlink(missing_ok=True)   # نیست ⇒ صفر بایت ⇒ عبور
        self.assertEqual(G.violations(), [], "عملیاتِ صفر-بایتی نباید جهش شمرده شود")
        benign = G.violations(include_benign=True)
        self.assertGreaterEqual(len(benign), 2, "نشتیِ اشاره‌ای باید ثبت شده باشد")
        self.assertTrue(all(v["benign"] for v in benign))

    # ── ۶. استثنا فقط اعلام‌شده ──────────────────────────────────────────────
    def t_allowed_writes_are_declared_and_recorded(self):
        f = self.state / "declared.txt"
        with G.allow_live_write("سنجهٔ گارد"):
            f.write_text("through", "utf-8")            # عبور می‌کند
        self.assertEqual(f.read_text("utf-8"), "through")
        self.assertEqual(G.violations(), [], "عبورِ اعلام‌شده نباید جهشِ بی‌اجازه شمرده شود")
        rec = G.violations(include_allowed=True)
        self.assertTrue(rec and rec[0]["allowed"] and rec[0]["reason"] == "سنجهٔ گارد")
        with self.assertRaises(ValueError):
            with G.allow_live_write(""):                # بی‌دلیل مجاز نیست
                pass
        # و اجازه نشت نمی‌کند: بعد از خروج از context دوباره مسدود است
        with self.assertRaises(G.LiveStateWriteError):
            f.write_text("after", "utf-8")

    # ── ۷. disarm واقعاً برمی‌گرداند ────────────────────────────────────────
    def t_disarm_restores_the_originals(self):
        G.disarm()
        f = self.state / "after-disarm.txt"
        f.write_text("free", "utf-8")
        self.assertEqual(f.read_text("utf-8"), "free")
        self.assertFalse(G.is_armed())

    # ── ۸. گاردِ شبکه ───────────────────────────────────────────────────────
    def t_external_network_is_blocked_loopback_is_not(self):
        G.arm_network()
        try:
            with self.assertRaises(G.ExternalNetworkError):
                socket.create_connection(("93.184.216.34", 80), timeout=2)
            with self.assertRaises(G.ExternalNetworkError):
                socket.socket().connect(("smtp.gmail.com", 587))
            # loopback نباید *توسط گارد* رد شود؛ خطای شبکه مجاز است.
            # هر دو شکلِ timeout سنجیده می‌شود: کلیدواژه‌ای **و موضعی**. شکلِ موضعی
            # رگرسیونِ واقعی بود — wrapper عددِ timeout را آدرس می‌خواند و loopback را
            # رد می‌کرد (`test_lead_boundary_http` قرمز شد).
            for label, call in (
                ("timeout کلیدواژه‌ای", lambda: socket.create_connection(("127.0.0.1", 9), timeout=0.3)),
                ("timeout موضعی",      lambda: socket.create_connection(("127.0.0.1", 9), 0.3)),
                ("متدِ سوکت",           lambda: socket.socket().connect(("127.0.0.1", 9))),
            ):
                try:
                    call().close()
                except G.ExternalNetworkError:
                    self.fail(f"loopback نباید مسدود شود ({label})")
                except (OSError, AttributeError):
                    pass
            # و آدرسِ گزارش‌شده باید خودِ آدرس باشد، نه timeout
            G._net_hits.clear()
            with self.assertRaises(G.ExternalNetworkError):
                socket.create_connection(("93.184.216.34", 80), 2)
            self.assertIn("93.184.216.34", G.network_hits()[-1]["addr"],
                          "آدرسِ گزارش‌شده باید میزبانِ واقعی باشد")
        finally:
            G.disarm()

    # ── ۹. هر دو ریشهٔ پیش‌فرض واقعاً درختِ زنده‌اند (بدونِ هیچ نوشتنی) ─────────
    def t_default_root_is_the_live_tree(self):
        saved = os.environ.pop("REAL_VAULT", None)
        try:
            roots = G.live_state_roots()
        finally:
            if saved is not None:
                os.environ["REAL_VAULT"] = saved
        self.assertEqual(len(roots), 2)
        self.assertEqual(roots[0], os.path.normcase(os.path.abspath(
            os.path.join(G.REAL_VAULT_DEFAULT, "_ops", "state"))))
        self.assertEqual(roots[1], os.path.normcase(os.path.abspath(
            os.path.join(G.REAL_VAULT_DEFAULT, "_ops", "agi2027_runtime"))))
        # و state/agi2027_runtime ِ خودِ این worktree زیرِ هیچ‌کدام نیست — وگرنه گارد
        # کلِ سوییت را می‌کُشت
        wt_state = str(_HERE.parent / "state")
        wt_runtime = str(_HERE.parent / "agi2027_runtime")
        for root in roots:
            self.assertFalse(os.path.normcase(os.path.abspath(wt_state)).startswith(root + os.sep))
            self.assertFalse(os.path.normcase(os.path.abspath(wt_runtime)).startswith(root + os.sep))


def _load():
    s = unittest.TestSuite()
    for name in sorted(n for n in dir(GuardCase) if n.startswith("t_")):
        s.addTest(GuardCase(name))
    return s


if __name__ == "__main__":
    r = unittest.TextTestRunner(verbosity=2).run(_load())
    print(f"\n{'✅' if r.wasSuccessful() else '❌'} test_live_state_guard: "
          f"{r.testsRun - len(r.failures) - len(r.errors)}/{r.testsRun}")
    sys.exit(0 if r.wasSuccessful() else 1)
