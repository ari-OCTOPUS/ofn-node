#!/usr/bin/env python3
"""Fix gemini 0/2 (root cause: Gemini 3.x thinking tokens eat maxOutputTokens)
+ make the benchmark scorer fence-tolerant (models wrap code in ``` fences)."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
F = "/home/ari/ofn/tools/brain_factory.py"
B = "/home/ari/ofn/tools/brain_benchmark.py"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


for p in (F, B):
    shutil.copy2(p, p + ".pre-geminifix-" + TS)
h0 = {p: sha(p) for p in (F, B)}

# ---- 1. GeminiBrain: disable thinking so the output budget is real text ----
s = pathlib.Path(F).read_text(encoding="utf-8")
old = ('    def _body(self, prompt, max_tokens):\n'
       '        return {"contents": [{"parts": [{"text": prompt}]}],\n'
       '                "generationConfig": {"maxOutputTokens": max_tokens}}')
new = ('    def _body(self, prompt, max_tokens):\n'
       '        # GEMINI-FIX 2026-09-18: gemini-3.x spends maxOutputTokens on\n'
       '        # *thinking* tokens first; with a 128-token cap the visible answer\n'
       '        # was truncated to "```python\\ndef" (benchmarked 0/2 on code).\n'
       '        # thinkingBudget=0 spends the whole budget on the answer text.\n'
       '        return {"contents": [{"parts": [{"text": prompt}]}],\n'
       '                "generationConfig": {"maxOutputTokens": max_tokens,\n'
       '                                     "thinkingConfig": {"thinkingBudget": 0}}}')
assert s.count(old) == 1, "factory anchor=%d" % s.count(old)
pathlib.Path(F).write_text(s.replace(old, new), encoding="utf-8", newline="\n")
print("factory patched", h0[F][:16], "->", sha(F)[:16])

# ---- 2. benchmark scorer: strip markdown fences before matching ----
b = pathlib.Path(B).read_text(encoding="utf-8")
old2 = ('def score(task_cls: str, expected: str | None, text: str) -> tuple[float, str]:\n'
        '    t = (text or "").strip()')
new2 = ('def _unfence(t: str) -> str:\n'
        '    """A correct answer wrapped in ``` fences is still a correct answer."""\n'
        '    s = (t or "").strip()\n'
        '    if s.startswith("```"):\n'
        '        lines = s.splitlines()\n'
        '        if lines and lines[0].startswith("```"):\n'
        '            lines = lines[1:]\n'
        '        if lines and lines[-1].strip().startswith("```"):\n'
        '            lines = lines[:-1]\n'
        '        s = chr(10).join(lines).strip()\n'
        '    return s\n'
        '\n'
        '\n'
        'def score(task_cls: str, expected: str | None, text: str) -> tuple[float, str]:\n'
        '    t = _unfence(text)')
assert b.count(old2) == 1, "benchmark anchor=%d" % b.count(old2)
pathlib.Path(B).write_text(b.replace(old2, new2), encoding="utf-8", newline="\n")
print("benchmark patched", h0[B][:16], "->", sha(B)[:16])

rec = {"schema": "octopus.fix-receipt.v1", "id": "GEMINIFIX-" + TS,
       "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
       "root_cause": "gemini-3.x thinking tokens consume maxOutputTokens (128) leaving "
                     "~6 tokens of visible text ('```python\\ndef'); the provider path was "
                     "healthy end-to-end (raw probe 200/STOP) so the 0/2 was a "
                     "budget+dialect artifact",
       "fixes": [{"file": F, "sha_before": h0[F], "sha_after": sha(F),
                  "what": "thinkingBudget=0 in GeminiBrain._body"},
                 {"file": B, "sha_before": h0[B], "sha_after": sha(B),
                  "what": "scorer strips markdown fences (format-tolerant scoring)"}],
       "rollback": "cp <preimage> <file>",
       "preimages": [F + ".pre-geminifix-" + TS, B + ".pre-geminifix-" + TS]}
json.dump(rec, open("/home/ari/ofn/state/receipts/GEMINIFIX-%s.json" % TS, "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
print("receipt: state/receipts/GEMINIFIX-%s.json" % TS)
