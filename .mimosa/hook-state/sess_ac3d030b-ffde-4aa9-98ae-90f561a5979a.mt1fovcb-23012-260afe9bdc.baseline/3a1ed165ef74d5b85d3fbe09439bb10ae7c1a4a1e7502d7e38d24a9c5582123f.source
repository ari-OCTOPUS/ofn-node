#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_graph.py — read existing graph-data.js and add freshness metadata."""
import os, json, re
from datetime import datetime, timezone

WORLDS_DIR = 'C:/Users/Armin/Desktop/پازل هشت پا/OCTOPUS/worlds'

def main():
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    graph_path = os.path.join(WORLDS_DIR, 'graph-data.js')
    with open(graph_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse existing assignment
    m = re.search(r'window\.OCTOPUS_GRAPH\s*=\s*({.*?});', content, re.DOTALL)
    if not m:
        print('graph-data.js parse failed')
        return

    data = json.loads(m.group(1))
    data['generated'] = generated
    js = 'window.OCTOPUS_GRAPH = ' + json.dumps(data, ensure_ascii=False) + ';\n'
    with open(graph_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print('graph-data.js refreshed', len(js), 'chars')

if __name__ == '__main__':
    main()
