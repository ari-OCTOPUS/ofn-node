"""Deliberate fixtures test verdict boundaries, not runtime evidence."""
import copy
import datetime as dt
import unittest
from evaluate_w1 import evaluate, SERVICES, PATHS

def fixture(n=2):
    t = dt.datetime(2026,9,17,8,28,19,tzinfo=dt.timezone.utc)
    units = {u:{'ExecMainStartTimestamp':'Thu 2026-09-17 07:18:41 UTC','NRestarts':'0','ActiveState':'inactive'} for u in SERVICES}
    units.update({u:{'ActiveState':'active'} for u in PATHS})
    rows = [{'event':'W1_START','ts':t.isoformat(),'baseline':copy.deepcopy(units)}]
    for i in range(n):
        rows.append({'sample':i,'ts':(t+dt.timedelta(seconds=i*300)).isoformat(),'units':copy.deepcopy(units),'apply_procs':[]})
    return rows

class WitnessTests(unittest.TestCase):
    def test_incomplete_never_passes(self):
        self.assertEqual(evaluate(fixture())['status'],'RUNNING')
    def test_reactivation_fails(self):
        rows=fixture(); rows[2]['units'][SERVICES[0]]['NRestarts']='1'
        self.assertEqual(evaluate(rows)['status'],'FAIL_OPEN_DEBUG')
    def test_process_fails(self):
        rows=fixture(); rows[1]['apply_procs']=['42 apply_signed_inbound']
        self.assertEqual(evaluate(rows)['status'],'FAIL_OPEN_DEBUG')
    def test_missing_unit_is_error(self):
        rows=fixture(); rows[1]['units'][SERVICES[0]]={}
        self.assertEqual(evaluate(rows)['status'],'ERROR')
    def test_missing_sample_is_error(self):
        rows=fixture(); rows[2]['sample']=2
        self.assertEqual(evaluate(rows)['status'],'ERROR')
    def test_disabled_watcher_is_not_pass(self):
        rows=fixture(); rows[2]['units'][PATHS[0]]['ActiveState']='inactive'
        self.assertEqual(evaluate(rows)['status'],'ERROR')
    def test_premature_completion_is_error(self):
        rows=fixture(); rows.append({'event':'W1_COMPLETED_BOUND_REACHED','ts':rows[-1]['ts']})
        self.assertEqual(evaluate(rows)['status'],'ERROR')
    def test_full_legacy_window_is_unvalidated(self):
        rows=fixture(288)
        rows.append({'event':'W1_COMPLETED_BOUND_REACHED','ts':'2026-09-18T08:28:19+00:00'})
        self.assertEqual(evaluate(rows)['status'],'UNVALIDATED')

    def test_complete_v2_measured_with_explicit_probe_success(self):
        rows=fixture(288)
        rows[0].update(collector_version=2,probe_status='OK')
        for row in rows[1:]: row['probe_status']='OK'
        rows.append({'event':'W1_COMPLETED_BOUND_REACHED','ts':'2026-09-18T08:28:19+00:00','elapsed_monotonic_seconds':86400})
        self.assertEqual(evaluate(rows)['status'],'MEASURED_24H_SAMPLED_FROZEN')
        rows[7]['probe_status']='ERROR'
        self.assertEqual(evaluate(rows)['status'],'ERROR')

if __name__ == '__main__': unittest.main()
