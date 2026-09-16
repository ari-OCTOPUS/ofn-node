# BrainPort (provider-swappable)
# Interface only — implement on Board2/laptop without baking Sakana forever.

class BrainPort:
    def ask(self, *, business: str, pipeline: str, prompt: str, tier: str = "default") -> dict:
        """Returns {ok, text, model, usage, provider}. Never logs secrets."""

# tier default → provider_model:
#   default → fugu (now) | deepseek-flash (later)
#   hard    → fugu-ultra (now) | deepseek-reasoner (later) — owner budget gate
#   local   → ollama/heuristic — secrets / offline

ALLOW_BUSINESS = {"ziman", "studio", "painting", "lab"}
DENY_TASK_PREFIX = ("architect_sys", "mining", "wlos", "etoro")

ENV (names only):
  BRAIN_PROVIDER=fugu|deepseek
  SAKANA_API_KEY=...
  DEEPSEEK_API_KEY=...   # later
  BRAIN_WEEKLY_SOFT_STOP_PCT=95
