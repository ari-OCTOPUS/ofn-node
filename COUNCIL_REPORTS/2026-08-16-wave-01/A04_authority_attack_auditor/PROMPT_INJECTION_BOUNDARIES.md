# A04 — PROMPT INJECTION BOUNDARIES

Sources of untrusted content and where they meet reasoning/effects.

## Source map

| Source | Entry module | Reaches brain context? | Fence/trust label | Reaches effects? |
|--------|--------------|------------------------|-------------------|------------------|
| Telegram messages (owner) | tg_api → center/approval_channel | Yes (commands, collab input) | `admit(trust_level="untrusted")` on collab path; commands are structured verbs | Owner-authenticated effects only |
| Telegram/MiniApp non-owner | dropped at `handle_update` | No | N/A (silent drop) | No |
| Lead emails (IMAP/Gmail) | lead_email_intake / email_inbound | Lead pipeline context | readonly EXAMINE; consent/suppression on replies | Drafts behind flag+consent (off) |
| Web pages (web_research) | DDG/Wikipedia/arXiv → research-latest.json | **Yes** — improve/synthesis/think | **NONE** (no fence, no allowlist) | Propose-only buffer (owner tap + shadow-green) |
| Web pages (world_discovery) | public_web.py | Yes (observations) | **UNTRUSTED_EXTERNAL_CONTENT fence + PII/secret redaction** (good pattern) | Evidence-only |
| Web (fetch_guard, ADR-041) | observatory/fetch_guard.py | Only allowlisted hosts | Allowlist+SSRF+audit (not in organism loop) | N/A |
| Obsidian vault notes | ChromaDB via vault_bridge (RAG **ON**) | Yes — evidence snippets | **No trust marker** in retrieval_router output; direction documented narrowing-only | Evidence-only |
| Memory (episodic/semantic) | retrieval_router → prompts | Yes | No markers | Evidence-only |
| Tool/agent results | agent_gateway_http (HMAC), board queue (Bearer) | Queue/panel context | Signed channels; content still data | ack/enqueue only |
| LLM output (model_router) | cortex/brains | Becomes drafts/proposals | Output_guard + propose-only + owner taps (effects); think-text is display-only | Buffered by approval layers |
| Logs/state files | beats | Yes (snapshots) | Trusted-ish (written by organism; but state writable by approved patches — R-8) | Feeds beats |

## Assessment
1. **Two good fences exist** (`UNTRUSTED_EXTERNAL_CONTENT`, quarantine plane) but coverage is partial: the *enabled* web path (`web_research`, flag default off) and the *enabled* memory path (vault RAG=1) are unfenced. Vault notes are the largest always-on untrusted corpus feeding prompts.
2. **Effect-side buffering is the real defence**: untrusted text can at most become proposals/drafts; consequential actions need deterministic owner interactions (tap/approval/chat-id). This held in every path traced.
3. **Residual risk chain:** unfenced web/vault content → improve()/synthesis proposals → owner rubber-stamp → code_autonomy apply (shadow-green + allow-roots). Mitigations exist at every arrow, but arrow 1 is cheap to fix (fence) and arrow 4 is owner behaviour.
4. **Model output treated as untrusted on the write side** (output_guard, propose-only) — consistent with the invariant; input-side provenance labelling is the gap.

## Recommendations (from 06, cross-referenced)
R2/#1: fence web_research output + trust-mark retrieval evidence; OD-D: route through fetch_guard before enabling.
