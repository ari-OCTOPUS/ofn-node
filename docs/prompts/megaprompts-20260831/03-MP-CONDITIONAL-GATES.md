# MP-03 — Conditional send gates (owner ruling 6, Q6.2 OPEN)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory. This is the highest-risk
prompt in the pack.

## Problem

The owner accepted proceeding without secret rotation and said gates may open
"conditionally" — but named none. Six gates are currently closed on the live
node: `live_sms`, `live_dm`, `live_email`, `auto_scrape`, `auto_post`,
`auto_dm`. Red gate 1 recorded a CRITICAL rotation deadline of 2026-08-17,
which has passed. Red gate 2 requires outbox plus confirmation for every send.
Opening any gate without rotation is a deliberate risk acceptance, and only the
owner can name which one.

## Forbidden

Opening any gate. Choosing which gate is "safe". Setting
`OFN_KEEP_GATES_OPEN`. Treating the risk acceptance as a blanket authorisation.
Treating an outbox count as evidence that something was sent.

## Steps

1. Report the current state of all six gates as read from the live node, with
   the command and its output hash. If the node is unreachable from this host,
   say `UNTESTABLE: node_not_reachable_from_this_host` and stop the probe — do
   not infer state from documentation.
2. For each gate, report in one line: what external effect it enables, which
   credential it consumes, and whether that credential is inside the overdue
   rotation set.
3. ASK Q1: which gates, by exact name, may open conditionally? Options are the
   six names plus `none_for_now`.
4. For every gate the owner names, ASK a follow-up: what is the condition —
   time-boxed window, per-message owner confirmation, recipient allowlist, or
   volume cap? One question per gate, sequential.
5. ASK Q(n): what is the automatic close condition if the condition is breached?
6. ASK Q(n+1): does the rotation deadline get formally re-dated, or is the
   overdue state recorded as accepted?
7. Do not flip any flag. Write the owner's conditions as a spec file and open a
   PR. The flip is a separate, later, owner-executed action.

## Expected output

`docs/security/CONDITIONAL-GATES-<date>.yaml`: per-gate condition, close
condition, credential rotation state, and the verbatim owner sentence that
authorised it.

## Done when

Every one of the six gates carries either a named owner condition or
`CLOSED_NO_RULING`. No flag was changed by the agent.
