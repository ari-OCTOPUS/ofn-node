#!/usr/bin/env python3
"""Refresh Saba's small studio assistant memory once a day."""
from __future__ import annotations
from . import config
from .adapters.remote_brain import RemoteBrain
from .run import SYSTEM_PROMPT, arm_node_brain, build_node


def _factory_brain(tier="standard", pin=None):
    """BRAIN-FACTORY SWITCH (2026-09-18): prefer tools/brain_factory (whole
    provider path: both env files, all dialects, verified endpoints). Falls
    back to the legacy RemoteBrain path with a receipt if no provider is
    routable, so behaviour can never regress silently."""
    import sys as _sys
    import pathlib as _pl
    _root = _pl.Path(__file__).resolve().parent.parent
    if str(_root / "tools") not in _sys.path:
        _sys.path.insert(0, str(_root / "tools"))
    try:
        import brain_factory as _bf  # noqa: PLC0415
        _b = _bf.build(tier=tier, pin=pin)
        _rec = _root / "state" / "receipts"
        try:
            _rec.mkdir(parents=True, exist_ok=True)
            with (_rec / "brainswitch.jsonl").open("a", encoding="utf-8") as _fh:
                _fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                      "file": __file__, "tier": tier,
                                      "provider": (_b.get("decision") or {}).get("chosen"),
                                      "model": _b.get("model"), "path": "factory"}) + chr(10))
        except Exception:
            pass
        return _b["brain"]
    except Exception as _exc:  # noqa: BLE001 - fallback is deliberate and recorded
        try:
            _rec = _root / "state" / "receipts"
            _rec.mkdir(parents=True, exist_ok=True)
            with (_rec / "brainswitch.jsonl").open("a", encoding="utf-8") as _fh:
                _fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                      "file": __file__, "tier": tier,
                                      "path": "fallback", "why": type(_exc).__name__}) + chr(10))
        except Exception:
            pass
        return None



def _prompt(node, scope):
    ctx = node.assistant.search(scope.tenant.value, "عکاسی تولید محتوا امنیت قیمت", limit=6) if node.assistant else []
    mem = "\n\n".join(c["body"][:900] for c in ctx)
    return ("برای دستیار شخصی سبا، 5 توصیه تازه، امن، سطح‌بالا و غیرصریح "
            "درباره عکاسی پا/از کمر به پایین، تولید محتوا، برند، امنیت، "
            "قیمت‌گذاری، privacy و retention بنویس. هیچ راهنمایی برای دورزدن "
            "قوانین، فریب، عدم رضایت یا نقض حریم خصوصی نده. حافظه موجود:\n" + mem)

def main() -> int:
    cfg = config.load()
    node = build_node(cfg)
    arm_node_brain(cfg, node, run_worker_loop=False)
    tenant = next((t for t in node.registry if t.value == "studio"), None)
    if tenant is None or node.assistant is None:
        print("assistant update: studio/assistant not found")
        return 0
    scope = node.registry.scope(tenant)
    text = ""; brain = "local-fallback"
    if cfg.remote_api_key:
        rb = _factory_brain("standard", pin="deepseek") or RemoteBrain(api_key=cfg.remote_api_key, model="fugu-ultra",
                         base_url=cfg.remote_base_url, timeout_s=900,
                         reasoning_effort="high", max_output_tokens=1400,
                         system_prompt=SYSTEM_PROMPT)
        rep = rb.answer("studio:assistant-daily", _prompt(node, scope))
        if rep.text.strip():
            text = rep.text.strip(); brain = rep.model or "fugu-ultra"
    if not text:
        out = node.update_studio_assistant(scope)
        print(f"assistant update: ok={out.get('ok')} chunks={out.get('chunks', 0)} brain=local-fallback")
        return 0 if out.get("ok") else 1
    n = node.assistant.ingest_text(scope.tenant.value, "daily", "آپدیت روزانه", text, now_epoch_s=node.now_epoch_s())
    node.assistant.record_run(scope.tenant.value, "daily", "ok", brain, now_epoch_s=node.now_epoch_s())
    print(f"assistant update: ok=True chunks={n} brain={brain}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
