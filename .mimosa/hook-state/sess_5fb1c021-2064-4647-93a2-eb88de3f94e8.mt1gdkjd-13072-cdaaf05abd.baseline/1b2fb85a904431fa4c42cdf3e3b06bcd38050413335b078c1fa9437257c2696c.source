#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_ops_data.py — read F:/backup/_ops/state and emit ops-data.js"""
import os, json
from datetime import datetime, timezone

OPS_DIR = 'F:/backup/_ops/state'
NS_DIR = 'C:/Users/Armin/Desktop/پازل هشت پا/OCTOPUS/nervous-system'

def main():
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(os.path.join(OPS_DIR, 'ORGANISM-STATE.json'), 'r', encoding='utf-8') as f:
        org = json.load(f)
    with open(os.path.join(OPS_DIR, 'fitness-latest.json'), 'r', encoding='utf-8') as f:
        fit = json.load(f)
    with open(os.path.join(OPS_DIR, 'cardiac-budget.json'), 'r', encoding='utf-8') as f:
        card = json.load(f)

    wiring = org.get('wiring', {})
    wires_on = sum(1 for v in wiring.values() if v is True)
    wires_total = len(wiring)

    ops_data = {
        'generated': generated,
        'money': {
            'month': org.get('month', {}),
            'today': org.get('today', {}),
            'confirmed': fit.get('attribution', {}).get('confirmed', 0),
            'claimed': fit.get('attribution', {}).get('claimed', 0),
            'weights': fit.get('weights', {}),
            'spend': card.get('spent', 0),
            'projects': [
                {'id': 'lead-naghshi', 'name': 'Lead-نقاشی', 'status': org.get('leg', {}).get('money_link', '?'), 'detail': 'incubating', 'content_free': False},
                {'id': 'mining-fleet', 'name': 'Mining Fleet', 'status': org.get('mining', {}).get('money_link', '?'), 'detail': org.get('mining', {}).get('autonomy_floor', '?'), 'content_free': False},
                {'id': 'vault-cartographer', 'name': 'Vault Cartographer', 'status': org.get('cartographer', {}).get('money_link', '?'), 'detail': 'map_age ' + str(org.get('cartographer', {}).get('map_age_days', '?')) + 'd', 'content_free': False}
            ],
            'proposals': []
        },
        'time': {
            'chrono_beat': org.get('chrono', {}).get('beat'),
            'metabolic_age': org.get('chrono', {}).get('metabolic_age'),
            'age_tick': org.get('chrono', {}).get('age_tick'),
            'deadlines': [],
            'wires_on': wires_on,
            'wires_total': wires_total,
            'epoch_mode': org.get('epoch_mode', 'allostatic')
        }
    }

    js = 'window.OPS_DATA = ' + json.dumps(ops_data, ensure_ascii=False, default=str) + ';\n'
    with open(os.path.join(NS_DIR, 'ops-data.js'), 'w', encoding='utf-8') as f:
        f.write(js)
    print('ops-data.js refreshed', len(js), 'chars')

if __name__ == '__main__':
    main()
