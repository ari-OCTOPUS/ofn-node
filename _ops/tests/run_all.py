#!/usr/bin/env python3
"""Ø§Ø¬Ø±Ø§ÛŒ Ú©Ù„ Ø³ÙˆØ¦ÛŒØª Ù…ØªØ§Ø¨ÙˆÙ„ÛŒØ³Ù…/Ù…Ù†Ø§Ø¸Ø±Ù‡/ØªÚ©Ø«ÛŒØ± â€” Ù‡Ø± ØªØ³Øª Ø¯Ø± Ù¾Ø±ÙˆØ³Ù‡Ù” Ø¬Ø¯Ø§ (env Ø§ÛŒØ²ÙˆÙ„Ù‡).
Ø§Ø¬Ø±Ø§: python -X utf8 run_all.py"""
import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # Ú©Ù†Ø³ÙˆÙ„Ù Ù¾ÛŒØ´â€ŒÙØ±Ø¶Ù ÙˆÛŒÙ†Ø¯ÙˆØ² (cp1252) ÙˆÚ¯Ø±Ù†Ù‡ Ø±ÙˆÛŒ Ø¨Ø±Ú†Ø³Ø¨Ù â”€/ÙØ§Ø±Ø³ÛŒ Ú©Ø±Ø´ Ù…ÛŒâ€ŒÚ©Ù†Ø¯

HERE = Path(__file__).resolve().parent
TESTS = ["test_client.py", "test_telemetry.py", "test_organ_gate.py",
         "test_epoch.py", "test_debate.py", "test_fitness_sigma.py",
         "test_budget_gate_v2.py", "test_money_gate.py", "test_capability_gate.py",
         "test_attribution.py", "test_panel_lead.py",
         "test_chrono_heartbeat.py", "test_pacemaker_pause_not_die.py", "test_chrono_langar.py",
         # M3 (2026-07-24): reproduction=C6 lifecycle recorder + agent-gateway red-team
         "test_c6_state_machine.py", "test_agent_gateway_redteam.py",
         # C2 (2026-07-25): ØªÙˆÙ„ÛŒØ¯Ú©Ù†Ù†Ø¯Ù‡Ù” ÙØ±Ø¶ÛŒÙ‡Ù” C6 + Ø±ÙØ¹Ù over-markingÙ _mark_hypothesis
         "test_c6_hypothesis_producer.py",
         # 2026-07-25 LIVE path: identity equations + collab/live telegram commands
         "test_identity_equations.py", "test_collab_and_live_commands.py",
         # 2026-07-25 LIVE path B: blackbox scanner + romajan bridge + heart wires
         "test_blackbox_and_bridge.py",
         # P5 (2026-07-24): fresh-arm-token + two-key gate for dangerous capabilities
         "test_arm_gate.py",
         "test_telegram_channel.py", "test_telegram_group_allowlist.py",
         # Task 2+3 (2026-07-24): writerÙ Ø²Ù†Ø¯Ù‡Ù” channel-status + Ø¯ÛŒØ§Ù„ÙˆÚ¯Ù ownerâ†”organ
         "test_channel_status.py", "test_organ_dialogue.py",
         "test_leg.py", "test_doctor.py",
         "test_chord.py", "test_chord_shadow.py",
         "test_phase5.py", "test_spectral.py", "test_chamber.py",
         "test_calibration.py", "test_box.py", "test_evolution.py",
         "test_box_b134.py", "test_sensory.py", "test_rhythm.py",
         "test_cockpit.py", "test_project_f.py",
         # 2026-07-24: test_studio_telegram.py Ùˆ test_dual_brain.py Ø§Ø² TESTS Ø®Ø§Ø±Ø¬ Ø´Ø¯Ù†Ø¯ â€” Ø§ÛŒÙ† Ø¯Ùˆ
         # ØªØ³ØªÙ organism Ø¨Ù‡ Ù…Ø§Ú˜ÙˆÙ„â€ŒÙ‡Ø§ÛŒ v1 (studio_telegram.py / dual_brain.py) Ø§Ø´Ø§Ø±Ù‡ Ø¯Ø§Ø´ØªÙ†Ø¯ Ú©Ù‡ Ø¯Ø±
         # reorgÙ Project-F (57f5138 Â«archive v1 codeÂ» + f63ce32ØŒ pytest 366/0) Ø¨Ù‡ 09-Archive
         # Ù…Ù†ØªÙ‚Ù„ Ùˆ Ø§Ø² Ø¯Ø±Ø®ØªÙ Ø²Ù†Ø¯Ù‡ Ø­Ø°Ù Ø´Ø¯Ù†Ø¯Ø› ÙÙ‚Ø· _v3 Ù…Ø§Ù†Ø¯ (StudioTelegramV3/DualBrainV3ØŒ APIÙ Ù…ØªÙØ§ÙˆØª:
         # _scan_forbidden/_check_compliance Ø¯ÛŒÚ¯Ø± ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø±Ø¯). Ù¾ÙˆØ´Ø´Ù Ù†Ø³Ø®Ù‡Ù” ÙØ¹Ø§Ù„ = ØªØ³ØªÙ Ø¯Ø§Ø®Ù„ÛŒÙ
         # subproject (brain/test_dual_brain_v3.py) Ø·Ø¨Ù‚ Â§11. Ù¾ÙˆØ´Ø´Ù PF Ø¯Ø± Ø³ÙˆØ¦ÛŒØª: test_project_f/
         # test_deep_pf/test_pf_full.
         "test_live_loop.py", "test_proposal_buttons.py", "test_acquisition.py",
             "test_neural.py", "test_deep_pf.py", "test_pf_full.py", "test_frontier.py",
             "test_organism_protective.py", "test_canonical_consolidation.py",
             "test_sprint_beat.py", "test_approval_queue_consistency.py",
             "test_consolidation_wiring.py", "test_spinal_cord_w1.py",
             "test_afferent_path_w2.py", "test_doctor_evolution_wiring.py",
             "test_box_wiring.py", "test_lead_leg_loop.py",
             "test_human_append_guard.py", "test_idea_graph.py",
             "test_connection_selftest.py", "test_germline_wiring.py",
             "test_checkpoint_wiring.py", "test_spectral_wiring.py",
             "test_profile_w3.py", "test_llm_routing_smoke.py",
             "test_barbell_attribution.py", "test_relationships_wired.py",
             "test_phase0_safety_net.py", "test_phase1_wiring.py",
             "test_phase2_scheduler.py", "test_phase4_epistemics.py",
             "test_phase3_trackb.py", "test_phase5_epistemics_wiring.py",
             "test_dashboard.py", "test_cardiac_allometry.py",
         "test_baseline.py", "test_held_out_evaluator.py", "test_phase_gate.py",
         "test_rfc_sweep.py", "test_rfc_submit_blocked.py",
         "test_consolidation_distinguish.py", "test_gate_sweep.py",
         "test_latent_space.py", "test_encoders.py", "test_consolidation_latent.py",
         "test_bcm_forgetting.py", "test_sparse_filter.py", "test_chamber_temperature.py",
         "test_fisher.py", "test_telegram_rfc_router.py",
         "test_cockpit_v2.py",
         "test_heart_math.py", "test_heart_producers.py",
         # 2026-07-21 HH-artery: Ø¬Ø¯Ø§Ø³Ø§Ø²ÛŒÙ Ø¯Ùˆ Ù¾ÙˆÙ„ â€” cognition_effect (Ø§Ø±Ø²Ø´Ù Ø¨ÛŒØ±ÙˆÙ†ÛŒ-ØªØ£ÛŒÛŒØ¯Ø´Ø¯Ù‡) +
         # fuel_meter (Ø³ÙˆØ®ØªÙ ÙˆØ§Ù‚Ø¹ÛŒÙ API=Ø®ÙˆÙ†Ù Ù‚Ù„Ø¨) + consumerÙ‡Ø§ÛŒØ´Ø§Ù† Ø¯Ø± producers.velocity_meterØ›
         # Ù‡Ø± Ø¯Ùˆ flag-off no-op (OCTOPUS_WIRE_COGNITION_EFFECT / OCTOPUS_WIRE_HEART_FUEL)
         "test_heart_cognition.py", "test_heart_fuel.py",
         # 2026-07-21 HH-artery wiring: Ø¨Ø³ØªÙ†Ù orphanÙ Ú©Ø§Ù†Ø§Ù„â€ŒÙ‡Ø§ÛŒ Ø®ÙˆÙ† â€” fuel_meter.record Ø¯Ø±
         # model_router.ask (Ù‡Ø± call ÙˆØ§Ù‚Ø¹ÛŒÙ LLM) + cognition_effect.record Ø¯Ø± live_loop.apply_ari_verdict
         # (ØªØ£ÛŒÛŒØ¯Ù owner=external-validation). Ù‡Ø± Ø¯Ùˆ flag-off no-opØ› producers Ø¯Ø§Ø¯Ù‡Ù” ÙˆØ§Ù‚Ø¹ÛŒ Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯.
         "test_heart_fuel_wiring.py", "test_heart_cognition_wiring.py",
         "test_heart_control.py", "test_heart_loop.py", "test_heart_work.py",
         # B-section three-heart-rhythm-math (2026-07-25): Ø¯Ø§ÙˆØ±Ù Ù†Ø¨Ø¶ + circuit-breakerÙ drawdown
         # (shadow-only) + Ú©Ø§Ø±ØªÙ Ø§Ù†Ø¯ÛŒÚ©Ø§ØªÙˆØ±. Ù‡Ù…Ù‡ advisory/flag-off (Ù¾Ø´ØªÙ OCTOPUS_WIRE_PULSE_ARBITER /
         # HH_DRAWDOWN_ENFORCEØ› enforced_live Ù‡Ù…ÛŒØ´Ù‡ False).
         "test_pulse_arbiter.py", "test_drawdown_guard.py", "test_indicator_scorecard.py",
         "test_needs_nudge.py", "test_cortex.py", "test_live_cockpit.py",
         "test_telegram_poll_e2e.py", "test_self_improve.py",
         "test_p0_security_fixes.py", "test_httpauth.py", "test_go_live.py",
         # 2026-07-20 Stage-1 Security: Ú¯Ø§Ø±Ø¯Ù P2 (Ú©Ø§Ú©Ù¾ÛŒØª Ù‡Ø±Ú¯Ø² STOPÙ Ù…Ø§Ù„Ú© Ø±Ø§ Ø­Ø°Ù/overwrite Ù†Ú©Ù†Ø¯)
         "S1-04_test_cockpit_stop_guard.py",
         # 2026-07-20 Stage-1 Security: ØªÙˆÚ©Ù†Ù HMACÙ callbackÙ ap: (P3ØŒ Ù¾Ø´ØªÙ OCTOPUS_WIRE_CB_TOKEN)
         "S1-05_test_ap_binding.py",
         # 2026-07-20: Ù¾Ù„â€ŒÙ‡Ø§ÛŒ flag-off Ø§Ù„Ø­Ø§Ù‚Ù Ø¯Ùˆ Ù¾Ø±ÙˆÚ˜Ù‡Ù” Ù…Ø§Ù„Ú© (TradeQuote / WLOS)
         "test_tradequote_bridge.py", "test_wlos_bridge.py",
         # 2026-07-20: spineÙ durable outcome + Paper Lead MVO (Ù¾ÛŒØ±Ùˆ Stage-1ØŒ Ø¯Ù„ØªØ§-Ø§Ø³Ú©Ù† Q20)
         "test_outcome_spine.py",
         # 2026-07-20: Decision Receipt (immutableØŒ append-onlyØŒ join Ø¨Ù‡ outcome_storeØ› inertØŒ v1 ÙÙ‚Ø· Ø«Ø¨Øª)
         "test_decision_receipt.py",
         # 2026-07-20 ÛŒÚ©Ù¾Ø§Ø±Ú†Ú¯ÛŒ: Memory Gate v1 (store+FTS5+FSMØŒ self_knowledge=ADVISORYØŒ join Ø¨Ù‡ receipt) + taxonomyÙ ÙˆØ§Ø­Ø¯
         "test_memory_gate.py",
         # 2026-07-28 Octopus-v2030 contracts: exact proposalâ†”approval binding, scoped context,
         # SQLite canonical memory zones, owner-only verified-shared promotion.
         "test_control_contracts_v2.py",
         # 2026-07-20 ÛŒÚ©Ù¾Ø§Ø±Ú†Ú¯ÛŒ: Ops Event Spine v1 (envelope + trace_id Ø§Ø¬Ø¨Ø§Ø±ÛŒ + replay + reconcile)
         "test_event_spine.py",
         # 2026-07-20 ÛŒÚ©Ù¾Ø§Ø±Ú†Ú¯ÛŒ: context fencing (DATA_NOT_INSTRUCTION + ØºØ±Ø¨Ø§Ù„Ù injectionØŒ flag-off passthrough)
         "test_context_fence.py",
         # 2026-07-20 Ø¢ÛŒØªÙ…Û²: reachabilityÙ context fence â€” model_router.ask ÙˆØ±ÙˆØ¯ÛŒÙ LLM Ø±Ø§ ØºØ±Ø¨Ø§Ù„
         # Ù…ÛŒâ€ŒÚ©Ù†Ø¯ (Ù¾Ø´ØªÙ OCTOPUS_WIRE_CONTEXT_FENCEØŒ observe-onlyØŒ flag-off passthroughØ› dead-flag Ø±ÙØ¹)
         "test_context_fence_wiring.py",
         # 2026-07-20 Sol-T1: reachabilityÙ Menu v2 â€” center.handle_update Ø§Ú©Ù†ÙˆÙ† /panel + verbÙ m:
         # Ø±Ø§ Ø¨Ù‡ menu_integration ÙˆØµÙ„ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ (Ù¾Ø´ØªÙ OCTOPUS_WIRE_MENU_V2ØŒ flag-off parityØ› orphan Ø±ÙØ¹)
         "test_menu_v2_wiring.py",
         # 2026-07-20 Sol-T2: Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© â†’ outcomeÙ Ù¾Ø§ÛŒØ¯Ø§Ø± (verdict_recorder + live_loopØŒ Ù¾Ø´ØªÙ
         # OCTOPUS_WIRE_VERDICT_OUTCOME): measurement-onlyØŒ idempotentØŒ restart-replayØ› Ù‚ÙˆØ³Ù Ø´Ú©Ø³ØªÙ‡Ù”
         # in-memory Ø¨Ø³ØªÙ‡ Ø´Ø¯. Ù‡Ø±Ú¯Ø² delivered/settled/revenue.
         "test_verdict_outcome.py",
         # 2026-07-20 Sol-T3: Ú¯Ø§Ø±Ø¯Ù Ø¶Ø¯Ù bypassÙ Ø®Ø§Ù…ÙˆØ´Ù context fence â€” inventoryÙ callerÙ‡Ø§ÛŒ Ù…Ø³ØªÙ‚ÛŒÙ…Ù
         # local_llm.ask Ù‚ÙÙ„ Ø´Ø¯ (callerÙ Ù†Ùˆ Ø®Ø§Ø±Ø¬ Ø§Ø² Ù…Ø¬Ù…ÙˆØ¹Ù‡Ù” Ù…Ø³ØªÙ†Ø¯ = fail).
         "test_llm_fence_coverage.py",
         # 2026-07-23 C2 (Resurrection-Safe Memory): GAP-2 ØªÙˆÚ©Ù†Ù statelessÙ HMAC (restart Ø¯Ú©Ù…Ù‡
         # Ø±Ø§ Ù†Ù…ÛŒâ€ŒÚ©Ø´Ø¯Ø› forged/expired/replay/wrong-owner fail-closed)Ø› GAP-3 Ø¨Ø§Ø²Ø³Ø§Ø²ÛŒÙ Ú©Ø§Ø±ØªÙ Ù…Ø¹ÙˆÙ‚
         # Ø§Ø² outcomes.db Ø¯Ø± Ø¨ÙˆØª (dedupeÙ durable)Ø› D-A Ø§ØªØµØ§Ù„Ù durable_journal Ø¨Ù‡ Ø¯Ú©ØªØ± + Ø¨Ø§Ø²ÛŒØ§Ø¨ÛŒÙ
         # resume-not-restart Ø¨ÙˆØª (EXECUTINGÙ Ø±Ù‡Ø§Ø´Ø¯Ù‡ â†’ RECONCILE_REQUIRED)Ø› Ø´Ù†Ø§Ø³Ù†Ø§Ù…Ù‡Ù” ØªÙˆÙ„Ø¯
         # (system.booted + Ø²Ù†Ø¬ÛŒØ±Ù‡Ù” boot_id)Ø› Ø¨Ø§ØªØ±ÛŒÙ Ù…Ø±Ú©Ø¨Ù Ø±Ø³ØªØ§Ø®ÛŒØ².
         "test_stateless_cb_restart.py",
         "test_deferral_rebuild_boot.py",
         "test_journal_recovery.py",
         "test_boot_certificate.py",
         "test_restart_battery.py",
         # 2026-07-23 C4 (One Event Spine): Ø³Ø·Ø­Ù ØªÙˆÙ„ÛŒØ¯Ù ÙˆØ§Ø­Ø¯Ù spine (spine_adapters.emit_event)ØŒ
         # Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯Ù envelope Û±Û°-ÙÛŒÙ„Ø¯Ù‡ + provenanceÙ never-nullØŒ Ùˆ PARITYÙ dual_write==emit_event
         # (Û² callerÙ Ù…Ø³ØªÙ‚ÛŒÙ… Ù¾Ø´ØªÙ OCTOPUS_SPINE_VIA_ADAPTER Ù‚Ø±Ù†Ø·ÛŒÙ†Ù‡ØŒ Ù¾ÛŒØ´â€ŒÙØ±Ø¶ 0).
         "test_spine_single_surface.py",
         # 2026-07-23 C3 (Durable Learning Loop): learning_gate â€” Ù‚Ø¯Ù…Ù outcomeâ†’Ø®Ø§Ø·Ø±Ù‡Ù” graded Ø¨Ø§
         # Ú¯ÛŒØªÙ held-out (Ø¶Ø¯Ø®ÙˆØ¯ÙØ±ÛŒØ¨ÛŒ: internal-pass+held-out-fail â†’ Ù…Ø³Ø¯ÙˆØ¯)ØŒ dedupÙ ÛŒØ§Ø¯Ú¯ÛŒØ±ÛŒØŒ
         # rollback/supersedeØŒ Ùˆ Ø¨Ø³ØªÙ†Ù Ø­Ù„Ù‚Ù‡ (ØªØµÙ…ÛŒÙ…Ù Ø¨Ø¹Ø¯ÛŒ memory_id Ø±Ø§ Ø§Ø³ØªÙ†Ø§Ø¯ Ù…ÛŒâ€ŒÚ©Ù†Ø¯) + restart.
         "test_learning_loop.py",
         # 2026-07-23 C5 (One Heartbeat shadow): BeatScheduler â€” ÛŒÚ© Ø²Ù…Ø§Ù†â€ŒØ¨Ù†Ø¯ØŒ Û¸ ÙØ§Ø²Ù Ù‚Ø·Ø¹ÛŒ
         # (SENSEâ†’â€¦â†’HEAL)ØŒ budget+circuit-breakerØŒ organ failure isolationØŒ restart continuity
         # (beat_counter durableØŒ beatÙ Ø¨Ø¹Ø¯ÛŒ Ù†Ù‡ Ø¯ÙˆØ¨Ø§Ø±Ù‡)ØŒ HALT ÙÙ‚Ø· ÙØ§Ø²Ù‡Ø§ÛŒ Ø§Ù…Ù†ØŒ ACT dry-run
         # (ØµÙØ± double-actuation)ØŒ system.beatâ†’spineØŒ watchdogÙ stall. Ù¾Ø´ØªÙ OCTOPUS_ONE_HEARTBEAT=0.
         "test_beat_scheduler.py",
         # C7 Slice 4: brain_core shadow composition root (real read-only adapters, zero ACT, parity, flag off)
         "test_brain_core.py",
         # 2026-07-23 C6 (Research & Governed Self-Improvement): research_contract (immutableØŒ
         # falsifiableØŒ tools fail-closed Ø¨Ù‡ constitutional-allowed) + research_loop (governance-gatedØŒ
         # budget Ø³Ø®ØªØŒ falsifyâ†’terminate Ø¨Ø¯ÙˆÙ†Ù Ø¨Ø§Ø²Ù†ÙˆÛŒØ³ÛŒÙ Ø¨ÛŒâ€ŒÙ†Ù‡Ø§ÛŒØªØŒ held-out verifyØŒ Ù†ØªÛŒØ¬Ù‡ ÙÙ‚Ø· Ø§Ø²
         # learning_gate ÙˆØ§Ø±Ø¯ memoryØŒ quarantineØŒ self-model calibrationØŒ durable research-journalØŒ
         # ØµÙØ± auto-apply/merge). owner-gatedØŒ proposal-only.
         "test_research_loop.py",
         # 2026-07-23 C7 Slice 1 (pending-card resurrection): money cards Ø§Ø² gated_effect (SoT) +
         # RFC cards Ø§Ø² rfcs.json Ø¨Ø¹Ø¯ Ø§Ø² restart Ø¨Ø§Ø²Ø³Ø§Ø²ÛŒ Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯ â€” projection-onlyØŒ ØªÙˆÚ©Ù†Ù stateless
         # HMAC (binding Ú©Ø§Ù…Ù„)ØŒ dedupÙ durableØŒ exactly-once RFC verdictØŒ HALT metadata-only-no-actionØŒ
         # terminal/EXECUTING/RECONCILE Ù‡Ø±Ú¯Ø² re-present Ù†Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯. ØµÙØ± ØªØºÛŒÛŒØ±Ù money-authorization.
         "test_pending_card_recovery.py",
         # 2026-07-20 Sol Step 5: Ø­Ù„Ù‚Ù‡Ù” Ø§Ø±Ø²Ø´Ù Paper Lead Ø³Ø±ØªØ§Ø³Ø±ÛŒ (Ù…Ø¹ÛŒØ§Ø±Ù Ø§ØµÙ„ÛŒÙ Ù¾Ø§ÛŒØ§Ù†) â€” Ù„ÛŒØ¯Ù synthetic
         # Ø§Ø² ØªÙˆØ§Ø¨Ø¹Ù ÙˆØ§Ù‚Ø¹ÛŒÙ production: scoreâ†’quoteâ†’Ú©Ø§Ø±ØªÙ TG(sandbox)â†’receipt+outcomeâ†’Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú©â†’spineâ†’
         # replayâ†’metricsÙ Ù‚Ø·Ø¹ÛŒâ†’digest. ØµÙØ± Ø´Ø¨Ú©Ù‡/Ù¾ÙˆÙ„/sendØ› IDÙ‡Ø§ Ø«Ø§Ø¨ØªØ› Ø­Ù„Ù‚Ù‡ ÙˆØ§Ù‚Ø¹Ø§Ù‹ Ø¨Ø³ØªÙ‡.
         "test_paper_lead_mvo_e2e.py",
         # 2026-07-21 Wave1-B: ÙÙ†Ø³Ù LLM â€” inventoryÙ Ù…Ø§Ø´ÛŒÙ†â€ŒÚ†Ú©Ù Ú©Ù„Ù call siteÙ‡Ø§ÛŒ production +
         # Ø¢Ø¯Ø§Ù¾ØªÙˆØ±Ù Ù…Ø´ØªØ±Ú©Ù fence_adapter (observe-onlyØŒ flag-off parityØŒ caller Ù†Ùˆ = fail)
         "test_llm_call_inventory.py",
         "test_fence_adapter_wiring.py",
         # 2026-07-21 Wave1-C: Ù¾ÙˆØ´Ø´Ù LIMITED MULTI-DOMAIN Ø³ØªÙˆÙ†Ù Ø±ÙˆÛŒØ¯Ø§Ø¯ (lead+doctor+ziman+proposalØ›
         # Ûµ Ù†Ø§Ù…Ù canonical Ø¯Ø± taxonomyØ› Ø¢Ø¯Ø§Ù¾ØªÙˆØ±Ù‡Ø§ÛŒ spine_adaptersØ› anti-PII Ø³Ø§Ø®ØªØ§Ø±ÛŒ)
         "test_spine_multidomain.py",
         # 2026-07-21 Trust-Engine: ÙÙ‡Ù…Ù free-text Ù…Ø§Ù„Ú© Ø¨Ø§ Ù…ØºØ²Ù Ø®ÙˆØ¯Ù Ø¨Ø§Øª (model_router) â†’ Ù¾ÛŒØ´Ù†Ù‡Ø§Ø¯Ù
         # Ø³Ø§Ø®ØªØ§Ø±ÛŒØ§ÙØªÙ‡Ø› propose-only (Ù‡Ø± Ø´Ú©Ø³Øª=ok=False fallback)ØŒ autonomy_matrix Ù¾ÛŒØ´Ù†Ù‡Ø§Ø¯ Ø±Ø§ re-check
         # Ù…ÛŒâ€ŒÚ©Ù†Ø¯ + Ù…ØªÙ†Ù Ø®Ø§Ù… Ø¯Ø± Ú¯ÛŒØª (Ù…Ø¯Ù„ Ù‡Ø±Ú¯Ø² Ú¯ÛŒØª Ø±Ø§ Ù¾Ø§ÛŒÛŒÙ† Ù†Ù…ÛŒâ€ŒØ¢ÙˆØ±Ø¯). flag OCTOPUS_TG_LLM_ASK Ø®Ø§Ù…ÙˆØ´.
         "test_llm_intent.py", "test_llm_intent_wiring.py",
         # 2026-07-21 Trust-Engine ÙØ§Ø² C: Ø¯ÛŒÙˆØ§Ø±Ù Ø±Ø¶Ø§ÛŒØª (fail-closed structural) + Ø¢Ø¯Ø§Ù¾ØªØ±Ù
         # canonicalÙ ÙˆØ±ÙˆØ¯ÛŒ (submit_candidate) + Ø¨Ø±Ø´Ù Ø¹Ù…ÙˆØ¯ÛŒÙ synthetic (ØµÙØ± Ø§Ø±Ø³Ø§Ù„Ù Ø¨ÛŒØ±ÙˆÙ†ÛŒØ›
         # market_signal ÙØ§ÛŒÙ„Ù draft Ù†Ù…ÛŒâ€ŒØ³Ø§Ø²Ø¯Ø› halt=receipt-onlyØ› flag OCTOPUS_WIRE_LEAD_CANDIDATES Ø®Ø§Ù…ÙˆØ´)
         "test_consent_firewall.py", "test_lead_candidate_inbox.py",
         # 2026-07-21 Ø³ÛŒÙ…â€ŒÚ©Ø´ÛŒÙ Ù†Ù‚Ø§Ø´ÛŒ/Ù„ÛŒØ¯: Ù‡Ù…Ú¯Ø±Ø§ÛŒÛŒÙ Ø¯Ùˆ inbox (Ú¯Ø§Ø±Ø¯Ù collision) + Ù…Ø³ÛŒØ±Ù canonicalÙ
         # owner_menuâ†’submit_candidate + launcherÙ boundary (flag-off) + freezeÙ inboxÙ Ù‚Ø¯ÛŒÙ…ÛŒ +
         # ÙÛŒÚ©Ø³Ù Ú©Ø±Ø´Ù Ù†Ù‡ÙØªÙ‡Ù” EffectorGate(db=None). Ù‡Ù…Ù‡ flag-off = parity.
         "test_lead_wiring.py",
         # 2026-07-21 LEAD-SAFETY-C1: Ú¯ÛŒØªÙ per-effect + Ú©Ø´ØªÙ†Ù footgunÙ batch-release â€” kindÙ‡Ø§ÛŒ
         # lead_outbound Ù‡Ø±Ú¯Ø² Ø¨Ø§ ÛŒÚ© human-append Ø¢Ø²Ø§Ø¯ Ù†Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯ (release_gated_effects Ù…Ø³ØªØ«Ù†ÛŒ)Ø›
         # ÙÙ‚Ø· release_one ØµØ±ÛŒØ­ + authorization + consent-recheck (market_signal/synthetic Ù‡Ø±Ú¯Ø²)Ø›
         # outbound worker Ù‡Ù…ÛŒØ´Ù‡ NOT_ARMED (ØµÙØ± Ø§Ø±Ø³Ø§Ù„). flag OCTOPUS_WIRE_LEAD_OUTBOUND Ø®Ø§Ù…ÙˆØ´.
         "test_lead_effect_gate.py",
         # 2026-08-02 LEG-SYNC: resumable sync_agent over studio_pf/cartographer/lead.
         # studio_pf has no callable build API, so the real adapter blocks honestly;
         # injected fakes prove the rest of authorizeâ†’draftâ†’first_reply is ordered and idempotent.
         "test_sync_agent.py",
         # 2026-08-02 (ZCode, OMEGA-PARITY-inspired): three additive observability
         # modules â€” budget frustration index (deny aggregation), cross-leg syndrome
         # (budget integrity + outbound funnel invariant), test green-lie classifier.
         # All flag-off, read-only, additive. Evidence in DEEP-SCAN-REPORT-2026-08-02.
         "test_octopus_parity_modules.py",
         # 2026-08-02 (ZCode, PHASE 9): MiniApp read-only state helpers â€”
         # secret-scrubbed, fail-closed, JSON-safe. Read-only; no actions.
         "test_miniapp_state.py",
         # 2026-07-24 Phase-D (Wave-2 WS-5): consent gate/store + funnel + speed-to-lead +
         # release/settle separation + verdictâ†’effect hook. Ù‡Ù…Ù‡ flag-off.
         # (Ø¹Ù…Ø¯Ø§Ù‹ Ù†ÛŒØ§Ù…Ø¯: D7 owner-transport â€” Ú¯Ø§Ø±Ø¯Ù no-networkÙ ØªØ§Ø²Ù‡â€ŒØªØ±Ù masterØ› producer-migration â€”
         #  Ø¨Ø§ Ú¯Ø§Ø±Ø¯Ù Â«harvest = ÛŒÚ© envØŒ ØµÙØ± Ø±Ø§Ø²Â»â€ŒÙ ØªØ§Ø²Ù‡â€ŒØªØ±Ù master ØªØ¶Ø§Ø¯ Ø¯Ø§Ø´Øª.)
         "test_consent_gate.py", "test_funnel_store.py", "test_speed_to_lead.py",
         "test_release_send_separation.py",
         "test_lead_verdict_wiring.py",
         # 2026-07-21 Trust-Engine D6: Ú¯Ø§Ø±Ø¯Ù stalenessÙ releasable Ø¯Ø± Ù„Ø§ÛŒÙ‡Ù” bridge (chrono
         # Ø¯Ø³Øªâ€ŒÙ†Ø®ÙˆØ±Ø¯Ù‡) â€” Ù¾ÛŒØ´ Ø§Ø² settleØŒ releasableÙ Ú©Ù‡Ù†Ù‡ refuse Ù…ÛŒâ€ŒØ´ÙˆØ¯ (Ø´Ú©Ø§ÙÛŒ Ú©Ù‡ sweep_stale_effects
         # Ù¾ÙˆØ´Ø´ Ù†Ù…ÛŒâ€ŒØ¯Ø§Ø¯ Ú†ÙˆÙ† ÙÙ‚Ø· pending Ø±Ø§ Ø¬Ø§Ø±Ùˆ Ù…ÛŒâ€ŒÚ©Ù†Ø¯)
         "test_effector_gate_bridge.py",
         # 2026-07-21 Trust-Engine D7: Ù…Ø±Ø²Ù Ø§Ù…Ø¶Ø§Ø´Ø¯Ù‡Ù” POST /api/v1/lead-candidates Ø±ÙˆÛŒ 127.0.0.1
         # (HMAC/nonce/idempotency/allowlist/haltâ†’503) + Ø§Ø«Ø¨Ø§ØªÙ Ø³Ù„Ø¨ÛŒÙ n8n (ØµÙØ± importÙ Ú¯ÛŒØª/Ø§Ø±Ø³Ø§Ù„)Ø›
         # flag OCTOPUS_WIRE_LEAD_BOUNDARY Ø®Ø§Ù…ÙˆØ´ = listener Ø¨Ø§Ù„Ø§ Ù†Ù…ÛŒâ€ŒØ¢ÛŒØ¯
         "test_lead_boundary_http.py",
         # 2026-07-21 Wave1-D: Ø¬Ø¯Ø§ÛŒÛŒÙ liveness Ø§Ø² Ú©Ø§Ø±/Ø§Ø±Ø²Ø´Ù validated â€” metric_separation Ø§Ø²
         # storeÙ durable Ù‚Ø·Ø¹ÛŒ Ø¨Ø§Ø²Ø³Ø§Ø²ÛŒ Ù…ÛŒâ€ŒØ´ÙˆØ¯Ø› ØªÙ¾Ø´â‰ Ù…ÙˆÙ„Ø¯ØŒ claimâ‰ revenueØŒ fakeâ‰ real delivery
         "test_metric_separation.py",
         # 2026-07-21 Wave1-A: ØµØ¯Ø§Ù‚ØªÙ Ù…Ù†ÙˆÛŒ v2 (ØµÙØ± Ø¯Ø³ØªÙˆØ±Ù Ù…Ø±Ø¯Ù‡/ØªØ¨Ù„ÛŒØºÙ Ù†Ø§Ù…ÙˆØ¬ÙˆØ¯) + Ø±Ø£ÛŒÙ Ø§Ø­Ø±Ø§Ø²Ø´Ø¯Ù‡Ù”
         # Ù…Ø§Ù„Ú© Ø§Ø² update-handlerÙ ÙˆØ§Ù‚Ø¹ÛŒ â†’ OutcomeStoreÙ Ù¾Ø§ÛŒØ¯Ø§Ø± (fail-closed Ø¨Ø¯ÙˆÙ†Ù secretØŒ
         # single-useØŒ replay-safeØ› Ù‡Ø±Ú¯Ø² delivered/settled/revenue)
         "test_menu_v2_honesty.py",
         "test_tg_verdict_durable.py",
         # 2026-07-21 D2: Ø§Ù‡Ø±Ù…â€ŒÙ‡Ø§ÛŒ ACTIVATION-*.flag Ø§Ø² Ú¯ÛŒØª untrack Ø´Ø¯Ù†Ø¯ (Û¸ ÙØ§ÛŒÙ„ØŒ Ø´Ø§Ù…Ù„Ù go-live/
         # cortex-paid/work-llm/heart-doctor/self-improve-auto) â†’ ØºÛŒØ§Ø¨Ø´Ø§Ù† Ù‡Ø± Ú¯ÛŒØªÙ Ø²Ù†Ø¯Ù‡ Ø±Ø§ Ù…ÛŒâ€ŒØ¨Ù†Ø¯Ø¯
         # Ø­ØªÛŒ post-rolloverØ› ÙØ¹Ø§Ù„â€ŒØ³Ø§Ø²ÛŒ = Ø¹Ù…Ù„Ù ØµØ±ÛŒØ­Ù Ù…Ø§Ù„Ú© Ù†Ù‡ Ù¾ÛŒØ´â€ŒÙØ±Ø¶Ù commitâ€ŒØ´Ø¯Ù‡
         "test_activation_untracked.py",
         # 2026-07-21 D1: Ú¯Ø§Ø±Ø¯Ù fail-closed Ø±Ø£ÛŒÙ per-item Ù…Ø§Ù„Ú© Ù‚Ø¨Ù„ Ø§Ø² Ù‡Ø± PUT Ø¨Ù‡ PocketSmith â€”
         # Ø­ØªÛŒ Ø¨Ø§ Ù‡Ø± Ø³Ù‡ ÙÙ„Ú¯Ù Ù…Ø³Ù„Ø­ØŒ Ø¨Ø¯ÙˆÙ†Ù Ø±Ø£ÛŒÙ durableÙ Ù‡Ù…Ø§Ù† Ø¢ÛŒØªÙ… (bind Ø¨Ù‡ tid+field+content_sha256)
         # ØµÙØ± PUTØ› ØµÙØ± auto-approveØ› HALT/whitelist/cap Ø­ÙØ¸ Ø´Ø¯
         "test_ps_writeback_verdict.py",
         # 2026-07-21 D3: Ú¯Ø§Ø±Ø¯Ù drawdown ÙÙ‚Ø·-Ø´Ø§Ø¯Ùˆ (HH_DRAWDOWN_ENFORCE Ø®Ø§Ù…ÙˆØ´) â€” Ø±ÙˆÛŒ breach ÙÙ‚Ø·
         # Ù‡Ø´Ø¯Ø§Ø±Ù advisoryØ› ØµÙØ± Ø§Ø«Ø±Ù Ù¾ÙˆÙ„/block/haltØ› Ø¢Ø³ØªØ§Ù†Ù‡ placeholderÙ owner-tunable
         "test_drawdown_shadow.py",
         # 2026-07-21 D4: Ø³Ø®Øªâ€ŒØ³Ø§Ø²ÛŒÙ G â€” ØªÙˆÚ©Ù†Ù CB Ø¨Ù‡ verbÙ‡Ø§ÛŒ legacy(ok/no/later)+mission(ms:) Ú¯Ø³ØªØ±Ø´ ÛŒØ§ÙØª
         "test_cb_token_legmiss.py",
         # 2026-07-21 D4: Ø¨Ù‡Ø¯Ø§Ø´ØªÙ Ø³Ø§Ø®ØªØ§Ø±ÛŒÙ payload Ø¯Ø§Ø®Ù„Ù event_spine.dual_write (defense-in-depth)
         "test_spine_sanitize.py",
         # 2026-07-20 D-G: Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯Ù STOP â€” HALT-ALL ØªÙˆØ³Ø·Ù watchdog.py + Ù‡Ø± Ø¯Ùˆ watchdogÙ .ps1 honor Ù…ÛŒâ€ŒØ´ÙˆØ¯
         "test_stop_contract.py",
         # 2026-07-20 ÛŒÚ©Ù¾Ø§Ø±Ú†Ú¯ÛŒ: Ø¨Ø³ØªÙ†Ù Ø­Ù„Ù‚Ù‡Ù” Ù„ÛŒØ¯ record-only (leadâ†’receiptâ†’outcomeØŒ memories_used Ø§Ø²
         # Memory GateØŒ verdict=PENDINGØŒ idempotentØ› ØµÙØ± send/money â€” ØªÙˆÙ„ÛŒØ¯Ú©Ù†Ù†Ø¯Ù‡Ù” ÙˆØ§Ù‚Ø¹ÛŒÙ Ø²Ù†Ø¬ÛŒØ±Ù‡Ù” spine)
         "test_lead_outcome_recorder.py",
         # 2026-07-20 ÛŒÚ©Ù¾Ø§Ø±Ú†Ú¯ÛŒ: reachabilityÙ ØªÙˆÙ„ÛŒØ¯Ú©Ù†Ù†Ø¯Ù‡ â€” lead_discovery_beat Ø§Ú©Ù†ÙˆÙ† recorder Ø±Ø§
         # ÙˆØ§Ù‚Ø¹Ø§Ù‹ ØµØ¯Ø§ Ù…ÛŒâ€ŒØ²Ù†Ø¯ (Ù¾Ø´ØªÙ OCTOPUS_WIRE_LEAD_OUTCOMEØŒ Ø®Ø§Ø±Ø¬ Ø§Ø² profile). flag-off=byte-identicalØŒ
         # flag-on=receipt(E1)+outcome Ù¾Ø§ÛŒØ¯Ø§Ø±ØŒ memories_used Ø§Ø² drÙˆÙ† beatØŒ fail-soft (dead-flag Ø±ÙØ¹ Ø´Ø¯).
         "test_lead_outcome_wiring.py",
         "test_lead_learning_wire.py",   # W1 (2026-07-25): Ù‚ÙˆØ³Ù ÛŒØ§Ø¯Ú¯ÛŒØ±ÛŒ Ø§Ø² ØªØµÙ…ÛŒÙ…Ù Ù„ÛŒØ¯
         # 2026-07-20 integration: Ù¾ÙˆØ´Ø´Ù orphan (ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ Ø³Ø¨Ø²Ù Ø±ÙˆÛŒâ€ŒØ¯ÛŒØ³Ú© Ú©Ù‡ Ø¯Ø± run_all Ù†Ø¨ÙˆØ¯Ù†Ø¯ â€”
         # Ù†Ù‚Ø¯Ù Ø³Ù†ØªØ²: Ø¨Ø¯ÙˆÙ†Ù Ø«Ø¨ØªØŒ Ø´Ú©Ø³ØªÙ extractionÙ Ø¢ÛŒÙ†Ø¯Ù‡ Ù†Ø§Ù…Ø±Ø¦ÛŒ Ø§Ø³Øª). ÙÙ‚Ø· Ø³Ø¨Ø²Ù‡Ø§Ø› Û´ orphanÙ Ù‚Ø±Ù…Ø²Ù
         # pre-existing (effector_idempotency/drawdown_enforcer/mining_leg/tg_approval_store) Ø¹Ù…Ø¯Ø§Ù‹ Ø¨ÛŒØ±ÙˆÙ†.
         "test_lead_leg_inbox.py", "test_tg_intent.py", "test_tg_metadata_scan.py",
         "test_ziman_branding.py", "test_merge_applies_knob.py", "test_mining_wiring.py",
         "test_web_research.py", "test_metacognitive.py", "test_discoveries.py",
         "test_events.py", "test_part_loops.py", "test_auto_approve.py",
         # 2026-07-16: Ù…Ø§ØªØ±ÛŒØ³Ù Ø±Ø¯Ù‡Ù” Ø®ÙˆØ¯Ù…Ø®ØªØ§Ø±ÛŒ (Ø±Ø£ÛŒ Ù…Ø§Ù„Ú©: Ú¯ÛŒØªÙ Ø§Ù†Ø³Ø§Ù†ÛŒ ÙÙ‚Ø· Ø¨Ø±Ø§ÛŒ Ù…Ù‡Ù…â€ŒÙ‡Ø§) â€”
         # important Ù‡Ø±Ú¯Ø² Ø¢Ø²Ø§Ø¯ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯Ø› ØºÛŒØ±Ù…Ù‡Ù… Ù¾Ø´ØªÙ OCTOPUS_AUTONOMY_FREE Ø®ÙˆØ¯ØªØµÙ…ÛŒÙ…Ù Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡.
         "test_autonomy_matrix.py",
         "test_business_brain.py", "test_vault_updater.py",
         "test_vault_updater_apply.py", "test_goal_directed.py",
         "test_stress.py", "test_innervation.py", "test_ignition.py",
         "test_standards_s.py", "test_replay_s.py", "test_softwta_shadow.py",
         "test_registry_scan.py", "test_phase1_envelope.py",
         "test_route_scorer.py", "test_calibration_probe.py", "test_consolidate.py",
         "test_execution_board.py", "test_depth_guard.py", "test_guidance_box.py",
         # WS-9 (Painting-OS): Ø§Ú©Ú†ÙˆØ§ÛŒØªÙˆØ±Ù approval â€” Ø±ÙØ¹Ù Â«ØªØ£ÛŒÛŒØ¯Ø´Ø¯Ù‡ ÙˆÙ„ÛŒ Ø¨ÛŒâ€ŒØ§Ú©Ø´Ù†Â» (visibilityØŒ flag-off)
         "test_approval_actuator.py",
         "test_tg_api.py", "test_tg_actions.py", "test_tg_render.py", "test_tg_center.py",
         "test_tg_power.py",   # 2026-07-17: Ù…Ø±Ú©Ø²Ù ÙØ±Ù…Ø§Ù†Ø¯Ù‡ÛŒ (Ù…Ú©Ø«Ù ØªÚ©â€ŒÙ¾Ø§ + Ø±Ø¯Ù‡Ù” Ù‚Ø¯Ø±ØªÙ Ø¯ÙˆÚ©Ù„ÛŒÚ©)
         # 2026-07-30: Ø¯Ø³ØªÙˆØ±Ø§Ù„Ø¹Ù…Ù„Ù Ø§Ø³ØªÙØ§Ø¯Ù‡ **Ø¯Ø§Ø®Ù„Ù** ØªÙ„Ú¯Ø±Ø§Ù… (Ù¾ÛŒÙ†Ù General Ù Ú¯Ø±ÙˆÙ‡).
         # Ù…Ù‡Ù…â€ŒØªØ±ÛŒÙ† Ø¨Ù†Ø¯Ø´ Â«Ù‡Ø± Ø§Ø¯Ø¹Ø§ÛŒ Ø±Ø§Ù‡Ù†Ù…Ø§ Ø¯Ø± Ú©Ø¯ Ø¨Ø±Ù‚Ø±Ø§Ø± Ø§Ø³ØªÂ» â€” Ø±Ø§Ù‡Ù†Ù…Ø§ÛŒ Ø¯Ø±ÙˆØº
         # ÙØ¹Ø§Ù„Ø§Ù†Ù‡ Ú¯Ù…Ø±Ø§Ù‡ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ØŒ Ø¨Ø¯ØªØ± Ø§Ø² Ù†Ø¨ÙˆØ¯Ù†Ø´.
         "test_tg_guide.py",
         "test_tg_mission.py", # 2026-07-18: Mission Genome + Action Graph Ø¨Ø±Ø§ÛŒ self-coding Ú©Ù†ØªØ±Ù„â€ŒØ´Ø¯Ù‡
         "test_tg_mission_runner.py", # 2026-07-18: Runner v0 â€” Ø§Ø¬Ø±Ø§ÛŒ Ø§ÛŒØ²ÙˆÙ„Ù‡Ù” allowlisted + evidence
         "test_code_autonomy.py",
         # 2026-07-29 â€” Ù¾Ù„Ù outboxÙ Ø¯Ú©ØªØ±Ù Ø§Ø®ØªØ§Ù¾ÙˆØ³ (OCTOPUS-DOCTOR) Ø¨Ù‡ Ù…Ø±Ú©Ø²Ù ØªÙ„Ú¯Ø±Ø§Ù…Ø›
         # flag-off no-op (OCTOPUS_WIRE_DOCTOR_TG). Ù‡Ø±Ù…ØªÛŒÚ©: ORG_ROOT Ù…ÙˆÙ‚Øª.
         "test_doctor_link.py",
         # Û²Û°Û²Û¶-Û°Û·-Û²Û· â€” Ú¯Ø§Ø±Ø¯Ù‡Ø§ÛŒ Ù…ØµØ±Ùâ€ŒÚ©Ù†Ù†Ø¯Ù‡â€ŒÙ‡Ø§ÛŒ ØªØ§Ø²Ù‡Ù” Ù…ØºØ²Ù Ú¯Ø±Ø§Ù†. Ù…Ù…ÛŒØ²ÛŒÙ Ù…ØªØ®Ø§ØµÙ…Ù Ù‡Ù…Ø§Ù† Ø±ÙˆØ²
         # Ù†Ø´Ø§Ù† Ø¯Ø§Ø¯ Ù‡ÛŒÚ†â€ŒÚ©Ø¯Ø§Ù… Ø§ÛŒÙ†â€ŒØ¬Ø§ Ø«Ø¨Øª Ù†Ø´Ø¯Ù‡ Ø¨ÙˆØ¯Ù†Ø¯: ÛµÛ² ØªØ³ØªÙ ØªØ§Ø²Ù‡ Ù†ÙˆØ´ØªÙ‡ Ø´Ø¯Ù‡ Ø¨ÙˆØ¯ Ú©Ù‡ Ø¯Ø±
         # Ø³ÙˆÛŒÛŒØªÙ Ø±Ø³Ù…ÛŒ (Ùˆ Ø¯Ø± Ø³ÙˆÛŒÛŒØªÙ Ø³Ø§ÛŒÙ‡Ù” Ø®ÙˆØ¯Ù self_patch) Ø§ØµÙ„Ø§Ù‹ Ù†Ù…ÛŒâ€ŒØ¯ÙˆÛŒØ¯.
         "test_deep_think.py",        # Ø¬Ù„Ø³Ù‡â€ŒÙ‡Ø§ÛŒ ÙÚ©Ø±Ù Ø¹Ù…ÛŒÙ‚ + Ù…Ø±Ø²Ù PII Ù„ÙˆÙ„Ù‡Ù” Ù„ÛŒØ¯
         "test_ask_brain.py",         # Ú¯ÙØªÚ¯ÙˆÛŒ Ø¢Ø²Ø§Ø¯Ù ØªÙ„Ú¯Ø±Ø§Ù… + Ø³Ù‡Ù…ÛŒÙ‡ + Ù…Ø±Ø²Ù Â«ÙÙ‚Ø· Ø­Ø±ÙÂ»
         "test_mirror_room.py",       # Ø§ØªØ§Ù‚Ù Ø¢ÛŒÙ†Ù‡: Ø­Ø§ÙØ¸Ù‡Ù” Ú¯ÙØªÚ¯Ùˆ + Ù„Ø§ÛŒÙ‡Ù” ØªØµØ­ÛŒØ­Ù Ù…Ø§Ù„Ú©
         "test_selfaware_wiring.py",  # Ù‚ÙÙ„Ù Ù¾Ù†Ø¬ Ø³ÛŒÙ…Ù Ø®ÙˆØ¯Ø¢Ú¯Ø§Ù‡ÛŒ (Ø§Ø³Ú©Ù†Ù Û°Û·-Û²Û·)
         "test_negotiate.py",         # Ù…Ø°Ø§Ú©Ø±Ù‡: Ø¬ÙˆØ§Ø¨Ù Ø³ÙˆÙ… + Â«Ù‚Ø¨ÙˆÙ„ â‰  Ø§Ø¬Ø±Ø§Â»
         "test_bcm_feed_and_verdicts.py",  # ØªØºØ°ÛŒÙ‡Ù” BCM + ØµÙÙ Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Ø¯Ø± Ø®ÙˆØ¯Ø¢Ú¯Ø§Ù‡ÛŒ
         "test_vault_wires.py",  # Ø¯Ø§Ù†Ø´Ù Ø§Ø¨Ø³ÛŒØ¯ÛŒÙ† â†’ Ø±ÙØªØ§Ø±
         "test_html_and_correction_safety.py",  # escape Ù Ù…ØªÙ†Ù Ù…Ø¯Ù„ + Ù…Ø±Ø²Ù Ú©Ù„Ù…Ù‡Ù” ØªØµØ­ÛŒØ­
         "test_owner_answers_2026_07_27.py",  # Ø³Ù‡ Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú©: Ú©ÙˆØª/Ø³Ú©ÙˆØª/Ù…Ù†Ù‚Ø¶ÛŒâ€ŒÙ‡Ø§
         "test_initiative_and_autonomy.py",  # Ø§Ø¨ØªÚ©Ø§Ø± + Ù…Ø±Ø²Ù Ø§Ø®ØªÛŒØ§Ø±
         "test_tool_request.py",  # Â«Ú†Ù‡ Ø§Ø¨Ø²Ø§Ø±ÛŒ Ù†Ø¯Ø§Ø±Ù…Â» â€” Ø«Ø¨Øª Ù‡Ø±Ú¯Ø² Ú¯ÛŒØª Ù†Ø¯Ø§Ø±Ø¯ØŒ ÙÙ‚Ø· ØªØ­ÙˆÛŒÙ„
         "test_recall_trend.py",  # Â«Ø¨Ù‡ ÛŒØ§Ø¯ Ù…ÛŒâ€ŒØ¢ÙˆØ±Ø¯ØŸÂ» â€” Ø³Ø±ÛŒØŒ Ù†Ù‡ Ø¹Ú©Ø³Ù Ù„Ø­Ø¸Ù‡â€ŒØ§ÛŒ
         "test_paid_truncation.py",  # Ù¾Ø§Ø³Ø®Ù Ø¨Ø±ÛŒØ¯Ù‡Ù” Ù…ØºØ²Ù Ù¾ÙˆÙ„ÛŒ = Ø´Ú©Ø³ØªØŒ Ù†Ù‡ ok=True
         # Û²Û°Û²Û¶-Û°Û·-Û³Û° â€” Ù‡Ø§Ø±Ù†Ø³Ù Ø®ÙˆØ¯Ù‡Ø¯Ùâ€ŒÚ¯Ø°Ø§Ø±ÛŒ. Ù‡Ø± Ú†Ù‡Ø§Ø± plain-assert Ø§Ù†Ø¯ (ØªØ§Ø¨Ø¹Ù `t_` +
         # Ø±Ø§Ù†Ø±Ù `__main__` + `harness.run`)ØŒ Ù¾Ø³ Ø¹Ù…Ø¯Ø§Ù‹ **Ø¯Ø± TESTS** Ø§Ù†Ø¯ Ù†Ù‡
         # PYTEST_TESTS â€” Ø¯Ø±Ø³Ù green-lie Ù `test_synapse_sense`: ÙØ§ÛŒÙ„Ù pytest-style
         # Ú©Ù‡ direct-run Ø´ÙˆØ¯ ØµÙØ± assert Ù…ÛŒâ€ŒØ¯ÙˆØ¯ Ùˆ exit 0 Ù…ÛŒâ€ŒØ¯Ù‡Ø¯.
         "test_goal_generator.py",   # Ù‡Ø¯ÙÙ Ø¨ÛŒâ€ŒØªØ±Ø§Ø²Ùˆ Ø³Ø§Ø®ØªÙ‡ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯ + Ú†Ø±Ø®Ø´Ù Ø±ÙˆØ´ ÙÙ‚Ø· Ø¨Ø¹Ø¯ Ø§Ø² FAIL
         "test_prereg_evaluator.py",  # Ù¾ÛŒØ´â€ŒØ«Ø¨ØªÙ fail-closed + Ø§Ø±Ø²ÛŒØ§Ø¨ÛŒ Ú©Ù‡ target Ø±Ø§ Ø¬Ø§Ø¨Ù‡â€ŒØ¬Ø§ Ù†Ù…ÛŒâ€ŒÚ©Ù†Ø¯
         "test_test_cycle_beat.py",  # ØµØ¯Ø§Ú©Ù†Ù†Ø¯Ù‡Ù” Ú†Ø±Ø®Ù‡: Ø²Ù†Ø¬ÛŒØ±Ù‡Ù” Ú©Ø§Ù…Ù„ØŒ Ø¶Ø¯Ù Ø¯ÙˆØ¨Ø§Ø±-Ø´Ù„ÛŒÚ©
         "test_target_guard.py",  # Ù…Ù‚ØµØ¯Ù Ù¾Ú†: resolve Ù‚Ø¨Ù„ Ø§Ø² Ù‚Ø¶Ø§ÙˆØª (Ú©ÙˆØ±Ù¾ÙˆØ³Ù ÙØ±Ø§Ø±Ù Û°Û·-Û³Û°)
         "test_goal_max_circular.py",  # Ø³Ù‡Ù…ÛŒÙ‡Ù” Ø¯Ø§ÛŒØ±Ù‡â€ŒØ§ÛŒ: Ø§Ø³ØªØ«Ù†Ø§ Ø¨Ø§ÛŒØ¯ **Ù…Ù†Ù‚Ø¶ÛŒ Ø´ÙˆØ¯**
         "test_schema_single_source.py",  # A3: Property Schema ØªÚ©â€ŒÙ…Ù†Ø¨Ø¹ â€” Ù†Ù‡ Ù‡Ø§Ø±Ø¯Ú©Ø¯Ù validator
         "test_spend_cap_window.py",  # A1: Ù¾Ù†Ø¬Ø±Ù‡Ù” Ø³Ù‚ÙÙ Ø®Ø±Ø¬ Ø¯Ø± Ú©Ø¯ â€” Ùˆ Ø®ÙˆØ¯Ø´ Ù…Ù†Ù‚Ø¶ÛŒ Ø´ÙˆØ¯
         "test_owner_verdicts.py",  # A2: Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Ø±Ø¯Ù Ú¯ÛŒØªâ€ŒØ¯Ø§Ø± Ø¯Ø§Ø±Ø¯ØŒ Ù†Ù‡ ÙÙ‚Ø· ÙØ§ÛŒÙ„Ù ignored
         "test_budget_judge.py",  # W1 â€” Ù‚Ø§Ø¶ÛŒÙ Ø¨ÙˆØ¯Ø¬Ù‡ (Ø±Ø²Ø±ÙˆÙ Ù…Ø§Ù„Ú© ØªØ®Ø·ÛŒâ€ŒÙ†Ø§Ù¾Ø°ÛŒØ±)
         "test_decision_gate.py",  # W2 â€” Ú¯ÛŒØªÙ ÛµÛ±/Û´Û¹ (HARD-STOP Ø¨Ø§ Ù…Ø¯Ø±Ú©Ù Ú©Ø§Ù…Ù„ Ù‡Ù… Ø¨Ø³ØªÙ‡)
         "test_trajectory_log.py",  # W3 â€” Ø¯ÙØªØ±Ù Ù…Ø³ÛŒØ± (redact Ù fail-closed)
         "test_teacher_loop.py",  # W4 â€” Ø­Ù„Ù‚Ù‡Ù” Ù…Ø¹Ù„Ù… (Ø¬ÙØªÙ Ø¨ÛŒâ€ŒÙ†Ù…Ø±Ù‡ØŒ Ø¨ÛŒâ€ŒÙ†Ù…Ø±Ù‡ Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯)
         "test_stuck_money.py",  # Û±Û³Û´ â€” Ù¾Ø±Ø¯Ø§Ø®ØªÙ Ù†ÛŒÙ…Ù‡â€ŒÚ©Ø§Ø±Ù‡ Ø¯ÛŒØ¯Ù‡ Ø´ÙˆØ¯ØŒ ÙˆÙ„ÛŒ Ø¯Ø³Øªâ€ŒÙ†Ø®ÙˆØ±Ø¯Ù‡
         "test_money_fsm.py",  # Û±Û³Û¶ â€” ØªØµÙ…ÛŒÙ…Ù Ù¾ÙˆÙ„ÛŒ Ù‡Ø±Ú¯Ø² Ø¨ÛŒâ€ŒØªØµÙ…ÛŒÙ… Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯ (Ø³Ø§ÛŒÙ‡)
         "test_capability_registry.py",  # ÙÙ‡Ø±Ø³ØªÙ Ø®ÙˆØ¯Ú©Ø´Ù â€” Ø³Ø·Ø­ Ø§Ø² Ø¨Ø¯Ù† Ø¹Ù‚Ø¨ Ù†Ù…Ø§Ù†Ø¯
         "test_owner_auth_log.py",  # Ù…Ø¬ÙˆØ²Ù Ù…Ø§Ù„Ú© Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ ÙˆÙ„ÛŒ Ù‡Ø±Ú¯Ø² Ø®ÙˆØ¯Ø´ Ø§Ø¬Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯
         "test_clock_guard.py",  # Û±Û³Ûµ â€” Ø³Ø§Ø¹ØªÙ Ø¹Ù‚Ø¨â€ŒÙ¾Ø±ÛŒØ¯Ù‡ Ø§Ù†Ù‚Ø¶Ø§ Ø±Ø§ Ø²Ù†Ø¯Ù‡ Ù†Ú©Ù†Ø¯
         "test_command_discoverability.py",  # Ø¯Ø³ØªÙˆØ±ÛŒ Ú©Ù‡ Ø¯ÛŒØ¯Ù‡ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯ØŒ Ù†ÛŒØ³Øª
         "test_improve_learning_loop.py",  # Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Ø¨Ø§ÛŒØ¯ Ø¨Ù‡ ÛŒØ§Ø¯Ú¯ÛŒØ±Ù†Ø¯Ù‡ Ø¨Ø±Ø³Ø¯
         "test_orphan_scan.py",  # Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù… Ø¨Ø¯Ø§Ù†Ø¯ Ú©Ø¯Ø§Ù… Ø§Ù†Ø¯Ø§Ù…Ø´ ÙˆØµÙ„ Ù†ÛŒØ³Øª
         # Û°Û¸-Û°Û³ Control Plane ÙØ§Ø² Û±: Ù‚Ø§Ø¹Ø¯Ù‡Ù” Ù…Ø§Ù„Ú©ÛŒØªÙ Ø­Ø§Ù„Øª Ø¨Ø§ÛŒØ¯ **Ø§Ø¬Ø±Ø§** Ø´ÙˆØ¯.
         # Ù…Ø§Ù„Ú© Ù¾Ø±ÙˆØ³Ù‡Ù” Ù…Ø³ØªÙ‚Ù„ Ø±Ø§ Ø§Ù†ØªØ®Ø§Ø¨ Ú©Ø±Ø¯Ø› Ø±ÛŒØ³Ú©Ø´ Â«Ù†ÙˆÛŒØ³Ù†Ø¯Ù‡Ù” Ø¯ÙˆÙ…Â» Ø§Ø³Øª Ú©Ù‡ Ø¯Ø± Ø§ÛŒÙ†
         # Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù… Ø¯Ùˆ Ø¨Ø§Ø± Ø¨Ø§Ú¯ Ø³Ø§Ø®ØªÙ‡. Ø§Ú¯Ø± Ø§ÛŒÙ† ØªØ³Øª Ø¯Ø± Ø³ÙˆÛŒÛŒØª Ù†Ø¨Ø§Ø´Ø¯ØŒ Ù‡Ù…Ø§Ù† Ú©Ù„Ø§Ø³Ù
         # Â«ØªØ³ØªÙ Ø³Ø¨Ø²ÛŒ Ú©Ù‡ Ù‡ÛŒÚ†â€ŒÙˆÙ‚Øª Ù†Ù…ÛŒâ€ŒØ¯ÙˆØ¯Â» Ù…ÛŒâ€ŒØ´ÙˆØ¯ Ú©Ù‡ Û°Û¸-Û°Û³ Ú©Ø´Ù Ø´Ø¯.
         "test_control_plane.py",
         # Û°Û¸-Û°Û³: Ú¯Ø§Ø±Ø¯Ù‡Ø§ÛŒ Ù¾ÛŒØ´â€ŒÙ¾Ø±ÙˆØ§Ø²Ù RESTART-ALL. ØªØ§ Ø§ÛŒÙ† ØªØ§Ø±ÛŒØ® Ø¢Ø²Ù…ÙˆÙ†â€ŒÙ†Ø§Ù¾Ø°ÛŒØ± Ø¨ÙˆØ¯Ù†Ø¯
         # Ú†ÙˆÙ† ØªÙ†Ù‡Ø§ Ø±Ø§Ù‡Ù Ø³Ù†Ø¬ÛŒØ¯Ù†Ø´Ø§Ù† ØªØ²Ø±ÛŒÙ‚Ù ÛŒÚ© `STOP-*` ÙˆØ§Ù‚Ø¹ÛŒ Ø¨Ù‡ Ø¯Ø±Ø®ØªÙ Ø²Ù†Ø¯Ù‡ Ø¨ÙˆØ¯ â€”
         # Ù‡Ù…Ø§Ù† Ú©Ø§Ø±ÛŒ Ú©Ù‡ Ú¯Ø§Ø±Ø¯ Ø¨Ø±Ø§ÛŒ Ø¬Ù„ÙˆÚ¯ÛŒØ±ÛŒâ€ŒØ§Ø´ ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø±Ø¯ (Ùˆ Ø³ÛŒØ³ØªÙ…Ù Ù…Ø¬ÙˆØ² Ø¯Ø±Ø³Øª Ø±Ø¯Ø´
         # Ù…ÛŒâ€ŒÚ©Ù†Ø¯). Ø¨Ø§ Ø¯Ø±Ø²Ù `-OpsRoot` Ú©Ù‡ Ø±ÛŒØ´Ù‡Ù” ØºÛŒØ±Ú©Ø§Ù†ÙˆÙ†ÛŒ Ø±Ø§ preflight-only Ù†Ú¯Ù‡
         # Ù…ÛŒâ€ŒØ¯Ø§Ø±Ø¯ØŒ Ø­Ø§Ù„Ø§ Ù‡Ø± Ú†Ù‡Ø§Ø± Ù…Ø§Ø±Ú©Ø± + ÙØ§ÛŒÙ„Ù ÙÙ„Ú¯Ù LF Ø¬Ø¯Ø§ Ø³Ù†Ø¬ÛŒØ¯Ù‡ Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯.
         # Ù‡Ø± Ø³Ù‡ Ú¯Ø§Ø±Ø¯ Ø¬Ù‡Ø´â€ŒØ¢Ø²Ù…ÙˆØ¯Ù‡â€ŒØ§Ù†Ø¯Ø› Ø®ÙˆØ¯Ù Ø¯Ø±Ø² Ù‡Ù… ÛŒÚ© ØªØ³Øª Ø¯Ø§Ø±Ø¯ Ú©Ù‡ Ø§Ú¯Ø± Ø­Ø°Ù Ø´ÙˆØ¯ Ù‚Ø±Ù…Ø² Ø´ÙˆØ¯.
         "test_restart_preflight.py",
         # Û°Û¸-Û°Û³ Ú¯Ø§Ù…â€ŒÙ‡Ø§ÛŒ Û±â€“Û³ Ù UNIFICATION-DESIGN. ØªØ±ØªÛŒØ¨Ø´Ø§Ù† ÙˆØ§Ø¨Ø³ØªÚ¯ÛŒ Ø§Ø³Øª Ù†Ù‡ Ø³Ù„ÛŒÙ‚Ù‡:
         # provenance ØªÙ†Ù‡Ø§ Ø¬Ø§ÛŒÛŒ Ø§Ø³Øª Ú©Ù‡ Ù‚ÙˆØ§Ø¹Ø¯Ù LIVE/HELD/CONSTANT/UNKNOWN ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø±Ù†Ø¯Ø›
         # lifecycle_fold ØªÙ†Ù‡Ø§ Ø¬Ø§ÛŒÛŒ Ú©Ù‡ Â«ØªØµÙ…ÛŒÙ… Ø§Ø«Ø± Ú©Ø±Ø¯Â» Ø§Ø² Â«ØªØµÙ…ÛŒÙ… Ø«Ø¨Øª Ø´Ø¯Â» Ø¬Ø¯Ø§ Ù…ÛŒâ€ŒØ´ÙˆØ¯
         # (Ø³Ù†Ø¬Ø´Ù Ø²Ù†Ø¯Ù‡: decided=21ØŒ effected=0)Ø› Ùˆ probe_predicate_rule Ù‚Ø§Ø¹Ø¯Ù‡â€ŒØ§ÛŒ Ø§Ø³Øª
         # Ú©Ù‡ Ù‡Ø± ÙÛŒÙ„ØªØ±Ù Ø³Ø§Ø®ØªØ§Ø±Ø§Ù‹-Ù…Ø±Ø¯Ù‡ Ø±Ø§ Ù…ÛŒâ€ŒÚ¯ÛŒØ±Ø¯ â€” Ù†Ù…ÙˆÙ†Ù‡â€ŒØ§Ø´ Û²Û° Ú©Ø§Ø±ØªÙ Ø±Ø§Ú©Ø¯ Ø±Ø§ Ù‡Ø´Øª Ø±ÙˆØ²
         # Ù¾Ø´ØªÙ ÛŒÚ© ØµÙØ±Ù ØªÙ…ÛŒØ² Ù¾Ù†Ù‡Ø§Ù† Ú©Ø±Ø¯Ù‡ Ø¨ÙˆØ¯.
         "test_provenance.py",
         "test_lifecycle_fold.py",
         "test_probe_predicate_rule.py",
         # Û°Û¸-Û°Û³ Ú¯Ø§Ù…â€ŒÙ‡Ø§ÛŒ Û¶â€“Û±Û±. Ù‡Ù…Ù‡ Ú¯Ø§Ø±Ø¯ ÛŒØ§ ØµØ¯Ø§Ù‚ØªÙ Ú¯Ø²Ø§Ø±Ø´â€ŒØ§Ù†Ø¯ØŒ Ù‡ÛŒÚ†â€ŒÚ©Ø¯Ø§Ù… Ø±ÙØªØ§Ø± Ø¹ÙˆØ¶ Ù†Ù…ÛŒâ€ŒÚ©Ù†Ù†Ø¯:
         # Û¶ â† Û´Û°Û¹ Ù Ù†Ù‡ÙØªÙ‡Ù” Ø¨Ø§ØªÙ Û´D Ù¾ÛŒØ´ Ø§Ø² Ù‡Ø± Ø¯Ø³Øªâ€ŒØ²Ø¯Ù†ÛŒ Ø¨Ù‡ Ø¢Ù† Ø¯Ø§ÛŒØ±Ú©ØªÙˆØ±ÛŒ Ø®Ù†Ø«ÛŒ Ø´Ø¯
         # Û· â† ÙØ§ÛŒÙ„â€ŒÙ‡Ø§ÛŒ ACTIVATION-* Ú¯ÛŒØªâ€ŒØ§ÛŒÚ¯Ù†ÙˆØ±Ù†Ø¯ØŒ Ù¾Ø³ Ø­Ø°ÙØ´Ø§Ù† ØªØ§Ø±ÛŒØ®Ú†Ù‡ Ù†Ø¯Ø§Ø±Ø¯Ø› heartstate
         #     Ø¨Ø§ ÙØ§ÛŒÙ„ Ù…Ø³Ù„Ø­ Ø§Ø³Øª Ù†Ù‡ envØŒ Ùˆ Ù‡Ø± Ù…Ù…ÛŒØ²ÛŒÙ ÙÙ„Ú¯ Ø¢Ù† Ø±Ø§ Â«Ø®Ø§Ù…ÙˆØ´Â» Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯
         # Û¸ â† Ø¯Ùˆ Ú©Ù„Ø§Ø³Ù phantom: ØªØ³ØªÙ Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡Ù” untracked (Û±Û³ Ù…ÙˆØ±Ø¯) Ùˆ ÙÙ„Ú¯Ù Ø¨ÛŒâ€ŒÙ…Ø­Ù„Ù Ø§Ø¹Ù„Ø§Ù†
         # Û±Û° â† Â«Ø§Ø¬Ù…Ø§Ø¹Â» Ø¨Ø§ ÛŒÚ© Ù‚Ù„Ø¨Ù Ù…ØªØ­Ø±Ú© Ùˆ Ø¯Ùˆ Ø«Ø§Ø¨Øª Ø¯ÛŒÚ¯Ø± Ù…Ù…Ú©Ù† Ù†ÛŒØ³Øª
         # Û±Û± â† Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ ÛŒÚ© Ù†ÙˆÛŒØ³Ù†Ø¯Ù‡ Ø±ÙˆÛŒ ORGANISM-STATE.json (Ù…Ø³ØªÙ‚ÛŒÙ… Ùˆ ØºÛŒØ±Ù…Ø³ØªÙ‚ÛŒÙ…)
         "test_latent_poller_guard.py",
         "test_activation_flag_presence.py",
         "test_phantom_guards.py",
         # Û°Û¸-Û°Û´ â† Ù†Ú¯Ù‡Ø¨Ø§Ù†Ù tracked Ø¨Ø±Ø§ÛŒ `OCTOPUS-flags.cmd` Ù gitignoreâ€ŒØ´Ø¯Ù‡.
         # phantom_guards Ù†Ú¯Ù‡Ø¨Ø§Ù†Ù **Ù†Ø§Ù…Ù** ÙÙ„Ú¯ Ø§Ø³ØªØ› Ø§ÛŒÙ† ÛŒÚ©ÛŒ Ù†Ú¯Ù‡Ø¨Ø§Ù†Ù **Ù…Ù‚Ø¯Ø§Ø±**ØŒ
         # Ú†ÙˆÙ† `=0` Ù‡Ù… Ù†Ø§Ù… Ø±Ø§ Ø­ÙØ¸ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ Ùˆ Ø§Ø¹Ù„Ø§Ù† Ø±Ø§ Ø³Ø¨Ø² Ù†Ú¯Ù‡ Ù…ÛŒâ€ŒØ¯Ø§Ø±Ø¯.
         "test_safety_flags_stay_armed.py",
         # Û°Û¸-Û°Û´ â† Ù‡ÙˆÚ©Ù PII ÙÙ‚Ø· `Read` Ø±Ø§ Ù…ÛŒâ€ŒØ¯ÛŒØ¯Ø› Bash/Grep/Glob Ù‡Ù…Ø§Ù† Ù…Ø­ØªÙˆØ§
         # Ø±Ø§ Ù…ÛŒâ€ŒØ¢ÙˆØ±Ø¯Ù†Ø¯ Ùˆ Ø§ØµÙ„Ø§Ù‹ ØµØ¯Ø§ Ø²Ø¯Ù‡ Ù†Ù…ÛŒâ€ŒØ´Ø¯. Ø§ÛŒÙ† ØªØ³Øª Ù‡Ù… Ù¾ÙˆØ´Ø´ Ø±Ø§ Ù…ÛŒâ€ŒØ³Ù†Ø¬Ø¯ Ùˆ
         # Ù‡Ù… Ù…Ø«Ø¨ØªÙ Ú©Ø§Ø°Ø¨ Ø±Ø§ (Ø±ÙˆÛŒ Û³Û·Û± ÙØ±Ù…Ø§Ù†Ù ÙˆØ§Ù‚Ø¹ÛŒÙ Ø¬Ù„Ø³Ù‡: ØµÙØ±).
         "test_pii_guard_covers_every_read_tool.py",
         # Û°Û¸-Û°Û´ â† Ø¨ÙˆØ¯Ø¬Ù‡Ù” Ø§ÛŒÙ†Ø¯Ú©Ø³Ù Ø§Ø¨Ø³ÛŒØ¯ÛŒÙ†. Û¸Û±Ùª Ø§Ø² Ú†ÛŒØ²ÛŒ Ú©Ù‡ Ø¨Ø§Ø± Ù…ÛŒâ€ŒÚ©Ø±Ø¯
         # ØºÛŒØ±Ù‚Ø§Ø¨Ù„Ùâ€ŒØ±Ù†Ø¯Ø± Ø¨ÙˆØ¯ (npy+py ØªÙ†Ù‡Ø§ÛŒÛŒ Û´Û²Ùª). app.json Ø±Ø§ Ø®ÙˆØ¯Ù Ø§Ø¨Ø³ÛŒØ¯ÛŒÙ†
         # Ù‡Ù… Ù…ÛŒâ€ŒÙ†ÙˆÛŒØ³Ø¯ØŒ Ù¾Ø³ Ø¨Ø¯ÙˆÙ†Ù Ú¯Ø§Ø±Ø¯ Ø¨ÛŒâ€ŒØµØ¯Ø§ Ø¨Ø±Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø¯.
         "test_obsidian_index_budget.py",
         # Û°Û¸-Û°Û´ â† Â§Û±Û± Ù…Ù†Ø´ÙˆØ± Ù…ÛŒâ€ŒÚ¯ÙˆÛŒØ¯ Ù‡Ø± Ø¯Ùˆ validator Ù vault Ø¨Ø§ÛŒØ¯ Ù¾Ø§Ø³ Ø´ÙˆÙ†Ø¯ØŒ
         # ÙˆÙ„ÛŒ ØµÙØ± ØµØ¯Ø§Ú©Ù†Ù†Ø¯Ù‡ Ø¯Ø§Ø´Øª. ratchet Ø§Ø³Øª Ù†Ù‡ Ú¯ÛŒØªÙ ØµÙØ±: Û³Û° Ù„ÛŒÙ†Ú©Ù Ø´Ú©Ø³ØªÙ‡ Ùˆ
         # Û²Û· Ø®Ø·Ø§ÛŒ ÙØ±Ø§Ù†Øªâ€ŒÙ…ØªØ± Ø¨Ø¯Ù‡ÛŒÙ Ù¾ÛŒØ´â€ŒÙ…ÙˆØ¬ÙˆØ¯Ù†Ø¯ Ùˆ ÙÙ‚Ø· Ù†Ø¨Ø§ÛŒØ¯ Ø¨Ø¯ØªØ± Ø´ÙˆÙ†Ø¯.
         "test_vault_hygiene_ratchet.py",
         # Û°Û¸-Û°Û´ â† gateway ØªÙ†Ù‡Ø§ Ù¾Ø§ÛŒÛŒ Ø¨ÙˆØ¯ Ú©Ù‡ env_loader Ø±Ø§ ØµØ¯Ø§ Ù†Ù…ÛŒâ€ŒØ²Ø¯ â‡’ Ø¨Ø¯ÙˆÙ†Ù
         # ØªÙˆÚ©Ù† Ø¨Ø§Ù„Ø§ Ù…ÛŒâ€ŒØ¢Ù…Ø¯ Ùˆ Û±Û°Û°Ùª Ø¯Ø±Ø®ÙˆØ§Ø³Øªâ€ŒÙ‡Ø§ Ø±Ø§ Û´Û°Û³ Ù…ÛŒâ€ŒÚ©Ø±Ø¯. Ø§Ø² Ø¨ÛŒØ±ÙˆÙ† Ø¯Ù‚ÛŒÙ‚Ø§Ù‹
         # Ø´Ø¨ÛŒÙ‡Ù Â«Ø§Ø­Ø±Ø§Ø² Ø³Ø§Ù„Ù…Â» Ø¨ÙˆØ¯.
         "test_every_limb_loads_its_credentials.py",
         # Û°Û¸-Û°Û´ â† Ø­Ù„Ù‚Ù‡Ù” poll Ù Ù…Ø±Ú©Ø² Ø´Ú©Ø³ØªÙ handle_update Ø±Ø§ Ø¨ÛŒâ€ŒØµØ¯Ø§ Ù…ÛŒâ€ŒØ¨Ù„Ø¹ÛŒØ¯ Ùˆ
         # offset Ø§Ø² Ø±ÙˆÛŒØ´ Ø±Ø¯ Ù…ÛŒâ€ŒØ´Ø¯ â‡’ Ù¾ÛŒØ§Ù…Ù Ù…Ø§Ù„Ú© Ø¨Ø±Ø§ÛŒ Ù‡Ù…ÛŒØ´Ù‡ Ú¯Ù…. Ø´Ú©Ø§ÛŒØªÙ Ø²ÛŒØ³ØªÙ‡:
         # Â«Ø§Ù†Ú¯Ø§Ø± Ù‡Ø±Ú©Ø§Ø±ÛŒ Ù…ÛŒâ€ŒÚ©Ù†Ù… Ø¯ÛŒØ¯Ù‡ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯Â».
         "test_no_silent_message_drop.py",
         # Û°Û¸-Û°Û´ â† Ø¯Ùˆ Ø¯Ø±ÙˆØº Ùˆ ÛŒÚ© Ú†Ø±Ø®Ù†Ø¯Ù‡ Ø±ÙˆÛŒ Ø³Ø·Ø­Ù ØªÙ„Ú¯Ø±Ø§Ù…: Ø³Ù†ØªÛŒÙ†Ù„Ù Â«Ù†Ø§Ù…Ø¹Ù„ÙˆÙ…Â» Ú©Ù‡
         # Û±Û±Ù«Û¶ Ø±ÙˆØ² Ø±Ù†Ø¯Ø± Ù…ÛŒâ€ŒØ´Ø¯ Â· Ø§Ø¯Ø¹Ø§ÛŒ Ø¨ÛŒâ€ŒÙ¾Ø§ÛŒÙ‡Ù” Â«Ù¾ÛŒØ§Ù…Øª Ø±Ø§ Ù†Ø¯ÛŒØ¯Ù…Â» Â· Ùˆ Ú©Ø§Ø±ØªÛŒ Ú©Ù‡
         # Ø¨Ø§ Ù‡Ø± hold Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ù…ÛŒâ€ŒØ±ÙØª (Û±Û°Û´ Ø§Ø±Ø³Ø§Ù„Ù ÛŒÚ©Ø³Ø§Ù† Ø¯Ø± Û¸Û° Ø¯Ù‚ÛŒÙ‚Ù‡).
         "test_telegram_truthful_receipts.py",
         # Û°Û¸-Û°Û´ â† Ø¯Ùˆ Ø´Ú©Ø§ÙÙ Ø³Ø§Ø®ØªØ§Ø±ÛŒ: Ù‡ÛŒÚ† Ù„Ø§Ú¯Ù ÙˆØ±ÙˆØ¯ÛŒ Ù†Ø¨ÙˆØ¯ (Ù¾Ø³ Â«Ù¾ÛŒØ§Ù…Ù… Ø±Ø³ÛŒØ¯ØŸÂ»
         # Ø¬ÙˆØ§Ø¨ Ù†Ø¯Ø§Ø´Øª)ØŒ Ùˆ ÙˆØ§Ú†â€ŒØ¯Ø§Ú¯ Ø²Ù†Ø¯Ù‡â€ŒØ¨ÙˆØ¯Ù† Ø±Ø§ Ø§Ø² **ÙˆØ¬ÙˆØ¯** Ø§Ø³ØªÙ†ØªØ§Ø¬ Ù…ÛŒâ€ŒÚ©Ø±Ø¯ØŒ
         # Ù¾Ø³ ÛŒÚ© Ù…Ø±Ú©Ø²Ù Ù‡Ù†Ú¯â€ŒÚ©Ø±Ø¯Ù‡ Û²Ø³Û³Û´Ø¯ Ù†Ø§Ù…Ø±Ø¦ÛŒ Ù…Ø§Ù†Ø¯.
         "test_inbound_log_and_hang_detection.py",
         # Û°Û¸-Û°Û´ â† Ø¯Ùˆ Ø¯Ú©Ù…Ù‡Ù” Ú©Ø§Ø±ØªÙ Ù„ÛŒØ¯ Ø±ÙˆØª Ù†Ø¯Ø§Ø´ØªÙ†Ø¯: Ú©Ù„ÛŒÚ© Ù…ÛŒâ€ŒØ´Ø¯Ù†Ø¯ Ùˆ Ù‡ÛŒÚ† Ø§ØªÙØ§Ù‚ÛŒ
         # Ù†Ù…ÛŒâ€ŒØ§ÙØªØ§Ø¯. Ú¯Ø§Ø±Ø¯Ù **Ø±ÙØªØ§Ø±ÛŒ** Ù„Ø§Ø²Ù… Ø¨ÙˆØ¯ Ú†ÙˆÙ† test_callback_routing Ø³ÙˆØ±Ø³
         # Ø±Ø§ Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯ Ùˆ Û¶/Û¶ Ù…ÛŒâ€ŒØ¯Ø§Ø¯ Ø¯Ø± Ø­Ø§Ù„ÛŒ Ú©Ù‡ Ú©Ø¯ Ø¯Ø± Ø§Ø¬Ø±Ø§ Ù…ÛŒâ€ŒØªØ±Ú©ÛŒØ¯.
         "test_lead_card_buttons_live.py",
         # Û°Û¸-Û°Û´ â† Ø§ÛŒÙ† Ø±ÛŒÙ¾Ùˆ **Ø¯Ùˆ** poller Ø¯Ø§Ø±Ø¯. Ù„Ø§Ú¯Ù ÙˆØ±ÙˆØ¯ÛŒ Ø§ÙˆÙ„ ÙÙ‚Ø· Ø±ÙˆÛŒ Ø¨Ø§ØªÙ
         # Ø¨ÛŒØ±ÙˆÙ†ÛŒ Ø±ÙØª â€” Ú©Ù‡ Ø³Ø§Ú©Øª Ø§Ø³Øª â€” Ùˆ ØªØ±Ø§ÙÛŒÚ©Ù ÙˆØ§Ù‚Ø¹ÛŒÙ Ù…Ø§Ù„Ú© Ø§Ø² Ø¨Ø§ØªÙ Ø¯Ø±ÙˆÙ†ÛŒ
         # Ù…ÛŒâ€ŒÚ¯Ø°Ø´Øª. Ù‡Ø± Ø§Ø¨Ø²Ø§Ø±Ù Ø±ØµØ¯ÛŒ Ø¨Ø§ÛŒØ¯ Ù‡Ø± Ø¯Ùˆ Ø±Ø§ Ø¨Ù¾ÙˆØ´Ø§Ù†Ø¯.
         "test_both_bots_log_inbound.py",
         # Û°Û¸-Û°Û´ â† Ù…ØºØ² Ù¾Ø§Ø³Ø®Ù Ø®ÙˆØ¯Ø´ Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ¯ÛŒØ¯: Ø¯Ùˆ ÙÙ‡Ø±Ø³ØªÙ ØºÛŒØ±Ù‚Ø§Ø¨Ù„Ùâ€ŒÙ¾ÛŒÙˆÙ†Ø¯ Ø¯Ø±
         # _context. Û·Û² Ø¯Ø±Ø®ÙˆØ§Ø³ØªÙ pendingØŒ Û¸ Ø±Ø£ÛŒÙ granted â€” Ùˆ Ù‡Ù…Ø§Ù† Ù†ÛŒØ§Ø² Ø´Ø´ Ø¨Ø§Ø±
         # Ø¯Ø± ÛŒÚ© Ø±ÙˆØ² ØªÚ©Ø±Ø§Ø± Ø´Ø¯.
         "test_tool_request_sees_its_answers.py",
         # Û°Û¸-Û°Û´ â† Ù¾Ù„Ù Â«Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© â†’ Ù‚Ø§Ø¨Ù„ÛŒØªÙ ÙˆØ§Ù‚Ø¹ÛŒÂ». Û³Û¶ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù‡Ù…Ù‡ pending Ùˆ
         # Û´ Ø±Ø£ÛŒÙ granted Ú©Ù‡ Ù‡ÛŒÚ† Ú©Ø¯ÛŒ Ù…ØµØ±ÙØ´Ø§Ù† Ù†Ù…ÛŒâ€ŒÚ©Ø±Ø¯ â€” Ø¯Ø± Ø­Ø§Ù„ÛŒ Ú©Ù‡ Ù‚Ø§Ø¨Ù„ÛŒØªÙ
         # Ø¯Ø±Ø®ÙˆØ§Ø³ØªÛŒ Ø§Ø² Ù‚Ø¨Ù„ ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø´Øª Ùˆ **Ø±ÙˆØ´Ù†** Ø¨ÙˆØ¯.
         "test_capability_bridge.py",
         # Û°Û¸-Û°Û´ â† Ø´Ù„Ù Ø®Ø§Ù…ØŒ Ø¨Ù‡ Ø±Ø£ÛŒÙ ØµØ±ÛŒØ­Ù Ù…Ø§Ù„Ú©. "Ø¨Ø§Ø²" ÛŒØ¹Ù†ÛŒ Ù…Ù‡Ø§Ø±Ø´Ø¯Ù‡: Ø¯Ùˆ
         # Ú©ÛŒÙ„â€ŒØ³ÙˆÛŒÛŒÚ†ØŒ Ø±Ø³ÛŒØ¯Ù Ù‚Ø¨Ù„â€ŒØ§Ø²â€ŒØ§Ø¬Ø±Ø§ØŒ Ùˆ deny-list Ø§ÛŒ Ú©Ù‡ Â§Û° Ù Ù…Ù†Ø´ÙˆØ± Ø§Ø³Øª.
         "test_raw_shell_capability.py",
         # Û°Û¸-Û°Û´ ÙØ§Ø² Û° â† Ø±ÙÛŒÚ¯Ù Ø±Ø³ÛŒØ¯. `inbound-log` (ISO Ù Ù…Ø­Ù„ÛŒ) Ùˆ `tg-send-log`
         # (Ø§Ù¾Ø§Ú©Ù Ø§Ø¹Ø´Ø§Ø±ÛŒ) Ù‡ÛŒÚ† Ú©Ù„ÛŒØ¯Ù Ù…Ø´ØªØ±Ú©ÛŒ Ù†Ø¯Ø§Ø´ØªÙ†Ø¯ØŒ Ù¾Ø³ Â«Ø¢Ù† Ù¾ÛŒØ§Ù…Ù Ù…Ù† Ø¬ÙˆØ§Ø¨ Ú¯Ø±ÙØªØŸÂ»
         # ÛŒÚ© Ø­Ø¯Ø³Ù Ø²Ù…Ø§Ù†ÛŒ Ø¨ÙˆØ¯ Ù†Ù‡ ÛŒÚ© join â€” Ùˆ Ø¨Ø§ Ø¯Ùˆ Ø¨Ø§ØªÛŒ Ú©Ù‡ Ø¨Ù‡ ÛŒÚ© Ú†Øª Ù…ÛŒâ€ŒÙØ±Ø³ØªÙ†Ø¯ØŒ
         # Ø­Ø¯Ø³ÛŒ Ø§Ø¨Ø·Ø§Ù„â€ŒÙ†Ø§Ù¾Ø°ÛŒØ±. Ø­Ø§Ù„Ø§ Ù¾Ø§Ø³Ø® Ù‡Ù…Ø§Ù† update_id Ø±Ø§ Ø­Ù…Ù„ Ù…ÛŒâ€ŒÚ©Ù†Ø¯. Ù¾Ø±ÙˆØ¨Ù
         # Ù‡Ù…ÛŒÙ† ÙØ§Ø² Ø¯Ùˆ Ú†ÛŒØ² Ø±Ø§ ØªØµØ­ÛŒØ­ Ú©Ø±Ø¯: ÙØ±Ù…Ø§Ù†Ù Ù†Ø§Ø´Ù†Ø§Ø®ØªÙ‡ Ø³Ø§Ú©Øª **Ù†ÛŒØ³Øª** (Ù¾Ù„
         # Ø¬ÙˆØ§Ø¨ Ù…ÛŒâ€ŒØ¯Ù‡Ø¯)ØŒ ÙˆÙ„ÛŒ ÙØ±Ù…Ø§Ù†Ù Ú¯ÛŒØªâ€ŒØ´Ø¯Ù‡ Ø¨Ø§ ÙÙ„Ú¯Ù Ø®Ø§Ù…ÙˆØ´ Ù‡Ø³Øª â€” Ùˆ Ø¨Ø¯ØªØ±ØŒ Ù¾Ù„ÛŒ Ú©Ù‡
         # `sent=False` Ø¨Ø±Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø§Ù†Ø¯ Ø§Ø² Ø¨Ø§Ù„Ø§Ø¯Ø³Øª Â«Ù…ÙˆÙÙ‚Â» Ø¨Ù‡â€ŒÙ†Ø¸Ø± Ù…ÛŒâ€ŒØ±Ø³Ø¯.
         "test_phase0_receipt_rig.py",
         # Û°Û¸-Û°Û´ ÙØ§Ø² Û± â† Â«ÛŒÚ© Ù…ÙˆØ¶ÙˆØ¹ØŒ ÛŒÚ© Ù¾ÛŒØ§Ù…Â». Ø§Ù†Ø¯Ø§Ø²Ù‡â€ŒÚ¯ÛŒØ±ÛŒ ÙØ±Ø¶Ù Ø®ÙˆØ¯Ù Ù¾Ù„Ù† Ø±Ø§ Ø±Ø¯
         # Ú©Ø±Ø¯: Ø¯Ø± Û²Û´ Ø³Ø§Ø¹Øª Û·Û¶ Ù¾ÛŒØ§Ù…Ù Ù†Ùˆ Ø¯Ø± Ø¨Ø±Ø§Ø¨Ø± Û³Û²Û¸ ÙˆÛŒØ±Ø§ÛŒØ´ Ùˆ ÙÙ‚Ø· **Û´Ùª** ØªÚ©Ø±Ø§Ø±ØŒ
         # ÛŒØ¹Ù†ÛŒ Ø­Ø¬Ù… Ù…Ø´Ú©Ù„ Ù†ÛŒØ³Øª â€” Ø¨ÛŒâ€ŒÙ†Ø¸Ù…ÛŒÙ Ø³Ø§Ø®ØªØ§Ø±ÛŒ Ø§Ø³Øª (Ø´Ø´ ØªÙˆÙ„ÛŒØ¯Ú©Ù†Ù†Ø¯Ù‡Ù” Ù…Ø³ØªÙ‚Ù„ Ø¯Ø±
         # DMØŒ Ø¨ÛŒâ€ŒÙ‡ÛŒÚ† Â«Ø®Ø§Ù†Ù‡Â»Ø§ÛŒ). Ø³Ù‡ Ù†Ø§ÙˆØ±Ø¯ÛŒ Ú©Ù‡ Ù‚ÙÙ„ Ù…ÛŒâ€ŒØ´ÙˆØ¯: Ø®Ø§Ù…ÙˆØ´ = ØµÙØ± ÙØ±Ø§Ø®ÙˆØ§Ù†
         # (Ø¯Ú©Ù…Ù‡Ù” Ø¨Ø±Ú¯Ø´Øª) Â· Ø¨ÛŒâ€ŒØªØºÛŒÛŒØ± = ØµÙØ± ÙØ±Ø§Ø®ÙˆØ§Ù† Â· Ùˆ Ú©Ø§Ø±ØªÙ Ù¾Ø§Ú©â€ŒØ´Ø¯Ù‡ Ø¨Ø±Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø¯
         # (Ú†ÙˆÙ† `edit` ÙÙ‚Ø· bool Ù…ÛŒâ€ŒØ¯Ù‡Ø¯ØŒ Ø±Ø¯ Ú©Ø±Ø¯Ù†Ù Ø³Ø§Ú©ØªÙ Ø´Ú©Ø³Øª = Ù…Ø±Ú¯Ù Ø¯Ø§Ø¦Ù…ÛŒ).
         "test_living_card.py",
         # ۰۸-۰۴ فاز ۱ ← گزارشِ ترافیک، و گاردِ «رگبارِ کهنه». ایجنت روی کلِ
         # لاگ ۲۱۶ پیامِ یکسان شمرد و نزدیک بود «باگِ زنده» گزارش کند؛ توزیعِ
         # ساعتی نشان داد مالِ ۰۸-۰۲ است. عددِ تجمعی می‌گوید «چقدر»، فقط توزیعِ
         # زمانی می‌گوید «هنوز؟». و گارد در **هر دو جهت** سنجیده می‌شود: رگبارِ
         # زنده هرگز نباید «کهنه» نامیده شود، وگرنه حادثه را پنهان می‌کند.
         "test_tg_traffic.py",
         # ۰۸-۰۴ ← دیده‌بانِ هنگ. مرکز امروز دو بار ~۲٫۵ ساعت هنگ کرد و علتش
         # نامعلوم ماند، چون RUN-TG-CENTER.bat پایتون را بدونِ هیچ ریدایرکتی
         # اجرا می‌کند ⇒ stdout/stderr هیچ‌جا نمی‌رود. حالا اگر نبض کهنه شد،
         # پشتهٔ همهٔ نخ‌ها روی دیسک می‌نشیند — در آستانهٔ ۲۴۰ ثانیه، **زیرِ**
         # ۳۰۰ ثانیه‌ای که واچ‌داگ با آن می‌کُشد؛ وگرنه ابزارِ تشخیصی همیشه
         # بعد از مرگ می‌رسد. و راهنمای نامِ نخ‌ها، چون faulthandler فقط
         # شناسهٔ هگز می‌نویسد و «کدام لِن گیر کرده؟» بی‌جواب می‌ماند.
         "test_stall_probe.py",
         # ۰۸-۰۴ فاز ۲ ← سبزی که چهار روز دروغ گفت. گزارشِ آمادگی فقط
         # **دسترس‌پذیری** را می‌سنجید (آدرس https است، پورت جواب می‌دهد) و
         # هرگز نمی‌پرسید «تلگرام اصلاً این اپ را می‌شناسد؟». جوابِ زنده:
         # has_main_web_app=False و منویِ commands — یعنی هیچ مینی‌اپی ثبت
         # نشده بود. شاهدِ رفتاری: در ۸۸ ساعت لاگ، **یک** نشستِ احرازشده.
         # ناوردیِ مرکزی: `unknown` هرگز `ok` نمی‌شود.
         "test_miniapp_registration.py",
         # ۰۸-۰۴ فاز ۳ (فرانت) ← پوستهٔ Mini Apps 2.0. کلِ یکپارچگیِ تلگرامِ
         # این اپ یک خط بود (expand + setHeaderColor)، پس روی گوشی محتوا زیرِ
         # نُچ می‌رفت. دو تلهٔ ثبت‌شده هم بسته شد: فایلِ تاریک (اگر allowlist ِ
         # گیت‌وی tg_shell.js را نداشته باشد، ۴۰۴ بی‌صدا همهٔ قابلیت‌ها را
         # می‌برد) و تستِ تاریک (۱۳ تستِ JS که run_all پایتونی هرگز صدایشان
         # نمی‌زد — این فایل با node اجرایشان می‌کند و شمار را می‌سنجد).
         "test_miniapp_shell_2026.py",
         "test_sync_health_unknown.py",
         "test_arbiter_consensus_rule.py",
         "test_state_write_monopoly.py",
         # Û°Û¸-Û°Û³ Ú¯Ø§Ù…â€ŒÙ‡Ø§ÛŒ Û±Û²â€“Û²Û°. Ø¨Ø±Ø¬Ø³ØªÙ‡â€ŒØªØ±ÛŒÙ† ÛŒØ§ÙØªÙ‡ Ø­ÛŒÙ†Ù Ø§Ø¬Ø±Ø§: `parse_ts` Ù Ú¯Ø§Ù…Ù Û±
         # â€ISO Ù Ø¨Ø¯ÙˆÙ†Ù Ù…Ù†Ø·Ù‚Ù‡ Ø±Ø§ UTC Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯ Ø¯Ø± Ø­Ø§Ù„ÛŒ Ú©Ù‡ `opslib.now_iso()` **Ù…Ø­Ù„ÛŒ**
         # Ù…ÛŒâ€ŒÙ†ÙˆÛŒØ³Ø¯ â‡’ Ù‡Ø± age Ø±ÙˆÛŒ Ø¯Ø§Ø¯Ù‡Ù” Ø²Ù†Ø¯Ù‡ Û±Û° Ø³Ø§Ø¹Øª Ù…Ù†ÙÛŒ â‡’ HELD Ù‡Ø±Ú¯Ø² Ø´Ù„ÛŒÚ© Ù†Ù…ÛŒâ€ŒÚ©Ø±Ø¯.
         # Ù‡Ù…Ø§Ù† Ú©Ù„Ø§Ø³Ù Ø¨Ø§Ú¯Ù Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡ (Â«UTC Ø¯Ø± Ù†ÙˆÛŒØ³Ù†Ø¯Ù‡ØŒ Ù…Ø­Ù„ÛŒ Ø¯Ø± Ø®ÙˆØ§Ù†Ù†Ø¯Ù‡Â»). Ú¯Ø§Ø±Ø¯Ø´
         # round-trip Ø§Ø² Ù…Ø³ÛŒØ±Ù Ù†ÙˆÛŒØ³Ù†Ø¯Ù‡Ù” ØªÙˆÙ„ÛŒØ¯ÛŒ Ø§Ø³ØªØŒ Ù†Ù‡ ÙÛŒÚ©Ø³Ú†Ø±.
         "test_scanner_provenance.py",
         "test_card_spec_contract.py",
         "test_reconcile_card.py",
         "test_proposal_metrics_honesty.py",
         "test_miniapp_lifecycle_view.py",
         "test_owner_debt.py",
         # Û°Û¸-Û°Û³ Ú¯Ø§Ù…â€ŒÙ‡Ø§ÛŒ Û´ Ùˆ Ûµ. Ú¯Ø§Ù… Û´: Ø§Ø³Ú©Ù†Ù Ù†Ù‚Ø´Ù‡ Ù‡Ø±Ú¯Ø² ÙˆØ§Ù„Øª Ø±Ø§ Ù†Ø¯ÛŒØ¯Ù‡ Ø¨ÙˆØ¯ â€” Ø³Ù‚ÙØ´ Ø¯Ø±
         # Ù…Ø­Ù„Ù ÙØ±Ø§Ø®ÙˆØ§Ù†ÛŒ Ù‡Ø§Ø±Ø¯Ú©Ø¯ Ø¨ÙˆØ¯ Ùˆ `.claude` Ø§Ø³ØªØ«Ù†Ø§ Ù†Ø´Ø¯Ù‡ Ø¨ÙˆØ¯ØŒ Ù¾Ø³ Û´Û¹Ù¬Û¹Û³Û¹ Ø§Ø² ÛµÛ°Ù¬Û°Û°Û°
         # Ø±Ú©ÙˆØ±Ø¯ Ù†ÙÙ‡ Ø±ÙˆÙ†ÙˆØ´ØªÙ Ú©Ù‡Ù†Ù‡Ù” ÙˆØ§Ù„Øª Ø²ÛŒØ±Ù worktreeÙ‡Ø§ Ø¨ÙˆØ¯Ù†Ø¯. Ú¯Ø§Ù… Ûµ: `_sha256_file`
         # Ø±ÙˆÛŒ Ø®Ø·Ø§ Ø±Ø´ØªÙ‡Ù” Ù„ÙØ¸ÛŒÙ "unavailable" Ù…ÛŒâ€ŒØ¯Ø§Ø¯ Ú©Ù‡ truthy Ø§Ø³ØªØŒ Ù¾Ø³ Ù‡Ù… Ú¯Ø§Ø±Ø¯Ù null
         # Ùˆ Ù‡Ù… Ú¯Ø§Ø±Ø¯Ù Ø­Ø¶ÙˆØ±Ù Ù‡Ø´ Ø§Ø² Ú©Ù†Ø§Ø±Ø´ Ø±Ø¯ Ù…ÛŒâ€ŒØ´Ø¯Ù†Ø¯ Ùˆ Ù‚ÙÙ„ÛŒ Ù†ÙˆØ´ØªÙ‡ Ù…ÛŒâ€ŒØ´Ø¯ Ú©Ù‡ Ø³Ù‡ Ú¯ÛŒØªÙ
         # Ø²Ù†Ø¯Ù‡Ù” Ù‚Ù„Ø¨ Ø±Ø§ Ù‡Ù†ÙˆØ² `locked` Ù†Ø´Ø§Ù† Ù…ÛŒâ€ŒØ¯Ø§Ø¯.
         "test_metadata_scan_honesty.py",
         "test_sog_provenance.py",
         "test_funnel_cmd.py",  # D3b â€” Ù…Ø§Ù„Ú© ÙˆØ§Ù‚Ø¹ÛŒØªÙ Ø¨Ø§Ø²Ø§Ø± Ø±Ø§ Ù…ÛŒâ€ŒÚ¯ÙˆÛŒØ¯
         "test_two_bot_bridge.py",  # Ù¾Ù„Ù Ø¹Ø§Ù… â€” Ø¯Ø³ØªÙˆØ±Ù ØªØ¨Ù„ÛŒØºâ€ŒØ´Ø¯Ù‡ Ø§Ø² Ú¯Ø±ÙˆÙ‡ Ú©Ø§Ø± Ú©Ù†Ø¯
         "test_self_coding_chain.py",  # Ø²Ù†Ø¬ÛŒØ±Ù‡Ù” Ù‡ÙØªâ€ŒØ­Ù„Ù‚Ù‡â€ŒØ§ÛŒÙ Ú©Ø¯Ù†ÙˆÛŒØ³ÛŒÙ ÙˆØ§Ù‚Ø¹ÛŒ
         "test_output_critic.py",  # Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù… Ø®Ø±ÙˆØ¬ÛŒÙ Ø®ÙˆØ¯Ø´ Ø±Ø§ Ù†Ù…Ø±Ù‡ Ø¨Ø¯Ù‡Ø¯
         "test_callback_routing.py",  # Ù‡ÛŒÚ† Ø¯Ú©Ù…Ù‡â€ŒØ§ÛŒ Ø¨ÛŒâ€ŒÙ…Ø³ÛŒØ± Ù†Ù…Ø§Ù†Ø¯
         "test_self_patch.py",        # Ø­Ù„Ù‚Ù‡Ù” Ù…Ø±ÙˆØ±â†’ØµÙâ†’Ù¾Ú† + Ù‚ÙÙ„Ù Û¶ ÛŒØ§ÙØªÙ‡Ù” Ù…Ù…ÛŒØ²ÛŒ
         "test_improve_deep.py",      # Ù„Ø§ÛŒÙ‡Ù” Ø¹Ù…ÛŒÙ‚Ù improve + Ø³Ù‚ÙÙ Ø³Ø®ØªÙ Ø±ÙˆØ²Ø§Ù†Ù‡
         "test_governor_contract.py",  # Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯Ù ØªØ®ØµÛŒØµ + Ø¯ÛŒØ¯Ù‡â€ŒØ´Ø¯Ù†Ù Ø¨Ø±ÛŒØ¯Ú¯ÛŒ
         "test_hebbian_signals.py",   # ÙˆØ§Ú˜Ú¯Ø§Ù†Ù Ø³ÛŒÚ¯Ù†Ø§Ù„Ù Hebbian (Ø¶Ø¯Ù Ø³ÛŒÚ¯Ù†Ø§Ù„Ù Ù‡Ù…ÛŒØ´Ù‡â€ŒØ±ÙˆØ´Ù†)
         "test_ziman_leg.py",
         "test_ziman_phase2.py",
         # 2026-07-13: Ø¯Ùˆ ÙˆØ±ÙˆØ¯ÛŒÙ phantom Ø­Ø°Ù Ø´Ø¯Ù†Ø¯ â€” test_ziman_wiring.py Ùˆ
         # test_ziman_biology.py Ù‡Ø±Ú¯Ø² Ø¯Ø± ØªØ§Ø±ÛŒØ®Ù Ú¯ÛŒØª ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø´ØªÙ†Ø¯ (pytest exit=4 â†’
         # Ø³ÙˆÛŒÛŒØª Ø±Ø§ Ø¯Ø§Ø¦Ù… Ù‚Ø±Ù…Ø² Ùˆ markerÙ capability Ø±Ø§ Ø¯Ø§Ø¦Ù… revoke Ù…ÛŒâ€ŒÚ©Ø±Ø¯Ø› Ø±ÛŒØ´Ù‡Ù” C-01/C-04).
         # Ø§Ú¯Ø± Ù‚Ø±Ø§Ø± Ø§Ø³Øª Ù†ÙˆØ´ØªÙ‡ Ø´ÙˆÙ†Ø¯ØŒ Ø±Ø¬ÙˆØ¹: AGENT_QUESTIONS Â«2026-07-13Â». Ù¾ÙˆØ´Ø´Ù ziman ÙØ¹Ù„ÛŒ =
         # test_ziman_leg + test_ziman_phase2.
         "test_cartographer_leg.py",
         "test_cartographer_wiring.py",
         "test_master_halt.py",
         # 2026-07-23 D1: outbound worker honors canonical hard-halt at entry (was RISK: 0 halt refs;
         # safety relied on downstream gate + NOT_ARMED stub). master_halted() supreme over flag. script-native.
         "test_d1_outbound_halt.py",
         # 2026-07-23 D2: every wiring beat honors canonical hard-halt (static coverage guard,
         # 28/28) + _tg_halt_reason/master_halted functional under HALT-ALL/architect-STOP. script-native.
         "test_d2_halt_coverage.py",
         "test_panic_command.py", "test_tg_restart.py", "test_backup_visibility.py",
         "test_cortex_shadow_wiring.py", "test_route_scorer_wire.py",
         "test_leg_chain_wire.py", "test_render_legs.py", "test_new_legs.py",
         "test_school_bridge.py",   # 2026-07-14: orphan test Ø¨ÙˆØ¯ (ÙØ§ÛŒÙ„ Ù…ÙˆØ¬ÙˆØ¯ØŒ Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡) â€” Ø«Ø¨Øª Ø´Ø¯
         "test_self_claims.py", "test_octopus_logger_wire.py", "test_improve_refractory.py",
         "test_wiring_cleanup.py", "test_deadwrite_readers.py",
         # 2026-07-15: ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ Ù†ÙˆÙ Ø±Ø§Ø³Øªâ€ŒÚ¯ÙˆÛŒÛŒ/Ú©Ø§Ø¨ÛŒÙ† + Ø¯Ùˆ orphanÙ ziman (Ø³Ø¨Ø²ØŒ Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡ Ø¨ÙˆØ¯Ù†Ø¯)
         "test_business_legs_shape.py", "test_correlation_id_generated.py",
         # 2026-08-03 (Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Â«Ø§Ø®ØªØ§Ù¾ÙˆØ³ ÛŒØ§Ø¯Ø´ Ø¨Ù…ÙˆÙ†Ù‡Â»): Ù¾Ø§ÛŒ Project-F Ø§Ø² ÙÙ‡Ø±Ø³ØªÙ
         # business_legs ØºØ§ÛŒØ¨ Ø¨ÙˆØ¯ â‡’ Û±Û² Ù…ØµØ±Ùâ€ŒÚ©Ù†Ù†Ø¯Ù‡ Ù†Ù…ÛŒâ€ŒØ¯ÛŒØ¯Ù†Ø¯Ø´. Ú†Ù‡Ø§Ø± Ú¯Ø§Ø±Ø¯Ù Ø¬Ù‡Ø´â€ŒØ¢Ø²Ù…ÙˆØ¯Ù‡:
         # content-free (#Û·) Â· Ø³Ù‡â€ŒØ­Ø§Ù„ØªÛŒÙ ØµØ§Ø¯Ù‚ Â· live ÙÙ‚Ø· Ø¨Ø§ Ù…Ù‡Ø±Ù Ø§Ù†Ø³Ø§Ù†ÛŒ Â· Ø«Ø¨Øª Ø¯Ø± Ø±Ø¬ÛŒØ³ØªØ±ÛŒ.
         "test_studio_pf_leg.py",
         # 2026-08-03: Ú¯Ø§Ø±Ø¯Ù **Ú©Ù„Ø§Ø³Ù** Ø¨Ø§Ú¯ â€” Ø±Ø¬ÛŒØ³ØªØ±ÛŒÙ Ù¾Ø§Ù‡Ø§ Ø³Ù‡ Ø¬Ø§Ø³Øª Ùˆ Ø§Ø² Ù‡Ù… Ù…Ø´ØªÙ‚
         # Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯Ø› Ù‡Ø± Ù¾Ø§ÛŒ ØªØ§Ø²Ù‡ Ú©Ù‡ Ø¨Ù‡ ÛŒÚ©ÛŒ Ø§Ø¶Ø§ÙÙ‡ Ø´ÙˆØ¯ Ùˆ Ø¨Ù‡ Ø¨Ù‚ÛŒÙ‡ Ù†Ù‡ØŒ Ù†Ø§Ù…Ø±Ø¦ÛŒ Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯.
         "test_leg_registry_parity.py",
         "test_channel_status_stale_not_green.py", "test_cockpit_truthful.py",
         "test_tg_exec_consumer.py",
         "test_ziman_wiring.py", "test_ziman_biology.py",
         # 2026-07-15: ÙÛŒÚ©Ø³Ù Ù…ØºØ²Ù Ù¾ÙˆÙ„ÛŒ (Ø¨Ø§Ú¯ Û±) + Ù…ÙˆØªÙˆØ±Ù Ú©Ø´ÙÙ Ù„ÛŒØ¯ (Ù†Ù‚Ø´Ù‡Ù” Ù„ÛŒØ¯ØŒ Ù…Ø±Ø§Ø­Ù„ Û±-Û²)
         "test_brain_fix.py",
         "test_lead_scorer.py", "test_lead_discovery_beat.py",
         "test_harvest_austender.py", "test_cadence_aliasing.py",
         "test_organism_honesty.py", "test_genome_safety.py",
         # 2026-07-17: ØªØ¹Ù…ÛŒØ±Ù‡Ø§ÛŒ truth-map (P3 Ø¹ØµØ¨Ù Ø¯Ø±Ø¯ØŒ P5 Ø¨ÙˆØ¯Ø¬Ù‡Ù” ØµØ§Ø¯Ù‚ØŒ P6 Ø¢Ø±ØªÛŒÙÚ©ØªÙ pacemakerØŒ â€¦)
         "test_truthmap_fixes.py", "test_p4_p9_fixes.py", "test_doctor_selfknowledge.py",
         # 2026-07-28: Ù…Ø¹ÛŒØ§Ø±Ù Ø¯Ù‚ØªÙ Ø®ÙˆØ¯Ù…Ø¯Ù„ (C3) â€” Ø®ÙˆØ¯Ú¯Ø²Ø§Ø±Ø´Ù snapshot Ø¯Ø± Ø¨Ø±Ø§Ø¨Ø±Ù Ù…Ù†Ø§Ø¨Ø¹Ù Ø­Ù‚ÛŒÙ‚ØªÙ Ù…Ø³ØªÙ‚Ù„.
         "test_self_accuracy.py",
         # 2026-07-16: Ù†Ù‚Ø´Ù‡Ù” Ù„ÛŒØ¯ Ù…Ø±Ø§Ø­Ù„ Û³-Ûµ (Ù¾Ù„Ù Ø§ÛŒÙ…ÛŒÙ„ØŒ ØºÙ†ÛŒâ€ŒØ³Ø§Ø²ÛŒÙ LLMØŒ Ù¾ÛŒØ´â€ŒÙØ§Ú©ØªÙˆØ±Ù ÙˆØ§Ù‚Ø¹ÛŒ)
         "test_email_lead_bridge.py", "test_lead_llm_enrich.py",
         "test_lead_quote_chain.py",
         # 2026-07-16: Ø«Ø¨ØªÙ ÛŒØªÛŒÙ…â€ŒÙ‡Ø§ÛŒ ØªØ£ÛŒÛŒØ¯Ø´Ø¯Ù‡ (Ø¨Ø±Ù†Ø§Ù…Ù‡ Û³) â€” Ù‡Ø± Ø³Ù‡ Ø³Ø¨Ø²Ù Ø§ÛŒØ²ÙˆÙ„Ù‡ Ø¯Ø± worktree.
         # Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡â€ŒÙ‡Ø§ÛŒ Ø¹Ù…Ø¯Ø§Ù‹ Ú©Ù†Ø§Ø±Ú¯Ø°Ø§Ø´ØªÙ‡: test_mining_leg/test_mining_wiring (phantom â€”
         # MiningLeg Ø¯ÙˆÙ…ØºØ²ÛŒ Ùˆ wiring.make_mining_leg Ø¯Ø± Ø§ÛŒÙ† Ø¯Ø±Ø®Øª ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø±Ø¯)ØŒ
         # test_drawdown_enforcer (phantom â€” budget_gate.DRAWDOWN_LOG/drawdown_status Ù†ÛŒØ³Øª)ØŒ
         # test_effector_idempotency (phantom â€” EffectorGate.request_idempotent Ù†ÛŒØ³Øª).
         # 2026-07-16 (audit R-04): test_durable_journal Ø¯ÛŒÚ¯Ø± phantom/Ù‚Ø±Ù…Ø² Ù†ÛŒØ³Øª â€” ØªØ³ØªÙ setup
         # Ø§Ú©Ù†ÙˆÙ† Ø¯Ø§ÛŒØ±Ú©ØªÙˆØ±ÛŒÙ state/journal Ø±Ø§ Ù…ÛŒâ€ŒØ³Ø§Ø²Ø¯ (Ù…Ø«Ù„Ù _default_path) â†’ Ø«Ø¨Øª Ø´Ø¯ (direct-run).
         "test_durable_journal.py",
         "test_ui_truth.py", "test_organ_console.py", "test_organ_create.py",
         # 2026-07-16: Ù…ÙˆØ¬Ù Ø¯Ù‡â€ŒØ¨Ø±Ù†Ø§Ù…Ù‡ â€” Ú©Ø§Ù„ÛŒØ¨Ø±Ø§Ø³ÛŒÙˆÙ† (Ø¨Ø±Ù†Ø§Ù…Ù‡ Û¶) + ØµØ¯Ø§Ù‚ØªÙ Ú©Ø§Ø¨ÛŒÙ† Ù¾Ø³ Ø§Ø² GO-LIVE (Ø¨Ø±Ù†Ø§Ù…Ù‡ Û¹)
         "test_calibration_loop.py", "test_cockpit_golive_honesty.py",
         "test_legs_freshness.py",   # Ø¨Ø±Ù†Ø§Ù…Ù‡ Û·: ØµØ¯Ø§Ù‚ØªÙ ØªØ§Ø²Ú¯ÛŒÙ Ù¾Ø§Ù‡Ø§
         "test_ziman_catalog_bridge.py",   # Ø¨Ø±Ù†Ø§Ù…Ù‡ Û¸: Ù¾Ù„Ù Ú©Ø§ØªØ§Ù„ÙˆÚ¯Ù Ø²ÛŒÙ…Ø§Ù†
         # 2026-07-16: Ù…ØªØ§Ø¨ÙˆÙ„ÛŒØ³Ù…Ù Ø¯Ø§Ø¯Ù‡Ù” $0 Ù‡Ù…Ù‡Ù” Ù¾Ø§Ù‡Ø§ (leg_cultivate + Ø¯Ú©ØªØ± + Ù…ØºØ²Ù B)
         "test_legs_cultivation.py",
         # 2026-07-16: Ú¯Ø§Ø±Ø¯Ù read Ø¯Ø§Ø¯Ù‡Ù” ÙˆÛŒÚ˜Ù‡Ù” PII/PHI (audit R-05 + R-15) â€” Ø´Ø±ÛŒÚ©/DNA/EEG/HRV/Ù¾Ø±ÙˆÙØ§ÛŒÙ„Ù Ø±ÙˆØ§Ù†â€ŒØ¯Ø±Ù…Ø§Ù†ÛŒ
         "test_pii_read_guard.py",
         # 2026-07-16: EVAL-GATE (audit R-03) â€” Ø¯ÛŒØªØ§Ø³ØªÙ Ù…Ø­Ú©Ù Ø®ØµÙ…Ø§Ù†Ù‡Ù” Ù†Ø³Ø®Ù‡â€ŒØ¯Ø§Ø± (adv-eval.v1)
         # + Ø§Ø¬Ø±Ø§Ú©Ù†Ù†Ø¯Ù‡Ù” $0 Ø¢ÙÙ„Ø§ÛŒÙ† Ú©Ù‡ Ø®ÙˆØ¯Ù…Ø®ØªØ§Ø±ÛŒ Ø±Ø§ Ú¯ÙÛŒØª Ù…ÛŒâ€ŒÚ©Ù†Ø¯ (_ops/eval/).
         "test_adversarial_eval.py",
         "test_personal_ledger.py", "test_pocketsmith_import.py",
         # 2026-07-17: ÙØ§Ø² Û±+Û² Ù‚Ù„Ø¨Ù Ù¾ÙˆÙ„ â€” Ø®Ø±ÙˆØ¬ÛŒâ€ŒØ³Ø§Ø²Ù ÙˆØ§Ø±ÛŒØ²ÛŒ + backfillÙ Ø§Ø¯Ø¹Ø§ + Ø®Ø·Ù Ù„ÙˆÙ„Ù‡Ù” Ú©Ø§Ù…Ù„Ù reconcile
         "test_claims_backfill.py",
         # 2026-07-16: Ú©Ù„Ø§ÛŒÙ†ØªÙ ÙÙ‚Ø·â€ŒØ®ÙˆØ§Ù†Ø¯Ù†ÛŒÙ PocketSmith API v2 (me/accounts/transactions/sync)
         # Ù¾Ø´ØªÙ OCTOPUS_WIRE_POCKETSMITHØ› mockÙ urlopen (ØµÙØ± Ø´Ø¨Ú©Ù‡/Ú©Ù„ÛŒØ¯Ù ÙˆØ§Ù‚Ø¹ÛŒ)Ø› Ø­Ù…Ù„Ù category/labels.
         "test_pocketsmith_api.py",
         # 2026-07-16: write-backÙ Ú¯Ø§Ø±Ø¯Ø´Ø¯Ù‡Ù” Ø¨Ø±Ú†Ø³Ø¨â€ŒÙ‡Ø§ Ø¨Ù‡ PocketSmith (Ø±Ø£ÛŒ Ù…Ø§Ù„Ú©) â€” ÙÙ‚Ø· PUT labels
         # Ø¨Ù‡ /transactions/{id}ØŒ whitelist Ø³Ø®ØªØŒ Ø³Ù‚ÙÙ flushØŒ ØµÙÙ Ù…Ø­Ù„ÛŒØŒ Ù¾Ø´ØªÙ OCTOPUS_WIRE_PS_WRITEBACK.
         "test_ps_writeback.py",
         # 2026-07-16: Ø­Ø³Ø§Ø¨Ø¯Ø§Ø±Ù Ù…ÙˆÙ„ØªÛŒâ€ŒØ§ÛŒØ¬Ù†Øª (Ø³Ù†Øª/Ø§Ù†ØªØ³Ø§Ø¨/Ø§Ø±Ú©Ø³ØªØ±Ø§ØªÙˆØ±)
         # (dedupe 2026-07-21 wave-1: test_txn_store/test_attributor ÙÙ‚Ø· Ø¯Ø± Ø±Ø¯ÛŒÙâ€ŒÙ‡Ø§ÛŒ Ú©Ø§Ù…Ù†Øªâ€ŒØ¯Ø§Ø±Ù
         # Ù¾Ø§ÛŒÛŒÙ† Ø«Ø¨Øªâ€ŒØ§Ù†Ø¯ â€” Ù‚Ø¨Ù„Ø§Ù‹ Ø§ÛŒÙ†â€ŒØ¬Ø§ Ù‡Ù… Ø¨ÙˆØ¯Ù†Ø¯ Ùˆ Ù‡Ø±Ú©Ø¯Ø§Ù… Ø¯ÙˆØ¨Ø§Ø± Ø§Ø¬Ø±Ø§ Ù…ÛŒâ€ŒØ´Ø¯)
         "test_accountant.py",
         # 2026-07-16: Ø§Ù†Ø¨Ø§Ø±Ù ØªØ¬Ù…ÛŒØ¹ÛŒÙ ØªØ±Ø§Ú©Ù†Ø´ (txn_store) â€” xlsx+CSV â†’ ÛŒÚ© Ø§Ù†Ø¨Ø§Ø±Ù cents-Ù…Ø­ÙˆØ±ØŒ
         # dedupÙ content-hashØŒ reconcile tie-out. txn-store.json ÙˆØ§Ù‚Ø¹ÛŒ gitignore.
         "test_txn_store.py",
         # 2026-07-16: ASSET-OVERSIGHT â€” Ù†Ù‚Ø´Ù‡Ù” Ø¯Ø§Ø±Ø§ÛŒÛŒÙ Ú©Ù„ (asset_map + asset_map_beat)
         # propose-onlyØŒ fail-softØŒ ØµÙØ± Ù…Ø¨Ù„Øº/net-worthØŒ Ù¾Ø´ØªÙ OCTOPUS_WIRE_ASSET_MAP.
         "test_asset_map.py",
         # 2026-07-16: ØªØ¨Ù ðŸ’° Ø¯Ø§Ø±Ø§ÛŒÛŒâ€ŒÙ‡Ø§/Ø­Ø³Ø§Ø¨ Ú©Ø§Ø¨ÛŒÙ† â€” asset_map + personal_ledger (ÙÙ‚Ø·â€ŒØ®ÙˆØ§Ù†Ø¯Ù†ÛŒØŒ
         # ØªØ±Ø§Ø²Ù ØªØ¬Ù…ÛŒØ¹ÛŒØŒ ØµÙØ± ØªØ±Ø§Ú©Ù†Ø´/Ø´Ù…Ø§Ø±Ù‡â€ŒØ­Ø³Ø§Ø¨ØŒ ØµÙØ± Ù…Ø³ÛŒØ±Ù mutation).
         "test_finance_card.py",
         # 2026-07-16: CATEGORIZER â€” attributor (Ù‚Ø§Ø¹Ø¯Ù‡â€ŒÙ‡Ø§ÛŒ Ù‚Ø·Ø¹ÛŒ: wage/transfer-passthrough/
         # vendorØ› enumÙ auto|needs_review Ù†Ù‡ Ø§Ø·Ù…ÛŒÙ†Ø§Ù†Ù Ø¹Ø¯Ø¯ÛŒØ› propose-onlyØŒ Ù…Ø§Ù„Ú© ØªØ£ÛŒÛŒØ¯ Ù†Ù‡ Ø§ÛŒØ¬Ù†Øª).
         "test_attributor.py",
         # 2026-07-16: Ø¯Ø³ØªÛŒØ§Ø±Ù AIÙ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒÙ Ù¾Ø³â€ŒÙ…Ø§Ù†Ø¯ (txn_categorize) â€” Ù…Ø­Ù„ÛŒ-Ø§ÙˆÙ„ ollama $0ØŒ
         # Ø§Ø¨Ø±ÛŒ Fugu ÙÙ‚Ø· Ù¾Ø´ØªÙ OCTOPUS_WIRE_ACCT_CLOUD + scrub_piiØ› Ù‡ÛŒÚ† Ù…Ø¨Ù„Øº Ø¨Ù‡ LLMØ› propose-only.
         "test_txn_categorize.py",
         # 2026-07-16: Ø­Ø³Ø§Ø¨Ø¯Ø§Ø±Ù Ú¯ÙØªÚ¯ÙˆÙ…Ø­ÙˆØ±Ù ØªÙ„Ú¯Ø±Ø§Ù… (/review) â€” Ù…ÙˆØªÙˆØ± + Ù„Ø§ÛŒÙ‡Ù” ØªÙ„Ú¯Ø±Ø§Ù…Ø› Ú¯Ø§Ø±Ø¯Ù
         # Ù‡ÙˆÛŒØªÙ ØªØ±Ø§Ú©Ù†Ø´ Ø¯Ø± callbackØŒ Ù…ØªÙ†Ù Ø¢Ø²Ø§Ø¯Ù proposal-onlyØŒ Ù‡ÛŒÚ† Ù…Ø¨Ù„Øº Ø¨Ù‡ LLM.
         "test_acct_review.py", "test_review_telegram.py",
         # 2026-07-16: ÙØ§Ø²Ù ØµÙØ±Ù Ø¯ÙØªØ±Ù ÙˆØ§Ù‚Ø¹ÛŒ (Ù†Ù‚Ø¯Ù Ø¨ÛŒØ±ÙˆÙ†ÛŒ + Ø³Ø®Øªâ€ŒØ³Ø§Ø²ÛŒÙ auditÙ Û´Û¸-Ø§ÛŒØ¬Ù†ØªÛŒ):
         # ledger_core (Ø¯ÙˆØ·Ø±ÙÙ‡Ù” Ù…ØªÙˆØ§Ø²Ù†ØŒ Ù‚ÙÙ„â€ŒØ¯Ø§Ø±ØŒ append-only+fsyncØŒ reversalØŒ GST fail-closed)
         # raw_store (Ø´ÙˆØ§Ù‡Ø¯Ù Ø®Ø§Ù…Ù immutable) Â· recon (reconciliation ÙˆØ§Ù‚Ø¹ÛŒØŒ Ø¶Ø¯Ù netÙ Ø¨Ø±Ø§Ø¨Ø±Ù Ø¯Ø±ÙˆØº).
         "test_ledger_core.py", "test_raw_store.py", "test_recon.py",
         # 2026-07-16: ÙØ§Ø²Ù Û± â€” Ù¾Ù„Ù Ø¨Ø±Ú†Ø³Ø¨â†’Ø¯ÙØªØ± (journal_bridge: Ù†Ú¯Ø§Ø´ØªÙ Ù‚Ø·Ø¹ÛŒØŒ Ø¯Ùˆ-ØªØ£ÛŒÛŒØ¯ÛŒØŒ
         # Ù‡ÛŒÚ† tax_code) + Ù„Ø§ÛŒÙ‡Ù” ØªÙ„Ú¯Ø±Ø§Ù…Ù /books (Ø«Ø¨Øª Ø¨Ø§ Ù‡ÙˆÛŒØªÙ txnØŒ ØªÙ¾Ù ØªÚ©Ø±Ø§Ø±ÛŒ Ø§Ù…Ù†).
         "test_journal_bridge.py", "test_books_telegram.py",
         # 2026-07-16: two-rails â€” Ø¢Ø¯Ø§Ù¾ØªÙˆØ±Ù Ø±ÛŒÙ„Ù Ø´Ø±Ú©Øª (company_books: provider-agnosticØŒ
         # DRAFT-only ØªØ­Ù…ÛŒÙ„ÛŒØŒ ÙÙ„Ú¯â€ŒØ®Ø§Ù…ÙˆØ´ ØµØ§Ø¯Ù‚ØŒ ØµÙØ± secret-echo).
         "test_company_books.py", "test_books_xero.py",
         # 2026-07-16: Ø¬Ø±ÛŒØ§Ù†Ù Ø²Ù†Ø¯Ù‡Ù” Ø­Ø³Ø§Ø¨Ø¯Ø§Ø±ÛŒ â€” Ø­Ø§ÙØ¸Ù‡Ù” Ø¶Ø¯Ù ÙØ±Ø§Ù…ÙˆØ´ÛŒ (Ù‚ÙˆØ§Ø¹Ø¯Ù merchant Ø§Ø²
         # ØªØ£ÛŒÛŒØ¯Ù‡Ø§ØŒ Ø¨Ø§Ø²ØªÙˆÙ„ÛŒØ¯Ù¾Ø°ÛŒØ±ØŒ drift) + Ø¶Ø±Ø¨Ø§Ù†Ù acct_beat (ÙÙ„Ú¯â€ŒØ®Ø§Ù…ÙˆØ´ØŒ Ø³Ø§ÛŒØ¯Ú©Ø§Ø±).
         "test_acct_memory.py", "test_acct_beat.py",
         # 2026-07-18 Ø±Ø£ÛŒ Ù…Ø§Ù„Ú© Â«Ø³Ø±ÛŒØ¹â€ŒØªØ± + Ù‡ÙˆØ´Ù…Ù†Ø¯ØªØ±Â» (ÙØ§Ø² Ø¨+Ø§Ù„ÙØ› Ø¬ Ù¾Ø§Ø±Ú©): boot-thinkØŒ
         # Ú¯ÛŒØªÙ Ú©ÛŒÙÛŒØªÙ Ù…Ø­Ù„ÛŒ-Ø§ÙˆÙ„ (Ù¾Ø§ÛŒØ§Ù†Ù Ú¯Ø±Ø³Ù†Ú¯ÛŒÙ Fugu)ØŒ Ù…Ø§Ø´Ù‡Ù” Ú©ÙˆØ±ØªÛŒØ²ÙˆÙ„ÛŒ (flag-off).
         "test_brain_cortisol.py",
         # 2026-07-22 PRE-0/F: ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ Ù‡Ø±Ù…ØªÛŒÚ©Ù Ø³Ù‡ BLOCKER (fail-closed guardØŒ id-bound
         # releaseØŒ STOP canonical). pytest-native (monkeypatch)Ø› Ø¯Ø± PYTEST_TESTS Ø«Ø¨Øª Ø´Ø¯.
         "test_blocker_fixes_2026_07_22.py",
         # 2026-07-22 C1: Ú†Ø§Ø±Ú†ÙˆØ¨Ù migrationÙ Ø§Ø³Ú©ÛŒÙ…Ø§ÛŒ chrono.db (Ø­Ø°ÙÙ PRAGMAÙ clobberâ€ŒÚ©Ù†Ù†Ø¯Ù‡ Ø§Ø²
         # DDL + dispatcherÙ transactionalÙ fail-closed + ØªÙÚ©ÛŒÚ©Ù empty/legacy/malformed). script-native.
         "test_chrono_schema_migration.py",
         # 2026-07-22 C3: RESURRECTED Ø§Ø² phantom (owner #7) â€” idempotency Ø¯Ø± request()
         # (UNIQUE(idempotency_key)Ø› keyless=Ø¨Ø¯ÙˆÙ† dedupØ› same-key+different-content=Conflict). script-native.
         "test_effector_idempotency.py",
         # 2026-07-23 C4: exact per-effect fail-closed money/E4 authorization â€” money NEVER
         # batches (release_gated_effects excludes _E4_MONEY_KINDS)Ø› release_effect single
         # atomic bind (id+content_hash+action_kind+target_ref+single-use approval+expiry). script-native.
         "test_c4_exact_authorization.py",
         # 2026-07-23 C4.1: close the E4 id-only single-effect bypass â€” release_one REFUSES
         # money (E4 releasable ONLY via release_effect exact binding + human ledger ref);
         # legacy-unbound money â†’ NEEDS_OWNER_REVIEW. script-native.
         "test_c41_e4_id_only.py",
         # 2026-07-23 C5: CAS execution â€” migration v4 (execution columns + EXECUTING/
         # FAILED_SAFE/RECONCILE_REQUIRED Ø¯Ø± CHECKØ› Ø§ÛŒÙ†Ø¯Ú©Ø³Ù UNIQUEÙ C3 Ù¾Ø³ Ø§Ø² rebuild Ø¨Ø§Ø²Ø³Ø§Ø®ØªÙ‡
         # Ù…ÛŒâ€ŒØ´ÙˆØ¯)Ø› claim/commit Ø§ØªÙ…ÛŒÚ© Ø¨Ø§ execution_id (Ø¯Ùˆ executor ÛŒÚ© Ø¨Ø±Ù†Ø¯Ù‡Ø› stale/wrong xid
         # Ù‡Ø±Ú¯Ø² finalize Ù†Ù…ÛŒâ€ŒÚ©Ù†Ø¯)Ø› halt-during â†’ RECONCILE_REQUIREDØ› settle Ø¨ÛŒâ€ŒTOCTOU. script-native.
         "test_c5_cas_execution.py",
         # 2026-07-23 C6: receipt/reconciliation lane â€” sweep Ø¬Ø¯Ø§Ú¯Ø§Ù†Ù‡Ù” releasableÙ Ú©Ù‡Ù†Ù‡
         # (refuseÙ Ø§Ù…Ù†Ù Ù¾ÛŒØ´-claim) Ùˆ EXECUTINGÙ Ú©Ù‡Ù†Ù‡ (â†’ RECONCILE_REQUIREDØŒ Ù‡Ø±Ú¯Ø² refuseÙ
         # Ø¯Ø±ÙˆØºÛŒÙ†)Ø› reconcile_effect Ø§Ù†Ø³Ø§Ù†ÛŒ Ø¨Ø§ evidence+operator (receipt Ù‡Ø±Ú¯Ø² Ø¨Ø§Ø²Ù†ÙˆÛŒØ³ÛŒ
         # Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯)Ø› redrive_approval Ø¨Ø¯ÙˆÙ†Ù appendÙ Ø¯ÙˆØ¨Ø§Ø±Ù‡ (crash window aØŒ idempotent). script-native.
         "test_c6_receipt_reconciliation.py",
         # 2026-07-25 W6: Ù‚ÙÙ„Ù Ù…Ø±Ø²Ù propose-only Ø­Ù„Ù‚Ù‡Ù” C6 â€” Ú¯ÛŒØªÙ Ø¯ÙˆÚ¯Ø§Ù†Ù‡ (env + ÙØ§ÛŒÙ„Ù Ù…Ø§Ù„Ú©)ØŒ
         # Ù…Ù…Ù†ÙˆØ¹ÛŒØªÙ merge_or_deployØŒ ØµÙØ± Ø§Ø¨ØªØ¯Ø§ÛŒÛŒÙ Ø®Ø·Ø±Ù†Ø§Ú©ØŒ Ú¯Ø§Ø±Ø¯Ù Ø±Ø¬ÛŒØ³ØªØ±ÛŒÙ Ø¯Ú©ØªØ±.
         "test_c6_trigger_propose_only.py",
         # 2026-07-25 C1: Ø¨Ù†Ú†Ù C6 Ø¯ÛŒÚ¯Ø± Ø®ÙˆØ¯Ø´ Ø±Ø§ ØªØ£ÛŒÛŒØ¯ Ù†Ù…ÛŒâ€ŒÚ©Ù†Ø¯ â€” NULL Ø±Ø¯ Ù…ÛŒâ€ŒØ´ÙˆØ¯ØŒ
         # baselineÙ Ø§Ø¹Ù„Ø§Ù…ÛŒ Ø¨ÛŒâ€ŒØ§Ø«Ø± Ø§Ø³ØªØŒ Ø§Ø¯Ø¹Ø§ÛŒ Ù…Ú©Ø§Ù†ÛŒØ²Ù…ÛŒ Ù…Ù‚Ø¯Ù… Ø¨Ø± Ø³Ø§Ø¹ØªÙ Ø¯ÛŒÙˆØ§Ø±ÛŒ.
         "test_c6_bench_honesty.py",
         # 2026-07-25 C2: ØªÙˆÙ„ÛŒØ¯Ú©Ù†Ù†Ø¯Ù‡Ù” ØµØ§Ø¯Ù‚Ù ÙØ±Ø¶ÛŒÙ‡Ù” C6 + ØµÙÙ id-safeØ› ØµÙ Ø®Ø§Ù„ÛŒ Ø´Ø±Ø§ÙØªÙ…Ù†Ø¯Ø§Ù†Ù‡
         # Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ Ùˆ mechanism_count ÙÙ‚Ø· Ù†Ù‚Øµ Ø±Ø§ Ø¨Ø§Ø²ØªÙˆÙ„ÛŒØ¯ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ØŒ Ù†Ù‡ Ø¨Ù‡Ø¨ÙˆØ¯Ù Ø§Ø¹Ù…Ø§Ù„â€ŒØ´Ø¯Ù‡.
         # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” ÙˆØ±ÙˆØ¯ÛŒÙ ØªÚ©Ø±Ø§Ø±ÛŒ Ø­Ø°Ù Ø´Ø¯: Ù‡Ù…ÛŒÙ† ÙØ§ÛŒÙ„ Ø¯Ø± Ø®Ø·Ù Û²Û± Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø¨ÙˆØ¯ØŒ Ù¾Ø³
         # Ù‡Ø± Ø§Ø¬Ø±Ø§ÛŒ Ø³ÙˆØ¦ÛŒØª Ø¯ÙˆØ¨Ø§Ø± Ù…ÛŒâ€ŒØ¯ÙˆÛŒØ¯Ø´. ØªÙˆØ¶ÛŒØ­Ù Ø¨Ø§Ù„Ø§ Ù†Ú¯Ù‡ Ø¯Ø§Ø´ØªÙ‡ Ø´Ø¯ Ú†ÙˆÙ† Ø¯Ù„ÛŒÙ„Ù Ø«Ø¨Øª Ø±Ø§
         # Ø¨Ù‡ØªØ± Ø§Ø² ÙˆØ±ÙˆØ¯ÛŒÙ Ø§ÙˆÙ„ Ø´Ø±Ø­ Ù…ÛŒâ€ŒØ¯Ù‡Ø¯Ø› ÙÙ‚Ø· Ù†Ø§Ù…Ù ØªÚ©Ø±Ø§Ø±ÛŒ Ø±ÙØª.
         # 2026-07-25 C3: Ø¬Ø¹Ù„ Ø§Ø¹ØªÙ…Ø§Ø¯ Ù…Ø§Ù„Ú© Ù…Ø³Ø¯ÙˆØ¯ Ø´Ø¯Ø› claim Ø¨ÛŒâ€ŒÚ¯ÙˆØ§Ù‡ÛŒ Ø¨Ù‡ GRADED cap Ù…ÛŒâ€ŒØ´ÙˆØ¯
         # Ùˆ Ù…Ø³ÛŒØ± ÙˆØ§Ù‚Ø¹ÛŒ Ø±Ø£ÛŒ Ù…Ø§Ù„Ú© Ø§Ø² verdict_recorder Ù‡Ù…Ú†Ù†Ø§Ù† OWNER_CONFIRMED Ø§Ø³Øª.
         "test_c3_owner_trust_forgery.py",
         # 2026-07-25: Ù…Ø³ÛŒØ±Ù‡Ø§ÛŒ router Ú¯Ø§ÙˆØ±Ù†Ø±/Ù‚Ù„Ø¨/Ø®ÙˆØ¯Ø´Ù†Ø§Ø³ÛŒ ØªØ§Ø±ÛŒÚ© Ù…ÛŒâ€ŒÙ…Ø§Ù†Ù†Ø¯Ø› Ú†Ù‡Ø§Ø± ÙÙ„Ú¯ Ø¯Ø±
         # OCTOPUS-flags.cmd ØµØ±ÛŒØ­Ø§Ù‹ ØµÙØ± Ø«Ø¨Øª Ø´Ø¯ Ùˆ Ø¨Ø§ ØªØ³Øª hermetic Ù‚ÙÙ„ Ø´Ø¯.
         "test_paid_router_dark_config.py",
         # 2026-07-25: Ø¨Ø®Ø´Ù resilience.circuit_breaker Ø¯Ø± budgets.yaml Ø§Ø¶Ø§ÙÙ‡ Ø´Ø¯ (additive)
         # ØªØ§ breakerÙ per-provider Ø²ÙˆØ¯ØªØ± fail-fast Ú©Ù†Ø¯ Ùˆ Ø³Ù‡Ù…ÛŒÙ‡Ù” Ù†Ø§Ù¾Ø§ÛŒØ¯Ø§Ø±ÛŒÙ fugu Ù†Ø³ÙˆØ²Ø¯.
         "test_budgets_resilience_config.py",
         # 2026-07-25 (build-spec Â§4): Ø§Ù†Ø¶Ø¨Ø§Ø·Ù Ø³Ú©ÙˆØªÙ event_bridge â€” Ø¶Ø¯ÙØªÚ©Ø±Ø§Ø±Ù Ø§Ù…Ø¶Ø§ÛŒ
         # Ù…Ø­ØªÙˆØ§ (ÛµÛ° Ù‡Ù…â€ŒØ§Ù…Ø¶Ø§ â†’ Û± push)ØŒ Ø³Ù‚ÙÙ Ø±ÙˆØ²Ø§Ù†Ù‡Ù” Û¶ØŒ Ø­ÙØ¸Ù Ø³Ù‚ÙÙ Ø³Ø§Ø¹ØªÛŒÙ Û±Û°.
         "test_telegram_silence.py",
         # 2026-07-25: money-pulse â€” ÙØ§Ø²Ù Ø¬Ø¯ÛŒØ¯ Ø¨Ù‡ Ø¶Ø±Ø¨Ø§Ù†Ù Ù‚Ù„Ø¨. Ø¯Ø±Ø¢Ù…Ø¯Ù Ù¾Ø§Ù‡Ø§ Ø±Ùˆ Ù…ÛŒâ€ŒØ®ÙˆÙ†Ù‡ØŒ
         # Ù‡Ø±Ú¯Ø² MONEY_ATTRIBUTION Ø¬Ø¹Ù„ÛŒ Ù†Ù…ÛŒâ€ŒÙ†ÙˆÛŒØ³Ù‡ (wall anti-reward-hacking).
         "test_money_pulse.py",
         # 2026-07-25 T1 (megaprompt): int() Ø±ÙˆÛŒ Ø¨Ø±Ú†Ø³Ø¨Ù Ø´Ø¯Øª â€” Û³Û´Û¸ Ú©Ø±Ø´Ù doctor_digest_beat
         # Ø¨Ø³ØªÙ‡ Ø´Ø¯Ø› severity Ø±Ø´ØªÙ‡â€ŒØ§ÛŒ/Ø¹Ø¯Ø¯ÛŒ/None/Ù†Ø§Ø´Ù†Ø§Ø®ØªÙ‡ Ù‡Ù…Ù‡ Ù…ØªÙ†Ù ØºÛŒØ±Ø®Ø§Ù„ÛŒ Ù…ÛŒâ€ŒØ¯Ù‡Ù†Ø¯.
         "test_organ_dialogue_digest.py",
         # 2026-07-25 T3 (megaprompt): self-heal Ú©ÙˆØ± â†’ Ø¨Ø§Ø¹Ù„ØªØ› phi-timeout Ø¯Ø± chrono Ùˆ
         # Ø§Ø³ØªØ«Ù†Ø§ Ø¯Ø± leg_beat Ù‡Ø± Ø¯Ùˆ Ø¹Ù„ØªÙ Ù¾Ø§ÛŒØ¯Ø§Ø± Ø¯Ø± state/legs/ Ø«Ø¨Øª Ù…ÛŒâ€ŒÚ©Ù†Ù†Ø¯.
         "test_leg_failure_reason.py",
         # 2026-07-25 T4 (megaprompt): Ú¯Ø§Ø±Ø¯Ù Ù…ØªØ±ÙˆÙŽÙ†ÙˆÙ… (self_referential + authoritative=false)
         # Ùˆ Ø§Ù†ØªØ´Ø§Ø±Ù Î” Ù…Ù†ÙÛŒ Ù¾Ø´ØªÙ OCTOPUS_HEART_HONEST_PULSEØ› gate0 Ø¨Ø§ Î”â‰¤0 Ø¨Ø³ØªÙ‡.
         "test_heart_honest_pulse.py",
         # 2026-07-25 T8 (megaprompt): ØµÙÙ RFC Ø¨Ø§ ÙˆØ§Ù‚Ø¹ÛŒØªÙ Ø²Ù†Ø¯Ù‡ ØªØ·Ø¨ÛŒÙ‚ Ù…ÛŒâ€ŒØ®ÙˆØ±Ø¯ â€” dedupe Ø±ÙˆÛŒ
         # Ù…ØªÙ†Ù Ú¯Ù„ÙˆÚ¯Ø§Ù‡ØŒ stale-input Ø¨Ø±Ø§ÛŒ Ø´Ø±Ø·Ù Ù…Ø±Ø¯Ù‡ (Ïƒ/FREEZE)ØŒ submit idempotent.
         "test_doctor_rfc_stale_dedup.py",
         # 2026-07-25 T2 (megaprompt): Ø³Ù†Ø¬Ù‡Ù” Ø®ÙˆØ¯Ø¨Ù‡Ø¨ÙˆØ¯ÛŒ â€” dedupe Ù†ÛŒØª Ø¨Ø± idØŒ Ù…Ø®Ø±Ø¬Ù Ù†ÛŒØªÙ Ù…ØªÙ…Ø§ÛŒØ²ØŒ
         # Ø¯Ø±ÙˆÙ†â€ŒØ²Ø§Ø¯ Ø±Ø£ÛŒ Ù†Ù…ÛŒâ€ŒØ¯Ù‡Ø¯. Ù¾Ø´ØªÙ OCTOPUS_HONEST_OUTCOMES (Ø®Ø§Ù…ÙˆØ´ = Ø¨Ø§ÛŒØªâ€ŒØ¨Ù‡â€ŒØ¨Ø§ÛŒØª).
         "test_honest_outcomes.py",
         # 2026-07-25 (Ø¯ÛŒØ¨Ø§Ú¯Ù Ø²Ù†Ø¯Ù‡Ù” Ù¾Ø³ Ø§Ø² Ø±ÛŒØ³ØªØ§Ø±ØªÙ Û±Û´:Û±Û´:Û²Ûµ â€” Ø´Ø´ ÙÛŒÚ©Ø³ Ø¨Ø§ Ø´Ø§Ù‡Ø¯Ù Ø²Ù†Ø¯Ù‡):
         # (Û±) spectral Ø±ÙˆÛŒ Ú¯Ø±Ø§ÙÙ Ø¨ÛŒâ€ŒÛŒØ§Ù„Ù Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù…Ù *Ø³Ø§Ù„Ù…* Â«Ïƒâ‰ˆ1/criticalÂ» Ù…ÛŒâ€ŒØ¯Ø§Ø¯ â†’ Ø¢Ø³ÛŒØ§Ø¨Ù
         # Û¸ RFCÙ ÛŒÚ©Ø³Ø§Ù†Ø› (Û²) created_ts persist Ù†Ù…ÛŒâ€ŒØ´Ø¯ â†’ sweep Ù‡Ø±Ú¯Ø² expire Ù†Ù…ÛŒâ€ŒÚ©Ø±Ø¯Ø›
         # (Û³) phi Ø¨Ø§ Û² ack ÛŒÚ© Ø³Ú©ÙˆÙ†Ù Û²Ã—mean Ø±Ø§ Â«Ù…Ø±Ú¯Â» Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯ (Û¶Û¶ Ø±ÛŒâ€ŒØ§Ø³ØªØ§Ø±ØªØŒ phi=300 =
         # Ø³Ù‚ÙÙ p_later) â€” ØªØ­Ù…Ù‘Ù„Ù ØµØ§Ø¯Ù‚ Ù¾Ø´ØªÙ OCTOPUS_CHRONO_PHI_HONESTØ› (Û´) legs_diag ØªØ§
         # Ø§Ù…Ø±ÙˆØ² ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø´Øª Ù¾Ø³ Ù…Ø±Ú¯Ù ÙˆØ§Ù‚Ø¹ÛŒ Ø§Ø² Ø¢Ø±ØªÛŒÙÚ©ØªÙ Ø³Ù†Ø¬Ø´ Ø¬Ø¯Ø§ Ù†Ù…ÛŒâ€ŒØ´Ø¯Ø› (Ûµ) Gate-0 Ø¯Ø±
         # shadow Ø¨Ø§ Î”Ù *Ù…Ù†ÙÛŒ* Ù‡Ù… Ø¨Ø§Ø² Ù…ÛŒâ€ŒØ´Ø¯ (ÙÙ‚Ø· authoritative Ø±Ø§ Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯)Ø› (Û¶) Ø³Ù‡ ÙÙ„Ú¯Ù
         # Ù…ØºØ²Ù Ù¾ÙˆÙ„ÛŒ Ø¯Ø± wire_summary Ù†Ø¨ÙˆØ¯Ù†Ø¯ â†’ Ù…Ø³Ù„Ø­â€ŒØ¨ÙˆØ¯Ù† Ø§Ø² state Ø¯ÛŒØ¯Ù‡ Ù†Ù…ÛŒâ€ŒØ´Ø¯.
         "test_live_debug_fixes_2026_07_25.py",
         "test_thesis_queue.py",
         "test_governor_lapsed_deadline.py",
         "test_paid_timeout_chain.py",
         "test_card_render_profile.py",
         "test_audit_origin_guard.py",
         "test_coherence.py",
         # 2026-07-23 D3/D4/D5: (D3) ØµÙØ± provider-call/authorization/settle Ø²ÛŒØ±Ù HALT-ALL â€”
         # Ø´Ú©Ø§ÙÙ release_one/release_gated_effects Ø¨ÛŒâ€ŒÚ¯Ø§Ø±Ø¯Ù kill Ù‡Ù… Ø¨Ø³ØªÙ‡ Ø´Ø¯Ø› (D4) Ú¯Ø§Ø±Ø¯Ù
         # boot-halt Ø¯Ø± Ù‡Ø± Û¶ launcher + parity ÙˆØ§Ú†â€ŒØ¯Ø§Ú¯ PS1/py + Ù…Ø§ØªØ±ÛŒØ³Ù should_reviveØ›
         # (D5) Ø³Ù†Ø§Ø±ÛŒÙˆÛŒ ØªØ±Ú©ÛŒØ¨ÛŒÙ halt Ø¨Ø§ Ø²Ù…Ø§Ù†Ù Ù…Ø¬Ø§Ø²ÛŒ: ØµÙØ± Ø§Ø«Ø± Ø²ÛŒØ±Ù haltØŒ Ø¨Ø¯ÙˆÙ†Ù duplicateØŒ
         # recovery ØªÙ…ÛŒØ² + reconcile. script-native.
         "test_d3_provider_effect_halt.py",
         "test_d4_launcher_halt.py",
         "test_d5_halt_integration.py",
         # 2026-07-23 PRE-0: Ø¯Ù‡ invariant Ù‚Ø§Ù†ÙˆÙ† Ø§Ø³Ø§Ø³ÛŒ Ø§Ø² Ù†Ù‚Ø§Ø·Ù ÙˆØ±ÙˆØ¯Ù ÙˆØ§Ù‚Ø¹ÛŒ (MemoryGateØŒ
         # model_router Ø²ÛŒØ±Ù haltØŒ on_human_judgment Ø¨Ø§ Ú¯ÛŒØªÙ ÙˆØ§Ù‚Ø¹ÛŒØŒ code_autonomy.allowed_targetØŒ
         # watchdog/launcher) + seamÙ‡Ø§ÛŒ canonicalÙ governance Ø¨Ø±Ø§ÛŒ Ù„Ø§ÛŒÙ†â€ŒÙ‡Ø§ÛŒ Ù‡Ù†ÙˆØ²-ØºÛŒØ±ÙØ¹Ø§Ù„. script-native.
         "test_pre0_real_entry.py",
         # 2026-07-22 F-COVERAGE adjudication: test_tg_approval_store Ø¯ÛŒÚ¯Ø± orphanÙ Ø±Ø¯ Ù†ÛŒØ³Øª â€”
         # Ù…Ø§Ú˜ÙˆÙ„/API ÙˆØ§Ù‚Ø¹ÛŒ Ø§Ø³Øª Ùˆ reachable Ø¯Ø± production (center.py:1223-1224 approve/reject Ø±ÙˆÛŒ
         # Ù…Ø³ÛŒØ±Ù approval Ù…Ø§Ù„Ú©). ØªÙ†Ù‡Ø§ Ø´Ú©Ø³ØªØŒ stale characterization Ø¨ÙˆØ¯ (whitelistÙ t_n ÙØ§Ù‚Ø¯Ù
         # expires_epoch)Ø› contract migrate Ø´Ø¯. invariantÙ content-free Ø¯Ø³Øªâ€ŒÙ†Ø®ÙˆØ±Ø¯Ù‡. script-native.
         "test_tg_approval_store.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø§Ø¨Ø²Ø§Ø±Ù‡Ø§ÛŒ Ø®ÙˆØ¯Ù†Ú¯Ø±ÛŒ: Ú¯ÛŒØªÙ Ù…Ø§Ø´ÛŒÙ†â€ŒØ®ÙˆØ§Ù†ØŒ Ø±Ø§Ù†Ø´Ù ÙÙ„Ú¯ØŒ
    # Ø±Ø¯Ù Ø§Ø±Ø³Ø§Ù„ØŒ Ù…Ù…ÛŒØ²ÛŒÙ Ù…Ø³ÛŒØ±Ù Ø§Ø±Ø³Ø§Ù„ØŒ Ø§Ø³Ú©Ù†Ù Ù†Ù‚Ø§Ø·Ù Ú©ÙˆØ±ØŒ Ù„Ø§ÛŒÙ‡Ù” Ø¨ÛŒÙ†Ø´.
    "test_gate_report.py", "test_flag_drift.py", "test_tg_trace.py",
    "test_tg_send_audit.py", "test_self_scan.py", "test_self_insight.py",
    "test_tg_topic_reply_parity.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Û±Ûµ ØªØ³ØªÛŒ Ú©Ù‡ Ø±ÙˆÛŒ Ø¯ÛŒØ³Ú© Ø¨ÙˆØ¯Ù†Ø¯ Ùˆ Ø¯Ø± **Ù‡ÛŒÚ†** Ù„ÛŒØ³ØªÛŒ Ù†Ø¨ÙˆØ¯Ù†Ø¯.
    # Ú©Ø´Ù: run_all â€Û³ÛµÛ± ØªØ³ØªÙ ÛŒÚ©ØªØ§ Ù…ÛŒâ€ŒØ´Ù†Ø§Ø®Øª ÙˆÙ„ÛŒ Û³Û¶Û¶ ÙØ§ÛŒÙ„ Ø±ÙˆÛŒ Ø¯ÛŒØ³Ú© Ø¨ÙˆØ¯. Ø§Ø² Û±Û¸ Ø§Ø®ØªÙ„Ø§ÙØŒ
    # Û² ØªØ§ Ø§Ø³ØªØ«Ù†Ø§ÛŒ Ù…Ø³ØªÙ†Ø¯ Ø¨ÙˆØ¯ (drawdown_enforcer/mining_legØŒ Ø¯Ø± Ú©Ø§Ù…Ù†Øªâ€ŒÙ‡Ø§ÛŒ Ù‡Ù…ÛŒÙ† ÙØ§ÛŒÙ„) Ùˆ
    # Û±Û¶ ØªØ§ Ù‡ÛŒÚ† Ø±Ø¯ÛŒ Ù†Ø¯Ø§Ø´ØªÙ†Ø¯ â€” Ù†Ù‡ Ø¯Ø± Ù„ÛŒØ³ØªØŒ Ù†Ù‡ Ø¯Ø± Ú©Ø§Ù…Ù†Øª. ÛŒØ¹Ù†ÛŒ Ø§ÙØªØ§Ø¯Ú¯ÛŒØŒ Ù†Ù‡ ØªØµÙ…ÛŒÙ….
    # Ù¾Ø³ Â«Û³Û´Û²/Û³Û´Û² Ø³Ø¨Ø²Â» Ø¹Ø¯Ø¯Ø´ Ø¯Ø±Ø³Øª Ø¨ÙˆØ¯ Ùˆ Ø¯Ø§Ù…Ù†Ù‡â€ŒØ§Ø´ Ù†Ø§Ù‚Øµ: ØªØ³Øª Ù†ÙˆØ´ØªÙ‡ Ø´Ø¯Ù‡ Ø¨ÙˆØ¯ØŒ Ø¨Ù‡ Ø±Ø§Ù†Ø±
    # ÙˆØµÙ„ Ù†Ø´Ø¯Ù‡ Ø¨ÙˆØ¯. Ù†Ù…ÙˆÙ†Ù‡Ù” Ú¯ÙˆÛŒØ§: test_tg_topic_reply_quiet Ø¯Ø±Ø¨Ø§Ø±Ù‡Ù” ØªØ§Ù¾ÛŒÚ©â€ŒØ±ÙˆØªÛŒÙ†Ú¯ØŒ Ù†ÙˆØ´ØªÙ‡Ù”
    # Û°Û·-Û²Û¶ØŒ Ùˆ Ù‡Ù…Ø§Ù† Ø±ÙˆØ²ÛŒ Ú©Ù‡ Ù‡Ù…Ø§Ù† Ù…Ø³ÛŒØ± Ø¨Ø§Ú¯ Ø¯Ø§Ø´Øª Ø§Ø¬Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ´Ø¯.
    # Ù‡Ø± Û±Ûµ ØªØ§ Ù‚Ø¨Ù„ Ø§Ø² Ø«Ø¨Øª Ø¬Ø¯Ø§ Ø§Ø¬Ø±Ø§ Ø´Ø¯Ù†Ø¯: Û±Ûµ/Û±Ûµ Ø³Ø¨Ø² â†’ Ø«Ø¨ØªØ´Ø§Ù† ØµÙØ± Ø±ÛŒØ³Ú©.
    "test_c6_card_redelivery.py", "test_c6_probe_coverage.py",
    "test_cortex_circuit_breaker.py", "test_cortex_symmetric_revive.py",
    "test_ledger_integrity_probe.py", "test_module_self_manifest.py",
    "test_operator_doctrine.py", "test_route_scorer_shadow_log.py",
    "test_staleness_stamp.py", "test_synapse_sense.py", "test_synapse_beat.py",
    "test_tg_callback_actor.py", "test_tg_instant_and_sendlog.py",
    "test_tg_stream_routing.py", "test_tg_topic_reply_quiet.py",
    "test_unified_bus_guard.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø­Ù„Ù‚Ù‡Ù” Û· (Ø±Ø£ÛŒÙ ØµØ±ÛŒØ­Ù Ù…Ø§Ù„Ú© Â«Ø¨Ù„Ù‡ØŒ ÙˆØµÙ„ Ú©Ù†Â»). Ø¯Ø±Ø§ÛŒÙˆØ±Ù Ø§Ø¹Ù…Ø§Ù„Ù Ù¾Ú† ØªØ§
    # Ø§Ù…Ø±ÙˆØ² Ù‡ÛŒÚ† ØµØ¯Ø§Ú©Ù†Ù†Ø¯Ù‡â€ŒØ§ÛŒ Ù†Ø¯Ø§Ø´ØªØ› Ø­Ø§Ù„Ø§ Ø¯Ø§Ø±Ø¯ØŒ Ù¾Ø³ Ù‚ÙÙ„â€ŒÙ‡Ø§ÛŒØ´ Ø¨Ø§ÛŒØ¯ Ø³Ù†Ø¬ÛŒØ¯Ù‡ Ø´ÙˆÙ†Ø¯ Ù†Ù‡ Ø§Ø¯Ø¹Ø§.
    "test_code_apply_wiring.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø§Ø² Ø±ÙˆÙ†ÙˆØ´ØªÙ ÙˆØ§Ù‚Ø¹ÛŒÙ Ú¯Ø±ÙˆÙ‡: Â«Ø¯Ø±Ø¨Ø§Ø±Ù‡Ù” A08 ØªØ­Ù‚ÛŒÙ‚ Ú©Ø±Ø¯Ù… â€” A8Â» Ã—Û·.
    # Ø´Ù†Ø§Ø³Ù‡Ù” Ø¯Ø§Ø®Ù„ÛŒ Ùˆ Ø§Ø³Ù„Ø§Ú¯ Ù…Ø³ØªÙ‚ÛŒÙ…Ø§Ù‹ Ø¨Ù‡ Ù…ÙˆØªÙˆØ±Ù Ø¬Ø³ØªØ¬Ùˆ Ù…ÛŒâ€ŒØ±ÙØªÙ†Ø¯Ø› Ù†ØªÛŒØ¬Ù‡ ØºÛŒØ±ØµÙØ± Ø¨ÙˆØ¯ Ù¾Ø³
    # Ù‡ÛŒÚ† Ú¯Ø§Ø±Ø¯ÛŒ ØµØ¯Ø§ÛŒØ´ Ø±Ø§ Ø¯Ø±Ù†ÛŒØ§ÙˆØ±Ø¯. Ø§ÛŒÙ† ØªØ³Øª Ù‡Ø± Ø¯Ùˆ Ù…Ø±Ø² Ø±Ø§ Ù‚ÙÙ„ Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
    "test_research_query_sanity.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø¨Ø±Ø¯Ø§Ø± Ø³Ø§Ø®ØªÙ‡ Ù…ÛŒâ€ŒØ´Ø¯ØŒ Ø¯Ø± Ø§ÛŒÙ†Ø¯Ú©Ø³ Ø´Ù„ÛŒÚ© Ù…ÛŒâ€ŒÚ©Ø±Ø¯ØŒ Ùˆ Ø¯Ø± ØªØ§Ø±ÛŒØ®Ú†Ù‡
    # `None` Ø«Ø¨Øª Ù…ÛŒâ€ŒØ´Ø¯. Ø¨Ø§Ú¯Ù **ØªØ±ØªÛŒØ¨**: run() Ù‚Ø¨Ù„ Ø§Ø² ØºÙ†ÛŒâ€ŒØ³Ø§Ø²ÛŒ save Ù…ÛŒâ€ŒÚ©Ø±Ø¯.
    "test_latent_persist.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø¯Ùˆ ÙØ§ÛŒÙ„Ù ØªØ³ØªÙ Ù†ÙˆØ´ØªÙ‡â€ŒØ´Ø¯Ù‡ Ú©Ù‡ Ø¯Ø± Ù‡ÛŒÚ† Ù„ÛŒØ³ØªÛŒ Ù†Ø¨ÙˆØ¯Ù†Ø¯. Ù‡Ù…Ø§Ù† Ø§Ù„Ú¯ÙˆÛŒ
    # Ù‡Ù…ÛŒØ´Ú¯ÛŒ: ØªØ³Øª Ø³Ø§Ø®ØªÙ‡ Ø´Ø¯ØŒ Ø¨Ù‡ Ø±Ø§Ù†Ø± ÙˆØµÙ„ Ù†Ø´Ø¯ØŒ Ùˆ Â«Ø³ÙˆØ¦ÛŒØªÙ Ø³Ø¨Ø²Â» Ø¨ÛŒâ€ŒØ¢Ù†Ú©Ù‡ Ø¨Ø¯Ø§Ù†Ø¯
    # Ù¾ÙˆØ´Ø´Ø´ Ø±Ø§ Ø§Ø² Ø¯Ø³Øª Ø¯Ø§Ø¯. Ù‡Ø± Ø¯Ùˆ Ø¬Ø¯Ø§ Ø§Ø¬Ø±Ø§ Ùˆ Ø³Ø¨Ø² Ø´Ø¯Ù†Ø¯ Ù¾ÛŒØ´ Ø§Ø² Ø«Ø¨Øª.
    "test_neural_loop_close.py", "test_redact_failclosed.py",
    "test_extract_json_robust.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ú†Ù‡Ø§Ø± Ø¬ÙˆØ§Ø¨Ù Ù…Ø§Ù„Ú© Ø¯Ø±Ø¨Ø§Ø±Ù‡Ù” Ø³Ø·Ø­Ù ØªÙ„Ú¯Ø±Ø§Ù…ØŒ ØªØ¨Ø¯ÛŒÙ„â€ŒØ´Ø¯Ù‡ Ø¨Ù‡ Ù†Ø§ÙˆØ±Ø¯ÛŒ:
    # Ú¯Ø±ÙˆÙ‡=Ù¾Ø§Ù‡Ø§ Â· Ú†ØªÙ Ø®ØµÙˆØµÛŒ=Ø®ÙˆØ¯Ø¢Ú¯Ø§Ù‡ÛŒ Â· Ø¨Ù‚ÛŒÙ‡ Ù†Ú¯Ù‡â€ŒØ¯Ø§Ø´ØªÙ‡ (Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡ØŒ Ù†Ù‡ Ø¯ÙˆØ±Ø§Ù†Ø¯Ø§Ø®ØªÙ‡)
    # Â· Ø§ÛŒÙ…Ù†ÛŒ Ù‡Ø±Ú¯Ø² Ø³Ø§Ú©Øª Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯ Â· ÛŒÚ© Ú†ÛŒØ²ØŒ ÛŒÚ© Ø¯Ú©Ù…Ù‡.
    "test_surface_policy.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø±ÛŒØ´Ù‡Ù” Â«Ú©Ø§Ø±ØªÙ Û¶Ø³Ø§Ø¹ØªÙ‡ Ú†Ù‡Ø§Ø± Ø¨Ø§Ø± Ø¯Ø± ÛŒÚ© Ø³Ø§Ø¹ØªÂ»: Û±Û¸ Ú©Ø§Ø¯Ù†Ø³ Ø­Ø§Ù„ØªÙ
    # Ù¾Ù†Ø¬Ø±Ù‡â€ŒØ´Ø§Ù† Ø±Ø§ Ø¯Ø± Ø­Ø§ÙØ¸Ù‡ Ù†Ú¯Ù‡ Ù…ÛŒâ€ŒØ¯Ø§Ø´ØªÙ†Ø¯ØŒ Ù¾Ø³ Ù‡Ø± Ø¨ÙˆØª Ù‡Ù…Ù‡ Ø±Ø§ Ø¨ÛŒâ€ŒÙ‚ÛŒØ¯ Ø´Ù„ÛŒÚ© Ù…ÛŒâ€ŒÚ©Ø±Ø¯.
    # Ø¢Ø®Ø±ÛŒÙ† Ú†Ú©Ù Ø§ÛŒÙ† ÙØ§ÛŒÙ„ Ø¬Ù„ÙˆÛŒ Ø¨Ø±Ú¯Ø´ØªÙ†Ù Ø§Ù„Ú¯Ùˆ Ø±Ø§ Ù…ÛŒâ€ŒÚ¯ÛŒØ±Ø¯ØŒ Ù†Ù‡ ÙÙ‚Ø· Ø´Ø´ Ù†Ù…ÙˆÙ†Ù‡ Ø±Ø§.
    "test_epoch_guard.py",
    # âš ï¸ Ø´Ø§Ù†Ø²Ø¯Ù‡Ù…ÛŒ Ø¹Ù…Ø¯Ø§Ù‹ Ù†ÛŒØ§Ù…Ø¯: test_kill_seam_closer.py Ù‡Ù… STOP-ORGANISM Ø±Ø§ Ù†Ø§Ù…
    # Ù…ÛŒâ€ŒØ¨Ø±Ø¯ Ùˆ Ù‡Ù… harness.setup Ù†Ø¯Ø§Ø±Ø¯ â€” ÛŒØ¹Ù†ÛŒ Ø±ÙˆÛŒ Ø¯Ø±Ø®ØªÙ Ø²Ù†Ø¯Ù‡ Ù…ÛŒâ€ŒÙ†ÙˆÛŒØ³Ø¯ØŒ Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ ØªÙ„Ù‡Ù”
    # test_tg_power. ØªØ§ Ø§ÛŒØ²ÙˆÙ„Ù‡ Ù†Ø´Ø¯Ù‡ Ø§Ø¶Ø§ÙÙ‡â€ŒØ§Ø´ Ù†Ú©Ù†Ø› Ø§ÙˆÙ„ harness Ø¨Ú¯ÛŒØ±Ø¯ØŒ Ø¨Ø¹Ø¯ Ø«Ø¨Øª.
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø¨Ø³ØªÙ‡Ù” `mining_os` (Û³Û² ØªØ³ØªÙ Ø³Ø¨Ø²Ù Ø¯Ø±ÙˆÙ†-Ø¨Ø³ØªÙ‡) Ø§Ø² `88aaa29` ØªØ§ Ø§Ù…Ø±ÙˆØ²
    # **ØµÙØ± ØµØ¯Ø§Ú©Ù†Ù†Ø¯Ù‡** Ø¯Ø§Ø´Øª: Ù‡ÙˆÚ©Ø´ Ù‡Ø±Ú¯Ø² Ú©Ø§Ù…ÛŒØª Ù†Ø´Ø¯ Ùˆ ACTIVATION.md Ø®Ø·Ù Ø§Ø´ØªØ¨Ø§Ù‡ÛŒ Ø±Ø§
    # Ø¨Ù‡â€ŒØ¹Ù†ÙˆØ§Ù† Ù…Ø­Ù„Ù Ø§ØªØµØ§Ù„ Ø§Ø¹Ù„Ø§Ù… Ù…ÛŒâ€ŒÚ©Ø±Ø¯. ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ Ø®ÙˆØ¯Ù Ø¨Ø³ØªÙ‡ Ø§ÛŒÙ† Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ¯ÛŒØ¯Ù†Ø¯ Ú†ÙˆÙ† Ù‡Ù…Ù‡
    # Ø¯Ø±ÙˆÙ†-Ø¨Ø³ØªÙ‡â€ŒØ§Ù†Ø¯. Ø§ÛŒÙ† ÙØ§ÛŒÙ„ call site Ø±Ø§ Ù…ÛŒâ€ŒØ³Ù†Ø¬Ø¯ Ù†Ù‡ Ø´Ú©Ù„Ù Ø¨Ø³ØªÙ‡ Ø±Ø§. script-native.
    "test_mining_os_wiring.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø§ØªØ§Ù‚Ù Ú†Øª (Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú©: Â«ØªÙˆ Ú¯Ø±ÙˆÙ‡ ÛŒÙ‡ Ø¬Ø§ Ø±Ùˆ Ø¨Ø²Ø§Ø± Ú†Øª Ú©Ù†Ù… â€¦ ØªØ¹Ø§Ù…Ù„Ø§Ø±Ùˆ
    # Ú†Øªâ€ŒÚ¯ÙˆÙ†Ù‡ Ù…ÛŒØ®ÙˆØ§Ù…Â»). Ø³Ù‡ Ø¨Ù†Ø¯ Ø§Ø² Ú†Ù‡Ø§Ø± Ø¨Ù†Ø¯Ø´ Ø¯Ø±Ø¨Ø§Ø±Ù‡Ù” Ú†ÛŒØ²ÛŒ Ø§Ø³Øª Ú©Ù‡ Ù†Ø¨Ø§ÛŒØ¯ Ø¨Ø´ÙˆØ¯:
    # ÙÙ„Ú¯â€ŒØ®Ø§Ù…ÙˆØ´=Ø¨ÛŒâ€ŒØ§Ø«Ø±ØŒ Ù…Ø¨Ù‡Ù…=Ù…ÛŒâ€ŒÙ¾Ø±Ø³Ø¯ØŒ Ùˆ Ù‡ÛŒÚ† ÙØ±Ù…Ø§Ù†Ù Ø®ÛŒØ§Ù„ÛŒ ØªØ¨Ù„ÛŒØº Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯ â€” Ù‡Ù…Ø§Ù†
    # Û¸ ÙØ±Ù…Ø§Ù†ÛŒ Ú©Ù‡ Ø§Ù…Ø±ÙˆØ² ØµØ¨Ø­ ØªØ¨Ù„ÛŒØº Ù…ÛŒâ€ŒØ´Ø¯ Ùˆ Ø¯Ø± Ù‡ÛŒÚ† Ø¨Ø§ØªÛŒ ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø´Øª.
    "test_chat_room.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ú¯Ø§Ø±Ø¯Ù Ø¨Ø±Ø§Ø¨Ø±ÛŒÙ Ù¾Ø§Ù‡Ø§ (Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú©: Â«Ú¯Ø±ÙˆÙ‡ Ùˆ Ù¾Ø§Ù‡Ø§ Ù‡Ù…Ù‡â€ŒØ±Ùˆ Ø§ØªØµØ§Ù„Ø§Øª Ø±Ùˆ
    # Ú©Ø¯Ù†ÙˆÛŒØ³ÛŒ Ú©Ù†Â»). Ú†Ù‡Ø§Ø± Ø±Ø¬ÛŒØ³ØªØ±ÛŒÙ Ù…Ø³ØªÙ‚Ù„ ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø´Øª Ú©Ù‡ Ù‡ÛŒÚ†â€ŒÚ©Ø¯Ø§Ù… Ø¯ÛŒÚ¯Ø±ÛŒ Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ¯ÛŒØ¯ØŒ
    # Ùˆ Ø§Ø®ØªÙ„Ø§ÙØ´Ø§Ù† Ø¨ÛŒâ€ŒØµØ¯Ø§ Ø¨ÙˆØ¯: Ø³Ù‡ Ø§Ù†Ø¯Ø§Ù…Ù Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡ Ù‡ÛŒÚ† Ø±Ø§Ù‡ÛŒ Ø¨Ø±Ø§ÛŒ Ø±Ø³ÛŒØ¯Ù† Ù†Ø¯Ø§Ø´ØªÙ†Ø¯ Ùˆ
    # Ù‡ÛŒÚ† ØªØ³ØªÛŒ Ù‚Ø±Ù…Ø² Ù†Ù…ÛŒâ€ŒØ´Ø¯ Ú†ÙˆÙ† Ù‡Ø± Ø±Ø¬ÛŒØ³ØªØ±ÛŒ **Ø¨Ù‡â€ŒØªÙ†Ù‡Ø§ÛŒÛŒ** Ø³Ø§Ù„Ù… Ø¨ÙˆØ¯.
    "test_leg_parity.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” ØµØ¯Ø§ÛŒ Ù¾Ø§Ù‡Ø§ Ø¯Ø± Ú¯Ø±ÙˆÙ‡. Ø±ÛŒØ´Ù‡Ù” Û· ØªØ§Ù¾ÛŒÚ©Ù Ø®Ø§Ù„ÛŒ Ù†Ø¨ÙˆØ¯Ù Ù†Ú¯Ø§Ø´Øª Ù†Ø¨ÙˆØ¯Ø›
    # Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù… ÙÙ‚Ø· Ûµ Ø¬Ø±ÛŒØ§Ù† ØªÙˆÙ„ÛŒØ¯ Ù…ÛŒâ€ŒÚ©Ø±Ø¯ Ùˆ Ù‡ÛŒÚ†â€ŒÚ©Ø¯Ø§Ù… Ù¾Ø§ Ù†Ø¨ÙˆØ¯. Ø¨ÛŒØ´ØªØ±Ù Ø§ÛŒÙ† ØªØ³Øª
    # Ø¯Ø±Ø¨Ø§Ø±Ù‡Ù” **Ù†ÙØ±Ø³ØªØ§Ø¯Ù†** Ø§Ø³Øª: Ø®Ø§Ù…ÙˆØ´ØŒ Ø¨ÛŒâ€ŒØªØºÛŒÛŒØ±ØŒ Ù„Ø±Ø²Ø§Ù†ØŒ Ø¨ÛŒâ€ŒØ¯Ø§Ø¯Ù‡ØŒ Ø¨ÛŒâ€ŒØ§ØªØ§Ù‚.
    "test_leg_rooms.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ù¾Ù„ Ú©Ù„ÛŒØ¯Ù `keyboard` Ù…ÛŒâ€ŒØ®ÙˆØ§Ù†Ø¯ Ùˆ Ø±ÙˆØªØ± `reply_markup` Ù…ÛŒâ€ŒØ¯Ø§Ø¯ØŒ Ù¾Ø³
    # Û²Û¹ Ø±Ø¯ÛŒÙ Ø¯Ú©Ù…Ù‡ (queue Û±Û° Â· doctor Û¶ Â· money Ûµ Â· organs Û´ Â· school Û³ Â·
    # heart Û±) Ø¨ÛŒâ€ŒØµØ¯Ø§ Ø¯ÙˆØ± Ø±ÛŒØ®ØªÙ‡ Ù…ÛŒâ€ŒØ´Ø¯. Ù…ØªÙ† Ù…ÛŒâ€ŒØ±Ø³ÛŒØ¯ØŒ Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§ Ù†Ù‡ØŒ ØµÙØ± Ø®Ø·Ø§ â€” Ùˆ Ú©Ù„Ù
    # Ù…Ø³ÛŒØ±Ù Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Ø§Ø² Ú¯Ø±ÙˆÙ‡ Ø±ÙˆÛŒ Ù‡Ù…Ø§Ù† Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§Ø³Øª.
    "test_bridge_buttons.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ Û±Û¹:ÛµÛ· â€” ÛŒÚ© Ù¾Ø±ÙˆØ¨Ù Ø¨Ø¯Ø§ÛŒØ²ÙˆÙ„Ù‡ `power.stop_organism()` Ø±Ø§ Ø±ÙˆÛŒ Ø¯Ø±Ø®ØªÙ
    # Ø²Ù†Ø¯Ù‡ ØµØ¯Ø§ Ø²Ø¯ Ùˆ Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù… Ùˆ Ù…Ø±Ú©Ø² Û³Û° Ø¯Ù‚ÛŒÙ‚Ù‡ Ø®ÙˆØ§Ø¨ÛŒØ¯Ù†Ø¯. Ú¯Ø§Ø±Ø¯ Ø¯Ø± Ø®ÙˆØ¯Ù `power.py`
    # Ù†Ø´Ø³Øª Ù†Ù‡ Ø¯Ø± ØªØ³ØªØŒ Ú†ÙˆÙ† Ù…Ù‡Ø§Ø¬Ù… Ù¾Ø±ÙˆØ¨Ù Ø¯Ø³Øªâ€ŒÙ†ÙˆÛŒØ³ Ø¨ÙˆØ¯ Ù†Ù‡ ØªØ³Øª. Ø¬Ù‡ØªÙ failØ´ Ø¹Ù…Ø¯Ø§Ù‹
    # Ø¨Ù‡â€ŒØ³Ù…ØªÙ **Ø§Ø¬Ø§Ø²Ù‡** Ø§Ø³Øª: Ø¨Ø³ØªÙ†Ù ØªØ±Ù…Ø²Ù Ø§Ø¶Ø·Ø±Ø§Ø±ÛŒÙ ÙˆØ§Ù‚Ø¹ÛŒ Ø¨Ø¯ØªØ± Ø§Ø² Ù†Ø´Ø§Ù†Ú¯Ø±Ù Ø³Ø±Ú¯Ø±Ø¯Ø§Ù†.
    "test_power_isolation_guard.py",
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ø¨Ø³ØªÙ†Ù Ø­Ù„Ù‚Ù‡â€ŒÙ‡Ø§ÛŒ Ø°Ù‡Ù†ØŒ Ø¨Ø¹Ø¯ Ø§Ø² Ù…Ù…ÛŒØ²ÛŒÙ Ù…ØªØ®Ø§ØµÙ…Ù Û±Û±-Ø§ÛŒØ¬Ù†ØªÛŒ Ú©Ù‡ Ù‡Ø± Ù¾Ù†Ø¬
    # Ø²ÛŒØ±Ø³ÛŒØ³ØªÙ… Ø±Ø§ PARTIAL Ø¯Ø§Ø¯ Ùˆ Ù‡Ø± Û¶ Ù†Ù…Ø±Ù‡Ù” CREDIBLE Ø±Ø§ ØªÙ†Ø²Ù„ Ø¯Ø§Ø¯. Ø§Ù„Ú¯ÙˆÛŒ ÙˆØ§Ø­Ø¯Ø´:
    # Â«Ù…Ú©Ø§Ù†ÛŒØ²Ù… Ø¯Ø±Ø³Øª Ù¾ÛŒØ§Ø¯Ù‡ Ø´Ø¯Ù‡ Ùˆ Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ Ø¯Ø± Ø®Ø·ÛŒ Ú©Ù‡ Ø¨Ø§ÛŒØ¯ Ø±ÙØªØ§Ø± Ø±Ø§ Ø¹ÙˆØ¶ Ú©Ù†Ø¯ Ø®Ø§Ù…ÙˆØ´ Ø§Ø³ØªÂ».
    # Ù‡Ø± Ù¾Ù†Ø¬ ÙØ§ÛŒÙ„ Ø¬Ø¯Ø§ Ù†ÙˆØ´ØªÙ‡ Ø´Ø¯ (Ù…Ø§Ù„Ú©ÛŒØªÙ Ø§Ù†Ø­ØµØ§Ø±ÛŒÙ ÙØ§ÛŒÙ„ØŒ Ø¨Ø¯ÙˆÙ†Ù worktree Ú†ÙˆÙ† Ù…Ø®Ø²Ù†
    # ~Û´Û´Û° ÙØ§ÛŒÙ„Ù Ú©Ø§Ù…ÛŒØªâ€ŒÙ†Ø´Ø¯Ù‡ Ø¯Ø§Ø±Ø¯ Ùˆ worktree Ú©Ø¯Ù Ø¯ÛŒØ±ÙˆØ² Ø±Ø§ Ù…ÛŒâ€ŒØ¯Ø§Ø¯)ØŒ Ùˆ Ù‡Ø±Ú©Ø¯Ø§Ù… Ø±Ø§ ÛŒÚ©
    # Ø§ÛŒØ¬Ù†ØªÙ Ø¯ÙˆÙ…Ù Ù…Ø³ØªÙ‚Ù„ Ø¨Ø§ Ø¨Ø§Ø²Ø³Ø§Ø²ÛŒÙ Ú©Ø¯Ù Ù‚Ø¨Ù„-Ø§Ø²-ÙÛŒÚ©Ø³ Ø±Ø§Ø³ØªÛŒâ€ŒØ¢Ø²Ù…Ø§ÛŒÛŒ Ú©Ø±Ø¯.
    # Ù‡Ù…Ù‡ Ù¾Ø´ØªÙ ÙÙ„Ú¯Ù ØªØ§Ø²Ù‡ Ùˆ Ù¾ÛŒØ´â€ŒÙØ±Ø¶ Ø®Ø§Ù…ÙˆØ´: ÙÙ„Ú¯â€ŒØ®Ø§Ù…ÙˆØ´ = Ø±ÙØªØ§Ø±Ù Ø§Ù…Ø±ÙˆØ²ØŒ Ø¨Ø§ÛŒØªâ€ŒØ¨Ù‡â€ŒØ¨Ø§ÛŒØª.
    "test_selfknow_unknown_bridge.py",              # ØªØµØ­ÛŒØ­Ù Ù…Ø§Ù„Ú© Ø¨Ù‡ Ø´Ø§Ø®Ù‡Ù” heuristic
    "test_selfknow_calibration.py",                 # Ø§ÙˆÙ„ÛŒÙ† BrierÙ ÙˆØ§Ù‚Ø¹ÛŒÙ Ø³ÛŒØ³ØªÙ…
    "test_pain_calibration.py",                     # Ø¢Ø³ØªØ§Ù†Ù‡Ù” Ø¯Ø±Ø¯ Ø§Ø² ØªÙˆØ²ÛŒØ¹Ù ÙˆØ§Ù‚Ø¹ÛŒ
    "test_consolidation_compress_and_recall.py",    # ØªØ«Ø¨ÛŒØª: Ú©Ù¾ÛŒ â†’ ÙØ´Ø±Ø¯Ù‡â€ŒØ³Ø§Ø²ÛŒ
    "test_debate_owner_verdict.py",                 # Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Ù…Ø§Ù†Ø¯Ú¯Ø§Ø± Ùˆ Ø¨ÛŒâ€ŒØªÚ©Ø±Ø§Ø±
    # Û²Û°Û²Û¶-Û°Û·-Û³Û° â€” Ù‡Ø± Ø¯Ùˆ plain-asserts Ø§Ù†Ø¯ (ØªØ§Ø¨Ø¹â€ŒÙ‡Ø§ÛŒ `t_*` + `harness.run`)ØŒ Ù¾Ø³ Ø¯Ø±
    # TESTS Ù…ÛŒâ€ŒØ¢ÛŒÙ†Ø¯ Ù†Ù‡ PYTEST_TESTS: Ø²ÛŒØ±Ù pytest ØµÙØ± ØªØ³Øª collect Ù…ÛŒâ€ŒØ´ÙˆØ¯ â‡’ exit 5 â‡’
    # Ù‚Ø±Ù…Ø²Ù Ú©Ø§Ø°Ø¨Ù Ø¯Ø§Ø¦Ù…. run_all Ù‡ÛŒÚ† glob/discovery Ù†Ø¯Ø§Ø±Ø¯ â‡’ Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡ = Ù‡Ø±Ú¯Ø² Ø§Ø¬Ø±Ø§ Ù†Ø´Ø¯Ù‡.
    "test_hebbian_eventclock.py",                   # Ø³Ø§Ø¹ØªÙ Ø±Ø®Ø¯Ø§Ø¯Ù hebbian + Ø³Ù‚ÙÙ learned
    "test_watchdog_stall.py",                       # Ø§Ø³ØªØ§Ù„Ù Ø­Ù„Ù‚Ù‡ + Ø§Ø­ÛŒØ§ÛŒ Ø¨Ø§ØµØ¯Ø§
    # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ù…ÙˆØ¬Ù Â«Ø§ØªØµØ§Ù„ØŒ Ù†Ù‡ Ø§Ù†Ø¯Ø§Ù…Ù Ù†ÙˆÂ» (Ø³Ù†Ø¯Ù OCTOPUS-VS-FRONTIER): Ù¾Ù†Ø¬
    # ÙØ§ÛŒÙ„ØŒ Ù‡Ù…Ù‡ plain-asserts (ØªØ§Ø¨Ø¹â€ŒÙ‡Ø§ÛŒ t_ + harness.run) â‡’ Ø¯Ø± TESTSØŒ Ù†Ù‡ PYTEST.
    "test_action_durability.py",     # Ø¯ÙØªØ±Ù idempotency/nonce Ù persistedØ› replay=NOOPØ›
                                     # Ù‡Ù…ÛŒÙ† ØªØ³Øª Ø¨Ø§Ú¯Ù split/rsplit Ù CONFLICT Ø±Ø§ Ø±Ùˆ Ú©Ø±Ø¯
    "test_retrieval_router.py",      # Ø­Ø§ÙØ¸Ù‡ Ø¯Ø± Ù†Ù‚Ø·Ù‡Ù” ØªØµÙ…ÛŒÙ… â€” ÙÙ‚Ø· narrowingØŒ Ù‡Ø±Ú¯Ø² Ù…Ø¬ÙˆØ²
    "test_mission_kernel.py",        # Ù¾Ø±ÙˆÙ†Ø¯Ù‡Ù” ÙˆØ§Ø­Ø¯Ù Ù…Ø£Ù…ÙˆØ±ÛŒØª: timeline/resume/fsckØŒ ÙÙ‚Ø·â€ŒØ®ÙˆØ§Ù†Ø¯Ù†ÛŒ
    "test_state_write_retry.py",     # Ø±ÛŒØ´Ù‡Ù” VQ-STATE-WRITE-001: retry Ù os.replace + breadcrumb
    "test_action_schema_drift.py",   # Ø¯Ùˆ Ú©Ù¾ÛŒÙ Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬Ù action-request â€” Ú¯Ø§Ø±Ø¯Ù drift
    # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ø§ØªØ§Ù‚Ù Ú©Ù†ØªØ±Ù„Ù Ù¾Ø§Ù‡Ø§. Ø¯Ùˆ ÙØ§ÛŒÙ„Ù Ø§ÙˆÙ„ Û°Û·-Û³Û° Ù†ÙˆØ´ØªÙ‡ Ø´Ø¯Ù‡ Ø¨ÙˆØ¯Ù†Ø¯ Ùˆ Ø¯Ø±
    # **Ù‡ÛŒÚ†** Ù„ÛŒØ³ØªÛŒ Ù†Ø¨ÙˆØ¯Ù†Ø¯ (Ù‡Ù…Ø§Ù† ØªÙ„Ù‡Ù” Ù…Ø³ØªÙ†Ø¯Ù Ø¨Ø§Ù„Ø§: ØªØ³Øª Ø³Ø§Ø®ØªÙ‡ Ø´Ø¯ØŒ Ø¨Ù‡ Ø±Ø§Ù†Ø± ÙˆØµÙ„
    # Ù†Ø´Ø¯). Ù‡Ø± Ø³Ù‡ Ù‚Ø¨Ù„ Ø§Ø² Ø«Ø¨Øª Ø¬Ø¯Ø§ Ø§Ø¬Ø±Ø§ Ùˆ Ø³Ø¨Ø² Ø´Ø¯Ù†Ø¯ (Û±Û¸/Û±Û¸ Â· Û·/Û· Â· Û±Ûµ/Û±Ûµ).
    "test_tg_leg_tasks.py",         # Ù…Ø¯Ù„Ù Task Ù Ú¯Ø±ÙˆÙ‡: Û´ ÙˆØ¶Ø¹ÛŒØªØŒ Ú©Ø§Ø±ØªØŒ Ø±Ø³ÛŒØ¯
    "test_tg_group_is_legs_only.py",  # Ú¯Ø±ÙˆÙ‡ legs-only: Ø¬Ø±ÛŒØ§Ù†Ù Ù‡Ø³ØªÙ‡â€ŒØ§ÛŒ Ù‡Ø±Ú¯Ø² Ø¯Ø± Ú¯Ø±ÙˆÙ‡
    "test_tg_leg_commands.py",      # Û¹ ÙØ±Ù…Ø§Ù†Ù Ø·Ø¨ÛŒØ¹ÛŒ + Ø±ÙØ¹Ù Ù…Ø§Ù†Ø¹ Ø¨Ø§ Ø±ÛŒÙ¾Ù„Ø§ÛŒ + Ú¯Ø²Ø§Ø±Ø´Ù Ø±ÙˆØ²Ø§Ù†Ù‡
    # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ø§Ø³Ú©Ù†Ù Ø¹Ù…ÛŒÙ‚Ù ØªÙ„Ú¯Ø±Ø§Ù… Û¹ Ø³ÙˆÛŒÛŒØªÙ Ø³Ø¨Ø²Ù Ø¯ÛŒÚ¯Ø± Ø±Ø§ Ù‡Ù… Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡ ÛŒØ§ÙØªØ›
    # Ø§Ø² Ø¬Ù…Ù„Ù‡ test_tg_callback_emitter_parity Ú©Ù‡ **Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ Ú¯Ø§Ø±Ø¯Ù Ú©Ø§Ø±ØªÙ Ù…Ø±Ø¯Ù‡**
    # Ø§Ø³Øª Ùˆ Ù‡Ø±Ú¯Ø² Ù†Ù…ÛŒâ€ŒØ¯ÙˆÛŒØ¯. Ù‡Ø± Û¹ ØªØ§ Ù‚Ø¨Ù„ Ø§Ø² Ø«Ø¨Øª Ø¬Ø¯Ø§ Ø§Ø¬Ø±Ø§ Ùˆ Ø³Ø¨Ø² Ø´Ø¯Ù†Ø¯.
    # (test_mining_leg Ø¹Ù…Ø¯Ø§Ù‹ Ø«Ø¨Øª Ù†Ø´Ø¯ â€” ImportError Ù ÙˆØ§Ù‚Ø¹ÛŒÙ Ù¾ÛŒØ´â€ŒÙ…ÙˆØ¬ÙˆØ¯:
    # `MiningLeg` Ø¯ÛŒÚ¯Ø± Ø¯Ø± legs/mining_leg.py Ù†ÛŒØ³ØªØ› ÙÛŒÚ©Ø³Ø´ Ú©Ø§Ø±Ù Ø¬Ø¯Ø§Ø³Øª.
    # test_studio_telegram Ù‡Ù… self-skip Ø§Ø³Øª: Ù…Ø§Ú˜ÙˆÙ„Ø´ Ø¯Ø± worktree Ù Project-F Ø§Ø³Øª.)
    "test_tg_callback_emitter_parity.py",   # Ù‡Ø± verb Ù Ø³Ø§Ø®ØªÙ‡â€ŒØ´Ø¯Ù‡ Ø­ØªÙ…Ø§Ù‹ route Ù…ÛŒâ€ŒØ´ÙˆØ¯
    "test_tg_input_surface_policy.py",      # Ú¯ÛŒØªÙ ÙˆØ±ÙˆØ¯ÛŒ: outer/inner Ã— DM/group
    "test_tg_surface_router.py",            # stream â†’ (client, chat, topic)
    "test_tg_canonical_access_model.py",    # Ù…Ø¯Ù„Ù Ø¯Ø³ØªØ±Ø³ÛŒÙ Ù…ØµÙˆØ¨
    "test_tg_client_contract.py",           # Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯Ù Ú©Ù„Ø§ÛŒÙ†ØªÙ Ø¯Ùˆ-Ø¨Ø§ØªÛŒ
    "test_capability_manifest_registry.py", # Ú©Ø§ØªØ§Ù„ÙˆÚ¯Ù Ù‚Ø§Ø¨Ù„ÛŒØªâ€ŒÙ‡Ø§
    "test_tg_hold_policy.py",               # Ù…Ø§Ø´ÛŒÙ†Ù Ø­Ø§Ù„ØªÙ HOLD (VQ-TG-HOLD-001)
    "test_tg_route_seam.py",                # Ø¯Ø±Ø²Ù _route_send
    "test_tg_build_surface.py",             # Ø³Ø·Ø­Ù Â«Ø¨Ø³Ø§Ø²:Â» + Ø­Ù„Ù‚Ù‡Ù” Ø³Ø§Ø®ØªÙ Ø®ÙˆØ¯
    # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ø­Ù„Ù‚Ù‡Ù” Ø¹Ù…Ù„ÛŒØ§ØªÛŒ (Ø¨Ø±Ù†Ú† claude/operational-loop-agi-566734):
    "test_state_write_loudness.py",              # VQ-STATE-WRITE-001: Ø´Ú©Ø³ØªÙ Ù†ÙˆØ´ØªÙ† Ø¨Ø§ØµØ¯Ø§
    "test_mission_approval_and_receipt_critic.py",  # Ú©Ø§Ø±ØªÙ A3 â†’ ØµÙÙ Ù…Ø§Ù„Ú© + Ù…Ù†ØªÙ‚Ø¯Ù Ø±Ø³ÛŒØ¯
    "test_verdict_feedback_loop.py",             # Ø­Ú©Ù…Ù Ù…Ø§Ù„Ú© â†’ ØªÙˆÚ©Ù†â€ŒÙ‡Ø§ â†’ ØªØµÙ…ÛŒÙ…Ù Ø¨Ø¹Ø¯ÛŒ
    "test_mission_reconcile_step1.py",           # Ú¯Ø°Ø§Ø±Ù Ù‚Ø§Ù†ÙˆÙ†ÛŒÙ Genome + ÙˆØ§Ú˜Ú¯Ø§Ù†Ù Û±Û²â†’Û¶
    # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ù…ÙˆØ¬Ù ÛŒÚ©Ù¾Ø§Ø±Ú†Ù‡â€ŒØ³Ø§Ø²ÛŒ:
    "test_ledger_reanchor_2026_07_31.py",   # Ø±Ú¯Ø±Ø³ÛŒÙˆÙ†Ù ØªØ±Ù…ÛŒÙ…Ù Ø²Ù†Ø¬ÛŒØ±Ù‡Ù” ledger (genesis ØªØ§Ø²Ù‡)
    "test_tg_send_receipt_schema.py",       # Ø±Ø³ÛŒØ¯Ù Ø§Ø±Ø³Ø§Ù„: bot_role+surface+state Ø³Ù‡â€ŒØ­Ø§Ù„ØªÛŒ (gate 8)
    "test_redact_before_archive.py",        # redact Ù‚Ø¨Ù„ Ø§Ø² hold (boundary-3: Ù†Ø´Øª Ø¯Ø± Ø¢Ø±Ø´ÛŒÙˆ)
    "test_tg_409_rival_poller.py",           # ØªØ´Ø®ÛŒØµÙ pollerÙ Ø±Ù‚ÛŒØ¨ Ø±ÙˆÛŒ Ø¨Ø§ØªÙ Ù…Ø±Ú©Ø² (boundary-12)
    "test_flag_load_shortfall.py",             # Ù¾ÛŒÚ©Ø±Ø¨Ù†Ø¯ÛŒÙ Ù†ØµÙÙ‡ Ø³Ø±Ù boot Ø¯Ø§Ø¯ Ø¨Ø²Ù†Ø¯ (ÙØ±ÙˆÙ¾Ø§Ø´ÛŒÙ Û°Û¹:Û°Û·)
    "test_tg_poll_health.py",                # Ú¯ÙˆØ´Ù Ù…Ø±Ø¯Ù‡ Ø¯ÛŒØ¯Ù‡ Ø´ÙˆØ¯: Ù‡Ø± Ø¯ÙˆØ±Ù getUpdates Ø«Ø¨Øª + Ù‡Ø´Ø¯Ø§Ø±Ù Ú©ÙˆØ±ÛŒ
    "test_tg_voice_worker.py",               # ÙˆÛŒØ³Ù Ú©Ù†Ø¯ Ø±ÙˆÛŒ Ù†Ø®Ù Ú©Ø§Ø±Ú¯Ø±ØŒ Ù†Ù‡ Ø±ÙˆÛŒ Ø­Ù„Ù‚Ù‡Ù” poll
    "test_tg_model_cache.py",                 # Ù…Ø¯Ù„ ÛŒÚ©â€ŒØ¨Ø§Ø± Ø¨Ø§Ø± Ø´ÙˆØ¯ØŒ Ù†Ù‡ Ø¨Ù‡â€ŒØ§Ø²Ø§ÛŒ Ù‡Ø± ÙˆÛŒØ³
    "test_tg_voice_keep_audio.py",           # ØµÙˆØª ÙÙ‚Ø· Ø¨Ø§ ÙÙ„Ú¯Ù ØµØ±ÛŒØ­Ù ØªØ´Ø®ÛŒØµ Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯
    # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ø³Ø§Ø®ØªÙ Û´Ù…ÙˆØ¬Ù‡Ù” Ù…Ù†Ø´ÙˆØ±Ù UI ØªÙ„Ú¯Ø±Ø§Ù… (Û¸ Ù„ÙÛŒÙ† + Ù„ÙÛŒÙ†Ù Ø³ÛŒÙ…â€ŒÚ©Ø´ÛŒ):
    "test_tg_menu_contract.py",             # Ù…Ù†ÙˆÛŒ DM â‰¤Û±Û° Ù scope-Ø¯Ø§Ø± + ØªÚ©â€ŒÙ†ÙˆÛŒØ³Ù†Ø¯Ù‡Ù” Ù…Ù†ÙˆÛŒ inner
    "test_tg_callback_answer.py",           # Ù‡ÛŒÚ† ØªÙ¾ÛŒ Ø¨ÛŒâ€Œanswer Ù†Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ (Ù…Ø±Ú¯Ù spinner)
    "test_tg_group_allowlist_policy.py",    # Ú¯ÛŒØªÙ Ú¯Ø±ÙˆÙ‡ deny-by-default + Ú¯ÛŒØªÙ callback
    "test_tg_send_receipts.py",             # Ø±Ø³ÛŒØ¯Ù Ø³Ù‡â€ŒØ­Ø§Ù„ØªÛŒ state/bot_role/surface Ø¯Ø± Ù‡Ø± Ù…Ø³ÛŒØ±
    "test_tg_capture.py",                   # capture ÛŒÚ©â€ŒÚ˜Ø³ØªÙ‡ â†’ vault (Ø±Ø£ÛŒ Û¹-Û±Û°)
    "test_tg_reminders.py",                 # ÛŒØ§Ø¯Ø¢ÙˆØ±ÛŒÙ NL + Ø³Ú©ÙˆØªÙ Û²Û³-Û· (Ø±Ø£ÛŒ Û¶/Û¸)
    "test_tg_brief.py",                     # Ø¨Ø±ÛŒÙÙ ØµØ¨Ø­/Ø´Ø¨ + Ù„ÛŒÙ†Ú©Ù ØªØ§Ù¾ÛŒÚ© (Ø±Ø£ÛŒ Û±Û±)
    "test_tg_ask_vault.py",                 # Ø³Ø¤Ø§Ù„-Ø§Ø²-vault Ø¨Ø§ Ù…Ù†Ø¨Ø¹ (Ø±Ø£ÛŒ Û¹)
    "test_miniapp_gateway.py",              # Ú¯ÛŒØªÙ initData Ù Mini App (Ø±Ø£ÛŒ Û²Û²)
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û³ (GO Ù Ù…Ø§Ù„Ú©ØŒ PROP-D5 ÙØ§Ø² Û±): Ú©Ø§Ø±Øªâ€ŒÙ‡Ø§ÛŒ read-only Ù Project-F.
    # Ú†Ù‡Ø§Ø± Ú¯Ø§Ø±Ø¯Ù Ø¬Ù‡Ø´â€ŒØ¢Ø²Ù…ÙˆØ¯Ù‡: flag-off=404 Â· Ø¯ÛŒÙˆØ§Ø±Ù auth Â· content-free (Ù‚Ø§Ø¹Ø¯Ù‡Ù” #Û·) Â·
    # Ø³Ù‡â€ŒØ­Ø§Ù„ØªÛŒÙ ØµØ§Ø¯Ù‚ (ÙØ§ÛŒÙ„Ù ØºØ§ÛŒØ¨ = unknownØŒ Ù†Ù‡ ØµÙØ±Ù Ø¬Ø¹Ù„ÛŒ).
    "test_pf_miniapp.py",
    "test_tg_leg_activation.py",            # Ù‚Ø§Ù„Ø¨Ù Ù¾Ø§ÛŒ ÙØ¹Ø§Ù„â€ŒØ´ÙˆÙ†Ø¯Ù‡ + Ú¯Ø§Ø±Ø¯Ù ØµÙØ±-template
    "test_tg_weekly_review.py",             # Ù…Ø±ÙˆØ±Ù Ù‡ÙØªÚ¯ÛŒÙ Ø´Ù†Ø¨Ù‡ (Ø±Ø£ÛŒ Û±Û² + Â§Û¹)
    "test_tg_question_budget.py",           # Ø¨ÙˆØ¯Ø¬Ù‡Ù” Û³Û°-Ø³Ø¤Ø§Ù„/Ù‡ÙØªÙ‡ (Ø±Ø£ÛŒ Û²Û´)
    "test_tg_wiring_w2.py",                 # Ø³ÛŒÙ…â€ŒÚ©Ø´ÛŒÙ Ø³Ø±ÛŒØ§Ù„Ù Ù‡Ù…Ù‡Ù” Ù…Ø§Ú˜ÙˆÙ„â€ŒÙ‡Ø§ Ø¯Ø± center
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û± â€” Ù…ÙˆØ¬Ù Â«Ù‡Ø± ÙˆØ¹Ø¯Ù‡ ÙˆØ§Ù‚Ø¹ÛŒ Ø´ÙˆØ¯Â» (ÙˆÛŒØ³ØŒ Ø§Ø±Ø³Ø§Ù„Ù Ù„ÛŒØ¯ØŒ Ø¨ÙˆØ¯Ø¬Ù‡â€ŒÙ‡Ø§ØŒ ÛŒØªÛŒÙ…â€ŒÙ‡Ø§):
    "test_tg_wiring_w3.py",                 # Ø³ÛŒÙ…â€ŒÚ©Ø´ÛŒÙ Ø¯ÙˆØ±Ù Ø¯ÙˆÙ… (ÙˆÛŒØ³/Ø¨ÙˆØ¯Ø¬Ù‡/Ø³Ø¤Ø§Ù„/ÛŒØªÛŒÙ…)
    "test_tg_transcribe.py",                # Ù†Ø±Ø¯Ø¨Ø§Ù†Ù Ù…ØªÙ†â€ŒØ³Ø§Ø²ÛŒÙ ÙˆÛŒØ³ + ØµØ¯Ø§Ù‚ØªÙ Ø´Ú©Ø³Øª
    "test_tg_notify_budget.py",             # Ø³Ù‚ÙÙ Ûµ Ø§Ø¹Ù„Ø§Ù†Ù Ù‚Ø·Ø¹â€ŒÚ©Ù†Ù†Ø¯Ù‡ (Ù…Ù†Ø´ÙˆØ± Â§Û³)
    "test_tg_question_producers.py",        # Ø§Ø®ØªØ§Ù¾ÙˆØ³ ÙˆØ§Ù‚Ø¹Ø§Ù‹ Ø³Ø¤Ø§Ù„ Ù…ÛŒâ€ŒØ³Ø§Ø²Ø¯ (Ø±Ø£ÛŒ Û²Û´)
    "test_tg_send_log_stats.py",            # Ø®Ø·Ù Ø¢Ù…Ø§Ø±Ù Ø¶Ø¯ÙØ§Ø³Ù¾Ù… Ø¯Ø± Ù¾Ø§Ù„Ø³
    "test_tg_orphans_wired.py",             # Ø³Ù‡ Ù…Ø§Ú˜ÙˆÙ„Ù Ø³Ø§Ø®ØªÙ‡â€ŒØ´Ø¯Ù‡ Ú©Ù‡ Ø­Ø§Ù„Ø§ ØµØ¯Ø§Ú©Ù†Ù†Ø¯Ù‡ Ø¯Ø§Ø±Ù†Ø¯
    "test_mail_credentials.py",             # Ø§Ø¹ØªØ¨Ø§Ø±Ù SMTP: Ù‡Ø±Ú¯Ø² Ø®ÙˆØ¯Ù Ø±Ø§Ø² Ø±Ø§ Ø¨Ø±Ù†Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø§Ù†Ø¯
    "test_tg_owner_readiness.py",           # Ú†Ú©â€ŒÙ„ÛŒØ³ØªÙ Ø¢Ù…Ø§Ø¯Ú¯ÛŒÙ Ù…Ø§Ù„Ú© (ÙÙ‚Ø·â€ŒØ®ÙˆØ§Ù†Ø¯Ù†ÛŒ)
    "test_tg_acceptance_journey.py",        # Ø³ÙØ±Ù Û¶Ø³Ø§Ø¹ØªÙ‡Ù” Ù¾Ø°ÛŒØ±Ø´ (ØªØ³ØªÙ Ø®ÙˆØ¯Ù Ù‡Ø§Ø±Ù†Ø³)
    "test_lead_pipeline.py",                # Ø­Ù„Ù‚Ù‡Ù” Ù„ÛŒØ¯: Ú©Ø´Ùâ†’ØªØ­Ù‚ÛŒÙ‚â†’Ù¾ÛŒØ´â€ŒÙ†ÙˆÛŒØ³â†’Ú¯ÛŒØ±/Ú©Ø§Ø±Øª (Ø±Ø£ÛŒ Û±Û³)
    "test_lead_send_cap.py",                # Ø³Ù‚ÙÙ Û±Û°/Ø±ÙˆØ² (Ø±Ø£ÛŒ ARM Ù Ù…Ø§Ù„Ú© Û°Û·-Û³Û±) Ø¯Ùˆ-Ù„Ø§ÛŒÙ‡
    "test_lead_outbound_transport.py",      # transport Ù SMTP: Ø¨ÛŒâ€Œcreds=NOT_ARMED ØµØ§Ø¯Ù‚
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û± â€” Ø³Ù‡ Ø´Ú©Ø§ÙÙ Ù¾ÛŒØ´ Ø§Ø² Ù…Ø³Ù„Ø­â€ŒØ³Ø§Ø²ÛŒÙ Ù„ÛŒØ¯ + Ù¾Ø±ÙˆØ¨Ù Ø¯Ø±ÛŒØ§ÙØª.
    # Ø«Ø¨Øª Ø¹Ù…Ø¯Ø§Ù‹ Ù…Ø±Ú©Ø²ÛŒ Ø§Ø³Øª: Ù¾Ù†Ø¬ Ù„ÙÛŒÙ†Ù Ù…ÙˆØ§Ø²ÛŒ Ø­Ù‚ Ù†Ø¯Ø§Ø´ØªÙ†Ø¯ run_all Ø±Ø§ Ø¯Ø³Øª Ø¨Ø²Ù†Ù†Ø¯ØŒ
    # Ú†ÙˆÙ† ØªØµØ§Ø¯Ù…Ù Ù‡Ù…ÛŒÙ† ÙØ§ÛŒÙ„ Ø§Ù…Ø±ÙˆØ² ÛŒÚ© deploy Ø±Ø§ Ù…ØªÙˆÙ‚Ù Ú©Ø±Ø¯.
    "test_lead_send_notify.py",            # GAP-1: Ø§ÛŒÙ…ÛŒÙ„Ù Ø±ÙØªÙ‡ Ø¯ÛŒÚ¯Ø± Ø¨ÛŒâ€ŒØµØ¯Ø§ Ù†Ù…ÛŒâ€ŒØ±ÙˆØ¯ (ÙÙ„Ú¯ default-off)
    "test_lead_price_in_email.py",         # GAP-2: Ú©ÙˆØª Ø¨Ø¯ÙˆÙ†Ù Ø¹Ø¯Ø¯ Ú©ÙˆØª Ù†ÛŒØ³Øª
    "test_funnel_sent.py",                 # GAP-3: /funnel Â«ÙØ±Ø³ØªØ§Ø¯Ù‡ Ø´Ø¯Â» Ø±Ø§ Ù‡Ù… Ù†Ø´Ø§Ù† Ù…ÛŒâ€ŒØ¯Ù‡Ø¯
    "test_tg_receive_probe.py",            # Ù¾Ø±ÙˆØ¨Ù Ø³Ù„Ø§Ù…ØªÙ Ø¯Ø±ÛŒØ§ÙØª (Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú© Û°Û¸-Û°Û±ØŒ ØªÙˆÚ©Ù† ÙÙ‚Ø· Ø§Ø² env)
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û³ â€” B5 (Ø³Ø·Ø­Ù Ú©Ù†ØªØ±Ù„Ù ÛŒÚ©Ù¾Ø§Ø±Ú†Ù‡). Ø«Ø¨Øª Ù…Ø±Ú©Ø²ÛŒ Ø§Ø³Øª Ú†ÙˆÙ†
    # ÙˆÛŒØ±Ø§ÛŒØ´Ù Ù‡Ù…â€ŒØ²Ù…Ø§Ù†Ù run_all Ø§Ù…Ø±ÙˆØ² Ú†Ù‡Ø§Ø± Ø¨Ø§Ø± deploy Ø±Ø§ Ø¨Ø³Øª.
    "test_governor_routing.py",          # B5.1 â€” Ù…Ø³ÛŒØ±ÛŒØ§Ø¨ÛŒÙ Ú¯Ø§ÙˆØ±Ù†Ø±: Ø±Ø§Ø² Ù‡Ø±Ú¯Ø² Ø¨Ù‡ ØªÛŒØ±Ù Ø¯ÙˆØ± Ù†Ù…ÛŒâ€ŒØ±Ø³Ø¯
    "test_miniapp_ops_readmodel.py",   # B5.0 â€” /api/ops: Ú©Ù„ÛŒØ¯Ù‡Ø§ÛŒ Ù‚Ø¯ÛŒÙ…ÛŒ Ø¯Ø³Øªâ€ŒÙ†Ø®ÙˆØ±Ø¯Ù‡ØŒ fail-softØŒ Ú¯Ø§Ø±Ø¯Ù Ø²ÛŒØ±Ù…Ø³ÛŒØ±
    "test_tg_ops_buttons.py",            # B5 â€” Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§ÛŒ /ops: Ù…Ø§Ù„Ú©â€ŒÙÙ‚Ø·ØŒ idempotentØŒ audited
    "test_miniapp_cockpit_ui.py",        # B5 â€” Ú©Ø§Ú©Ù¾ÛŒØª: Ù‡Ø¯Ø±Ù initData Ùˆ Â«Ù†Ù…ÛŒâ€ŒØ¯Ø§Ù†Ù…Â» Ù‡Ø±Ú¯Ø² Ø³Ø¨Ø²
    # â”€â”€ union Ø§Ø² Ù„ÙÛŒÙ†Ù Ø§ÛŒÙ…ÛŒÙ„/Ù„ÛŒØ¯ (Û°Û¸-Û°Û±) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Ù‡ÙØª ÙØ§ÛŒÙ„ Ø±ÙˆÛŒ Ø¯Ø±Ø®ØªÙ Ø²Ù†Ø¯Ù‡â€ŒØ§Ù†Ø¯ Ùˆ Ø¢Ù†â€ŒØ¬Ø§ Ø³Ø¨Ø²Ø› Ø¯Ø± Ø§ÛŒÙ† Ø´Ø§Ø®Ù‡ Ù‡Ù†ÙˆØ² untracked
    # Ù…Ø§Ù†Ø¯Ù‡â€ŒØ§Ù†Ø¯ØŒ Ù¾Ø³ ØªØ§ ÙˆÙ‚ØªÛŒ Ø¢Ù† Ù„ÙÛŒÙ† Ú©Ø§Ù…ÛŒØª Ù†Ú©Ù†Ø¯ØŒ Ø§Ø¬Ø±Ø§ÛŒ Ø³ÙˆÛŒÛŒØª Ø§Ø² Ø§ÛŒÙ† worktree
    # Ø¨Ø±Ø§ÛŒØ´Ø§Ù† Ù‚Ø±Ù…Ø²Ù Â«ÙØ§ÛŒÙ„ Ù†ÛŒØ³ØªÂ» Ù…ÛŒâ€ŒØ¯Ù‡Ø¯ â€” fail-closed Ùˆ Ø¨ÛŒâ€ŒØ³Ø±ÙˆØµØ¯Ø§ Ù†Ù‡.
    "test_proposal_counter_durable.py",      # Ø´Ù…Ø§Ø±Ù†Ø¯Ù‡Ù” Ù¾ÛŒØ´Ù†Ù‡Ø§Ø¯: Ø±ÛŒâ€ŒØ§Ø³ØªØ§Ø±Øª ØµÙØ±Ø´ Ù…ÛŒâ€ŒÚ©Ø±Ø¯
    "test_invoice_unpayable_is_loud.py",     # ÙØ§Ú©ØªÙˆØ±Ù Ø¨ÛŒâ€ŒØ¨Ø§Ù†Ú© Ø¯ÛŒÚ¯Ø± Ø¨ÛŒâ€ŒØµØ¯Ø§ Ù†ÛŒØ³Øª
    "test_dark_capabilities.py",             # Ú©Ø¯ÛŒ Ú©Ù‡ Ù‡Ø³Øª Ùˆ Ù†Ù…ÛŒâ€ŒØ¯ÙˆØ¯ â€” Ø§Ø¨Ø²Ø§Ø±Ø´ Ø¯Ø±ÙˆØº Ù†Ú¯ÙˆÛŒØ¯
    "test_lead_email_intake.py",             # ØªÙˆÙ„ÛŒØ¯Ú©Ù†Ù†Ø¯Ù‡Ù” Ú¯Ù…Ø´Ø¯Ù‡Ù” Ø­Ù„Ù‚Ù‡Ù” Ø§Ø±Ø²Ø´: Ø§ÛŒÙ…ÛŒÙ„ â†’ Ú©Ø§Ù†Ø¯ÛŒØ¯
    "test_lead_first_reply.py",              # Ù¾Ø§Ø³Ø®Ù Ø§ÙˆÙ„: Ù‡Ø±Ú¯Ø² Ù‚ÛŒÙ…ØªØŒ Ù‡Ø±Ú¯Ø² ØªØ¹Ù‡Ø¯ØŒ Ù‡Ø±Ú¯Ø² Ø§Ø±Ø³Ø§Ù„
    "test_lead_form_notification.py",        # Ø¯Ø±Ø²Ù Ø¯Ùˆ Ù…Ø§Ú˜ÙˆÙ„: Ø§Ø¹Ù„Ø§Ù†Ù ÙØ±Ù…Ù Ø³Ø§ÛŒØª
    "test_lead_inbound_consent.py",          # Ù…Ø±Ø²Ù Ø±Ø¶Ø§ÛŒØª Ù¾Ù‡Ù† Ø´Ø¯ â€” Ú¯Ø§Ø±Ø¯Ù Ø¯ÛŒÚ¯Ø±ÛŒ Ø´Ù„ Ù†Ø´ÙˆØ¯
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û± â€” Ù…Ú¯Ø§Ù¾Ø±Ø§Ù…Ù¾ØªÙ Ø¢Ø²Ø§Ø¯Ø³Ø§Ø²ÛŒ: Ù‚Ø§Ø¨Ù„ÛŒØªâ€ŒÙ‡Ø§ÛŒÛŒ Ú©Ù‡ Ø³Ø§Ø®ØªÙ‡ Ø¨ÙˆØ¯Ù†Ø¯
    # ÙˆÙ„ÛŒ Ù…Ø§Ù„Ú© Ù†Ù…ÛŒâ€ŒØªÙˆØ§Ù†Ø³Øª Ø¨Ù‡ Ø¢Ù†â€ŒÙ‡Ø§ Ø¨Ø±Ø³Ø¯. Ø«Ø¨Øª Ù…Ø±Ú©Ø²ÛŒ Ø§Ø³Øª Ú†ÙˆÙ† Ù„ÙÛŒÙ†â€ŒÙ‡Ø§
    # Ø­Ù‚ Ù†Ø¯Ø§Ø´ØªÙ†Ø¯ run_all Ø±Ø§ Ø¯Ø³Øª Ø¨Ø²Ù†Ù†Ø¯.
    "test_approval_actuator_panel.py",       # Û´Û³ ØªØ£ÛŒÛŒØ¯Ù âœ… Ù Ø¨ÛŒâ€ŒØ§Ú©Ø´Ù† Ø¨Ù‡ Ú©Ø§Ø±ØªÙ Ù…Ø§Ù„Ú© Ù…ÛŒâ€ŒØ±Ø³Ø¯
    "test_kill_seam_closer.py",              # Ø¯Ø±Ø²Ù /stop: Ù…Ø³ÛŒØ±Ù Ù¾ÙˆÙ„ Ù‡Ù… Ù…ÛŒâ€ŒØ§ÛŒØ³ØªØ¯
    "test_kill_seam_wire.py",                # Ù‡Ù…Ø§Ù† Ø¯Ø±Ø²ØŒ Ø§Ø² Ø³Ù…ØªÙ Ø³ÛŒÙ…â€ŒÚ©Ø´ÛŒ
    "test_debate_card_roundtrip.py",         # Ú©Ø§Ø±ØªÙ Ù…Ù†Ø§Ø¸Ø±Ù‡: ØªÙˆÚ©Ù† Ø¨Ù‡ jobÙ ÙˆØ§Ù‚Ø¹ÛŒ Ø¨Ø§ÛŒÙ†Ø¯ Ø´ÙˆØ¯
    "test_fence_ledger_owner_surface.py",    # ØºØ±Ø¨Ø§Ù„Ù ØªØ²Ø±ÛŒÙ‚: ÛŒØ§ÙØªÙ‡ Ø¨Ù‡ Ø³Ø·Ø­Ù Ù…Ø§Ù„Ú© Ø¨Ø±Ø³Ø¯
    # union Ø§Ø² Ù„ÙÛŒÙ†Ù Ù…ÙˆØ§Ø²ÛŒ (Ù…Ø§ÛŒÙ†ÛŒÙ†Ú¯/Ù¾ÙˆÙ„) â€” Ø§ÛŒÙ† Ù‡ÙØª Ø«Ø¨Øª Ø¯Ø± Ø¯Ø±Ø®ØªÙ Ø²Ù†Ø¯Ù‡ Ø¨ÙˆØ¯Ù†Ø¯
    # (Ù¾Ù†Ø¬ stage-Ø´Ø¯Ù‡ØŒ Ø¯Ùˆ Ù†Ù‡) Ùˆ deploy Ø¯Ø±Ø³Øª Ø­Ø§Ø¶Ø± Ù†Ø´Ø¯ Ø±ÙˆÛŒØ´Ø§Ù† ff Ø¨Ø²Ù†Ø¯. Ø«Ø¨Øª
    # Ø§ÙØ²Ø§ÛŒØ´ÛŒ Ø§Ø³Øª Ùˆ Ù‡Ø± Ù‡ÙØª ÙØ§ÛŒÙ„ Ø±ÙˆÛŒ Ø¯ÛŒØ³Ú©â€ŒØ§Ù†Ø¯ØŒ Ù¾Ø³ union Ù†Ù‡ Ø§Ù†ØªØ®Ø§Ø¨.
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û± (Ø´Ø¨) â€” Ø¨Ø§Ø²Ø³Ø§Ø²ÛŒÙ Ù…Ø§Ø´ÛŒÙ†Ù Ù„ÛŒØ¯. union Ø§Ø³Øª Ù†Ù‡ Ø§Ù†ØªØ®Ø§Ø¨:
    # Ù‡Ø± Ù¾Ù†Ø¬ ÙØ§ÛŒÙ„ Ø±ÙˆÛŒ Ø¯ÛŒØ³Ú© Ùˆ Ø³Ø¨Ø²Ù†Ø¯.
    "test_lead_suppression.py",              # Ù‚ÙÙ„Ù Ù‚Ø§Ù†ÙˆÙ†ÛŒÙ STOP â€” Spam ActØŒ Ùˆ transport Ù…Ø³Ù„Ø­ Ø§Ø³Øª
    "test_lead_suppression_wired.py",        # Ù‡Ù…Ø§Ù† Ù‚ÙÙ„ØŒ ÙˆÙ„ÛŒ Ø¯Ø± **Ø¯Ø±Ø²Ù‡Ø§**: Ø´Ù†ÛŒØ¯Ù†Ù ÙˆØ±ÙˆØ¯ÛŒ + ØªØ·Ø§Ø¨Ù‚Ù Ù†ÙˆÛŒØ³Ù†Ø¯Ù‡/Ø®ÙˆØ§Ù†Ù†Ø¯Ù‡
    "test_lead_property_extract.py",         # suburb/Ù…ØªØ±Ø§Ú˜ â€” Ø¨Ø¯ÙˆÙ†Ø´ Ù‡Ø± Ú©ÙˆØª A$0.00 Ø§Ø³Øª
    "test_lead_scorer_farsi.py",             # Ø§Ø³ØªØ¹Ù„Ø§Ù…Ù ÙØ§Ø±Ø³ÛŒ Ø¯ÛŒÚ¯Ø± ØµÙØ± Ù†Ù…ÛŒâ€ŒÚ¯ÛŒØ±Ø¯
    "test_lead_card.py",                     # Ú©Ø§Ø±ØªÙ Ù‚Ø§Ø¨Ù„Ùâ€ŒÙ„Ù…Ø³: tel: Ùˆ Ù†Ø§Ù…Ù Ù…Ø´ØªØ±ÛŒ
    "test_new_capability_cards.py",            # Ú©Ø§Ø±Øªâ€ŒÙ‡Ø§ÛŒ ØªØ§Ø²Ù‡ â€” Ù‚Ø§Ø¨Ù„ÛŒØªÛŒ Ú©Ù‡ Ø¯ÛŒØ¯Ù‡ Ù†Ø´ÙˆØ¯ ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø±Ø¯
    # 2026-08-05 — هفت سوییتِ موجِ «مغزِ کابین». همان تلهٔ مستندِ بالا دوباره:
    # ساخته شدند، سبز بودند، و در هیچ لیستی نبودند ⇒ هرگز نمی‌دویدند. شش‌تای
    # اول plain-asserts اند (هارنسِ خودشان + خروجیِ n/n) و هفتمی unittest؛
    # هر دو سبک با `python <file>` درست exit code می‌دهند، پس هر هفت در TESTS
    # می‌آیند نه PYTEST_TESTS. هر هفت قبل از ثبت جدا اجرا و سبز شدند
    # (9/9 · 14/14 · 12/12 · 6/6 · 7/7 · 9/9 · 6/6).
    "test_absence_is_not_emptiness.py",       # نبودِ داده = UNKNOWN، نه صفرِ جعلی
    "test_miniapp_vitals.py",                 # سه سنجهٔ ارزان + حلقه‌های کابین
    "test_miniapp_look_locked.py",            # قفلِ ظاهرِ دارک — رأیِ مالک، نه سلیقه
    "test_ops_action_crash_recovery.py",      # کلیدِ مسمومِ idempotency بعدِ کرش
    "test_proposal_decision.py",              # تأیید/ردِ مالک از وب‌اپ، بی‌بازنویسی
    "test_reach_probe.py",                    # دفترِ دسترسیِ PEP 669
    "test_write_invalidates_read_cache.py",   # «زدم و هیچ نشد»: کشِ ۳ث بعدِ نوشتن
         ]
# ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ Ø®Ø§Ø±Ø¬ Ø§Ø² _ops/tests/ (path tuyá»‡tÙ‚)
EXTRA_TESTS = [HERE.parents[1] / "07 - Knowledge" / "Time-Architecture" / "test_fusion_sim.py",
               HERE.parents[1] / "07 - Knowledge" / "school-memory" / "test_curriculum.py",
               # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ unified_control (Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡ = Ù‡Ø±Ú¯Ø² Ø§Ø¬Ø±Ø§ Ù†Ø´Ø¯Ù‡):
               HERE.parent / "unified_control" / "tests" / "test_snapshot_staleness.py",
               HERE.parent / "unified_control" / "tests" / "test_snapshot_linkage.py",
               # Û²Û°Û²Û¶-Û°Û·-Û³Û± â€” Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬Ù Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯Ù ØªÙ„Ú¯Ø±Ø§Ù… (ØªØ§ Ø§Ù…Ø±ÙˆØ² ØµØ¯Ø§Ú©Ù†Ù†Ø¯Ù‡â€Œ Ù†Ø¯Ø§Ø´Øª).
               HERE.parent / "telegram_contract" / "validate_contract.py"]

# Ø§ÛŒÙ† ÙØ§ÛŒÙ„â€ŒÙ‡Ø§ pytest-style Ù‡Ø³ØªÙ†Ø¯ (fixtureÙ‡Ø§ÛŒ monkeypatch/tmp_path) Ùˆ Ø§Ø¬Ø±Ø§ÛŒ Ù…Ø³ØªÙ‚ÛŒÙ…Ø´Ø§Ù†
# Ø³Ø¨Ø²Ù Ø¯Ø±ÙˆØºÛŒÙ† Ù…ÛŒâ€ŒØ¯Ù‡Ø¯. run_all Ø¨Ø§ÛŒØ¯ ÙˆØ§Ù‚Ø¹Ø§Ù‹ pytest Ø±Ø§ Ø§Ø¬Ø±Ø§ Ú©Ù†Ø¯.
PYTEST_TESTS = {
    "test_ziman_leg.py", "test_ziman_phase2.py",
    # 2026-07-16 (audit R-04): test_ziman_wiring/biology Ù¾ÛŒØ´â€ŒØªØ± Ø¯Ø± TESTS Ø¨ÙˆØ¯Ù†Ø¯ ÙˆÙ„ÛŒ Ù†Ù‡ Ø¯Ø± Ø§ÛŒÙ†
    # set â†’ run_all Ø¢Ù†â€ŒÙ‡Ø§ Ø±Ø§ direct-run Ù…ÛŒâ€ŒÚ©Ø±Ø¯ (Ø¨Ø¯ÙˆÙ†Ù __main__ â†’ ØµÙØ± assert â†’ green-lie:
    # exit 0 Ø¯Ø± Ø­Ø§Ù„ÛŒ Ú©Ù‡ Ø²ÛŒØ±Ù pytest ÙˆØ§Ù‚Ø¹Ø§Ù‹ Ø§Ø¬Ø±Ø§/Ø§Ø«Ø¨Ø§Øª Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯). Ù‡Ø± Ø¯Ùˆ ÙØ§ÛŒÙ„Ù pytest-style
    # (fixtureÙ monkeypatch/tmp_path) Ù‡Ø³ØªÙ†Ø¯Ø› Ø§ÛŒÙ†â€ŒØ¬Ø§ Ø«Ø¨Øª Ø´Ø¯Ù†Ø¯ ØªØ§ ÙˆØ§Ù‚Ø¹Ø§Ù‹ Ø§Ø¬Ø±Ø§ Ø´ÙˆÙ†Ø¯.
    "test_ziman_wiring.py", "test_ziman_biology.py",
    "test_cartographer_leg.py", "test_cartographer_wiring.py",
    "test_blocker_fixes_2026_07_22.py",   # pytest-native (monkeypatch fixtures)
    # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” Ù‡Ù…Ø§Ù† green-lieØŒ Ø¯ÙˆØ§Ø²Ø¯Ù‡ Ø±ÙˆØ² Ø¨Ø¹Ø¯. `test_synapse_sense.py`
    # pytest-style Ø§Ø³Øª (ØµÙØ± ØªØ§Ø¨Ø¹Ù `t_`ØŒ ØµÙØ± Ø±Ø§Ù†Ø±Ù `__main__`)ØŒ Ù¾Ø³ direct-run
    # ØµÙØ± assert Ù…ÛŒâ€ŒØ¯ÙˆØ¯ Ùˆ `exit 0` Ù…ÛŒâ€ŒØ¯Ù‡Ø¯. Ø²ÛŒØ±Ù pytest **Û²Û° ØªØ³ØªØŒ Ù‡Ù…Ù‡ Ø³Ø¨Ø²** â€”
    # ÛŒØ¹Ù†ÛŒ Ø¨ÛŒØ³Øª ØªØ³ØªÙ Ø³Ø§Ù„Ù… Ø¯Ø± Ø³ÙˆØ¦ÛŒØª Ø´Ù…Ø±Ø¯Ù‡ Ù…ÛŒâ€ŒØ´Ø¯Ù†Ø¯ Ùˆ Ù‡Ø±Ú¯Ø² Ø§Ø¬Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ´Ø¯Ù†Ø¯.
    #
    # Ø±ÙˆØ´Ù Ù¾ÛŒØ¯Ø§ Ø´Ø¯Ù†Ø´ Ù…Ù‡Ù…â€ŒØªØ± Ø§Ø² Ø®ÙˆØ¯Ø´ Ø§Ø³Øª: Ú†Ú©Ù **Ø³Ø§Ø®ØªØ§Ø±ÛŒ** (ÙˆØ¬ÙˆØ¯Ù `__main__`) Ø§ÛŒÙ†
    # Ø±Ø§ Ù†Ú¯Ø±ÙØª Ùˆ ÛµÛ° Ú©Ø§Ø°Ø¨ Ø¯Ø§Ø¯. ØªÙ†Ù‡Ø§ Ú†ÛŒØ²ÛŒ Ú©Ù‡ Ú¯Ø±ÙØªØŒ Ø§Ø¬Ø±Ø§ÛŒ **ØªØ¬Ø±Ø¨ÛŒÙ** Ù‡Ø± Û³Û¶Û¶ ÙØ§ÛŒÙ„Ù
    # ØºÛŒØ±pytest Ùˆ Ù†Ú¯Ù‡â€ŒØ¯Ø§Ø´ØªÙ†Ù Ø¢Ù†â€ŒÙ‡Ø§ÛŒÛŒ Ø¨ÙˆØ¯ Ú©Ù‡ `exit 0` Ø¨Ø§ **ØµÙØ± Ø®Ø±ÙˆØ¬ÛŒ** Ù…ÛŒâ€ŒØ¯Ù‡Ù†Ø¯.
    # Ø§Ú¯Ø± Ø±ÙˆØ²ÛŒ Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ø´Ú© Ú©Ø±Ø¯ÛŒØŒ Ù‡Ù…Ø§Ù† Ø±Ø§ Ø§Ø¬Ø±Ø§ Ú©Ù† Ù†Ù‡ grep.
    "test_synapse_sense.py",
    # Û²Û°Û²Û¶-Û°Û¸-Û°Û± â€” Ø³ÙˆÙ…ÛŒÙ† ØªÚ©Ø±Ø§Ø±Ù Ù‡Ù…Ø§Ù† green-lieØŒ Ø§ÛŒÙ† Ø¨Ø§Ø± Mining (Ø±Ø£ÛŒÙ Ù…Ø§Ù„Ú©: Ú¯Ø²ÛŒÙ†Ù‡Ù” Ø§Ù„Ù).
    # `test_mining_wiring.py` Ø¯Ø± `TESTS` Ø¨ÙˆØ¯ ÙˆÙ„ÛŒ Ù†Ù‡ Ø§ÛŒÙ†â€ŒØ¬Ø§ â†’ direct-runØŒ ØµÙØ± assertØŒ
    # `exit 0`. Ø²ÛŒØ±Ù pytest ÙˆØ§Ù‚Ø¹ÛŒØªØ´ **Û¶ Ù‚Ø±Ù…Ø² / Û´ Ø³Ø¨Ø²** Ø§Ø³Øª.
    #
    # Ù†Ú©ØªÙ‡Ù” ØªÙ„Ø®: Ù…Ù…ÛŒØ²ÛŒÙ R-04 (Û°Û·-Û±Û¶) Ù‡Ù…ÛŒÙ† ÙØ§ÛŒÙ„ Ø±Ø§ Â«phantomÙ Ø¹Ù…Ø¯Ø§Ù‹ Ú©Ù†Ø§Ø±Ú¯Ø°Ø§Ø´ØªÙ‡Â» Ø«Ø¨Øª
    # Ú©Ø±Ø¯Ù‡ Ø¨ÙˆØ¯ (Ú©Ø§Ù…Ù†ØªÙ Ø¯Ø§Ø®Ù„Ù `TESTS`)ØŒ ÙˆÙ„ÛŒ Ø¬Ø§Ø±ÙˆÛŒ ÛŒØªÛŒÙ…â€ŒÙ‡Ø§ (Û°Û·-Û²Û°) Ø¢Ù† Ø±Ø§ Ø¨Ù‡â€ŒØ¹Ù†ÙˆØ§Ù†
    # Â«Ø³Ø¨Ø²Ù Ø±ÙˆÛŒâ€ŒØ¯ÛŒØ³Ú©Â» Ø¨Ø±Ú¯Ø±Ø¯Ø§Ù†Ø¯ â€” Ú†ÙˆÙ† Ù…Ø¹ÛŒØ§Ø±Ù Ø³Ø¨Ø²Ø¨ÙˆØ¯Ù† Ø±Ø§ Ø§Ø² Ù‡Ù…Ø§Ù† direct-runÙ Ù…Ø¹ÛŒÙˆØ¨
    # Ù¾Ø±Ø³ÛŒØ¯. ÛŒØ¹Ù†ÛŒ Ø¯Ø±ÙˆØºÙ Ø³Ø¨Ø² Ø¨Ø§Ø¹Ø«Ù Ø«Ø¨ØªÙ Ø®ÙˆØ¯Ø´ Ø´Ø¯. Ø§Ú¯Ø± Ø¬Ø§Ø±ÙˆÛŒ Ø¨Ø¹Ø¯ÛŒ Ù‡Ù… Ù‡Ù…Ø§Ù† Ø±Ø§ Ø¨Ù¾Ø±Ø³Ø¯ØŒ
    # Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ø¨Ø±Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø¯Ø› Ù…Ø¹ÛŒØ§Ø± Ø¨Ø§ÛŒØ¯ pytest Ø¨Ø§Ø´Ø¯ Ù†Ù‡ exit code Ù Ø§Ø¬Ø±Ø§ÛŒ Ù…Ø³ØªÙ‚ÛŒÙ….
    #
    # Ø«Ø¨Øª Ø§ÛŒÙ†â€ŒØ¬Ø§ Ø³ÙˆÛŒÛŒØª Ø±Ø§ **ØµØ§Ø¯Ù‚Ø§Ù†Ù‡ Ù‚Ø±Ù…Ø²** Ù…ÛŒâ€ŒÚ©Ù†Ø¯: Ûµ Ù‚Ø±Ù…Ø² `AttributeError` Ø§Ø³Øª
    # (`wiring.make_mining_leg`/`mining_beat` ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø±Ù†Ø¯ â€” Mining Ø¨Ø§ Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯Ù
    # `_BUSINESS_LEGS_SPEC` Ø³Ø§Ø®ØªÙ‡ Ø´Ø¯ØŒ Ù†Ù‡ Ø§Ù„Ú¯ÙˆÛŒ Ú©Ø§Ø±Ø®Ø§Ù†Ù‡â€ŒØ§ÛŒ) Ùˆ Û± Ù‚Ø±Ù…Ø²Ù ÙˆØ§Ù‚Ø¹ÛŒÙ Ø±Ù†Ø¯Ø±
    # (ØªÙ„Ù…ØªØ±ÛŒÙ `mining_os` Ø¨Ù‡ Ø¯Ø§ÛŒØ¬Ø³Øª ÙˆØµÙ„ Ù†Ø´Ø¯Ù‡). ØªÙØµÛŒÙ„ Ùˆ Ø¯Ùˆ ØªØµÙ…ÛŒÙ…Ù Ø¨Ø§Ù‚ÛŒâ€ŒÙ…Ø§Ù†Ø¯Ù‡:
    # `00 - Inbox/AGENT_QUESTIONS.md` â€” ÙˆØ±ÙˆØ¯ÛŒÙ Û²Û°Û²Û¶-Û°Û¸-Û°Û±.
    "test_mining_wiring.py",
}

# Û²Û°Û²Û¶-Û°Û·-Û³Û° â€” Â«Ù‚Ø±Ù…Ø²Ù Ú©Ø§Ø°Ø¨Ù Û±Û²Û°Â». Ù¾Ø§Ø³Ù Ø§ÙˆÙ„Ù Ø³ÙˆÛŒÛŒØª Ø¨Ø¯ÙˆÙ†Ù capture Ø§Ø¬Ø±Ø§ Ù…ÛŒâ€ŒØ´Ø¯ØŒ Ù¾Ø³ Ù‡Ø±
# ~Û³Û¶Û¶ ÙØ±Ø²Ù†Ø¯ Ú©Ù†Ø³ÙˆÙ„Ù Ù…Ø´ØªØ±Ú©Ù ÙˆØ§Ù„Ø¯ Ø±Ø§ Ø§Ø±Ø« Ù…ÛŒâ€ŒØ¨Ø±Ø¯Ù†Ø¯. Ø²ÛŒØ±Ù Ø¨Ø§Ø±ØŒ ÙØ±Ø²Ù†Ø¯ÛŒ Ú©Ù‡ Ø³Ø§Ù„Ù… Ø§Ø³Øª Ùˆ
# `exit 0` Ù…ÛŒâ€ŒØ¯Ù‡Ø¯ Ø¯Ø± **flushÙ Ù¾Ø§ÛŒØ§Ù†ÛŒÙ Ù…ÙØ³Ø±** Ø´Ú©Ø³Øª Ù…ÛŒâ€ŒØ®ÙˆØ±Ø¯ Ùˆ Û±Û²Û° Ø¨Ø±Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø§Ù†Ø¯Ø› Ø±Ø§Ù†Ø±
# Û±Û²Û° Ø±Ø§ Ø¹ÛŒÙ†Ø§Ù‹ Ù…Ø«Ù„Ù AssertionError Ù…ÛŒâ€ŒØ´Ù…Ø±Ø¯. Ø´ÙˆØ§Ù‡Ø¯Ù Ø±ÙˆÛŒ Ø¯ÛŒØ³Ú© Ø¯Ø± `_flaky`:
#     Û³Û³ Ã— exit(1)=120 exit(2)=0   â† Û³Û³ ØªØ³ØªÙ Ø³Ø§Ù„Ù… Ú©Ù‡ Ø¯Ø± ÛŒÚ© Ø§Ø¬Ø±Ø§ Ù‚Ø±Ù…Ø² Ø´Ù…Ø±Ø¯Ù‡ Ø´Ø¯Ù†Ø¯
#      Û¶ Ã— exit(1)=1   exit(2)=1   â† Ù‚Ø±Ù…Ø²Ù ÙˆØ§Ù‚Ø¹ÛŒ Ùˆ Ù¾Ø§ÛŒØ¯Ø§Ø±
#      Û² Ã— exit(1)=1   exit(2)=0   â† Ù„Ø±Ø²Ø´Ù ÙˆØ§Ù‚Ø¹ÛŒ (Ø­Ú©Ù…Ù ØªØ³Øª Ø¨ÙˆØ¯ØŒ Ù†Ù‡ Ù…Ø­ÛŒØ·)
# Ùˆ Ù‡Ø± `failed` ØºÛŒØ±Ø®Ø§Ù„ÛŒ `revoke_capability()` Ø±Ø§ ØµØ¯Ø§ Ù…ÛŒâ€ŒØ²Ù†Ø¯.
#
# âš ï¸ Û±Û²Û° **Ù…Ø¨Ù‡Ù…** Ø§Ø³ØªØŒ Ù†Ù‡ Ø¨ÛŒâ€ŒØ¶Ø±Ø±. ØªØµØ­ÛŒØ­Ù Û²Û°Û²Û¶-Û°Û·-Û³Û° (Ø¨Ø§Ø²Ø¨ÛŒÙ†ÛŒÙ Ù…ØªØ®Ø§ØµÙ…ØŒ Ø§Ø«Ø¨Ø§ØªÙ
# ØªØ¬Ø±Ø¨ÛŒ): ÙˆÙ‚ØªÛŒ `Py_FinalizeEx()` Ø´Ú©Ø³Øª Ù…ÛŒâ€ŒØ®ÙˆØ±Ø¯ØŒ Ù…ÙØ³Ø± exitcode Ø±Ø§ Ø¨Ø§ Û±Û²Û°
# **Ø¨Ø§Ø²Ù†ÙˆÛŒØ³ÛŒ** Ù…ÛŒâ€ŒÚ©Ù†Ø¯ â€” ÛŒØ¹Ù†ÛŒ Ø­Ú©Ù…Ù ÙˆØ§Ù‚Ø¹ÛŒ Ø±Ø§ Ø¯ÙˆØ± Ù…ÛŒâ€ŒØ±ÛŒØ²Ø¯ØŒ Ù†Ù‡ Ø§ÛŒÙ†Ú©Ù‡ Ø¬Ø§ÛŒ Ø­Ú©Ù…Ù ØºØ§ÛŒØ¨
# Ø¨Ù†Ø´ÛŒÙ†Ø¯. Ù¾Ø±ÙˆØ¨Ù Ú†Ù‡Ø§Ø±Ø­Ø§Ù„ØªÙ‡ Ø²ÛŒØ±Ù sinkÙ Ø´Ú©Ø³ØªÙ‡: exit(0)â†’120 Â· exit(1)â†’120 Â·
# raise AssertionErrorâ†’120 Â· exit(3)â†’120. Ù¾Ø³ Â«Û±Û²Û° Ø¯ÛŒØ¯Ù… â‡’ ØªØ³Øª Ø³Ø§Ù„Ù… Ø¨ÙˆØ¯Â» ØºÙ„Ø· Ø§Ø³ØªØ›
# ÛŒÚ© AssertionErrorÙ ÙˆØ§Ù‚Ø¹ÛŒ Ù‡Ù… Ù‡Ù…ÛŒÙ† Ú©Ø¯ Ø±Ø§ Ù…ÛŒâ€ŒØ¯Ù‡Ø¯.
# Ù†ØªÛŒØ¬Ù‡Ù” Ø¹Ù…Ù„ÛŒ: Ø§Ø² Ø§ÛŒÙ† Ú©Ø¯ **Ù†Ù…ÛŒâ€ŒØªÙˆØ§Ù†** Ø¨Ù‡ Ø³Ø§Ù„Ù…â€ŒØ¨ÙˆØ¯Ù†Ù ØªØ³Øª Ø±Ø³ÛŒØ¯. ØªØ´Ø®ÛŒØµÙ Ø¯Ø±Ø³Øª Ø¨Ø§ÛŒØ¯
# stdout/stderr Ù Ù¾Ø§Ø³Ù Ø§ÙˆÙ„ Ø±Ø§ Ø¨Ø±Ø§ÛŒ Ø´Ø§Ù‡Ø¯Ù Ø´Ú©Ø³Øª (Traceback/AssertionError/FAILED)
# Ø¨Ø³Ù†Ø¬Ø¯ â€” Ú©Ù‡ hunkÙ capture Ù Ù‡Ù…ÛŒÙ† Ú©Ø§Ù…ÛŒØª Ø¢Ù† Ø±Ø§ Ø¯Ø± Ø¯Ø³ØªØ±Ø³ Ú¯Ø°Ø§Ø´Øª.
INFRA_EXIT_CODES = frozenset({120})   # Ú©Ø¯Ù Ù…ÙØ³Ø± â€” **Ù…Ø¨Ù‡Ù…**Ø› Ø¨Ù‡â€ŒØªÙ†Ù‡Ø§ÛŒÛŒ Ø­Ú©Ù… Ù†ÛŒØ³Øª


def is_infra_false_red(first_rc: int, retry_rc: int) -> bool:
    """**ÙÙ‚Ø· Ø¨Ø±Ú†Ø³Ø¨â€ŒÚ¯Ø°Ø§Ø±ÛŒÙ ØªØ´Ø®ÛŒØµÛŒ â€” Ù‡ÛŒÚ† ØªØµÙ…ÛŒÙ…Ù scoring Ø¨Ù‡ Ø§ÛŒÙ† ØªØ§Ø¨Ø¹ Ø¨Ù†Ø¯ Ù†ÛŒØ³Øª.**


    True ÛŒØ¹Ù†ÛŒ Â«Ø´Ø§ÛŒØ¯ artifactÙ Ú©Ù†Ø³ÙˆÙ„ Ø¨Ø§Ø´Ø¯Â»ØŒ Ù†Ù‡ Â«ØªØ³Øª Ø³Ø§Ù„Ù… Ø§Ø³ØªÂ». Ù¾Ø§Ú©â€ŒÚ©Ø±Ø¯Ù†Ù Ø¨Ø±Ú†Ø³Ø¨ Ø§Ø²
    `failed` Ø¨Ø± Ù¾Ø§ÛŒÙ‡Ù” Ø§ÛŒÙ† ØªØ§Ø¨Ø¹ Ø¯Ø± Û²Û°Û²Û¶-Û°Û·-Û³Û° **Ø¹Ù…Ø¯Ø§Ù‹ ØºÛŒØ±ÙØ¹Ø§Ù„ Ø´Ø¯**: Ø¨Ø§ retryÙ Ø³Ø¨Ø²ØŒ
    Ø¨Ú†Ù‡â€ŒØ§ÛŒ Ú©Ù‡ AssertionError Ø¯Ø§Ø¯Ù‡ Ø¨ÙˆØ¯ Ùˆ flushØ´ Ø´Ú©Ø³ØªÙ‡ Ø¨ÙˆØ¯ Ø¨Ù‡â€ŒØºÙ„Ø· PASS/MARK Ù…ÛŒâ€ŒÚ¯Ø±ÙØª
    â‡’ fail-OPEN Ø±ÙˆÛŒ Ú¯ÛŒØªÙ capability/Ù¾ÙˆÙ„. Ø±Ø§Ù†Ø± fail-closed Ù…ÛŒâ€ŒÙ…Ø§Ù†ÙŽØ¯.
    """
    return retry_rc == 0 and first_rc in INFRA_EXIT_CODES


# â”€â”€ Ú¯Ø§Ø±Ø¯Ù Ø­Ø§Ù„ØªÙ Ø²Ù†Ø¯Ù‡ Ø¨Ø±Ø§ÛŒ **Ù‡Ø±** ØªØ³ØªØŒ Ù†Ù‡ ÙÙ‚Ø· runnerÙ Ø§ÛŒØ²ÙˆÙ„Ù‡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ÛŒØ§ÙØªÙ‡Ù” Ù…Ù…ÛŒØ²ÛŒÙ Û²Û°Û²Û¶-Û°Û¸-Û°Û³: Ø§Ø² ÛµÛ´Û¸ ÙØ§ÛŒÙ„Ù ØªØ³ØªØŒ Û¸Û¸ ØªØ§ `harness` Ø±Ø§ import Ù†Ù…ÛŒâ€ŒÚ©Ù†Ù†Ø¯ â€”
# Ùˆ `harness.setup()` ØªÙ†Ù‡Ø§ Ø¬Ø§ÛŒÛŒ Ø§Ø³Øª Ú©Ù‡ `live_state_guard` Ø±Ø§ Ù…Ø³Ù„Ø­ Ù…ÛŒâ€ŒÚ©Ø±Ø¯. Ù¾ÙˆØ´Ø´Ù
# Ø¢Ù† Ø´Ú©Ø§Ù Ø§Ø² Ù‚Ø¨Ù„ Ø³Ø§Ø®ØªÙ‡ Ø´Ø¯Ù‡ Ø¨ÙˆØ¯ (`_isolation_boot/sitecustomize.py`) ÙˆÙ„ÛŒ ÙÙ‚Ø·
# `check_state_isolation.py` Ø¢Ù† Ø±Ø§ Ø±ÙˆÛŒ PYTHONPATH Ù…ÛŒâ€ŒÚ¯Ø°Ø§Ø´Øª. ÛŒØ¹Ù†ÛŒ Ø§Ø¬Ø±Ø§ÛŒ **Ø±ÙˆØ²Ù…Ø±Ù‡Ù”**
# Ø³ÙˆÛŒÛŒØª Û¸Û¸ ÙØ§ÛŒÙ„ Ø±Ø§ Ø¨ÛŒâ€ŒÚ¯Ø§Ø±Ø¯ Ù…ÛŒâ€ŒØ¯ÙˆØ§Ù†Ø¯ â€” Ùˆ Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ Ø§Ø² Ù‡Ù…Ø§Ù†â€ŒØ¬Ø§ Ø¨ÙˆØ¯ Ú©Ù‡ ÛŒÚ© ØªØ³ØªÙ
# Ø«Ø¨Øªâ€ŒÙ†Ø´Ø¯Ù‡ Ø§Ø³Ù„Ø§ØªÙ Ø§Ø±Ø³Ø§Ù„Ù ÙˆØ§Ù‚Ø¹ÛŒÙ Ù„ÛŒØ¯ Ø±Ø§ Ø³ÙˆØ²Ø§Ù†Ø¯.
#
# Ú¯Ø§Ø±Ø¯Ù **Ø´Ø¨Ú©Ù‡** Ø¹Ù…Ø¯Ø§Ù‹ Ø§ÛŒÙ†â€ŒØ¬Ø§ Ù…Ø³Ù„Ø­ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯: `test_llm_routing_smoke` Ø¹Ù…Ø¯Ø§Ù‹ ØªÙ…Ø§Ø³Ù
# Ø²Ù†Ø¯Ù‡ Ù…ÛŒâ€ŒØ²Ù†Ø¯ Ùˆ Ø¨Ø³ØªÙ†Ø´ Ø§ÛŒÙ†â€ŒØ¬Ø§ ÛŒÚ© Ù‚Ø±Ù…Ø²Ù Ú©Ø§Ø°Ø¨Ù Ù‡Ù…ÛŒØ´Ú¯ÛŒ Ù…ÛŒâ€ŒØ³Ø§Ø²Ø¯. Ø¢Ù† ÛŒÚ©ÛŒ Ù…Ø§Ù„Ù runnerÙ
# Ø§ÛŒØ²ÙˆÙ„Ù‡ Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ â€” Ù‡Ù…Ø§Ù† ØªÙÚ©ÛŒÚ©ÛŒ Ú©Ù‡ Ø®ÙˆØ¯Ù harness Ù…Ø³ØªÙ†Ø¯Ø´ Ú©Ø±Ø¯Ù‡.
_BOOT_DIR = HERE / "_isolation_boot"


def _guarded_env():
    """envÙ ÙØ±Ø²Ù†Ø¯ Ø¨Ø§ ØªØ±ÛŒÙ¾â€ŒÙˆØ§ÛŒØ±Ù state Ù Ø²Ù†Ø¯Ù‡. Ù†Ø¨ÙˆØ¯Ù boot-dir â‡’ Ø±ÙØªØ§Ø±Ù Ù‚Ø¨Ù„ÛŒ."""
    env = dict(os.environ)
    if not _BOOT_DIR.is_dir():
        return env
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_BOOT_DIR)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env.setdefault("OCTOPUS_TEST_LIVE_STATE_GUARD", "block")
    return env


if __name__ == "__main__":
    failed = []
    for t in TESTS + EXTRA_TESTS:
        p = HERE / t          # Ù†Ø§Ù…â€ŒÙ‡Ø§ÛŒ Ù†Ø³Ø¨ÛŒÙ TESTS â†’ _ops/testsØ› EXTRA_TESTSÙ absolute Ø¯Ø³Øªâ€ŒÙ†Ø®ÙˆØ±Ø¯Ù‡ Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯
        label = p.name
        print(f"\nâ”€â”€ {label} " + "â”€" * (60 - len(label)))
        cmd = ([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(p)]
               if label in PYTEST_TESTS else
               [sys.executable, "-X", "utf8", str(p)])
        # capture Ø¯Ø± **Ù¾Ø§Ø³Ù Ø§ÙˆÙ„** Ù‡Ù… Ù„Ø§Ø²Ù… Ø§Ø³Øª: Ù‡Ø± ÙØ±Ø²Ù†Ø¯ Ø¨Ù‡ Ù„ÙˆÙ„Ù‡Ù” Ø§Ø®ØªØµØ§ØµÛŒÙ Ø®ÙˆØ¯Ø´
        # flush Ù…ÛŒâ€ŒÚ©Ù†Ø¯ØŒ Ù†Ù‡ Ø¨Ù‡ Ú©Ù†Ø³ÙˆÙ„Ù Ù…Ø´ØªØ±Ú©Ù ÙˆØ§Ù„Ø¯ â€” Ø±ÛŒØ´Ù‡Ù” Û±Û²Û° Ù‡Ù…ÛŒÙ† Ø§Ø´ØªØ±Ø§Ú© Ø¨ÙˆØ¯.
        # ÙˆØ§Ù„Ø¯ Ø®Ø±ÙˆØ¬ÛŒ Ø±Ø§ Ø±ÙˆÛŒ Ù‡Ù…Ø§Ù† Ø¬Ø±ÛŒØ§Ù†Ù Ø§ØµÙ„ÛŒ Ø¨Ø§Ø²Ù¾Ø®Ø´ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ ØªØ§ Ù„Ø§Ú¯ Ú©Ù…â€Œ Ù†Ø´ÙˆØ¯.
        r = subprocess.run(cmd, cwd=str(p.parent), timeout=300,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=_guarded_env())
        if r.stdout:
            sys.stdout.write(r.stdout)
        if r.stderr:
            sys.stderr.write(r.stderr)   # unittest Ù¾ÛŒØ´Ø±ÙØªØ´ Ø±Ø§ Ø±ÙˆÛŒ stderr Ù…ÛŒâ€ŒÙ†ÙˆÛŒØ³Ø¯
        sys.stdout.flush()
        sys.stderr.flush()
        if r.returncode != 0:
            failed.append(label)   # Ù¾ÛŒØ´â€ŒÙØ±Ø¶Ù fail-closedØ› ÙÙ‚Ø· artifactÙ Ù…Ø­ÛŒØ· Ù¾Ø§Ú©Ø´ Ù…ÛŒâ€ŒÚ©Ù†Ø¯
            # Û²Û°Û²Û¶-Û°Û·-Û²Û¸ â€” ØªØ´Ø®ÛŒØµÙ Ù„Ø±Ø²Ø´. Ø§Ù„Ú¯ÙˆÛŒ Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡: ~Û´Û°Ùª Ø§Ø¬Ø±Ø§Ù‡Ø§ **ÛŒÚ©** ØªØ³ØªÙ
            # Ù…ØªÙØ§ÙˆØª Ù‚Ø±Ù…Ø² Ù…ÛŒâ€ŒØ´ÙˆØ¯ Ú©Ù‡ ØªÙ†Ù‡Ø§ Ø§Ø¬Ø±Ø§ Ø´ÙˆØ¯ Ø³Ø¨Ø² Ø§Ø³Øª. Ú†Ù‡Ø§Ø± ÙØ±Ø¶ÛŒÙ‡ (Ø§Ø±Ú¯Ø§Ù†ÛŒØ³Ù…Ù
            # Ø²Ù†Ø¯Ù‡ØŒ Ù¾Ø±ÙˆØ³Ù‡Ù” Ù…Ø¹Ù„Ù‚ØŒ Ù‚ÙÙ„Ù Û³Ø«Ø§Ù†ÛŒÙ‡â€ŒØ§ÛŒØŒ Ø¨Ø§Ø±) Ù‡ÛŒÚ†â€ŒÚ©Ø¯Ø§Ù… Ø§Ø«Ø¨Ø§Øª Ù†Ø´Ø¯ â€” Ú†ÙˆÙ†
            # ØªÙ†Ù‡Ø§ Ú†ÛŒØ²ÛŒ Ú©Ù‡ Ø§Ø² Ù‡Ø± Ø§Ø¬Ø±Ø§ Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ **Ù†Ø§Ù…Ù ØªØ³Øª** Ø§Ø³ØªØŒ Ù†Ù‡ Ø´ÙˆØ§Ù‡Ø¯Ø´.
            #
            # Ù¾Ø³ Ø¨Ù‡â€ŒØ¬Ø§ÛŒ ÙØ±Ø¶ÛŒÙ‡Ù” Ù¾Ù†Ø¬Ù…: Ù‡Ù…Ø§Ù† ØªØ³Øª Ø¨Ù„Ø§ÙØ§ØµÙ„Ù‡ Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ùˆ **Ø¨Ø§ Ø®Ø±ÙˆØ¬ÛŒÙ
            # Ú©Ø§Ù…Ù„** Ø§Ø¬Ø±Ø§ Ù…ÛŒâ€ŒØ´ÙˆØ¯. Ø§Ú¯Ø± Ø¨Ø§Ø±Ù Ø¯ÙˆÙ… Ø³Ø¨Ø² Ø´Ø¯ØŒ Ù„Ø±Ø²Ø´ ØªØ£ÛŒÛŒØ¯ Ù…ÛŒâ€ŒØ´ÙˆØ¯ Ùˆ
            # Ø®Ø±ÙˆØ¬ÛŒÙ Ù‚Ø±Ù…Ø² Ø±ÙˆÛŒ Ø¯ÛŒØ³Ú© Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ ØªØ§ Ø¯ÙØ¹Ù‡Ù” Ø¨Ø¹Ø¯ Ø­Ø¯Ø³ Ù†Ø²Ù†ÛŒÙ….
            try:
                _d = HERE / "_flaky"
                _d.mkdir(exist_ok=True)
                _r2 = subprocess.run(cmd, cwd=str(p.parent), timeout=300,
                                     capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", env=_guarded_env())
                _tag = "Ø³Ø¨Ø²-Ø¨Ø§Ø±Ù-Ø¯ÙˆÙ…" if _r2.returncode == 0 else "Ù‚Ø±Ù…Ø²Ù-Ù¾Ø§ÛŒØ¯Ø§Ø±"
                if is_infra_false_red(r.returncode, _r2.returncode):
                    # Û²Û°Û²Û¶-Û°Û·-Û³Û° â€” Ù¾Ø§Ú©â€ŒÚ©Ø±Ø¯Ù†Ù Ø¨Ø±Ú†Ø³Ø¨ **Ø¹Ù…Ø¯Ø§Ù‹ ØºÛŒØ±ÙØ¹Ø§Ù„ Ø´Ø¯** (Ø¨Ø§Ø²Ø¨ÛŒÙ†ÛŒÙ Ù…ØªØ®Ø§ØµÙ…).
                    # ÙØ±Ø¶Ù Â«Û±Û²Û° Ù‡Ø±Ú¯Ø² Ø­Ú©Ù…Ù ØªØ³Øª Ù†ÛŒØ³ØªÂ» ØºÙ„Ø· Ø§Ø³Øª: Ø§Ú¯Ø± Py_FinalizeEx Ø´Ú©Ø³Øª
                    # Ø¨Ø®ÙˆØ±Ø¯ØŒ Ù…ÙØ³Ø± exitcode Ø±Ø§ Ø¨Ø§ Û±Û²Û° **Ø¨Ø§Ø²Ù†ÙˆÛŒØ³ÛŒ** Ù…ÛŒâ€ŒÚ©Ù†Ø¯ â€” Ù¾Ø³ exit(1)
                    # Ùˆ Ø­ØªÛŒ AssertionError Ù‡Ù… Û±Û²Û° Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯. Ø§Ø«Ø¨Ø§ØªÙ end-to-end: Ø¨Ú†Ù‡â€ŒØ§ÛŒ
                    # Ú©Ù‡ AssertionError Ù…ÛŒâ€ŒØ¯Ù‡Ø¯ Ùˆ flushØ´ Ù…ÛŒâ€ŒØ´Ú©Ù†Ø¯ØŒ Ø¨Ø§ retryÙ Ø³Ø¨Ø² Ø¨Ù‡â€ŒØºÙ„Ø·
                    # MARK Ù…ÛŒâ€ŒÚ¯Ø±ÙØª â‡’ **fail-OPEN Ø±ÙˆÛŒ Ú¯ÛŒØªÙ Ù¾ÙˆÙ„** (Ø¨Ø¯ØªØ± Ø§Ø² Ø¨Ø§Ú¯ÛŒ Ú©Ù‡
                    # Ù…ÛŒâ€ŒØ®ÙˆØ§Ø³Øª Ø¨Ø¨Ù†Ø¯Ø¯). ØªØ§ ØªØµÙ…ÛŒÙ…Ù Ù…Ø§Ù„Ú©: ÙÙ‚Ø· Ù…Ø´Ø§Ù‡Ø¯Ù‡ Ø«Ø¨Øª Ù…ÛŒâ€ŒØ´ÙˆØ¯ Ùˆ Ø¨Ø±Ú†Ø³Ø¨
                    # Ø¯Ø± failed Ù…ÛŒâ€ŒÙ…Ø§Ù†Ø¯ (fail-closed). Ø±ÙØ¹Ù Ø¯Ø±Ø³Øª = Ø³Ù†Ø¬Ø´Ù stdout/stderr
                    # Ù Ù¾Ø§Ø³Ù Ø§ÙˆÙ„ Ø¨Ø±Ø§ÛŒ Ø´Ø§Ù‡Ø¯Ù Ø´Ú©Ø³ØªØŒ Ú©Ù‡ Ø­Ø§Ù„Ø§ capture Ù…ÛŒâ€ŒØ´ÙˆØ¯.
                    _tag += (f" Â· Ù…Ø´Ú©ÙˆÚ© Ø¨Ù‡ artifactÙ Ú©Ù†Ø³ÙˆÙ„ (exit {r.returncode}) â€” "
                             "Ø¨Ø±Ú†Ø³Ø¨ Ù†Ú¯Ù‡ Ø¯Ø§Ø´ØªÙ‡ Ø´Ø¯ (fail-closed)")
                (_d / f"{label}.txt").write_text(
                    f"# {label} Â· {_tag}\n"
                    f"# exit(1)={r.returncode} exit(2)={_r2.returncode}\n\n"
                    f"--- stdout ---\n{_r2.stdout}\n"
                    f"--- stderr ---\n{_r2.stderr}",
                    encoding="utf-8")
                print(f"   â†» Ø§Ø¬Ø±Ø§ÛŒ Ø¯ÙˆÙ…: {_tag} â†’ tests/_flaky/{label}.txt")
            except Exception as _e:  # noqa: BLE001 â€” ØªØ´Ø®ÛŒØµ Ù‡Ø±Ú¯Ø² Ø³ÙˆÛŒÛŒØª Ø±Ø§ Ù†Ù…ÛŒâ€ŒÚ©Ø´Ø¯
                print(f"   â†» Ø«Ø¨ØªÙ Ù„Ø±Ø²Ø´ Ù†Ø´Ø¯: {type(_e).__name__}")
    print("\n" + "=" * 66)

    # A3: markerÙ capability ÙÙ‚Ø· Ø¨Ø§ Ø§Ø¬Ø±Ø§ÛŒ Ø³Ø¨Ø²Ù Ú©Ø§Ù…Ù„Ù Ø³ÙˆØ¦ÛŒØª Ù†ÙˆØ´ØªÙ‡ Ù…ÛŒâ€ŒØ´ÙˆØ¯ (Ø¨Ø§ fingerprintÙ Ú©Ø¯Ù Ù¾ÙˆÙ„)Ø›
    # Ù‡Ø± Ø´Ú©Ø³Øª revokeØ´ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ (fail-closed). ØªÙ†Ù‡Ø§ ÛŒÚ©ÛŒ Ø§Ø² Ø³Ù‡ Ø´Ø±Ø·Ù Ú¯ÛŒØª Ø§Ø³Øª â€” Ø¨Ù‡â€ŒØªÙ†Ù‡Ø§ÛŒÛŒ Ù‡ÛŒÚ† Ø¨Ø§Ø² Ù†Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
    # markerÙ capability Ø¯Ø± Ù‡Ù…Ø§Ù† Ø¯Ø±Ø®ØªÛŒ Ù†ÙˆØ´ØªÙ‡ Ù…ÛŒâ€ŒØ´ÙˆØ¯ Ú©Ù‡ ØªØ³Øª Ø´Ø¯ (REAL_VAULT)ØŒ Ù†Ù‡ vault Ø²Ù†Ø¯Ù‡ â€”
    # Ø§Ø¬Ø±Ø§ÛŒ worktree Ù‡Ø±Ú¯Ø² marker/state Ø¯Ø±Ø®ØªÙ Ø²Ù†Ø¯Ù‡ Ø±Ø§ refresh/revoke Ù†Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
    _rv = os.environ.get("REAL_VAULT")
    if _rv and not os.environ.get("ORG_ROOT"):
        os.environ["ORG_ROOT"] = _rv
    sys.path.insert(0, str(HERE.parent / "budget"))
    try:
        import capability_gate as _cg
    except Exception as _e:  # noqa: BLE001 â€” Ú¯Ø²Ø§Ø±Ø´Ù Ø³ÙˆØ¦ÛŒØª Ù†Ø¨Ø§ÛŒØ¯ Ø¨Ù‡ import Ú¯Ø±Ù‡ Ø¨Ø®ÙˆØ±Ø¯
        _cg = None
        print(f"(Ù‡Ø´Ø¯Ø§Ø±: capability_gate Ù„ÙˆØ¯ Ù†Ø´Ø¯ØŒ marker Ø¯Ø³Øªâ€ŒÙ†Ø®ÙˆØ±Ø¯Ù‡: {_e})")

    if failed:
        if _cg:
            _cg.revoke_capability()
        print(f"âŒ Ø´Ú©Ø³Øª: {', '.join(failed)}  (capability revoked)")
        sys.exit(1)
    if _cg:
        _cg.mark_capability("green: " + ",".join(TESTS))
    print(f"âœ… Ù‡Ù…Ù‡Ù” {len(TESTS)} ÙØ§ÛŒÙ„ ØªØ³Øª Ø³Ø¨Ø²  (capability marker Ø¨Ø§ fingerprint Ù†ÙˆØ´ØªÙ‡ Ø´Ø¯)")
