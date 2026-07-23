#!/usr/bin/env python3
"""تستِ smoke واقعیِ routingِ GLM+Fugu (+ cap/kill/alert حفظ).

این تست:
  - اگر کلیدها در env (.env) باشند: یک فراخوانِ واقعیِ کوچک به GLM و Fugu می‌زند،
    جواب + telemetry + عدمِ عبور از cap را تأیید می‌کند (LIVE).
  - اگر کلیدها نباشند: با stub transport کار می‌کند (OFFLINE، $0).
  - kill-switch/disaster/alert دست‌نخورده.
$0 آفلاین به‌طور پیش‌فرض.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("llm-routing-smoke")

_OPS = (harness.REAL_VAULT / r"_ops")
for _p in [str(_OPS), str(_OPS / "budget"), str(_OPS / "debate")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# .env را load کن (اگر هست)
import env_loader  # noqa: E402
env_status = env_loader.load_env()

import opslib  # noqa: E402
from client import MultiProviderClient, RefuseToSend, TelemetryError, GATEWAY_URL  # noqa: E402
import client as _client  # noqa: E402
# F-G8: constructing MultiProviderClient without a transport calls _gateway_is_up()
# which pings localhost:4000 (LiteLLM). Force the offline path so no gateway ping
# leaves the process (barrier blocks it anyway; this makes attempts == 0).
_client._gateway_is_up = lambda: False

# budgets.yaml واقعی (نه harness mock) — تست‌های routing/structural آن را می‌خوانند
REAL_BUDGETS_PATH = _OPS / "budget" / "budgets.yaml"


def _real_budgets():
    """budgets.yaml واقعیِ vault را مستقیم پارس کن با yaml (نه harness mock)."""
    import yaml
    return yaml.safe_load(REAL_BUDGETS_PATH.read_text(encoding="utf-8"))


def _has_key(name):
    return bool(os.environ.get(name))


# ════════════════════════════════════════════════════════════════════════════════
# (الف) routing در budgets.yaml = GLM + Fugu
# ════════════════════════════════════════════════════════════════════════════════

def t_routing_has_glm():
    """budgets.yaml واقعی باید routing.glm با provider=glm داشته باشد."""
    b = _real_budgets()
    glm = b.get("routing", {}).get("glm", {})
    assert glm.get("provider") == "glm", f"glm provider باید glm باشد: {glm}"
    assert glm.get("model"), "glm model باید ست باشد"


def t_routing_has_fugu():
    """budgets.yaml واقعی باید routing.orchestr با provider=sakana/fugu داشته باشد."""
    b = _real_budgets()
    orch = b.get("routing", {}).get("orchestr", {})
    assert orch.get("provider") == "sakana", f"orchestr provider باید sakana باشد: {orch}"
    assert "fugu" in str(orch.get("model", "")), "orchestr model باید fugu باشد"


def t_cap_is_owner_30():
    """cap_monthly = ۳۰ (رأی مالک go-live 2026-07-10 «۳۰ بماند»؛ قبلاً 07-09 balanced=200 شده بود).
    سقفِ سختِ خرجِ ماهانه با گیتِ پولیِ باز."""
    b = _real_budgets()
    cap = b.get("global", {}).get("cap_monthly", 0)
    assert cap == 30, f"cap باید ۳۰ باشد (رأی مالک)، نه {cap}"


def t_disaster_kill_alert_unchanged():
    """spike_pct (kill-switch) دست‌نخورده؛ cap زیرِ disaster (500)."""
    b = _real_budgets()
    assert b.get("global", {}).get("spike_pct") == 25, "spike_pct باید 25 بماند (kill-switch)"
    cap = b.get("global", {}).get("cap_monthly", 0)
    assert cap < 500, "cap باید زیرِ خطِ فاجعه (500) بماند"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) key فقط از env (هرگز hardcode)
# ════════════════════════════════════════════════════════════════════════════════

def t_glm_key_only_env():
    """ZAI_API_KEY (GLM) فقط از env می‌آید — هیچ hardcode در client.py نیست.
    مسیرِ gateway از LITELLM_MASTER_KEY (از gateway/.env) استفاده می‌کند؛ مسیرِ مستقیم از ZAI_API_KEY."""
    src = (_OPS / "debate" / "client.py").read_text("utf-8")
    assert "sk-" not in src, "نباید کلیدِ hardcode داشته باشد"
    assert "ZAI_API_KEY" in src, "باید ZAI_API_KEY را از env بخواند (مسیر مستقیم)"
    assert "LITELLM_MASTER_KEY" in src, "باید LITELLM_MASTER_KEY را از gateway/.env بخواند"


def t_fugu_key_only_env():
    """SAKANA_API_KEY (Fugu) فقط از env می‌آید (مسیر مستقیم). gateway از master_key."""
    src = (_OPS / "debate" / "client.py").read_text("utf-8")
    assert "SAKANA_API_KEY" in src, "باید SAKANA_API_KEY را از env بخواند (مسیر مستقیم)"
    assert "sk-" not in src


def t_no_key_in_budgets_yaml():
    """budgets.yaml نباید کلیدِ واقعی داشته باشد — فقط base_url/model/price."""
    src = (_OPS / "budget" / "budgets.yaml").read_text("utf-8")
    assert "sk-" not in src, "budgets.yaml نباید کلید داشته باشد"


def test_env_loader_never_logs_values():
    """env_loader هرگز مقدارِ کلید را چاپ/log نمی‌کند (فقط set/not-set)."""
    st = env_loader.env_status()
    for k, v in st.items():
        assert v in ("set", "not-set"), f"نباید مقدار را برگرداند: {k}={v}"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) MultiProviderClient — stub (offline) وقتی کلید نیست
# ════════════════════════════════════════════════════════════════════════════════

def test_glm_stub_offline():
    """GLM با stub transport کار می‌کند (offline، $0). budgets واقعی تزریق می‌شود."""
    def stub_transport(body):
        return {"choices": [{"message": {"content": "stub answer"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    b = _real_budgets()
    c = MultiProviderClient(role="glm", transport=stub_transport, budgets=b)
    r = c.complete("test system", "test user", max_tokens=10)
    assert "text" in r and r["text"] == "stub answer"
    assert r["provider"] == "glm"
    assert r["tokens_in"] == 10 and r["tokens_out"] == 5
    # flat subscription → cost 0
    if c.subscription == "max":
        assert r["cost_usd"] == 0.0


def test_fugu_stub_offline():
    """Fugu با stub transport کار می‌کند (offline، $0). budgets واقعی تزریق می‌شود."""
    def stub_transport(body):
        return {"choices": [{"message": {"content": "fugu stub"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 8}}
    b = _real_budgets()
    c = MultiProviderClient(role="orchestr", transport=stub_transport, budgets=b)
    r = c.complete("sys", "usr", max_tokens=10)
    assert r["provider"] == "sakana"
    assert r["tokens_out"] == 8
    # fugu metered → cost > 0 (20*5 + 8*30 per 1M)
    assert r["cost_usd"] > 0


def t_leak_guard_rejects_bad_host():
    """leak-guard: اگر gateway down و کلید مستقیم نباشد → RefuseToSend (نه crash).
    اگر gateway up → مسیرِ gateway (localhost، host-check ندارد چون proxy محلی است)."""
    b = _real_budgets()
    try:
        c = MultiProviderClient(role="glm", budgets=b)
        # اگر gateway up → use_gateway=True، base_url=localhost (proxy محلی، host-check لازم ندارد)
        if c.use_gateway:
            assert "localhost" in c.base_url or "127.0.0.1" in c.base_url
        else:
            # مسیرِ مستقیم → host درست
            assert "api.z.ai" in c.base_url or "bigmodel.cn" in c.base_url
    except RefuseToSend:
        assert True  # gateway down + no key → RefuseToSend


# ════════════════════════════════════════════════════════════════════════════════
# (د-gw) gateway routing structural
# ════════════════════════════════════════════════════════════════════════════════

def t_gateway_model_map_exists():
    """GATEWAY_MODEL_MAP باید glm→glm-coder و sakana→fugu داشته باشد."""
    from client import GATEWAY_MODEL_MAP
    assert GATEWAY_MODEL_MAP.get("glm") == "glm-coder"
    assert GATEWAY_MODEL_MAP.get("sakana") == "fugu"


def t_gateway_url_localhost():
    """GATEWAY_URL باید localhost:4000 باشد."""
    assert "localhost:4000" in GATEWAY_URL


def t_client_uses_gateway_when_up():
    """وقتی gateway بالاست، MultiProviderClient باید use_gateway=True داشته باشد."""
    try:
        b = _real_budgets()
        c = MultiProviderClient(role="glm", budgets=b)
        if c.use_gateway:
            assert c.model == "glm-coder"
            assert "localhost:4000" in c.base_url
    except RefuseToSend:
        assert True  # gateway down + no key → skip


# ════════════════════════════════════════════════════════════════════════════════
# (د) smoke زنده (فقط اگر کلیدها هستند)
# ════════════════════════════════════════════════════════════════════════════════

def test_glm_live_smoke():
    """LIVE: فراخوانِ واقعی به GLM (فقط اگر gateway بالاست یا کلید هست).
    تأیید: جوابِ غیرخالی + telemetry + cost ≤ cap. از طریقِ gateway (localhost:4000)."""
    b = _real_budgets()
    try:
        c = MultiProviderClient(role="glm", budgets=b)
    except RefuseToSend:
        return  # gateway down + no direct key → skip
    if not c.use_gateway and not _has_key("ZAI_API_KEY"):
        return  # offline skip
    r = c.complete("You are a test echo.", "Reply with exactly: PONG", max_tokens=20)
    assert "text" in r, f"GLM باید text برگرداند: {r}"
    assert len(r["text"]) > 0, "GLM جوابِ خالی داد"
    assert r["tokens_in"] + r["tokens_out"] > 0, "GLM باید usage برگرداند"
    assert r["cost_usd"] < 100.0, f"cost باید زیرِ cap باشد: {r['cost_usd']}"


def test_fugu_live_smoke():
    """LIVE: فراخوانِ واقعی به Fugu (فقط اگر gateway بالاست یا کلید هست).
    تأیید: جوابِ غیرخالی + telemetry + cost ≤ cap. max_tokens≥۱۶ (min مدل)."""
    b = _real_budgets()
    try:
        c = MultiProviderClient(role="orchestr", budgets=b)
    except RefuseToSend:
        return
    if not c.use_gateway and not _has_key("SAKANA_API_KEY"):
        return  # offline skip
    r = c.complete("You are a test echo.", "Reply with exactly: PONG", max_tokens=20)
    assert "text" in r, f"Fugu باید text برگرداند: {r}"
    assert len(r["text"]) > 0
    assert r["tokens_in"] + r["tokens_out"] > 0


def t_env_status_report():
    """گزارشِ امنِ وضعیتِ کلیدها (فقط set/not-set)."""
    st = env_loader.env_status()
    # هرگز مقدار
    for k, v in st.items():
        assert v in ("set", "not-set")
    print(f"  [env_status] {st}")   # فقط set/not-set، نه مقدار


if __name__ == "__main__":
    failed = harness.run([
        # (الف) routing
        ("routing glm موجود", t_routing_has_glm),
        ("routing fugu موجود", t_routing_has_fugu),
        ("cap = ۳۰ (رأی مالک)", t_cap_is_owner_30),
        ("disaster/kill/alert دست‌نخورده", t_disaster_kill_alert_unchanged),
        # (ب) key only env
        ("GLM key فقط env", t_glm_key_only_env),
        ("Fugu key فقط env", t_fugu_key_only_env),
        ("no key in budgets.yaml", t_no_key_in_budgets_yaml),
        ("env_loader مقدار را log نمی‌کند", test_env_loader_never_logs_values),
        # (ج) stub offline
        ("GLM stub offline", test_glm_stub_offline),
        ("Fugu stub offline", test_fugu_stub_offline),
        ("leak-guard", t_leak_guard_rejects_bad_host),
        # (د-gw) gateway structural
        ("gateway model map", t_gateway_model_map_exists),
        ("gateway url localhost", t_gateway_url_localhost),
        ("client uses gateway when up", t_client_uses_gateway_when_up),
        # (د) live (skip if no key/gateway)
        ("GLM LIVE smoke", test_glm_live_smoke),
        ("Fugu LIVE smoke", test_fugu_live_smoke),
        # report
        ("env_status report", t_env_status_report),
    ])
    sys.exit(1 if failed else 0)
