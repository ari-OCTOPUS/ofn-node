"""Read-only authenticated fleet census; no config, credential or payload reads."""
import concurrent.futures
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NODES = {
    '138': ('ari', 'id_ed25519', 'commander'),
    '180': ('root', 'id_ed25519', 'quality_restore_copy_RO'),
    '182': ('root', 'id_ed25519', 'lab_witness'),
    '100': ('root', 'piggybank_id_ed25519', 'knowledge_retrieve'),
    '160': ('root', 'piggybank_id_ed25519', 'knowledge_prep'),
    '193': ('root', 'id_ed25519', 'model_infer'),
    '114': ('root', 'id_ed25519', 'eval_batch'),
}
REMOTE = '''import datetime,json,pathlib,subprocess,socket
def read(p):
 try: return pathlib.Path(p).read_text().strip().replace(chr(0),'')
 except OSError: return None
def cmd(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=10)
 return {'returncode':r.returncode,'stdout':r.stdout.strip()}
print(json.dumps({'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'model':read('/proc/device-tree/model'),'boot_id':read('/proc/sys/kernel/random/boot_id'),'uptime':read('/proc/uptime'),'meminfo':{l.split(':')[0]:l.split(':')[1].strip() for l in (read('/proc/meminfo') or '').splitlines() if l.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))},'leaf':cmd(['systemctl','is-active','nats-leaf.service']),'python':cmd(['python3','--version'])}))
'''

def probe(item):
    node, (user, key, role) = item
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=8', '-i', str(Path.home()/'.ssh'/key),
               f'{user}@192.168.0.{node}', 'python3 -']
    row = {'node_id':node, 'declared_role':role, 'role_source':'DEEP-ARCH-HARVEST-20260917',
           'runtime_job_proven':False, 'heartbeat_signature_verified':False}
    try:
        result = subprocess.run(command,input=REMOTE,capture_output=True,text=True,timeout=30)
        row['ssh_returncode'] = result.returncode
        if result.returncode == 0:
            row['observation'] = json.loads(result.stdout)
            row['status'] = 'AUTHENTICATED_OBSERVATION'
        else:
            row['status'] = 'UNKNOWN'
            row['error'] = result.stderr.strip()[:250]
    except (subprocess.SubprocessError, ValueError) as exc:
        row.update(status='ERROR', error=type(exc).__name__)
    return row

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        rows = list(pool.map(probe, NODES.items()))
    output = {'schema':'octopus.fleet-observation.v1','captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'self_model_integration':'NOT_VERIFIED','nodes':rows}
    (ROOT/'FLEET-OBSERVATION.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({r['node_id']:r['status'] for r in rows}))
