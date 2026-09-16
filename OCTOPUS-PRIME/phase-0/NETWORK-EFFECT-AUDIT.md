# NETWORK-EFFECT-AUDIT.md

> agent F-C (read-only recon). Writer must verify before acting.

## summary
Inventoried every network/external-effect call site under F:\octopus-phase0-isolated\_ops via grep + text reads (no execution, no imports). Effects fall into eight domains: Telegram Bot API (api.telegram.org), PocketSmith (api.pocketsmith.com, incl. the financially-active writeback), Xero, Gmail (googleapis.com), AusTender + generic REST ingest, web research (DDG/Wikipedia/arXiv), local Ollama LLM (127.0.0.1:11434), and cloud LLM providers via a LiteLLM gateway (localhost:4000; deepseek/glm/fugu keys). Plus local-effect sites: six HTTP servers binding 127.0.0.1, three socket liveness probes, and subprocess launches (git worktrees, python test runners, and .bat launcher Popen). Mock seams are uneven: web_research/local_llm/harvest expose clean injectable openers; ps_writeback/tg_api/books_xero/approval_channel expose module-level transport functions ideal for monkeypatch; but email_inbound and ingest_adapter have NO injection seam and require patching urllib.request.urlopen directly. The two most dangerous prod effects are legs/ps_writeback.py (writes back to a live financial account) and live/server.py Popen of .bat launchers (would boot the organism). Production is cleanly separable from test call sites; all networked prod modules are stdlib-urllib only (no requests/httpx/SDKs), and tests already fake at these seams (test_pocketsmith_api patches urlopen, test_books_xero patches _urlopen, test_paper_lead_mvo_e2e installs a socket net-guard).

## findings
- **[critical]** legs/ps_writeback.py performs LIVE financial writeback to PocketSmith via urllib; the only network seam is the module-level _transport(req, timeout) at line 137-139, used at line 180. This is the highest-risk external effect (mutates a real financial account's transaction labels/categories).  
  evidence: `F:\octopus-phase0-isolated\_ops\legs\ps_writeback.py:137`  
  fix: Mock by monkeypatching ps_writeback._transport with a fake returning canned responses; assert flag-off (_flag_on) and _halted() short-circuit before any _transport call. Never run with OCTOPUS_WIRE_* writeback flag on against real key.
- **[critical]** live/server.py launches the organism via subprocess.Popen(["cmd","/c",str(bat)]) at lines 315 and 329 — executing .bat launchers, which the mission forbids running.  
  evidence: `F:\octopus-phase0-isolated\_ops\live\server.py:315`  
  fix: Do not execute this module. In tests, monkeypatch subprocess.Popen and the socket.create_connection probe at line 145 so the 'already-live' guard is taken and no bat is spawned (see tests/S1-04 which patches the guard).
- **[medium]** legs/email_inbound.py calls urllib.request.urlopen directly at lines 112 and 141 against googleapis.com with a Bearer token and has NO injection seam (no opener param, no _transport function).  
  evidence: `F:\octopus-phase0-isolated\_ops\legs\email_inbound.py:112`  
  fix: Only mockable by monkeypatching urllib.request.urlopen at the module level; recommend refactoring to accept an injectable transport like ps_writeback/tg_api for testability.
- **[low]** legs/ingest_adapter.py IngestAdapter._get calls urllib.request.urlopen directly at line 117 with no opener/transport injection param, unlike its sibling harvest_austender which exposes get_json=.  
  evidence: `F:\octopus-phase0-isolated\_ops\legs\ingest_adapter.py:117`  
  fix: Mock via monkeypatch of urllib.request.urlopen or subclass overriding _get; consider adding an opener seam for parity.
- **[medium]** debate/client.py (MultiProviderClient / cloud LLM path) calls urllib.request.urlopen directly at lines 107, 304, 312 (marked pragma: no cover) routing to GATEWAY_URL http://localhost:4000 (LiteLLM proxy) using DEEPSEEK/GLM/FUGU keys; no per-call opener injection.  
  evidence: `F:\octopus-phase0-isolated\_ops\debate\client.py:304`  
  fix: Mock at the higher-level cortex.model_router.ask (pass tier/flags to force local, or fake MultiProviderClient) or monkeypatch urllib.request.urlopen; keep paid-provider keys unset in test env.

## artifact
# NETWORK-EFFECT-AUDIT — F:\octopus-phase0-isolated\_ops

Method: `grep` + text reads + structural inspection only. No execution, no production imports, no network. Every row is grounded in a file:line from the isolated clone. "PROD" = production call site; "TEST" = under `_ops\tests\`.

## A. External network — outbound to remote hosts (PRODUCTION)

| Domain | file:line | Prod/Test | Mock strategy |
|---|---|---|---|
| Telegram Bot API (`api.telegram.org`) | telegram_center/tg_api.py:122 (`_url_json_get`→urlopen), :147 (`_url_json_post`→urlopen); base :33 | PROD | Inject `post_fn`/`get_fn` into `TgClient.__init__`, OR monkeypatch module `tg_api._url_json_post`/`_url_json_get`. Host allowlist at :119/:141 already blocks non-telegram URLs. |
| Telegram Bot API (approval poller) | budget/approval_channel.py:178 (`_url_json_get`), :189 (`_url_json_post`); base `TELEGRAM_API_BASE` :97; consumed by approval_channel_merge.py:48 | PROD | Monkeypatch `approval_channel._url_json_post`/`_url_json_get`, or inject transport at client `__init__` :202. |
| PocketSmith read (`api.pocketsmith.com/v2`) | legs/pocketsmith_api.py:103 (`_get`→urlopen); base :40 | PROD | No dedicated transport fn — monkeypatch `urllib.request.urlopen` (as tests/test_pocketsmith_api.py:80-84 does). Guarded by `_flag_on` :55 + `_api_key` :60. |
| PocketSmith WRITEBACK (financial mutate) | legs/ps_writeback.py:139 (`_transport`→urlopen), invoked :180 | PROD | Monkeypatch `ps_writeback._transport`. HIGHEST RISK: mutates live account labels/categories. Verify `_flag_on`/`_halted` short-circuit. |
| Xero (`books`) | legs/books_xero.py:43 (`_urlopen`→urlopen), used :66/:93 | PROD | Monkeypatch module `books_xero._urlopen` (tests/test_books_xero.py:69-141 does exactly this). |
| Gmail (`www.googleapis.com/gmail`) | legs/email_inbound.py:112 (`fetch_unread`), :141 (`_fetch_message_detail`) | PROD | NO seam — monkeypatch `urllib.request.urlopen`. Recommend adding injectable transport. |
| AusTender (`api.tenders.gov.au`) | legs/harvest_austender.py:79 (`_get_json`→urlopen) | PROD | Clean seam: pass `fetch(get_json=<fake>)` :83. |
| Generic REST ingest | legs/ingest_adapter.py:117 (`IngestAdapter._get`→urlopen) | PROD | No opener param — monkeypatch `urllib.request.urlopen` or subclass `_get`. |
| Web research (DDG/Wikipedia/arXiv) | cortex/web_research.py:63 (`_default_opener`→urlopen) | PROD | Excellent seam: `opener=` threaded through search/research_topics/run_and_persist :137/:153/:186. Pass fake opener. |
| Local LLM — Ollama (`127.0.0.1:11434`) | cortex/local_llm.py:43, :53 (`open_fn = opener or urllib.request.urlopen`); base `OLLAMA_BASE_URL` :24 | PROD | `opener=` param injectable (tests/test_cortex, test_brain_cortisol fake it). |
| Cloud LLM providers via LiteLLM gateway (`localhost:4000`; deepseek/glm/fugu) | debate/client.py:107, :160 (health), :304, :312 (urlopen); `GATEWAY_URL` :132; keys :76/:265 | PROD | Mock at cortex.model_router.ask (force local tier / flags off) or fake `client.MultiProviderClient` (imported model_router.py:122); or monkeypatch urlopen. Keep provider keys unset. |
| LLM router (paid path) | cortex/model_router.py:122 (`import MultiProviderClient`), `_ask_paid` :111; local opener threaded :214/:256 | PROD | Route via flags (CORTEX_LOCAL_FIRST) / pass `opener=`; paid gated by `organ_gate` :123. |

## B. Local HTTP servers — bind 127.0.0.1 (listening-socket effect, PRODUCTION)

| Component | file:line | Prod/Test | Mock strategy |
|---|---|---|---|
| Organism status | organism.py:161 (ThreadingHTTPServer 127.0.0.1), :162 serve_forever | PROD | Test `_StatusHandler` methods directly; never call `_serve`. |
| Cortex | cortex/cortex.py:461 (`_Srv`), :549 serve_forever | PROD | Same — exercise `_Handler`, not serve_forever. |
| Live cockpit | live/server.py:794 (`_Srv`), :885 serve_forever; PORTS :34 | PROD | Test handler; avoid start paths (they Popen bats). |
| Dashboard | dashboard/server.py:954 (ThreadingHTTPServer 127.0.0.1:PORT), :963 serve_forever | PROD | tests/test_dashboard.py:45 binds ephemeral port 0 on loopback — acceptable local-only pattern. |
| Panel | panel/server.py:513 (`_ExclusivePanelServer`), :626 serve_forever | PROD | Test `Handler` methods; bind port 0 if a live server is needed. |
| Lead boundary HTTP | legs/lead_boundary_http.py:262 (HTTPServer), :263 serve_forever | PROD | tests/test_lead_boundary_http.py:173 binds 127.0.0.1:0 (loopback, no external net). |

## C. Socket liveness probes (PRODUCTION)

| Use | file:line | Prod/Test | Mock strategy |
|---|---|---|---|
| Watchdog port probe | watchdog.py:76 (socket.create_connection) | PROD | Monkeypatch socket.create_connection to raise/return. |
| Watchdog extension probe | watchdog_extension.py:85 (socket.create_connection) | PROD | Same. |
| Live server port probe | live/server.py:145 (socket.create_connection) | PROD | Patch to control the 'already-live' guard (blocks the Popen path). |

## D. Subprocess / external process launch (PRODUCTION)

| Use | file:line | Prod/Test | Mock strategy |
|---|---|---|---|
| Launch organism via .bat | live/server.py:315, :329 (Popen `cmd /c <bat>`) | PROD | NEVER run. Monkeypatch subprocess.Popen; force already-live guard. |
| Code-autonomy git+python | cortex/code_autonomy.py:117,126,132,144,292,294,299,305,309 (subprocess.run: git worktree/add/commit/revert/restore + python test runner) | PROD | Monkeypatch subprocess.run; isolate repo (worktree effects hit real git). |
| Mission runner git+python | telegram_center/mission_runner.py:106,115,130,143 (subprocess.run) | PROD | Monkeypatch subprocess.run. |
| Doctor sandbox suite | doctor/doctor.py:467 (subprocess.run suite_cmd) | PROD | `apply_fn`/`suite_cmd` are injectable — pass None/fake. |
| Phase gate | phase_gate.py:93, :111 (subprocess.run) | PROD | Monkeypatch subprocess.run. |
| Held-out evaluator | held_out_evaluator.py:59, :108 (subprocess.run) | PROD | Monkeypatch subprocess.run. |
| Export status ledger | export_status.py:127 (subprocess.run ledger.py) | PROD | Monkeypatch subprocess.run. |

## E. TEST call sites (local-only; kept separate — no external net)

| What | file:line | Notes |
|---|---|---|
| Loopback dashboard server + HTTPConnection | tests/test_dashboard.py:45, :48 (port 0) | Local only. |
| Loopback lead-boundary server + urlopen | tests/test_lead_boundary_http.py:173, :182, :187 (127.0.0.1:0) | Local only. |
| Socket net-guard (blocks all net) | tests/test_paper_lead_mvo_e2e.py:157-159, restored :281 | Installs `_no_net` over socket.connect/create_connection/getaddrinfo. |
| urlopen fake | tests/test_pocketsmith_api.py:80-84 (`FakeUrlopen`) | Patches `urllib.request.urlopen`. |
| _urlopen fake | tests/test_books_xero.py:69-141 | Patches `bx._urlopen`. |
| Telegram host-allowlist assertions | tests/test_tg_api.py:108, :262, :270 | Verifies non-telegram URLs blocked pre-network. |
| Sandbox python subprocess | tests/test_genome_safety.py:39 (`python -c`) | Test harness subprocess. |
| Suite runner subprocess | tests/run_all.py:303 (subprocess.run) | Test orchestrator. |
| Gateway URL assertion | tests/test_llm_routing_smoke.py:176-177 (`localhost:4000`) | Static assert, no net. |
| Static import-guards (assert forbidden net modules absent) | tests/test_drawdown_shadow.py:126; tests/test_spine_sanitize.py:196; tests/test_lead_effect_gate.py:178; tests/test_lead_candidate_inbox.py:202-203; tests/test_lead_boundary_http.py:160 | Source-scan guards; no network. |

## Cross-cutting observations
- All PROD networked modules are **stdlib `urllib` only** — zero `requests`/`httpx`/`aiohttp`/vendor SDKs — so a single `urllib.request.urlopen` (or the module-level transport seam) is the universal mock point.
- **Two remote hosts only** for financially/externally sensitive paths: `api.telegram.org` (host-allowlisted at tg_api.py:119/141 and approval_channel) and `api.pocketsmith.com` — everything else is localhost (Ollama, gateway) or read-only harvest.
- **Seam quality is uneven**: web_research / local_llm / harvest_austender expose clean injectable openers; ps_writeback / books_xero / tg_api / approval_channel expose module-level transport fns; **email_inbound and ingest_adapter lack any seam** and force patching `urllib.request.urlopen`.
- outbound_worker.py:10/37 has by-design **no network import** (`_transport_for` returns a `NOT_ARMED` stub) — safe.
