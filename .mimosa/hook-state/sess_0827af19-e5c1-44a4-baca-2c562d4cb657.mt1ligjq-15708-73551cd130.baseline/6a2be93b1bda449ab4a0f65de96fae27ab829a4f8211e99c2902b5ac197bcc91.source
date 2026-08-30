#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_live_data.py — read F:/backup/4d_system/outputs and emit live-data.js"""
import os, json, sqlite3
from datetime import datetime, timezone

OUT_DIR = 'F:/backup/4d_system/outputs'
NS_DIR = 'C:/Users/Armin/Desktop/پازل هشت پا/OCTOPUS/nervous-system'

def main():
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # daemon_state
    with open(os.path.join(OUT_DIR, 'daemon_state.json'), 'r', encoding='utf-8') as f:
        daemon_state = json.load(f)

    # decision_packets
    packets = []
    dp_path = os.path.join(OUT_DIR, 'decision_packets.jsonl')
    if os.path.exists(dp_path):
        with open(dp_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    packets.append(json.loads(line))

    # frontier
    frontier_path = os.path.join(OUT_DIR, 'self_evolved', 'frontier.json')
    if not os.path.exists(frontier_path):
        frontier_path = os.path.join(OUT_DIR, 'backups', '2026-07-11', 'frontier.json')
    with open(frontier_path, 'r', encoding='utf-8') as f:
        frontier_raw = json.load(f)

    # DB
    conn = sqlite3.connect(os.path.join(OUT_DIR, '4d_experiments.db'))
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM dashboard_events')
    total_events = cur.fetchone()[0]

    cur.execute('SELECT event_name, COUNT(*) FROM dashboard_events GROUP BY event_name')
    by_name = dict(cur.fetchall())

    cur.execute('SELECT status, COUNT(*) FROM dashboard_events GROUP BY status')
    by_status = dict(cur.fetchall())

    cur.execute('SELECT agent_id, COUNT(*) FROM dashboard_events GROUP BY agent_id')
    by_agent = dict(cur.fetchall())

    cur.execute('SELECT * FROM dashboard_events ORDER BY id DESC LIMIT 400')
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    recent = [dict(zip(cols, r)) for r in rows]

    cur.execute('SELECT * FROM experiments ORDER BY id DESC LIMIT 1')
    exp = cur.fetchone()
    exp_cols = [d[0] for d in cur.description]
    exp_dict = dict(zip(exp_cols, exp)) if exp else {}
    conn.close()

    identity_now = (exp_dict.get('delta_self', 0) or 0) + (exp_dict.get('e_shadow', 0) or 0)
    drift_now = exp_dict.get('temporal_mi', 0) or 0
    healthy = 'SUPPORTED' in (exp_dict.get('verdict', '') or '') and (exp_dict.get('confidence', '') or '') == 'high'

    families = set()
    cells = []
    for key, val in frontier_raw.items():
        fam = key.split('|')[0] if '|' in key else key
        families.add(fam)
        cells.append({
            'family': fam,
            'rho': val.get('best_rho'),
            'kurt': val.get('best_kurt'),
            'mi': val.get('best_mi'),
            'count': val.get('count')
        })

    budget = daemon_state.get('budget', {})

    live_data = {
        'generated': generated,
        'sog': {
            'identity_now': round(identity_now, 6),
            'drift_now': drift_now,
            'healthy': healthy,
            'default': {
                'Eshadow': exp_dict.get('e_shadow', 0) or 0,
                'Dself': exp_dict.get('delta_self', 0) or 0,
                'identity': round(identity_now, 6)
            },
            'surface': None
        },
        'events': {
            'total_rows': total_events,
            'recent': recent,
            'by_name': by_name,
            'by_status': by_status,
            'by_agent': by_agent
        },
        'frontier': {
            'total_cells': len(frontier_raw),
            'families': len(families),
            'generation': daemon_state.get('generation', 0),
            'cells': cells
        },
        'budget': {
            'cap': budget.get('cap'),
            'cloud_calls': budget.get('cloud_calls'),
            'remaining': budget.get('remaining'),
            'by_provider': budget.get('by_provider', {})
        },
        'packets': packets,
        'daemon': {
            'total_ticks': daemon_state.get('total_ticks'),
            'stopped_at': daemon_state.get('stopped_at'),
            'generation': daemon_state.get('generation')
        },
        'cycle': ['explore', 'real', 'synthesize', 'introspect', 'create', 'mutate', 'evolve', 'conclude', 'guard'],
        'tcb': [],
        'portrait': {
            'word_count': len(json.dumps(exp_dict)),
            'preview': (exp_dict.get('narrative', '') or '')[:80]
        }
    }

    js = 'window.LIVE_DATA = ' + json.dumps(live_data, ensure_ascii=False, default=str) + ';\n'
    with open(os.path.join(NS_DIR, 'live-data.js'), 'w', encoding='utf-8') as f:
        f.write(js)
    print('live-data.js refreshed', len(js), 'chars')

if __name__ == '__main__':
    main()
