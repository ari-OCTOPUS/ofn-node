"""Evaluate captured legacy W1 evidence without upgrading incomplete probes to PASS."""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

SERVICES = ('octopus-apply-checkpoint.service', 'octopus-apply-registry.service')
PATHS = tuple(u.replace('.service','.path') for u in SERVICES)

def epoch(value):
    return dt.datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()

def evaluate(rows):
    if not rows or rows[0].get('event') != 'W1_START':
        return {'status':'ERROR','reason':'missing_start'}
    try:
        baseline = rows[0]['baseline']
        if rows[0].get('probe_status') == 'ERROR':
            raise ValueError('baseline_probe_failed')
        for unit in SERVICES:
            if not baseline[unit]['ExecMainStartTimestamp'] or baseline[unit]['NRestarts'] != '0':
                raise ValueError('invalid_baseline')
        start = epoch(rows[0]['ts'])
        samples = [r for r in rows[1:] if 'sample' in r]
        if not samples:
            return {'status':'NOT_RUN','sample_count':0}
        previous = start
        for i, row in enumerate(samples):
            if row.get('probe_status') == 'ERROR':
                raise ValueError('sample_probe_failed')
            if row['sample'] != i:
                raise ValueError('missing_or_duplicate_sample')
            timestamp = epoch(row['ts'])
            if timestamp < previous or timestamp - previous > 360:
                raise ValueError('observation_gap_or_clock_regression')
            previous = timestamp
            if not isinstance(row['apply_procs'],list):
                raise ValueError('invalid_process_evidence')
            if row['apply_procs']:
                return {'status':'FAIL_OPEN_DEBUG','reason':'apply_process_observed','sample':i}
            for unit in SERVICES:
                props = row['units'][unit]
                if not props.get('ExecMainStartTimestamp') or 'NRestarts' not in props:
                    raise ValueError('incomplete_unit_probe')
                if (props['ExecMainStartTimestamp'] != baseline[unit]['ExecMainStartTimestamp']
                        or props['NRestarts'] != baseline[unit]['NRestarts']
                        or props['ActiveState'] != 'inactive'):
                    return {'status':'FAIL_OPEN_DEBUG','reason':'activation_changed','sample':i}
            for unit in PATHS:
                if row['units'][unit]['ActiveState'] != 'active':
                    return {'status':'ERROR','reason':'watch_path_not_active','sample':i}
        complete = [r for r in rows if r.get('event') == 'W1_COMPLETED_BOUND_REACHED']
        elapsed = previous - start
        result = {'status':'RUNNING','sample_count':len(samples),'sample_span_seconds':elapsed,
                  'observed_activation_changes':0,'scheduled_end_utc':dt.datetime.fromtimestamp(start+86400,dt.timezone.utc).isoformat(),
                  'collection_limitation':'Legacy collector suppresses pgrep failures and does not retain subprocess returncodes; empty process list cannot prove successful probe.'}
        if rows[0].get('collector_version') == 2:
            result['collection_limitation'] = 'Five-minute sampling cannot exclude transient processes between samples; final verdict requires full window and successful probes.'
        if complete:
            if len(complete) != 1 or len(samples) != 288 or epoch(complete[0]['ts'])-start < 86400:
                raise ValueError('invalid_completion_window')
            result['status'] = 'UNVALIDATED'
            result['reason'] = 'window_complete_but_probe_success_not_proven'
            if rows[0].get('collector_version') == 2 and rows[0].get('probe_status') == 'OK' and all(r.get('probe_status') == 'OK' for r in samples) and complete[0].get('elapsed_monotonic_seconds',0) >= 86400:
                result['status'] = 'MEASURED_24H_SAMPLED_FROZEN'
                result['reason'] = 'all_recorded_probes_successful_in_full_window'
                result['collection_limitation'] = 'Five-minute sampling cannot exclude transient processes between samples.'
        return result
    except (KeyError,TypeError,ValueError,AttributeError) as exc:
        return {'status':'ERROR','reason':str(exc)}

if __name__ == '__main__':
    path = Path(sys.argv[1])
    data = path.read_bytes()
    try:
        result = evaluate([json.loads(line) for line in data.decode('utf-8-sig').splitlines() if line])
    except (UnicodeError,ValueError) as exc:
        result = {'status':'ERROR','reason':type(exc).__name__}
    result['source_sha256'] = hashlib.sha256(data).hexdigest()
    print(json.dumps(result,indent=2))
