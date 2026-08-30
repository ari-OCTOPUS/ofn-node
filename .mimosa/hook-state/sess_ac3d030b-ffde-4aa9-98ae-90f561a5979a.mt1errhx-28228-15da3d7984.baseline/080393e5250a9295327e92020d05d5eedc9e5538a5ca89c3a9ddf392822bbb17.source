import config, brain, agents
from core import HumanCore, MentalModel, CommunicationManager
from core.self_improver import SelfImprover

# --- config ---
assert config._clean('"abc",') == "abc"
assert config._clean("  x  ") == "x"
probs = config.validate(config.Config(None, None, None, None, None, "m", "auto", False, 8))
assert len(probs) == 2
print("config OK")

# --- brain offline + factory fallback ---
bank = brain.QuestionBank()
class Cfg:
    brain_provider = "auto"; claude_key = None
    chatbox_api_key = None; chatbox_base_url = None; brain_model = "x"
prov = brain.get_brain_provider(Cfg(), bank)
assert prov.name == "offline"
assert "❓" in prov.ask("sys", {"domain": "body_hrv"})
print("brain OK ->", prov.name)

# --- agents + router ---
ag = [agents.HealthAgent(prov, bank, "base"), agents.ReflectionAgent(prov, bank, "base")]
r = agents.AgentRouter(ag)
a, d = r.choose({})
assert d in agents.ALL_DOMAINS and "❓" in a.generate_question(d, {"data": "x"}, {})
assert r.route("body_hrv").name == "health" and r.route("mind_emotion").name == "reflection"
# وزن‌دهی: حوزه‌ای با وزنِ بالا و پوششِ صفر باید انتخاب شود
r2 = agents.AgentRouter(ag, {"work_engineering": 5.0})
assert r2.pick_domain({}) == "work_engineering"
print("agents+router OK")

# --- mental model ---
mm = MentalModel(); mm.update_from_log({"sleep": 1})
assert mm.get_profile()["sleep_trend"] == "low"
assert MentalModel.from_json(mm.to_json()).get_profile()["sleep_trend"] == "low"
print("mental_model OK")

# --- communication ---
cm = CommunicationManager()
st = cm.decide_style({"stress_level": 0.9}, {"hour": 3})
assert st.tone == "minimal" and st.emoji_usage is False
adapted = cm.adapt_message("🧭 حوزه: x\n❓ سوال؟\nچرا امروز: چون", st)
assert "سوال" in adapted and "چرا امروز" not in adapted
print("communication OK ->", repr(adapted))

# --- self_improver.reflect (pure) ---
assert SelfImprover.reflect({"total": 3})["ok"] is False
rep = SelfImprover.reflect({"total": 10, "answer_rate": 0.2, "per_domain": {
    "body_hrv": {"asked": 5, "answered": 4}, "mind_emotion": {"asked": 5, "answered": 1}}})
assert rep["ok"] and rep["weight_changes"]["body_hrv"] > 0 and rep["weight_changes"]["mind_emotion"] < 0
print("self_improver OK")

# --- HumanCore end-to-end with a fake db ---
class FakeDB:
    def __init__(s): s.q = []; s.mm = None; s.weights = {}; s.reports = []
    def latest_mm_snapshot(s): return s.mm
    def brain_context(s): return {"data": "RMSSD پایین", "rmssd_low": True, "domain_counts": {}, "hour": 10}
    def log_question_quality(s, a, d, p, q): s.q.append([a, d, p, q, 0]); return len(s.q)
    def update_question_quality(s, qid, answered=None, response_time=None, led_to_log=None): s.q[qid-1][4] = answered
    def save_mm_snapshot(s, j): s.mm = j
    def question_quality_metrics(s, days=14): return {"total": 10, "answer_rate": 0.5, "per_domain": {}}
    def bump_agent_weight(s, domain, delta): s.weights[domain] = s.weights.get(domain, 1) + delta
    def save_improvement_report(s, m, sg, status): s.reports.append(status); return len(s.reports)
    def list_improvement_reports(s, status=None): return []
    def set_improvement_status(s, i, st): return True

fdb = FakeDB()
core = HumanCore(fdb, prov, bank, r, "base")
msg = core.get_daily_question()
assert "❓" in msg or "سوال" in msg
assert len(fdb.q) == 1
core.register_interaction("ask_answer", response="پاسخ", response_time=30)
assert fdb.mm is not None and fdb.q[0][4] == 1
assert "ok" in core.reflect_and_improve()
print("HumanCore end-to-end OK")

print("\nARCHITECTURE TESTS PASSED ✅")
