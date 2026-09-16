# 182-owned independent falsify. Do not import/run pc-worker test_once_cycle.py.
# Scope: isolated sandbox only. No 182 production. No inbox drain. No c3f085a8.
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'pc-worker-ref'))

from once_cycle import Worker, main_buggy, main_fixed  # noqa: E402

PROD = HERE / 'octopus_witness_worker.py.prodcopy'


class IndependentOnceFalsify(unittest.TestCase):
    def test_A_prod_main_never_calls_cycle(self):
        tree = ast.parse(PROD.read_text(encoding='utf-8'))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        names = []
        for c in ast.walk(main):
            if isinstance(c, ast.Call):
                if isinstance(c.func, ast.Attribute):
                    names.append(c.func.attr)
                elif isinstance(c.func, ast.Name):
                    names.append(c.func.id)
        self.assertNotIn('cycle', names)

    def test_B_buggy_once_is_noop(self):
        rc, w = main_buggy(['--once'], ['a', 'b', 'c'])
        self.assertEqual(rc, 0)
        self.assertEqual(w.cycle_calls, 0)
        self.assertEqual(w.claimed, [])

    def test_C_fixed_once_invokes_cycle(self):
        rc, w = main_fixed(['--once'], ['a', 'b', 'c'])
        self.assertEqual(rc, 0)
        self.assertEqual(w.cycle_calls, 1)

    def test_D_stampede_250_to_1(self):
        items = [f'x{i}' for i in range(250)]
        rc, w = main_fixed(['--once'], items)
        self.assertEqual(rc, 0)
        self.assertEqual(len(w.claimed), 1)
        self.assertEqual(w.claimed[0], 'x0')
        self.assertEqual(len(items), 250)

    def test_E_no_event_empty_inbox_exit_0(self):
        rc, w = main_fixed(['--once'], [])
        self.assertEqual(rc, 0)
        self.assertEqual(w.cycle_calls, 1)
        self.assertEqual(w.claimed, [])

    def test_F_crash_test_does_not_cycle(self):
        rc, w = main_fixed(['--crash-test'], ['keep', 'out'])
        self.assertEqual(rc, 0)
        self.assertEqual(w.cycle_calls, 0)
        self.assertEqual(w.claimed, [])

    def test_G_max_n_1_without_one_claim_flag(self):
        w = Worker([f'n{i}' for i in range(12)])
        out = w.cycle(max_n=1, one_claim=False)
        self.assertEqual(out['claimed'], 1)
        self.assertEqual(len(w.claimed), 1)


if __name__ == '__main__':
    r = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if r.result.wasSuccessful() else 1)
