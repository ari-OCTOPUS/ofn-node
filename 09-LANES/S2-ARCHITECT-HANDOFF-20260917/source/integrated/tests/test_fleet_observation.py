import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from ofn.adapters.fleet_observation import read_census, NODES
from ofn.adapters.self_model_producer import produce

class FleetObservationTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'census.json'
        self.data = {'schema':'octopus.fleet-observation.v1','nodes':[
            {'node_id':n,'status':'AUTHENTICATED_OBSERVATION','ssh_returncode':0,
             'declared_role':'test','observation':{'observed_at_utc':'2026-09-17T00:00:00Z',
             'hostname':'fixture-'+n,'boot_id':'fixture-boot'}} for n in NODES]}
        self.now = 1789603200.0

    def run_census(self):
        self.path.write_text(json.dumps(self.data),encoding='utf-8')
        return read_census(self.path,self.now)

    def test_fresh_coverage_does_not_grant_authority_or_jobs(self):
        result=self.run_census()
        self.assertEqual(result['observed_node_count'],7)
        self.assertFalse(result['may_authorize'])
        self.assertFalse(result['signature_verified'])
        self.assertTrue(all(n['job_status']=='UNKNOWN' for n in result['nodes']))

    def test_stale_is_not_observed(self):
        self.now += 181
        result=self.run_census()
        self.assertEqual(result['observed_node_count'],0)
        self.assertEqual(result['status'],'PARTIAL')

    def test_future_is_unknown(self):
        self.now -= 6
        self.assertEqual(self.run_census()['observed_node_count'],0)

    def test_duplicate_and_missing_fail_closed(self):
        self.data['nodes'][-1]=copy.deepcopy(self.data['nodes'][0])
        self.assertEqual(self.run_census()['status'],'UNKNOWN')

    def test_missing_identity_invalidates_census(self):
        del self.data['nodes'][0]['observation']['boot_id']
        self.assertEqual(self.run_census()['status'],'UNKNOWN')

    def test_malformed_identity_invalidates_census(self):
        for value in (True,{},' ',42):
            with self.subTest(value=value):
                self.data['nodes'][0]['observation']['hostname']=value
                self.assertEqual(self.run_census()['status'],'UNKNOWN')

    def test_nonfinite_and_wrong_role_fail_closed(self):
        for value in (float('nan'), True, {}, ' '):
            with self.subTest(value=value):
                self.data['nodes'][0]['declared_role']=value
                self.assertEqual(self.run_census()['status'],'UNKNOWN')

    def test_failed_ssh_never_counts(self):
        self.data['nodes'][0]['ssh_returncode']=255
        self.assertEqual(self.run_census()['observed_node_count'],6)

    def test_boolean_returncode_is_not_zero(self):
        self.data['nodes'][0]['ssh_returncode']=False
        self.assertEqual(self.run_census()['observed_node_count'],6)

    def test_bounded_read(self):
        self.path.write_bytes(b' '*65537)
        self.assertEqual(read_census(self.path,self.now)['status'],'UNKNOWN')

    def test_missing_input_unknown(self):
        self.assertEqual(read_census(self.path,self.now)['status'],'UNKNOWN')

    def test_timezone_required(self):
        self.data['nodes'][0]['observation']['observed_at_utc']='2026-09-17T00:00:00'
        self.assertEqual(self.run_census()['status'],'UNKNOWN')

    def test_real_producer_consumes_census_without_status_upgrade(self):
        self.run_census()
        arguments=dict(clock=lambda:self.now,repo_root=Path(__file__).resolve().parents[1],
                       git_runner=lambda *a:None,unit_prober=lambda u:(None,'unmeasured'))
        baseline=produce(**arguments)
        actual=produce(**arguments,fleet_census_path=self.path)
        self.assertEqual(actual['fleet']['observed_node_count'],7)
        self.assertEqual(actual['status'],baseline['status'])
        self.assertEqual(actual['data']['authority'],baseline['data']['authority'])
