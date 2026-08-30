#!/usr/bin/env python3
"""گاردِ scoringِ run_all — «قرمزِ کاذبِ ۱۲۰» و revokeِ بی‌دلیل.

باگ (۲۰۲۶-۰۷-۳۰): پاسِ اولِ سوییت `subprocess.run` را **بدونِ capture** صدا می‌زد،
پس هر ~۳۶۶ فرزند کنسولِ مشترکِ والد را ارث می‌بردند. فرزندی که سالم است و `exit 0`
می‌دهد، زیرِ بار در **flushِ پایانیِ مفسر** شکست می‌خورد و **۱۲۰** برمی‌گرداند.
رانر ۱۲۰ را عیناً مثلِ AssertionError می‌شمرد، برچسب را در `failed` می‌گذاشت و
هر `failed` غیرخالی `revoke_capability()` را صدا می‌زند.

شواهدِ روی دیسک (`_ops/tests/_flaky`، ۴۱ رکورد):
    ۳۳ × exit(1)=120 exit(2)=0   ← تستِ سالم، قرمز شمرده شد
     ۶ × exit(1)=1   exit(2)=1   ← قرمزِ واقعیِ پایدار
     ۲ × exit(1)=1   exit(2)=0   ← لرزشِ واقعی (حکمِ تست بود، نه محیط)

سه ناوردی که این فایل گارد می‌کند:
  ۱. مکانیزم — فرزندِ >۶۴KB با `exit 0` زیرِ capture سالم است؛ روی sinkِ مشترکِ
     شکسته همان فرزند غیرصفر می‌شود و فرزندِ بافرشده **دقیقاً ۱۲۰** می‌دهد.
  ۲. رانر واقعاً همان شکلِ صدا زدن را دارد (ASTِ خودِ run_all.py).
  ۳. scoring — همه‌ی شکست‌ها (چه artifactِ مشکوکِ کنسول، چه لرزشِ واقعیِ
     `1 → 0`) در `failed` می‌مانند و revoke می‌کنند — fail-closedِ همیشگی،
     رأیِ مالکِ ۲۰۲۶-۰۷-۳۰ (مستند در خودِ run_all.py: پاک‌کردنِ خودکارِ برچسب
     برای ۱۲۰-سپس-سبز عمداً غیرفعال شد، چون ۱۲۰ می‌تواند حکمِ واقعیِ تست هم
     باشد). فرق تنها در حاشیه‌نویسیِ رکوردِ `_flaky` است. ناوردی ۳ با اجرای
     **حلقهٔ واقعیِ** run_all در درختِ موقت سنجیده می‌شود، نه با بازنویسیِ
     منطق در تست.

اجرا: python -X utf8 test_run_all_scoring.py
"""
import harness

ENV = harness.setup("run-all-scoring")   # ORG_ROOT/OPS_DIR موقت — قبل از هر importِ _ops

import ast                     # noqa: E402
import os                      # noqa: E402
import shutil                  # noqa: E402
import subprocess              # noqa: E402
import sys                     # noqa: E402
import tempfile                # noqa: E402
import unittest                # noqa: E402
from pathlib import Path       # noqa: E402

HERE = Path(__file__).resolve().parent
RUN_ALL = HERE / "run_all.py"

sys.path.insert(0, str(HERE))
import run_all                 # noqa: E402  — فقط stdlib؛ حلقه زیرِ __main__ است پس اجرا نمی‌شود

LOUD = 250_000        # > ۶۴KB — همان آستانه‌ای که در بریف خواسته شده

# فرزندی که پرحرف است و **سالم** خارج می‌شود.
_CHILD_LOUD = (
    "import sys\n"
    "sys.stdout.write('z' * {n})\n"
    "sys.stdout.write('\\nLOUD-OK\\n')\n"
    "sys.exit(0)\n"
).format(n=LOUD)

# فرزندی که کم می‌نویسد: نوشته در بافرِ ۸KB می‌ماند و flush در **خروجِ مفسر**
# اتفاق می‌افتد. اگر آن لحظه sink شکسته باشد، مفسر ۱۲۰ برمی‌گرداند.
_CHILD_BUFFERED = (
    "import sys\n"
    "sys.stdout.write('y' * 1024)\n"
    "sys.exit(0)\n"
)


def _broken_shared_sink():
    """لولهٔ بدونِ خواننده — مدلِ کنسولِ مشترکِ زیرِ بار (همان چیزی که capture حذفش می‌کند)."""
    rd, wr = os.pipe()
    os.close(rd)
    return wr


def _child_two_pass(first_exit: int, payload: int = 0) -> str:
    """اجرای اول: exit=first_exit ؛ اجرای دوم (retryِ رانر): exit 0. قطعی، بی‌نیاز به بار."""
    return (
        "import os, sys\n"
        "flag = os.path.abspath(__file__) + '.seen'\n"
        "if os.path.exists(flag):\n"
        "    sys.stdout.write('retry-green\\n')\n"
        "    sys.exit(0)\n"
        "open(flag, 'w').close()\n"
        "sys.stdout.write('q' * {p})\n"
        "sys.exit({e})\n"
    ).format(p=payload, e=first_exit)


# استابِ capability_gate: تنها کاری که می‌کند ثبتِ شاهد است تا ببینیم رانر
# revoke کرد یا mark. (گیتِ واقعی هرگز در این تست لمس نمی‌شود.)
_GATE_STUB = (
    "import os\n"
    "from pathlib import Path\n"
    "_W = Path(os.environ['CAP_WITNESS'])\n"
    "def mark_capability(evidence: str) -> bool:\n"
    "    _W.open('a', encoding='utf-8').write('MARK\\n')\n"
    "    return True\n"
    "def revoke_capability() -> None:\n"
    "    _W.open('a', encoding='utf-8').write('REVOKE\\n')\n"
)


class Mechanism(unittest.TestCase):
    """ناوردی ۱ — خودِ مکانیزم، مستقل از run_all و مستقل از بار."""

    def _child(self, body: str) -> str:
        d = Path(tempfile.mkdtemp(prefix="runall-mech-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        f = d / "child.py"
        f.write_text(body, encoding="utf-8")
        return str(f)

    def test_loud_child_exit0_is_pass_when_captured(self):
        """فرزندِ >۶۴KB که `exit 0` می‌دهد، زیرِ capture باید PASS شمرده شود."""
        r = subprocess.run([sys.executable, "-X", "utf8", self._child(_CHILD_LOUD)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(r.returncode, 0, f"فرزندِ سالم غیرصفر شد: {r.returncode}")
        self.assertGreater(len(r.stdout), 64 * 1024,
                           "بارِ تست زیرِ ۶۴KB افتاد — گارد بی‌معنی می‌شود")
        self.assertIn("LOUD-OK", r.stdout, "خروجیِ فرزند کامل به والد نرسید")

    def test_same_loud_child_goes_red_on_a_shared_broken_sink(self):
        """همان فرزندِ سالم، روی sinkِ مشترکِ شکسته → غیرصفر. این همان قرمزِ کاذب است."""
        wr = _broken_shared_sink()
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", self._child(_CHILD_LOUD)],
                               stdout=wr, stderr=subprocess.DEVNULL, timeout=120)
        finally:
            os.close(wr)
        self.assertNotEqual(r.returncode, 0,
                            "sinkِ شکسته باید فرزند را غیرصفر کند؛ وگرنه این تست چیزی ثابت نمی‌کند")

    def test_buffered_child_returns_exactly_120_on_shared_broken_sink(self):
        """کدِ مستندشده در `_flaky`: flushِ ناموفق در خروجِ مفسر ⇒ **دقیقاً ۱۲۰**."""
        path = self._child(_CHILD_BUFFERED)
        wr = _broken_shared_sink()
        try:
            red = subprocess.run([sys.executable, "-X", "utf8", path],
                                 stdout=wr, stderr=subprocess.DEVNULL, timeout=120)
        finally:
            os.close(wr)
        self.assertEqual(red.returncode, 120,
                         f"انتظار ۱۲۰ (flushِ ناموفق)، دریافت {red.returncode}")
        green = subprocess.run([sys.executable, "-X", "utf8", path],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(green.returncode, 0,
                         "همان فرزند زیرِ capture باید سبز باشد — capture علتِ ۱۲۰ را حذف می‌کند")


class RunnerCallShape(unittest.TestCase):
    """ناوردی ۲ — رانر واقعاً پاسِ اول را capture می‌کند (ASTِ خودِ فایل)."""

    def _first_pass_call(self) -> ast.Call:
        tree = ast.parse(RUN_ALL.read_text(encoding="utf-8"))
        main = [n for n in tree.body
                if isinstance(n, ast.If) and "__main__" in ast.dump(n.test)]
        self.assertTrue(main, "بلوکِ __main__ در run_all.py پیدا نشد")
        calls = [n for n in ast.walk(main[-1])
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
        self.assertGreaterEqual(len(calls), 2,
                                "انتظار دو subprocess.run (پاسِ اول + retryِ تشخیصِ لرزش)")
        calls.sort(key=lambda n: (n.lineno, n.col_offset))
        return calls[0]      # اولی به ترتیبِ منبع = پاسِ اول

    def test_first_pass_is_captured(self):
        kw = {k.arg: k.value for k in self._first_pass_call().keywords}
        self.assertIn("capture_output", kw,
                      "پاسِ اولِ run_all بدونِ capture_output است ⇒ کنسولِ مشترک ⇒ قرمزِ کاذبِ ۱۲۰")
        node = kw["capture_output"]
        self.assertTrue(isinstance(node, ast.Constant) and node.value is True,
                        "capture_output باید ثابتِ True باشد")

    def test_first_pass_decodes_child_output_safely(self):
        kw = {k.arg: k.value for k in self._first_pass_call().keywords}
        for name, want in (("text", True), ("encoding", "utf-8"), ("errors", "replace")):
            self.assertIn(name, kw, f"{name} در پاسِ اول ست نشده")
            self.assertEqual(getattr(kw[name], "value", None), want,
                             f"{name} باید {want!r} باشد (خروجیِ فارسی/باینری نباید رانر را بکشد)")


class ScoringUnit(unittest.TestCase):
    """ناوردی ۳الف — جدولِ حقیقتِ تابعِ واقعیِ scoring."""

    def test_interpreter_code_then_green_is_not_a_test_failure(self):
        self.assertTrue(run_all.is_infra_false_red(120, 0))

    def test_genuine_flake_stays_a_failure(self):
        """`1 → 0` (دو رکورد در `_flaky`) حکمِ تست بود؛ نباید سبز شمرده شود."""
        self.assertFalse(run_all.is_infra_false_red(1, 0))

    def test_persistent_red_stays_a_failure(self):
        self.assertFalse(run_all.is_infra_false_red(1, 1))
        self.assertFalse(run_all.is_infra_false_red(120, 120))
        self.assertFalse(run_all.is_infra_false_red(120, 1))

    def test_120_is_the_registered_interpreter_code(self):
        self.assertIn(120, run_all.INFRA_EXIT_CODES)


class ScoringEndToEnd(unittest.TestCase):
    """ناوردی ۳ب — **حلقهٔ واقعیِ** run_all روی درختِ موقت با فرزندهای ساختگی.

    منطقِ scoring در تست بازنویسی نمی‌شود؛ خودِ فایل اجرا می‌شود و تصمیمش
    (exit code + mark/revoke) سنجیده می‌شود.
    """

    def _tree(self, children: dict) -> tuple:
        root = Path(tempfile.mkdtemp(prefix="runall-e2e-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        tests = root / "_ops" / "tests"
        tests.mkdir(parents=True)
        budget = root / "_ops" / "budget"
        budget.mkdir(parents=True)
        (budget / "capability_gate.py").write_text(_GATE_STUB, encoding="utf-8")
        for name, body in children.items():
            (tests / name).write_text(body, encoding="utf-8")

        src = RUN_ALL.read_text(encoding="utf-8")
        marker = 'if __name__ == "__main__":'
        head, sep, tail = src.partition(marker)
        self.assertTrue(sep, "شکلِ run_all عوض شده — بلوکِ __main__ پیدا نشد")
        # فقط فهرستِ تست‌ها جایگزین می‌شود؛ حلقه/scoring/گیت دست‌نخورده می‌ماند.
        inject = "TESTS = {!r}\nEXTRA_TESTS = []\n\n".format(list(children))
        (tests / "run_all.py").write_text(head + inject + sep + tail, encoding="utf-8")
        return root, tests

    def _run(self, children: dict) -> tuple:
        root, tests = self._tree(children)
        witness = root / "witness.txt"
        witness.write_text("", encoding="utf-8")
        env = dict(os.environ)
        env.update(CAP_WITNESS=str(witness), ORG_ROOT=str(root),
                   OPS_DIR=str(root / "_ops"), REAL_VAULT=str(root))
        r = subprocess.run([sys.executable, "-X", "utf8", str(tests / "run_all.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300, cwd=str(tests), env=env)
        return r, witness.read_text(encoding="utf-8"), tests

    def test_loud_healthy_child_is_scored_green_and_keeps_capability(self):
        """گاردِ اصلی: فرزندِ >۶۴KB با `exit 0` ⇒ سوییت سبز، capability marked."""
        r, w, _ = self._run({"test_loud_ok.py": _CHILD_LOUD})
        self.assertEqual(r.returncode, 0, f"سوییت باید سبز باشد.\n{r.stdout[-3000:]}")
        self.assertIn("MARK", w, "capability باید mark شود")
        self.assertNotIn("REVOKE", w, "revokeِ بی‌دلیل روی تستِ سالم")
        self.assertIn("LOUD-OK", r.stdout, "والد خروجیِ فرزند را بازپخش نکرد")

    def test_exit120_then_green_is_still_revoked_but_annotated_as_infra_suspect(self):
        """۲۰۲۶-۰۷-۳۰ (رأیِ مالک، مستند در خودِ run_all.py): پاک‌کردنِ برچسب برای
        قرمزِ کاذبِ ۱۲۰-سپس-سبز عمداً غیرفعال شد — چون ۱۲۰ می‌تواند حکمِ واقعیِ
        تست هم باشد (Py_FinalizeEx می‌تواند AssertionError را هم با ۱۲۰
        بازنویسی کند)؛ پاک‌کردنِ خودکار یعنی fail-OPEN روی گیتِ پول. پس امروز:
        قرمزِ کاذب هم مثلِ لرزشِ واقعی در failed می‌ماند و revoke می‌کند — تنها
        فرق، حاشیه‌نویسیِ رکوردِ `_flaky` است که این مورد را «مشکوک به
        artifactِ کنسول» و fail-closed علامت می‌زند تا دفعهٔ بعد حدس نزنیم."""
        r, w, tests = self._run({"test_flush120.py": _child_two_pass(120)})
        self.assertEqual(r.returncode, 1,
                         f"سیاستِ fail-closedِ همیشگی: قرمزِ کاذب هم باید سوییت را قرمز نگه دارد.\n{r.stdout[-3000:]}")
        self.assertIn("REVOKE", w, "قرمزِ کاذب هم باید revoke کند (fail-closedِ عمدیِ ۲۰۲۶-۰۷-۳۰)")
        self.assertNotIn("MARK", w)
        rec = (tests / "_flaky" / "test_flush120.py.txt").read_text(encoding="utf-8")
        self.assertIn("exit(1)=120 exit(2)=0", rec, "شواهدِ لرزش ثبت نشد")
        self.assertIn("fail-closed", rec,
                      "رکورد باید موردِ مشکوک به artifactِ کنسول را fail-closed علامت بزند")

    def test_genuine_flake_still_revokes_contract_unchanged(self):
        """`1 → 0` لرزشِ واقعی است: در failed می‌ماند و revoke می‌کند (fail-closed)."""
        r, w, _ = self._run({"test_real_flake.py": _child_two_pass(1)})
        self.assertEqual(r.returncode, 1, "لرزشِ واقعی نباید سبز شمرده شود")
        self.assertIn("REVOKE", w, "قراردادِ fail-closed شکست — لرزشِ واقعی باید revoke کند")
        self.assertNotIn("MARK", w)

    def test_persistent_red_revokes(self):
        r, w, _ = self._run({"test_hard_red.py": "import sys\nsys.exit(1)\n"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("REVOKE", w)
        self.assertNotIn("MARK", w)

    def test_mutating_capture_out_of_the_first_pass_turns_green_into_red(self):
        """مویتیشنِ خودکار: اگر capture از پاسِ اول برداشته شود و sink مشترک/شکسته
        باشد، همان فرزندِ سالم قرمز می‌شود. اثباتِ اینکه گارد تزئینی نیست."""
        root, tests = self._tree({"test_loud_ok.py": _CHILD_LOUD})
        runner = tests / "run_all.py"
        src = runner.read_text(encoding="utf-8")
        mutated = src.replace(
            'r = subprocess.run(cmd, cwd=str(p.parent), timeout=300,\n'
            '                           capture_output=True, text=True,\n'
            '                           encoding="utf-8", errors="replace", env=_guarded_env())',
            'r = subprocess.run(cmd, cwd=str(p.parent), timeout=300)')
        self.assertNotEqual(src, mutated, "الگوی پاسِ اول پیدا نشد — مویتیشن اعمال نشد")
        runner.write_text(mutated, encoding="utf-8")

        witness = root / "witness.txt"
        witness.write_text("", encoding="utf-8")
        env = dict(os.environ)
        env.update(CAP_WITNESS=str(witness), ORG_ROOT=str(root),
                   OPS_DIR=str(root / "_ops"), REAL_VAULT=str(root))
        wr = _broken_shared_sink()          # کنسولِ مشترکِ شکسته را به رانر می‌دهیم
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", str(runner)],
                               stdout=wr, stderr=subprocess.DEVNULL,
                               timeout=300, cwd=str(tests), env=env)
        finally:
            os.close(wr)
        self.assertNotEqual(r.returncode, 0,
                            "نسخهٔ مویتیت‌شده سبز ماند ⇒ گارد چیزی را نگه نمی‌دارد")


if __name__ == "__main__":
    unittest.main(verbosity=2)
