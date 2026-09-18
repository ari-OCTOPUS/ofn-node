import subprocess
import unittest
from w1_auditable import capture

class ProbeTests(unittest.TestCase):
    def fake(self, process_rc=1, unit_rc=0, throws=False):
        def run(args,**kwargs):
            if args[0]=='pgrep':
                if throws: raise subprocess.TimeoutExpired(args,10)
                return subprocess.CompletedProcess(args,process_rc,'42\n' if process_rc==0 else '','')
            return subprocess.CompletedProcess(args,unit_rc,'LoadState=loaded\nActiveState=inactive\nExecMainStartTimestamp=Thu 2026-09-17 07:18:41 UTC\nNRestarts=0\n','')
        return run
    def test_no_process_is_measured(self):
        row=capture(self.fake()); self.assertEqual(row['probe_status'],'OK'); self.assertEqual(row['apply_procs'],[])
    def test_timeout_is_unknown_not_empty_success(self):
        row=capture(self.fake(throws=True)); self.assertEqual(row['probe_status'],'ERROR'); self.assertIsNone(row['apply_procs'])
    def test_pgrep_error_is_not_absence(self):
        self.assertEqual(capture(self.fake(process_rc=2))['probe_status'],'ERROR')
    def test_unit_error_is_not_success(self):
        self.assertEqual(capture(self.fake(unit_rc=1))['probe_status'],'ERROR')
    def test_process_observation_retained(self):
        self.assertEqual(capture(self.fake(process_rc=0))['apply_procs'],['42'])

if __name__ == '__main__': unittest.main()
