import os, sys, tempfile, subprocess
from pathlib import Path
ROOT = Path(r"F:\backup")
state = Path(tempfile.mkdtemp(prefix="octopus-builder-verify-state-"))
env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
env["OCTOPUS_STATE_DIR"] = str(state)
env["OCTOPUS_TEST_LIVE_STATE_GUARD"] = "block"
env["OCTOPUS_TEST_NET_GUARD"] = "1"
env["GIT_TERMINAL_PROMPT"] = "0"
env["GIT_OPTIONAL_LOCKS"] = "0"
env["GCM_INTERACTIVE"] = "never"
env["GIT_CONFIG_COUNT"] = "2"
env["GIT_CONFIG_KEY_0"] = "commit.gpgsign"
env["GIT_CONFIG_VALUE_0"] = "false"
env["GIT_CONFIG_KEY_1"] = "core.askPass"
env["GIT_CONFIG_VALUE_1"] = ""
env["TELEGRAM_BOT_TOKEN"] = ""
env["TG_BOT_TOKEN"] = ""
iso = str(ROOT / "_ops/tests/_isolation_boot")
tests = str(ROOT / "_ops/tests")
ops = str(ROOT / "_ops")
env["PYTHONPATH"] = os.pathsep.join([iso, tests, ops])
log = ROOT / "06-EVIDENCE/OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22/builder-test-logs/test_evo_lab_bridge.retry.out.txt"
proc = subprocess.run([sys.executable, "-X", "utf8", "test_evo_lab_bridge.py"], cwd=tests, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
log.write_text((proc.stdout or "") + "\n---STDERR---\n" + (proc.stderr or ""), encoding="utf-8")
print(proc.stdout[-1500:] if proc.stdout else "")
print("EXIT", proc.returncode)
