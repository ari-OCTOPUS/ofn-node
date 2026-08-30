#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_git_status_data.py — scan project git repos and emit git-data.js

CH-02: Git Status → Dashboard
Sources: .git/ of project repos under F:/backup
Sink: JS data showing repo status, last commit, branch, dirty files, ahead/behind.

Stdlib-only. Works on Windows (Git Bash) and Unix.
"""
import os
import json
import subprocess
from datetime import datetime, timezone

ROOT = 'F:/backup'
NS_DIR = 'F:/backup/nervous-system'
MAX_DEPTH = 6

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def run_git(cwd, *args):
    """Run git in cwd; return stripped stdout or None on failure."""
    try:
        r = subprocess.run(
            ['git', '-C', cwd] + list(args),
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=30
        )
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except Exception:
        return None


def is_independent_repo(path):
    """True if `path` is its own git repo (git-dir resolves inside path)."""
    out = run_git(path, 'rev-parse', '--git-dir')
    if not out:
        return False
    # On Windows git may return forward slashes; normalize
    git_dir = os.path.normpath(os.path.join(path, out))
    real_path = os.path.normpath(path)
    # If git-dir is inside the candidate path, it's independent
    return git_dir.startswith(real_path + os.sep) or git_dir == real_path


def discover_repos(root, max_depth=6):
    """Walk root and return list of independent git repo absolute paths."""
    repos = []
    seen = set()
    for dirpath, dirnames, _filenames in os.walk(root):
        depth = dirpath.count(os.sep) - root.count(os.sep)
        if depth >= max_depth:
            del dirnames[:]
            continue
        if '.git' in dirnames:
            candidate = os.path.abspath(dirpath)
            if candidate in seen:
                continue
            seen.add(candidate)
            # Skip the .git directory itself from further recursion
            git_path = os.path.join(candidate, '.git')
            if os.path.isdir(git_path):
                if is_independent_repo(candidate):
                    repos.append(candidate)
            # Also prune .git from walking deeper
            if '.git' in dirnames:
                # keep walking, but don't recurse INTO .git
                pass
    return sorted(set(repos))


def parse_porcelain_v2(lines):
    """Parse git status --porcelain=2 --branch output."""
    summary = {
        'modified': 0, 'added': 0, 'deleted': 0,
        'renamed': 0, 'copied': 0, 'untracked': 0,
        'unmerged': 0, 'staged': 0,
        'ahead': 0, 'behind': 0,
        'upstream': None, 'oid': None, 'head': None,
    }
    files = []
    for line in lines:
        if not line:
            continue
        if line.startswith('# branch.'):
            parts = line[9:].split(' ', 1)
            if len(parts) == 2:
                key, val = parts
                if key == 'oid':
                    summary['oid'] = val
                elif key == 'head':
                    summary['head'] = val
                elif key == 'upstream':
                    summary['upstream'] = val
                elif key == 'ab':
                    # format: +<ahead> -<behind>
                    ab = val.split()
                    for token in ab:
                        if token.startswith('+') and token[1:].isdigit():
                            summary['ahead'] = int(token[1:])
                        elif token.startswith('-') and token[1:].isdigit():
                            summary['behind'] = int(token[1:])
            continue

        if line.startswith('1 ') or line.startswith('2 '):
            # 1 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <path>
            # 2 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <X><score> <path><sep><origPath>
            tokens = line.split(' ', 8)
            if len(tokens) >= 9:
                xy = tokens[1]
                path_raw = tokens[8]
                # XY codes: https://git-scm.com/docs/git-status#_porcelain_format_version_2
                x, y = xy[0] if len(xy) > 0 else '.', xy[1] if len(xy) > 1 else '.'
                status_label = '?'
                if x == 'M' or y == 'M':
                    status_label = 'M'
                    summary['modified'] += 1
                elif x == 'A' or y == 'A':
                    status_label = 'A'
                    summary['added'] += 1
                elif x == 'D' or y == 'D':
                    status_label = 'D'
                    summary['deleted'] += 1
                elif x == 'R':
                    status_label = 'R'
                    summary['renamed'] += 1
                elif x == 'C':
                    status_label = 'C'
                    summary['copied'] += 1
                elif x == 'U' or y == 'U':
                    status_label = 'U'
                    summary['unmerged'] += 1
                else:
                    status_label = xy
                if x != '.' and x != '?':
                    summary['staged'] += 1
                files.append({'status': status_label, 'path': path_raw})
            continue

        if line.startswith('? '):
            summary['untracked'] += 1
            files.append({'status': '?', 'path': line[2:]})
            continue

        if line.startswith('u '):
            summary['unmerged'] += 1
            tokens = line.split(' ', 9)
            if len(tokens) >= 10:
                files.append({'status': 'U', 'path': tokens[9]})
            continue

    return summary, files


def repo_name_from_path(repo_path, root):
    """Generate a short Persian-ish display name from repo path."""
    rel = os.path.relpath(repo_path, root)
    if rel == '.':
        return 'پروژهٔ اصلی'
    # basename or last meaningful segment
    base = os.path.basename(repo_path)
    # Map some known folders to Persian labels
    KNOWN = {
        'genome-system': 'ژنوم',
        'AI-sume': 'AI-sume',
        'app': 'اپلیکیشن',
        '4d_system': 'سیستم ۴بعدی',
        '_ops': 'عملیات',
        'OCTOPUS': 'اختاپوس',
    }
    return KNOWN.get(base, base)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    repos_data = []
    repo_paths = discover_repos(ROOT, MAX_DEPTH)

    # Always ensure the root itself is scanned even if no .git subdir found
    root_git = os.path.join(os.path.abspath(ROOT), '.git')
    if os.path.exists(root_git) and os.path.abspath(ROOT) not in repo_paths:
        repo_paths.insert(0, os.path.abspath(ROOT))

    for rpath in repo_paths:
        # Verify repo is readable
        branch = run_git(rpath, 'rev-parse', '--abbrev-ref', 'HEAD')
        if branch is None:
            continue

        # Last commit
        last = run_git(rpath, 'log', '-1', '--format=%H%n%s%n%an%n%aI%n%ar')
        last_commit = {}
        if last:
            parts = last.split('\n', 4)
            last_commit = {
                'hash': parts[0] if len(parts) > 0 else None,
                'hash_short': parts[0][:8] if len(parts) > 0 else None,
                'message': parts[1] if len(parts) > 1 else None,
                'author': parts[2] if len(parts) > 2 else None,
                'date_iso': parts[3] if len(parts) > 3 else None,
                'date_relative': parts[4] if len(parts) > 4 else None,
            }

        # Status
        raw = run_git(rpath, 'status', '--porcelain=2', '--branch')
        summary, files = parse_porcelain_v2(raw.splitlines() if raw else [])

        # Remote URL (optional)
        remote_url = run_git(rpath, 'remote', 'get-url', 'origin')

        dirty_total = (
            summary['modified'] + summary['added'] + summary['deleted'] +
            summary['renamed'] + summary['copied'] + summary['unmerged'] +
            summary['untracked']
        )

        repos_data.append({
            'id': os.path.basename(rpath) if os.path.basename(rpath) else 'root',
            'name': repo_name_from_path(rpath, ROOT),
            'path': rpath,
            'branch': branch,
            'last_commit': last_commit,
            'remote_url': remote_url,
            'status': {
                'clean': dirty_total == 0,
                'dirty_total': dirty_total,
                'modified': summary['modified'],
                'added': summary['added'],
                'deleted': summary['deleted'],
                'renamed': summary['renamed'],
                'copied': summary['copied'],
                'untracked': summary['untracked'],
                'unmerged': summary['unmerged'],
                'staged': summary['staged'],
                'ahead': summary['ahead'],
                'behind': summary['behind'],
                'upstream': summary['upstream'],
                'oid': summary['oid'],
            },
            'files': files[:50],  # cap at 50 for JS size
        })

    total_repos = len(repos_data)
    dirty_repos = sum(1 for r in repos_data if not r['status']['clean'])
    clean_repos = total_repos - dirty_repos
    ahead_repos = sum(1 for r in repos_data if r['status']['ahead'] > 0)
    behind_repos = sum(1 for r in repos_data if r['status']['behind'] > 0)

    git_data = {
        'generated': generated,
        'summary': {
            'total_repos': total_repos,
            'clean_repos': clean_repos,
            'dirty_repos': dirty_repos,
            'ahead_repos': ahead_repos,
            'behind_repos': behind_repos,
        },
        'repos': repos_data,
    }

    js = 'window.GIT_DATA = ' + json.dumps(git_data, ensure_ascii=False, default=str) + ';\n'
    out_path = os.path.join(NS_DIR, 'git-data.js')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print('git-data.js refreshed', len(js), 'chars', 'repos=', total_repos)


if __name__ == '__main__':
    main()
