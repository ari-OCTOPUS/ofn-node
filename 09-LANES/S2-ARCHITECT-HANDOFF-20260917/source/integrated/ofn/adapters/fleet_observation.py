"""Consume a bounded read-only census; liveness never grants job authority."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from ofn.kernel.self_model import classify_freshness

NODES = ('138', '180', '182', '100', '160', '193', '114')
MAX_BYTES = 65536

def reject_constant(value):
    raise ValueError('nonfinite_json_constant')

def read_census(path: Path, now_epoch: float) -> dict:
    result = {'schema':'octopus.fleet-self-model.v1', 'status':'UNKNOWN',
              'source':str(path), 'source_sha256':None, 'observed_node_count':0,
              'signature_verified':False, 'may_authorize':False, 'nodes':[]}
    try:
        with path.open('rb') as stream:
            body = stream.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError('census_too_large')
        result['source_sha256'] = hashlib.sha256(body).hexdigest()
        data = json.loads(body, parse_constant=reject_constant)
        if data.get('schema') != 'octopus.fleet-observation.v1':
            raise ValueError('unsupported_census_schema')
        rows = data['nodes']
        if not isinstance(rows,list) or len(rows) != len(NODES):
            raise ValueError('incomplete_roster')
        indexed = {row['node_id']:row for row in rows}
        if len(indexed) != len(rows) or set(indexed) != set(NODES):
            raise ValueError('invalid_roster')
        output = []
        for node in NODES:
            row = indexed[node]
            role = row.get('declared_role')
            if role is not None and (not isinstance(role,str) or not role.strip() or len(role)>128):
                raise ValueError('invalid_declared_role')
            state = 'UNKNOWN'
            observed = None
            if row.get('status') == 'AUTHENTICATED_OBSERVATION' and type(row.get('ssh_returncode')) is int and row['ssh_returncode'] == 0:
                observation = row['observation']
                stamp = datetime.fromisoformat(observation['observed_at_utc'].replace('Z','+00:00'))
                if stamp.tzinfo is None or any(not isinstance(observation.get(field),str)
                        or not observation[field].strip() or len(observation[field])>255
                        for field in ('hostname','boot_id')):
                    raise ValueError('incomplete_node_identity')
                observed = stamp.timestamp()
                freshness, _ = classify_freshness(observed, now_epoch, 180)
                state = {'healthy':'OBSERVED','stale':'STALE'}.get(freshness,'UNKNOWN')
            output.append({'node_id':node,'observation_status':state,
                           'observed_epoch':observed,'job_status':'UNKNOWN',
                           'role_status':'DECLARED','declared_role':role,
                           'authority':'NONE','signature_verified':False})
        result['nodes'] = output
        result['observed_node_count'] = sum(r['observation_status'] == 'OBSERVED' for r in output)
        result['status'] = 'OBSERVED' if result['observed_node_count'] == len(NODES) else 'PARTIAL'
        result['trust_boundary'] = 'Local census file reports SSH observations; content hash is not a signature or independent job witness.'
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        result['status'] = 'UNKNOWN'
        result['error_type'] = type(exc).__name__
        result['nodes'] = []
        result['observed_node_count'] = 0
    return result
