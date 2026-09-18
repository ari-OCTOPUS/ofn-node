"""Bounded read-only sidecar. Never replaces the historical W1 record."""
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path

OUT = Path('/root/s1-maturity-w1-20260917/observations.jsonl')
UNITS = ('octopus-apply-checkpoint.path','octopus-apply-checkpoint.service',
         'octopus-apply-registry.path','octopus-apply-registry.service')

def capture(run=subprocess.run):
    units, commands, errors = {}, [], []
    for unit in UNITS:
        try:
            completed = run(['systemctl','show',unit,'-p','LoadState','-p','ActiveState',
                             '-p','ExecMainStartTimestamp','-p','NRestarts'],
                            capture_output=True,text=True,timeout=15)
            props = dict(line.split('=',1) for line in completed.stdout.splitlines() if '=' in line)
            commands.append({'unit':unit,'returncode':completed.returncode})
            units[unit] = props
            required = ('LoadState','ActiveState') + (('NRestarts','ExecMainStartTimestamp') if unit.endswith('.service') else ())
            if completed.returncode != 0 or props.get('LoadState') != 'loaded' or any(k not in props for k in required):
                errors.append('unit_probe_failed:'+unit)
        except Exception as exc:
            errors.append('unit_probe_exception:'+unit+':'+type(exc).__name__)
    processes = None
    try:
        completed = run(['pgrep','-f','[a]pply_signed_inbound'],capture_output=True,text=True,timeout=10)
        commands.append({'probe':'pgrep','returncode':completed.returncode})
        if completed.returncode in (0,1):
            processes = completed.stdout.splitlines()
            if (completed.returncode == 1 and processes) or (completed.returncode == 0 and not processes):
                errors.append('process_probe_inconsistent')
        else:
            errors.append('process_probe_failed')
    except Exception as exc:
        errors.append('process_probe_exception:'+type(exc).__name__)
    return {'units':units,'apply_procs':processes,'commands':commands,
            'probe_status':'ERROR' if errors else 'OK','errors':errors}

def append(row):
    row['ts'] = dt.datetime.now(dt.timezone.utc).isoformat()
    with OUT.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(row)+'\n'); stream.flush(); os.fsync(stream.fileno())

def main():
    # Exclusive file creation prevents mixing two collector windows.
    OUT.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with OUT.open('x'): pass
    start = time.monotonic()
    baseline = capture()
    append({'event':'W1_START','baseline':baseline['units'],'probe_status':baseline['probe_status'],
            'commands':baseline['commands'],'collector_version':2,'duration_seconds':86400})
    for sample in range(288):
        row = capture(); row['sample']=sample; row['elapsed_monotonic_seconds']=time.monotonic()-start
        append(row)
        time.sleep(max(0,start+(sample+1)*300-time.monotonic()))
    append({'event':'W1_COMPLETED_BOUND_REACHED','elapsed_monotonic_seconds':time.monotonic()-start})

if __name__ == '__main__': main()
