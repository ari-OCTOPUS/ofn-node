#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_project_index.py — CH-13: Project Folders → Architecture Index

Sources: F:/backup/03 - Projects/ subfolders
Sink: JS data file mapping projects to status, files, health.
"""
import os
import re
import json
from datetime import datetime, timezone

PROJECTS_DIR = 'F:/backup/03 - Projects'
NS_DIR = 'F:/backup/nervous-system'

def parse_frontmatter(text):
    """Extract YAML-like frontmatter from markdown."""
    if not text.startswith('---'):
        return {}
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}
    fm = parts[1].strip()
    data = {}
    for line in fm.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # handle simple list like tags: [a, b]
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(',')]
            data[key] = val
    return data

def parse_manifest(text):
    """Lightweight YAML parser for MANIFEST.yaml key sections."""
    data = {}
    current_section = None
    current_list = None
    current_dict = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        # Section header (no indent)
        if not stripped.startswith(' ') and not stripped.startswith('\t') and stripped.endswith(':'):
            current_section = stripped[:-1].strip()
            data[current_section] = {}
            current_list = None
            current_dict = None
            i += 1
            continue
        # Key under section
        if current_section and ':' in stripped:
            indent = len(stripped) - len(stripped.lstrip())
            key_val = stripped.lstrip()
            if indent <= 2 and ':' in key_val:
                k, v = key_val.split(':', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                data[current_section][k] = v
                current_list = None
                current_dict = None
            i += 1
            continue
        i += 1
    return data

def count_files_and_dirs(root):
    """Count files and immediate subdirs, and find newest mtime."""
    file_count = 0
    subdir_count = 0
    newest_mtime = 0
    for entry in os.scandir(root):
        if entry.name.startswith('.'):
            continue
        try:
            stat = entry.stat()
        except OSError:
            continue
        if entry.is_dir(follow_symlinks=False):
            subdir_count += 1
            # recurse lightly for file count
            for subroot, subdirs, subfiles in os.walk(entry.path):
                # skip hidden dirs
                subdirs[:] = [d for d in subdirs if not d.startswith('.')]
                for f in subfiles:
                    if not f.startswith('.'):
                        file_count += 1
                        try:
                            mtime = os.path.getmtime(os.path.join(subroot, f))
                            if mtime > newest_mtime:
                                newest_mtime = mtime
                        except OSError:
                            pass
        else:
            file_count += 1
            if stat.st_mtime > newest_mtime:
                newest_mtime = stat.st_mtime
    return file_count, subdir_count, newest_mtime

def has_todos(filepath):
    """Count unchecked todo items in a markdown file."""
    if not os.path.exists(filepath):
        return 0
    count = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if re.search(r'^\s*-\s*\[\s*\]', line):
                    count += 1
    except Exception:
        pass
    return count

def count_open_questions(filepath):
    """Count lines that look like open questions/blockers."""
    if not os.path.exists(filepath):
        return 0
    count = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('-') and ('?' in line or 'BLOCKER' in line or 'To measure' in line or 'To do' in line):
                    count += 1
    except Exception:
        pass
    return count

def compute_health(project):
    """Compute a simple health score 0-100 for a project."""
    score = 50
    # key docs present
    if project.get('has_project_md'):
        score += 10
    if project.get('has_readme'):
        score += 5
    if project.get('has_manifest'):
        score += 10
    if project.get('has_decision_log'):
        score += 5
    if project.get('has_index'):
        score += 5
    # activity
    days_since_update = project.get('days_since_update', 999)
    if days_since_update < 1:
        score += 10
    elif days_since_update < 7:
        score += 7
    elif days_since_update < 30:
        score += 3
    else:
        score -= 10
    # blockers
    blockers = project.get('blockers', 0)
    if blockers == 0:
        score += 5
    elif blockers > 5:
        score -= 10
    elif blockers > 2:
        score -= 5
    # todos
    todos = project.get('open_todos', 0)
    if todos > 10:
        score -= 5
    elif todos == 0:
        score += 5
    # status override
    status = project.get('status', '').lower()
    if status == 'active':
        score += 5
    elif status in ('stalled', 'blocked', 'paused'):
        score -= 15
    elif status == 'archived':
        score -= 20
    return max(0, min(100, round(score, 1)))

def main():
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    projects = []
    total_files = 0
    total_subdirs = 0

    try:
        entries = sorted(os.listdir(PROJECTS_DIR))
    except OSError:
        entries = []

    for name in entries:
        path = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(path) or name.startswith('_') or name.startswith('.'):
            continue

        project = {
            'id': name,
            'name': name,
            'path': path.replace('\\', '/'),
            'status': 'unknown',
            'kind': 'unknown',
            'phase': 'unknown',
            'owner': 'unknown',
            'risk_level': 'unknown',
            'autonomy_level': 'unknown',
            'role_in_ecosystem': '',
            'tags': [],
            'file_count': 0,
            'subdir_count': 0,
            'days_since_update': None,
            'has_project_md': False,
            'has_readme': False,
            'has_manifest': False,
            'has_decision_log': False,
            'has_index': False,
            'open_todos': 0,
            'blockers': 0,
            'health': 0,
        }

        # Check key files
        project_md = os.path.join(path, 'PROJECT.md')
        readme_md = os.path.join(path, 'README.md')
        manifest_yaml = os.path.join(path, 'MANIFEST.yaml')
        decision_log = os.path.join(path, 'DecisionLog.md')
        index_md = os.path.join(path, 'INDEX.md')
        open_questions = os.path.join(path, 'OpenQuestions.md')

        project['has_project_md'] = os.path.exists(project_md)
        project['has_readme'] = os.path.exists(readme_md)
        project['has_manifest'] = os.path.exists(manifest_yaml)
        project['has_decision_log'] = os.path.exists(decision_log)
        project['has_index'] = os.path.exists(index_md)

        # Parse PROJECT.md frontmatter
        if project['has_project_md']:
            try:
                with open(project_md, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read(4000)
                fm = parse_frontmatter(text)
                project['status'] = fm.get('status', 'unknown')
                project['kind'] = fm.get('kind', 'unknown')
                project['owner'] = fm.get('owner', 'unknown')
                project['risk_level'] = fm.get('risk_level', 'unknown')
                project['autonomy_level'] = fm.get('autonomy_level', 'unknown')
                tags = fm.get('tags', [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.strip('[]').split(',') if t.strip()]
                project['tags'] = tags
            except Exception:
                pass

        # Parse MANIFEST.yaml for phase and role
        if project['has_manifest']:
            try:
                with open(manifest_yaml, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read(8000)
                mf = parse_manifest(text)
                identity = mf.get('identity', {})
                if 'phase' in identity:
                    project['phase'] = identity['phase']
                if 'role_in_ecosystem' in identity:
                    project['role_in_ecosystem'] = identity['role_in_ecosystem']
                status_snap = mf.get('status_snapshot', {})
                if 'primary_blocker' in status_snap and not project.get('blockers'):
                    # count blockers roughly
                    pb = status_snap['primary_blocker']
                    project['primary_blocker'] = pb
            except Exception:
                pass

        # File stats
        fc, sdc, newest = count_files_and_dirs(path)
        project['file_count'] = fc
        project['subdir_count'] = sdc
        total_files += fc
        total_subdirs += sdc

        if newest:
            days_since = (datetime.now(timezone.utc) - datetime.fromtimestamp(newest, tz=timezone.utc)).days
            project['days_since_update'] = days_since

        # Todos and blockers
        project['open_todos'] = has_todos(project_md)
        project['blockers'] = count_open_questions(open_questions)

        # Health
        project['health'] = compute_health(project)

        projects.append(project)

    # Summary
    active_count = sum(1 for p in projects if p['status'].lower() == 'active')
    stalled_count = sum(1 for p in projects if p['status'].lower() in ('stalled', 'blocked', 'paused'))
    archived_count = sum(1 for p in projects if p['status'].lower() == 'archived')
    avg_health = round(sum(p['health'] for p in projects) / len(projects), 1) if projects else 0

    project_data = {
        'generated': generated,
        'channel': 'CH-13',
        'label': 'ایندکس پروژه‌ها',
        'summary': {
            'total_projects': len(projects),
            'active': active_count,
            'stalled': stalled_count,
            'archived': archived_count,
            'total_files': total_files,
            'total_subdirs': total_subdirs,
            'average_health': avg_health,
        },
        'projects': projects,
    }

    js = 'window.PROJECT_DATA = ' + json.dumps(project_data, ensure_ascii=False, default=str) + ';\n'
    out_path = os.path.join(NS_DIR, 'project-data.js')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print('project-data.js refreshed', len(js), 'chars')

if __name__ == '__main__':
    main()
