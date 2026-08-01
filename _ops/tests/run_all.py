#!/usr/bin/env python3
"""اجرای کل سوئیت متابولیسم/مناظره/تکثیر — هر تست در پروسهٔ جدا (env ایزوله).
اجرا: python -X utf8 run_all.py"""
import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # کنسولِ پیش‌فرضِ ویندوز (cp1252) وگرنه روی برچسبِ ─/فارسی کرش می‌کند

HERE = Path(__file__).resolve().parent
TESTS = ["test_client.py", "test_telemetry.py", "test_organ_gate.py",
         "test_epoch.py", "test_debate.py", "test_fitness_sigma.py",
         "test_budget_gate_v2.py", "test_money_gate.py", "test_capability_gate.py",
         "test_attribution.py", "test_panel_lead.py",
         "test_chrono_heartbeat.py", "test_pacemaker_pause_not_die.py", "test_chrono_langar.py",
         # M3 (2026-07-24): reproduction=C6 lifecycle recorder + agent-gateway red-team
         "test_c6_state_machine.py", "test_agent_gateway_redteam.py",
         # C2 (2026-07-25): تولیدکنندهٔ فرضیهٔ C6 + رفعِ over-markingِ _mark_hypothesis
         "test_c6_hypothesis_producer.py",
         # 2026-07-25 LIVE path: identity equations + collab/live telegram commands
         "test_identity_equations.py", "test_collab_and_live_commands.py",
         # 2026-07-25 LIVE path B: blackbox scanner + romajan bridge + heart wires
         "test_blackbox_and_bridge.py",
         # P5 (2026-07-24): fresh-arm-token + two-key gate for dangerous capabilities
         "test_arm_gate.py",
         "test_telegram_channel.py", "test_telegram_group_allowlist.py",
         # Task 2+3 (2026-07-24): writerِ زندهٔ channel-status + دیالوگِ owner↔organ
         "test_channel_status.py", "test_organ_dialogue.py",
         "test_leg.py", "test_doctor.py",
         "test_chord.py", "test_chord_shadow.py",
         "test_phase5.py", "test_spectral.py", "test_chamber.py",
         "test_calibration.py", "test_box.py", "test_evolution.py",
         "test_box_b134.py", "test_sensory.py", "test_rhythm.py",
         "test_cockpit.py", "test_project_f.py",
         # 2026-07-24: test_studio_telegram.py و test_dual_brain.py از TESTS خارج شدند — این دو
         # تستِ organism به ماژول‌های v1 (studio_telegram.py / dual_brain.py) اشاره داشتند که در
         # reorgِ Project-F (57f5138 «archive v1 code» + f63ce32، pytest 366/0) به 09-Archive
         # منتقل و از درختِ زنده حذف شدند؛ فقط _v3 ماند (StudioTelegramV3/DualBrainV3، APIِ متفاوت:
         # _scan_forbidden/_check_compliance دیگر وجود ندارد). پوششِ نسخهٔ فعال = تستِ داخلیِ
         # subproject (brain/test_dual_brain_v3.py) طبق §11. پوششِ PF در سوئیت: test_project_f/
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
         # 2026-07-21 HH-artery: جداسازیِ دو پول — cognition_effect (ارزشِ بیرونی-تأییدشده) +
         # fuel_meter (سوختِ واقعیِ API=خونِ قلب) + consumerهایشان در producers.velocity_meter؛
         # هر دو flag-off no-op (OCTOPUS_WIRE_COGNITION_EFFECT / OCTOPUS_WIRE_HEART_FUEL)
         "test_heart_cognition.py", "test_heart_fuel.py",
         # 2026-07-21 HH-artery wiring: بستنِ orphanِ کانال‌های خون — fuel_meter.record در
         # model_router.ask (هر call واقعیِ LLM) + cognition_effect.record در live_loop.apply_ari_verdict
         # (تأییدِ owner=external-validation). هر دو flag-off no-op؛ producers دادهٔ واقعی می‌خواند.
         "test_heart_fuel_wiring.py", "test_heart_cognition_wiring.py",
         "test_heart_control.py", "test_heart_loop.py", "test_heart_work.py",
         # B-section three-heart-rhythm-math (2026-07-25): داورِ نبض + circuit-breakerِ drawdown
         # (shadow-only) + کارتِ اندیکاتور. همه advisory/flag-off (پشتِ OCTOPUS_WIRE_PULSE_ARBITER /
         # HH_DRAWDOWN_ENFORCE؛ enforced_live همیشه False).
         "test_pulse_arbiter.py", "test_drawdown_guard.py", "test_indicator_scorecard.py",
         "test_needs_nudge.py", "test_cortex.py", "test_live_cockpit.py",
         "test_telegram_poll_e2e.py", "test_self_improve.py",
         "test_p0_security_fixes.py", "test_httpauth.py", "test_go_live.py",
         # 2026-07-20 Stage-1 Security: گاردِ P2 (کاکپیت هرگز STOPِ مالک را حذف/overwrite نکند)
         "S1-04_test_cockpit_stop_guard.py",
         # 2026-07-20 Stage-1 Security: توکنِ HMACِ callbackِ ap: (P3، پشتِ OCTOPUS_WIRE_CB_TOKEN)
         "S1-05_test_ap_binding.py",
         # 2026-07-20: پل‌های flag-off الحاقِ دو پروژهٔ مالک (TradeQuote / WLOS)
         "test_tradequote_bridge.py", "test_wlos_bridge.py",
         # 2026-07-20: spineِ durable outcome + Paper Lead MVO (پیرو Stage-1، دلتا-اسکن Q20)
         "test_outcome_spine.py",
         # 2026-07-20: Decision Receipt (immutable، append-only، join به outcome_store؛ inert، v1 فقط ثبت)
         "test_decision_receipt.py",
         # 2026-07-20 یکپارچگی: Memory Gate v1 (store+FTS5+FSM، self_knowledge=ADVISORY، join به receipt) + taxonomyِ واحد
         "test_memory_gate.py",
         # 2026-07-28 Octopus-v2030 contracts: exact proposal↔approval binding, scoped context,
         # SQLite canonical memory zones, owner-only verified-shared promotion.
         "test_control_contracts_v2.py",
         # 2026-07-20 یکپارچگی: Ops Event Spine v1 (envelope + trace_id اجباری + replay + reconcile)
         "test_event_spine.py",
         # 2026-07-20 یکپارچگی: context fencing (DATA_NOT_INSTRUCTION + غربالِ injection، flag-off passthrough)
         "test_context_fence.py",
         # 2026-07-20 آیتم۲: reachabilityِ context fence — model_router.ask ورودیِ LLM را غربال
         # می‌کند (پشتِ OCTOPUS_WIRE_CONTEXT_FENCE، observe-only، flag-off passthrough؛ dead-flag رفع)
         "test_context_fence_wiring.py",
         # 2026-07-20 Sol-T1: reachabilityِ Menu v2 — center.handle_update اکنون /panel + verbِ m:
         # را به menu_integration وصل می‌کند (پشتِ OCTOPUS_WIRE_MENU_V2، flag-off parity؛ orphan رفع)
         "test_menu_v2_wiring.py",
         # 2026-07-20 Sol-T2: رأیِ مالک → outcomeِ پایدار (verdict_recorder + live_loop، پشتِ
         # OCTOPUS_WIRE_VERDICT_OUTCOME): measurement-only، idempotent، restart-replay؛ قوسِ شکستهٔ
         # in-memory بسته شد. هرگز delivered/settled/revenue.
         "test_verdict_outcome.py",
         # 2026-07-20 Sol-T3: گاردِ ضدِ bypassِ خاموشِ context fence — inventoryِ callerهای مستقیمِ
         # local_llm.ask قفل شد (callerِ نو خارج از مجموعهٔ مستند = fail).
         "test_llm_fence_coverage.py",
         # 2026-07-23 C2 (Resurrection-Safe Memory): GAP-2 توکنِ statelessِ HMAC (restart دکمه
         # را نمی‌کشد؛ forged/expired/replay/wrong-owner fail-closed)؛ GAP-3 بازسازیِ کارتِ معوق
         # از outcomes.db در بوت (dedupeِ durable)؛ D-A اتصالِ durable_journal به دکتر + بازیابیِ
         # resume-not-restart بوت (EXECUTINGِ رهاشده → RECONCILE_REQUIRED)؛ شناسنامهٔ تولد
         # (system.booted + زنجیرهٔ boot_id)؛ باتریِ مرکبِ رستاخیز.
         "test_stateless_cb_restart.py",
         "test_deferral_rebuild_boot.py",
         "test_journal_recovery.py",
         "test_boot_certificate.py",
         "test_restart_battery.py",
         # 2026-07-23 C4 (One Event Spine): سطحِ تولیدِ واحدِ spine (spine_adapters.emit_event)،
         # قراردادِ envelope ۱۰-فیلده + provenanceِ never-null، و PARITYِ dual_write==emit_event
         # (۲ callerِ مستقیم پشتِ OCTOPUS_SPINE_VIA_ADAPTER قرنطینه، پیش‌فرض 0).
         "test_spine_single_surface.py",
         # 2026-07-23 C3 (Durable Learning Loop): learning_gate — قدمِ outcome→خاطرهٔ graded با
         # گیتِ held-out (ضدخودفریبی: internal-pass+held-out-fail → مسدود)، dedupِ یادگیری،
         # rollback/supersede، و بستنِ حلقه (تصمیمِ بعدی memory_id را استناد می‌کند) + restart.
         "test_learning_loop.py",
         # 2026-07-23 C5 (One Heartbeat shadow): BeatScheduler — یک زمان‌بند، ۸ فازِ قطعی
         # (SENSE→…→HEAL)، budget+circuit-breaker، organ failure isolation، restart continuity
         # (beat_counter durable، beatِ بعدی نه دوباره)، HALT فقط فازهای امن، ACT dry-run
         # (صفر double-actuation)، system.beat→spine، watchdogِ stall. پشتِ OCTOPUS_ONE_HEARTBEAT=0.
         "test_beat_scheduler.py",
         # C7 Slice 4: brain_core shadow composition root (real read-only adapters, zero ACT, parity, flag off)
         "test_brain_core.py",
         # 2026-07-23 C6 (Research & Governed Self-Improvement): research_contract (immutable،
         # falsifiable، tools fail-closed به constitutional-allowed) + research_loop (governance-gated،
         # budget سخت، falsify→terminate بدونِ بازنویسیِ بی‌نهایت، held-out verify، نتیجه فقط از
         # learning_gate وارد memory، quarantine، self-model calibration، durable research-journal،
         # صفر auto-apply/merge). owner-gated، proposal-only.
         "test_research_loop.py",
         # 2026-07-23 C7 Slice 1 (pending-card resurrection): money cards از gated_effect (SoT) +
         # RFC cards از rfcs.json بعد از restart بازسازی می‌شوند — projection-only، توکنِ stateless
         # HMAC (binding کامل)، dedupِ durable، exactly-once RFC verdict، HALT metadata-only-no-action،
         # terminal/EXECUTING/RECONCILE هرگز re-present نمی‌شوند. صفر تغییرِ money-authorization.
         "test_pending_card_recovery.py",
         # 2026-07-20 Sol Step 5: حلقهٔ ارزشِ Paper Lead سرتاسری (معیارِ اصلیِ پایان) — لیدِ synthetic
         # از توابعِ واقعیِ production: score→quote→کارتِ TG(sandbox)→receipt+outcome→رأیِ مالک→spine→
         # replay→metricsِ قطعی→digest. صفر شبکه/پول/send؛ IDها ثابت؛ حلقه واقعاً بسته.
         "test_paper_lead_mvo_e2e.py",
         # 2026-07-21 Wave1-B: فنسِ LLM — inventoryِ ماشین‌چکِ کلِ call siteهای production +
         # آداپتورِ مشترکِ fence_adapter (observe-only، flag-off parity، caller نو = fail)
         "test_llm_call_inventory.py",
         "test_fence_adapter_wiring.py",
         # 2026-07-21 Wave1-C: پوششِ LIMITED MULTI-DOMAIN ستونِ رویداد (lead+doctor+ziman+proposal؛
         # ۵ نامِ canonical در taxonomy؛ آداپتورهای spine_adapters؛ anti-PII ساختاری)
         "test_spine_multidomain.py",
         # 2026-07-21 Trust-Engine: فهمِ free-text مالک با مغزِ خودِ بات (model_router) → پیشنهادِ
         # ساختاریافته؛ propose-only (هر شکست=ok=False fallback)، autonomy_matrix پیشنهاد را re-check
         # می‌کند + متنِ خام در گیت (مدل هرگز گیت را پایین نمی‌آورد). flag OCTOPUS_TG_LLM_ASK خاموش.
         "test_llm_intent.py", "test_llm_intent_wiring.py",
         # 2026-07-21 Trust-Engine فاز C: دیوارِ رضایت (fail-closed structural) + آداپترِ
         # canonicalِ ورودی (submit_candidate) + برشِ عمودیِ synthetic (صفر ارسالِ بیرونی؛
         # market_signal فایلِ draft نمی‌سازد؛ halt=receipt-only؛ flag OCTOPUS_WIRE_LEAD_CANDIDATES خاموش)
         "test_consent_firewall.py", "test_lead_candidate_inbox.py",
         # 2026-07-21 سیم‌کشیِ نقاشی/لید: همگراییِ دو inbox (گاردِ collision) + مسیرِ canonicalِ
         # owner_menu→submit_candidate + launcherِ boundary (flag-off) + freezeِ inboxِ قدیمی +
         # فیکسِ کرشِ نهفتهٔ EffectorGate(db=None). همه flag-off = parity.
         "test_lead_wiring.py",
         # 2026-07-21 LEAD-SAFETY-C1: گیتِ per-effect + کشتنِ footgunِ batch-release — kindهای
         # lead_outbound هرگز با یک human-append آزاد نمی‌شوند (release_gated_effects مستثنی)؛
         # فقط release_one صریح + authorization + consent-recheck (market_signal/synthetic هرگز)؛
         # outbound worker همیشه NOT_ARMED (صفر ارسال). flag OCTOPUS_WIRE_LEAD_OUTBOUND خاموش.
         "test_lead_effect_gate.py",
         # 2026-07-24 Phase-D (Wave-2 WS-5): consent gate/store + funnel + speed-to-lead +
         # release/settle separation + verdict→effect hook. همه flag-off.
         # (عمداً نیامد: D7 owner-transport — گاردِ no-networkِ تازه‌ترِ master؛ producer-migration —
         #  با گاردِ «harvest = یک env، صفر راز»‌ِ تازه‌ترِ master تضاد داشت.)
         "test_consent_gate.py", "test_funnel_store.py", "test_speed_to_lead.py",
         "test_release_send_separation.py",
         "test_lead_verdict_wiring.py",
         # 2026-07-21 Trust-Engine D6: گاردِ stalenessِ releasable در لایهٔ bridge (chrono
         # دست‌نخورده) — پیش از settle، releasableِ کهنه refuse می‌شود (شکافی که sweep_stale_effects
         # پوشش نمی‌داد چون فقط pending را جارو می‌کند)
         "test_effector_gate_bridge.py",
         # 2026-07-21 Trust-Engine D7: مرزِ امضاشدهٔ POST /api/v1/lead-candidates روی 127.0.0.1
         # (HMAC/nonce/idempotency/allowlist/halt→503) + اثباتِ سلبیِ n8n (صفر importِ گیت/ارسال)؛
         # flag OCTOPUS_WIRE_LEAD_BOUNDARY خاموش = listener بالا نمی‌آید
         "test_lead_boundary_http.py",
         # 2026-07-21 Wave1-D: جداییِ liveness از کار/ارزشِ validated — metric_separation از
         # storeِ durable قطعی بازسازی می‌شود؛ تپش≠مولد، claim≠revenue، fake≠real delivery
         "test_metric_separation.py",
         # 2026-07-21 Wave1-A: صداقتِ منوی v2 (صفر دستورِ مرده/تبلیغِ ناموجود) + رأیِ احرازشدهٔ
         # مالک از update-handlerِ واقعی → OutcomeStoreِ پایدار (fail-closed بدونِ secret،
         # single-use، replay-safe؛ هرگز delivered/settled/revenue)
         "test_menu_v2_honesty.py",
         "test_tg_verdict_durable.py",
         # 2026-07-21 D2: اهرم‌های ACTIVATION-*.flag از گیت untrack شدند (۸ فایل، شاملِ go-live/
         # cortex-paid/work-llm/heart-doctor/self-improve-auto) → غیابشان هر گیتِ زنده را می‌بندد
         # حتی post-rollover؛ فعال‌سازی = عملِ صریحِ مالک نه پیش‌فرضِ commit‌شده
         "test_activation_untracked.py",
         # 2026-07-21 D1: گاردِ fail-closed رأیِ per-item مالک قبل از هر PUT به PocketSmith —
         # حتی با هر سه فلگِ مسلح، بدونِ رأیِ durableِ همان آیتم (bind به tid+field+content_sha256)
         # صفر PUT؛ صفر auto-approve؛ HALT/whitelist/cap حفظ شد
         "test_ps_writeback_verdict.py",
         # 2026-07-21 D3: گاردِ drawdown فقط-شادو (HH_DRAWDOWN_ENFORCE خاموش) — روی breach فقط
         # هشدارِ advisory؛ صفر اثرِ پول/block/halt؛ آستانه placeholderِ owner-tunable
         "test_drawdown_shadow.py",
         # 2026-07-21 D4: سخت‌سازیِ G — توکنِ CB به verbهای legacy(ok/no/later)+mission(ms:) گسترش یافت
         "test_cb_token_legmiss.py",
         # 2026-07-21 D4: بهداشتِ ساختاریِ payload داخلِ event_spine.dual_write (defense-in-depth)
         "test_spine_sanitize.py",
         # 2026-07-20 D-G: قراردادِ STOP — HALT-ALL توسطِ watchdog.py + هر دو watchdogِ .ps1 honor می‌شود
         "test_stop_contract.py",
         # 2026-07-20 یکپارچگی: بستنِ حلقهٔ لید record-only (lead→receipt→outcome، memories_used از
         # Memory Gate، verdict=PENDING، idempotent؛ صفر send/money — تولیدکنندهٔ واقعیِ زنجیرهٔ spine)
         "test_lead_outcome_recorder.py",
         # 2026-07-20 یکپارچگی: reachabilityِ تولیدکننده — lead_discovery_beat اکنون recorder را
         # واقعاً صدا می‌زند (پشتِ OCTOPUS_WIRE_LEAD_OUTCOME، خارج از profile). flag-off=byte-identical،
         # flag-on=receipt(E1)+outcome پایدار، memories_used از drون beat، fail-soft (dead-flag رفع شد).
         "test_lead_outcome_wiring.py",
         "test_lead_learning_wire.py",   # W1 (2026-07-25): قوسِ یادگیری از تصمیمِ لید
         # 2026-07-20 integration: پوششِ orphan (تست‌های سبزِ روی‌دیسک که در run_all نبودند —
         # نقدِ سنتز: بدونِ ثبت، شکستِ extractionِ آینده نامرئی است). فقط سبزها؛ ۴ orphanِ قرمزِ
         # pre-existing (effector_idempotency/drawdown_enforcer/mining_leg/tg_approval_store) عمداً بیرون.
         "test_lead_leg_inbox.py", "test_tg_intent.py", "test_tg_metadata_scan.py",
         "test_ziman_branding.py", "test_merge_applies_knob.py", "test_mining_wiring.py",
         "test_web_research.py", "test_metacognitive.py", "test_discoveries.py",
         "test_events.py", "test_part_loops.py", "test_auto_approve.py",
         # 2026-07-16: ماتریسِ ردهٔ خودمختاری (رأی مالک: گیتِ انسانی فقط برای مهم‌ها) —
         # important هرگز آزاد نمی‌شود؛ غیرمهم پشتِ OCTOPUS_AUTONOMY_FREE خودتصمیمِ ثبت‌شده.
         "test_autonomy_matrix.py",
         "test_business_brain.py", "test_vault_updater.py",
         "test_vault_updater_apply.py", "test_goal_directed.py",
         "test_stress.py", "test_innervation.py", "test_ignition.py",
         "test_standards_s.py", "test_replay_s.py", "test_softwta_shadow.py",
         "test_registry_scan.py", "test_phase1_envelope.py",
         "test_route_scorer.py", "test_calibration_probe.py", "test_consolidate.py",
         "test_execution_board.py", "test_depth_guard.py", "test_guidance_box.py",
         # WS-9 (Painting-OS): اکچوایتورِ approval — رفعِ «تأییدشده ولی بی‌اکشن» (visibility، flag-off)
         "test_approval_actuator.py",
         "test_tg_api.py", "test_tg_actions.py", "test_tg_render.py", "test_tg_center.py",
         "test_tg_power.py",   # 2026-07-17: مرکزِ فرماندهی (مکثِ تک‌پا + ردهٔ قدرتِ دوکلیک)
         # 2026-07-30: دستورالعملِ استفاده **داخلِ** تلگرام (پینِ General ِ گروه).
         # مهم‌ترین بندش «هر ادعای راهنما در کد برقرار است» — راهنمای دروغ
         # فعالانه گمراه می‌کند، بدتر از نبودنش.
         "test_tg_guide.py",
         "test_tg_mission.py", # 2026-07-18: Mission Genome + Action Graph برای self-coding کنترل‌شده
         "test_tg_mission_runner.py", # 2026-07-18: Runner v0 — اجرای ایزولهٔ allowlisted + evidence
         "test_code_autonomy.py",
         # 2026-07-29 — پلِ outboxِ دکترِ اختاپوس (OCTOPUS-DOCTOR) به مرکزِ تلگرام؛
         # flag-off no-op (OCTOPUS_WIRE_DOCTOR_TG). هرمتیک: ORG_ROOT موقت.
         "test_doctor_link.py",
         # ۲۰۲۶-۰۷-۲۷ — گاردهای مصرف‌کننده‌های تازهٔ مغزِ گران. ممیزیِ متخاصمِ همان روز
         # نشان داد هیچ‌کدام این‌جا ثبت نشده بودند: ۵۲ تستِ تازه نوشته شده بود که در
         # سوییتِ رسمی (و در سوییتِ سایهٔ خودِ self_patch) اصلاً نمی‌دوید.
         "test_deep_think.py",        # جلسه‌های فکرِ عمیق + مرزِ PII لولهٔ لید
         "test_ask_brain.py",         # گفتگوی آزادِ تلگرام + سهمیه + مرزِ «فقط حرف»
         "test_mirror_room.py",       # اتاقِ آینه: حافظهٔ گفتگو + لایهٔ تصحیحِ مالک
         "test_selfaware_wiring.py",  # قفلِ پنج سیمِ خودآگاهی (اسکنِ ۰۷-۲۷)
         "test_negotiate.py",         # مذاکره: جوابِ سوم + «قبول ≠ اجرا»
         "test_bcm_feed_and_verdicts.py",  # تغذیهٔ BCM + صفِ رأیِ مالک در خودآگاهی
         "test_vault_wires.py",  # دانشِ ابسیدین → رفتار
         "test_html_and_correction_safety.py",  # escape ِ متنِ مدل + مرزِ کلمهٔ تصحیح
         "test_owner_answers_2026_07_27.py",  # سه رأیِ مالک: کوت/سکوت/منقضی‌ها
         "test_initiative_and_autonomy.py",  # ابتکار + مرزِ اختیار
         "test_tool_request.py",  # «چه ابزاری ندارم» — ثبت هرگز گیت ندارد، فقط تحویل
         "test_recall_trend.py",  # «به یاد می‌آورد؟» — سری، نه عکسِ لحظه‌ای
         "test_paid_truncation.py",  # پاسخِ بریدهٔ مغزِ پولی = شکست، نه ok=True
         # ۲۰۲۶-۰۷-۳۰ — هارنسِ خودهدف‌گذاری. هر چهار plain-assert اند (تابعِ `t_` +
         # رانرِ `__main__` + `harness.run`)، پس عمداً **در TESTS** اند نه
         # PYTEST_TESTS — درسِ green-lie ِ `test_synapse_sense`: فایلِ pytest-style
         # که direct-run شود صفر assert می‌دود و exit 0 می‌دهد.
         "test_goal_generator.py",   # هدفِ بی‌ترازو ساخته نمی‌شود + چرخشِ روش فقط بعد از FAIL
         "test_prereg_evaluator.py",  # پیش‌ثبتِ fail-closed + ارزیابی که target را جابه‌جا نمی‌کند
         "test_test_cycle_beat.py",  # صداکنندهٔ چرخه: زنجیرهٔ کامل، ضدِ دوبار-شلیک
         "test_target_guard.py",  # مقصدِ پچ: resolve قبل از قضاوت (کورپوسِ فرارِ ۰۷-۳۰)
         "test_goal_max_circular.py",  # سهمیهٔ دایره‌ای: استثنا باید **منقضی شود**
         "test_budget_judge.py",  # W1 — قاضیِ بودجه (رزروِ مالک تخطی‌ناپذیر)
         "test_decision_gate.py",  # W2 — گیتِ ۵۱/۴۹ (HARD-STOP با مدرکِ کامل هم بسته)
         "test_trajectory_log.py",  # W3 — دفترِ مسیر (redact ِ fail-closed)
         "test_teacher_loop.py",  # W4 — حلقهٔ معلم (جفتِ بی‌نمره، بی‌نمره می‌ماند)
         "test_stuck_money.py",  # ۱۳۴ — پرداختِ نیمه‌کاره دیده شود، ولی دست‌نخورده
         "test_money_fsm.py",  # ۱۳۶ — تصمیمِ پولی هرگز بی‌تصمیم نمی‌شود (سایه)
         "test_capability_registry.py",  # فهرستِ خودکشف — سطح از بدن عقب نماند
         "test_owner_auth_log.py",  # مجوزِ مالک می‌ماند ولی هرگز خودش اجرا نمی‌شود
         "test_clock_guard.py",  # ۱۳۵ — ساعتِ عقب‌پریده انقضا را زنده نکند
         "test_command_discoverability.py",  # دستوری که دیده نمی‌شود، نیست
         "test_improve_learning_loop.py",  # رأیِ مالک باید به یادگیرنده برسد
         "test_orphan_scan.py",  # ارگانیسم بداند کدام اندامش وصل نیست
         "test_funnel_cmd.py",  # D3b — مالک واقعیتِ بازار را می‌گوید
         "test_two_bot_bridge.py",  # پلِ عام — دستورِ تبلیغ‌شده از گروه کار کند
         "test_self_coding_chain.py",  # زنجیرهٔ هفت‌حلقه‌ایِ کدنویسیِ واقعی
         "test_output_critic.py",  # ارگانیسم خروجیِ خودش را نمره بدهد
         "test_callback_routing.py",  # هیچ دکمه‌ای بی‌مسیر نماند
         "test_self_patch.py",        # حلقهٔ مرور→صف→پچ + قفلِ ۶ یافتهٔ ممیزی
         "test_improve_deep.py",      # لایهٔ عمیقِ improve + سقفِ سختِ روزانه
         "test_governor_contract.py",  # قراردادِ تخصیص + دیده‌شدنِ بریدگی
         "test_hebbian_signals.py",   # واژگانِ سیگنالِ Hebbian (ضدِ سیگنالِ همیشه‌روشن)
         "test_ziman_leg.py",
         "test_ziman_phase2.py",
         # 2026-07-13: دو ورودیِ phantom حذف شدند — test_ziman_wiring.py و
         # test_ziman_biology.py هرگز در تاریخِ گیت وجود نداشتند (pytest exit=4 →
         # سوییت را دائم قرمز و markerِ capability را دائم revoke می‌کرد؛ ریشهٔ C-01/C-04).
         # اگر قرار است نوشته شوند، رجوع: AGENT_QUESTIONS «2026-07-13». پوششِ ziman فعلی =
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
         "test_school_bridge.py",   # 2026-07-14: orphan test بود (فایل موجود، ثبت‌نشده) — ثبت شد
         "test_self_claims.py", "test_octopus_logger_wire.py", "test_improve_refractory.py",
         "test_wiring_cleanup.py", "test_deadwrite_readers.py",
         # 2026-07-15: تست‌های نوِ راست‌گویی/کابین + دو orphanِ ziman (سبز، ثبت‌نشده بودند)
         "test_business_legs_shape.py", "test_correlation_id_generated.py",
         "test_channel_status_stale_not_green.py", "test_cockpit_truthful.py",
         "test_tg_exec_consumer.py",
         "test_ziman_wiring.py", "test_ziman_biology.py",
         # 2026-07-15: فیکسِ مغزِ پولی (باگ ۱) + موتورِ کشفِ لید (نقشهٔ لید، مراحل ۱-۲)
         "test_brain_fix.py",
         "test_lead_scorer.py", "test_lead_discovery_beat.py",
         "test_harvest_austender.py", "test_cadence_aliasing.py",
         "test_organism_honesty.py", "test_genome_safety.py",
         # 2026-07-17: تعمیرهای truth-map (P3 عصبِ درد، P5 بودجهٔ صادق، P6 آرتیفکتِ pacemaker، …)
         "test_truthmap_fixes.py", "test_p4_p9_fixes.py", "test_doctor_selfknowledge.py",
         # 2026-07-28: معیارِ دقتِ خودمدل (C3) — خودگزارشِ snapshot در برابرِ منابعِ حقیقتِ مستقل.
         "test_self_accuracy.py",
         # 2026-07-16: نقشهٔ لید مراحل ۳-۵ (پلِ ایمیل، غنی‌سازیِ LLM، پیش‌فاکتورِ واقعی)
         "test_email_lead_bridge.py", "test_lead_llm_enrich.py",
         "test_lead_quote_chain.py",
         # 2026-07-16: ثبتِ یتیم‌های تأییدشده (برنامه ۳) — هر سه سبزِ ایزوله در worktree.
         # ثبت‌نشده‌های عمداً کنارگذاشته: test_mining_leg/test_mining_wiring (phantom —
         # MiningLeg دومغزی و wiring.make_mining_leg در این درخت وجود ندارد)،
         # test_drawdown_enforcer (phantom — budget_gate.DRAWDOWN_LOG/drawdown_status نیست)،
         # test_effector_idempotency (phantom — EffectorGate.request_idempotent نیست).
         # 2026-07-16 (audit R-04): test_durable_journal دیگر phantom/قرمز نیست — تستِ setup
         # اکنون دایرکتوریِ state/journal را می‌سازد (مثلِ _default_path) → ثبت شد (direct-run).
         "test_durable_journal.py",
         "test_ui_truth.py", "test_organ_console.py", "test_organ_create.py",
         # 2026-07-16: موجِ ده‌برنامه — کالیبراسیون (برنامه ۶) + صداقتِ کابین پس از GO-LIVE (برنامه ۹)
         "test_calibration_loop.py", "test_cockpit_golive_honesty.py",
         "test_legs_freshness.py",   # برنامه ۷: صداقتِ تازگیِ پاها
         "test_ziman_catalog_bridge.py",   # برنامه ۸: پلِ کاتالوگِ زیمان
         # 2026-07-16: متابولیسمِ دادهٔ $0 همهٔ پاها (leg_cultivate + دکتر + مغزِ B)
         "test_legs_cultivation.py",
         # 2026-07-16: گاردِ read دادهٔ ویژهٔ PII/PHI (audit R-05 + R-15) — شریک/DNA/EEG/HRV/پروفایلِ روان‌درمانی
         "test_pii_read_guard.py",
         # 2026-07-16: EVAL-GATE (audit R-03) — دیتاستِ محکِ خصمانهٔ نسخه‌دار (adv-eval.v1)
         # + اجراکنندهٔ $0 آفلاین که خودمختاری را گِیت می‌کند (_ops/eval/).
         "test_adversarial_eval.py",
         "test_personal_ledger.py", "test_pocketsmith_import.py",
         # 2026-07-17: فاز ۱+۲ قلبِ پول — خروجی‌سازِ واریزی + backfillِ ادعا + خطِ لولهٔ کاملِ reconcile
         "test_claims_backfill.py",
         # 2026-07-16: کلاینتِ فقط‌خواندنیِ PocketSmith API v2 (me/accounts/transactions/sync)
         # پشتِ OCTOPUS_WIRE_POCKETSMITH؛ mockِ urlopen (صفر شبکه/کلیدِ واقعی)؛ حملِ category/labels.
         "test_pocketsmith_api.py",
         # 2026-07-16: write-backِ گاردشدهٔ برچسب‌ها به PocketSmith (رأی مالک) — فقط PUT labels
         # به /transactions/{id}، whitelist سخت، سقفِ flush، صفِ محلی، پشتِ OCTOPUS_WIRE_PS_WRITEBACK.
         "test_ps_writeback.py",
         # 2026-07-16: حسابدارِ مولتی‌ایجنت (سنت/انتساب/ارکستراتور)
         # (dedupe 2026-07-21 wave-1: test_txn_store/test_attributor فقط در ردیف‌های کامنت‌دارِ
         # پایین ثبت‌اند — قبلاً این‌جا هم بودند و هرکدام دوبار اجرا می‌شد)
         "test_accountant.py",
         # 2026-07-16: انبارِ تجمیعیِ تراکنش (txn_store) — xlsx+CSV → یک انبارِ cents-محور،
         # dedupِ content-hash، reconcile tie-out. txn-store.json واقعی gitignore.
         "test_txn_store.py",
         # 2026-07-16: ASSET-OVERSIGHT — نقشهٔ داراییِ کل (asset_map + asset_map_beat)
         # propose-only، fail-soft، صفر مبلغ/net-worth، پشتِ OCTOPUS_WIRE_ASSET_MAP.
         "test_asset_map.py",
         # 2026-07-16: تبِ 💰 دارایی‌ها/حساب کابین — asset_map + personal_ledger (فقط‌خواندنی،
         # ترازِ تجمیعی، صفر تراکنش/شماره‌حساب، صفر مسیرِ mutation).
         "test_finance_card.py",
         # 2026-07-16: CATEGORIZER — attributor (قاعده‌های قطعی: wage/transfer-passthrough/
         # vendor؛ enumِ auto|needs_review نه اطمینانِ عددی؛ propose-only، مالک تأیید نه ایجنت).
         "test_attributor.py",
         # 2026-07-16: دستیارِ AIِ دسته‌بندیِ پس‌ماند (txn_categorize) — محلی-اول ollama $0،
         # ابری Fugu فقط پشتِ OCTOPUS_WIRE_ACCT_CLOUD + scrub_pii؛ هیچ مبلغ به LLM؛ propose-only.
         "test_txn_categorize.py",
         # 2026-07-16: حسابدارِ گفتگومحورِ تلگرام (/review) — موتور + لایهٔ تلگرام؛ گاردِ
         # هویتِ تراکنش در callback، متنِ آزادِ proposal-only، هیچ مبلغ به LLM.
         "test_acct_review.py", "test_review_telegram.py",
         # 2026-07-16: فازِ صفرِ دفترِ واقعی (نقدِ بیرونی + سخت‌سازیِ auditِ ۴۸-ایجنتی):
         # ledger_core (دوطرفهٔ متوازن، قفل‌دار، append-only+fsync، reversal، GST fail-closed)
         # raw_store (شواهدِ خامِ immutable) · recon (reconciliation واقعی، ضدِ netِ برابرِ دروغ).
         "test_ledger_core.py", "test_raw_store.py", "test_recon.py",
         # 2026-07-16: فازِ ۱ — پلِ برچسب→دفتر (journal_bridge: نگاشتِ قطعی، دو-تأییدی،
         # هیچ tax_code) + لایهٔ تلگرامِ /books (ثبت با هویتِ txn، تپِ تکراری امن).
         "test_journal_bridge.py", "test_books_telegram.py",
         # 2026-07-16: two-rails — آداپتورِ ریلِ شرکت (company_books: provider-agnostic،
         # DRAFT-only تحمیلی، فلگ‌خاموش صادق، صفر secret-echo).
         "test_company_books.py", "test_books_xero.py",
         # 2026-07-16: جریانِ زندهٔ حسابداری — حافظهٔ ضدِ فراموشی (قواعدِ merchant از
         # تأییدها، بازتولیدپذیر، drift) + ضربانِ acct_beat (فلگ‌خاموش، سایدکار).
         "test_acct_memory.py", "test_acct_beat.py",
         # 2026-07-18 رأی مالک «سریع‌تر + هوشمندتر» (فاز ب+الف؛ ج پارک): boot-think،
         # گیتِ کیفیتِ محلی-اول (پایانِ گرسنگیِ Fugu)، ماشهٔ کورتیزولی (flag-off).
         "test_brain_cortisol.py",
         # 2026-07-22 PRE-0/F: تست‌های هرمتیکِ سه BLOCKER (fail-closed guard، id-bound
         # release، STOP canonical). pytest-native (monkeypatch)؛ در PYTEST_TESTS ثبت شد.
         "test_blocker_fixes_2026_07_22.py",
         # 2026-07-22 C1: چارچوبِ migrationِ اسکیمای chrono.db (حذفِ PRAGMAِ clobber‌کننده از
         # DDL + dispatcherِ transactionalِ fail-closed + تفکیکِ empty/legacy/malformed). script-native.
         "test_chrono_schema_migration.py",
         # 2026-07-22 C3: RESURRECTED از phantom (owner #7) — idempotency در request()
         # (UNIQUE(idempotency_key)؛ keyless=بدون dedup؛ same-key+different-content=Conflict). script-native.
         "test_effector_idempotency.py",
         # 2026-07-23 C4: exact per-effect fail-closed money/E4 authorization — money NEVER
         # batches (release_gated_effects excludes _E4_MONEY_KINDS)؛ release_effect single
         # atomic bind (id+content_hash+action_kind+target_ref+single-use approval+expiry). script-native.
         "test_c4_exact_authorization.py",
         # 2026-07-23 C4.1: close the E4 id-only single-effect bypass — release_one REFUSES
         # money (E4 releasable ONLY via release_effect exact binding + human ledger ref);
         # legacy-unbound money → NEEDS_OWNER_REVIEW. script-native.
         "test_c41_e4_id_only.py",
         # 2026-07-23 C5: CAS execution — migration v4 (execution columns + EXECUTING/
         # FAILED_SAFE/RECONCILE_REQUIRED در CHECK؛ ایندکسِ UNIQUEِ C3 پس از rebuild بازساخته
         # می‌شود)؛ claim/commit اتمیک با execution_id (دو executor یک برنده؛ stale/wrong xid
         # هرگز finalize نمی‌کند)؛ halt-during → RECONCILE_REQUIRED؛ settle بی‌TOCTOU. script-native.
         "test_c5_cas_execution.py",
         # 2026-07-23 C6: receipt/reconciliation lane — sweep جداگانهٔ releasableِ کهنه
         # (refuseِ امنِ پیش-claim) و EXECUTINGِ کهنه (→ RECONCILE_REQUIRED، هرگز refuseِ
         # دروغین)؛ reconcile_effect انسانی با evidence+operator (receipt هرگز بازنویسی
         # نمی‌شود)؛ redrive_approval بدونِ appendِ دوباره (crash window a، idempotent). script-native.
         "test_c6_receipt_reconciliation.py",
         # 2026-07-25 W6: قفلِ مرزِ propose-only حلقهٔ C6 — گیتِ دوگانه (env + فایلِ مالک)،
         # ممنوعیتِ merge_or_deploy، صفر ابتداییِ خطرناک، گاردِ رجیستریِ دکتر.
         "test_c6_trigger_propose_only.py",
         # 2026-07-25 C1: بنچِ C6 دیگر خودش را تأیید نمی‌کند — NULL رد می‌شود،
         # baselineِ اعلامی بی‌اثر است، ادعای مکانیزمی مقدم بر ساعتِ دیواری.
         "test_c6_bench_honesty.py",
         # 2026-07-25 C2: تولیدکنندهٔ صادقِ فرضیهٔ C6 + صفِ id-safe؛ صف خالی شرافتمندانه
         # می‌ماند و mechanism_count فقط نقص را بازتولید می‌کند، نه بهبودِ اعمال‌شده.
         # ۲۰۲۶-۰۷-۲۸ — ورودیِ تکراری حذف شد: همین فایل در خطِ ۲۱ ثبت شده بود، پس
         # هر اجرای سوئیت دوبار می‌دویدش. توضیحِ بالا نگه داشته شد چون دلیلِ ثبت را
         # بهتر از ورودیِ اول شرح می‌دهد؛ فقط نامِ تکراری رفت.
         # 2026-07-25 C3: جعل اعتماد مالک مسدود شد؛ claim بی‌گواهی به GRADED cap می‌شود
         # و مسیر واقعی رأی مالک از verdict_recorder همچنان OWNER_CONFIRMED است.
         "test_c3_owner_trust_forgery.py",
         # 2026-07-25: مسیرهای router گاورنر/قلب/خودشناسی تاریک می‌مانند؛ چهار فلگ در
         # OCTOPUS-flags.cmd صریحاً صفر ثبت شد و با تست hermetic قفل شد.
         "test_paid_router_dark_config.py",
         # 2026-07-25: بخشِ resilience.circuit_breaker در budgets.yaml اضافه شد (additive)
         # تا breakerِ per-provider زودتر fail-fast کند و سهمیهٔ ناپایداریِ fugu نسوزد.
         "test_budgets_resilience_config.py",
         # 2026-07-25 (build-spec §4): انضباطِ سکوتِ event_bridge — ضدِتکرارِ امضای
         # محتوا (۵۰ هم‌امضا → ۱ push)، سقفِ روزانهٔ ۶، حفظِ سقفِ ساعتیِ ۱۰.
         "test_telegram_silence.py",
         # 2026-07-25: money-pulse — فازِ جدید به ضربانِ قلب. درآمدِ پاها رو می‌خونه،
         # هرگز MONEY_ATTRIBUTION جعلی نمی‌نویسه (wall anti-reward-hacking).
         "test_money_pulse.py",
         # 2026-07-25 T1 (megaprompt): int() روی برچسبِ شدت — ۳۴۸ کرشِ doctor_digest_beat
         # بسته شد؛ severity رشته‌ای/عددی/None/ناشناخته همه متنِ غیرخالی می‌دهند.
         "test_organ_dialogue_digest.py",
         # 2026-07-25 T3 (megaprompt): self-heal کور → باعلت؛ phi-timeout در chrono و
         # استثنا در leg_beat هر دو علتِ پایدار در state/legs/ ثبت می‌کنند.
         "test_leg_failure_reason.py",
         # 2026-07-25 T4 (megaprompt): گاردِ متروَنوم (self_referential + authoritative=false)
         # و انتشارِ Δ منفی پشتِ OCTOPUS_HEART_HONEST_PULSE؛ gate0 با Δ≤0 بسته.
         "test_heart_honest_pulse.py",
         # 2026-07-25 T8 (megaprompt): صفِ RFC با واقعیتِ زنده تطبیق می‌خورد — dedupe روی
         # متنِ گلوگاه، stale-input برای شرطِ مرده (σ/FREEZE)، submit idempotent.
         "test_doctor_rfc_stale_dedup.py",
         # 2026-07-25 T2 (megaprompt): سنجهٔ خودبهبودی — dedupe نیت بر id، مخرجِ نیتِ متمایز،
         # درون‌زاد رأی نمی‌دهد. پشتِ OCTOPUS_HONEST_OUTCOMES (خاموش = بایت‌به‌بایت).
         "test_honest_outcomes.py",
         # 2026-07-25 (دیباگِ زندهٔ پس از ریستارتِ ۱۴:۱۴:۲۵ — شش فیکس با شاهدِ زنده):
         # (۱) spectral روی گرافِ بی‌یالِ ارگانیسمِ *سالم* «σ≈1/critical» می‌داد → آسیابِ
         # ۸ RFCِ یکسان؛ (۲) created_ts persist نمی‌شد → sweep هرگز expire نمی‌کرد؛
         # (۳) phi با ۲ ack یک سکونِ ۲×mean را «مرگ» می‌خواند (۶۶ ری‌استارت، phi=300 =
         # سقفِ p_later) — تحمّلِ صادق پشتِ OCTOPUS_CHRONO_PHI_HONEST؛ (۴) legs_diag تا
         # امروز وجود نداشت پس مرگِ واقعی از آرتیفکتِ سنجش جدا نمی‌شد؛ (۵) Gate-0 در
         # shadow با Δِ *منفی* هم باز می‌شد (فقط authoritative را می‌خواند)؛ (۶) سه فلگِ
         # مغزِ پولی در wire_summary نبودند → مسلح‌بودن از state دیده نمی‌شد.
         "test_live_debug_fixes_2026_07_25.py",
         "test_thesis_queue.py",
         "test_governor_lapsed_deadline.py",
         "test_paid_timeout_chain.py",
         "test_card_render_profile.py",
         "test_audit_origin_guard.py",
         "test_coherence.py",
         # 2026-07-23 D3/D4/D5: (D3) صفر provider-call/authorization/settle زیرِ HALT-ALL —
         # شکافِ release_one/release_gated_effects بی‌گاردِ kill هم بسته شد؛ (D4) گاردِ
         # boot-halt در هر ۶ launcher + parity واچ‌داگ PS1/py + ماتریسِ should_revive؛
         # (D5) سناریوی ترکیبیِ halt با زمانِ مجازی: صفر اثر زیرِ halt، بدونِ duplicate،
         # recovery تمیز + reconcile. script-native.
         "test_d3_provider_effect_halt.py",
         "test_d4_launcher_halt.py",
         "test_d5_halt_integration.py",
         # 2026-07-23 PRE-0: ده invariant قانون اساسی از نقاطِ ورودِ واقعی (MemoryGate،
         # model_router زیرِ halt، on_human_judgment با گیتِ واقعی، code_autonomy.allowed_target،
         # watchdog/launcher) + seamهای canonicalِ governance برای لاین‌های هنوز-غیرفعال. script-native.
         "test_pre0_real_entry.py",
         # 2026-07-22 F-COVERAGE adjudication: test_tg_approval_store دیگر orphanِ رد نیست —
         # ماژول/API واقعی است و reachable در production (center.py:1223-1224 approve/reject روی
         # مسیرِ approval مالک). تنها شکست، stale characterization بود (whitelistِ t_n فاقدِ
         # expires_epoch)؛ contract migrate شد. invariantِ content-free دست‌نخورده. script-native.
         "test_tg_approval_store.py",
    # ۲۰۲۶-۰۷-۲۸ — ابزارهای خودنگری: گیتِ ماشین‌خوان، رانشِ فلگ،
    # ردِ ارسال، ممیزیِ مسیرِ ارسال، اسکنِ نقاطِ کور، لایهٔ بینش.
    "test_gate_report.py", "test_flag_drift.py", "test_tg_trace.py",
    "test_tg_send_audit.py", "test_self_scan.py", "test_self_insight.py",
    "test_tg_topic_reply_parity.py",
    # ۲۰۲۶-۰۷-۲۸ — ۱۵ تستی که روی دیسک بودند و در **هیچ** لیستی نبودند.
    # کشف: run_all ‏۳۵۱ تستِ یکتا می‌شناخت ولی ۳۶۶ فایل روی دیسک بود. از ۱۸ اختلاف،
    # ۲ تا استثنای مستند بود (drawdown_enforcer/mining_leg، در کامنت‌های همین فایل) و
    # ۱۶ تا هیچ ردی نداشتند — نه در لیست، نه در کامنت. یعنی افتادگی، نه تصمیم.
    # پس «۳۴۲/۳۴۲ سبز» عددش درست بود و دامنه‌اش ناقص: تست نوشته شده بود، به رانر
    # وصل نشده بود. نمونهٔ گویا: test_tg_topic_reply_quiet دربارهٔ تاپیک‌روتینگ، نوشتهٔ
    # ۰۷-۲۶، و همان روزی که همان مسیر باگ داشت اجرا نمی‌شد.
    # هر ۱۵ تا قبل از ثبت جدا اجرا شدند: ۱۵/۱۵ سبز → ثبتشان صفر ریسک.
    "test_c6_card_redelivery.py", "test_c6_probe_coverage.py",
    "test_cortex_circuit_breaker.py", "test_cortex_symmetric_revive.py",
    "test_ledger_integrity_probe.py", "test_module_self_manifest.py",
    "test_operator_doctrine.py", "test_route_scorer_shadow_log.py",
    "test_staleness_stamp.py", "test_synapse_sense.py", "test_synapse_beat.py",
    "test_tg_callback_actor.py", "test_tg_instant_and_sendlog.py",
    "test_tg_stream_routing.py", "test_tg_topic_reply_quiet.py",
    "test_unified_bus_guard.py",
    # ۲۰۲۶-۰۷-۲۸ — حلقهٔ ۷ (رأیِ صریحِ مالک «بله، وصل کن»). درایورِ اعمالِ پچ تا
    # امروز هیچ صداکننده‌ای نداشت؛ حالا دارد، پس قفل‌هایش باید سنجیده شوند نه ادعا.
    "test_code_apply_wiring.py",
    # ۲۰۲۶-۰۷-۲۸ — از رونوشتِ واقعیِ گروه: «دربارهٔ A08 تحقیق کردم — A8» ×۷.
    # شناسهٔ داخلی و اسلاگ مستقیماً به موتورِ جستجو می‌رفتند؛ نتیجه غیرصفر بود پس
    # هیچ گاردی صدایش را درنیاورد. این تست هر دو مرز را قفل می‌کند.
    "test_research_query_sanity.py",
    # ۲۰۲۶-۰۷-۲۸ — بردار ساخته می‌شد، در ایندکس شلیک می‌کرد، و در تاریخچه
    # `None` ثبت می‌شد. باگِ **ترتیب**: run() قبل از غنی‌سازی save می‌کرد.
    "test_latent_persist.py",
    # ۲۰۲۶-۰۷-۲۸ — دو فایلِ تستِ نوشته‌شده که در هیچ لیستی نبودند. همان الگوی
    # همیشگی: تست ساخته شد، به رانر وصل نشد، و «سوئیتِ سبز» بی‌آنکه بداند
    # پوششش را از دست داد. هر دو جدا اجرا و سبز شدند پیش از ثبت.
    "test_neural_loop_close.py", "test_redact_failclosed.py",
    "test_extract_json_robust.py",
    # ۲۰۲۶-۰۷-۲۸ — چهار جوابِ مالک دربارهٔ سطحِ تلگرام، تبدیل‌شده به ناوردی:
    # گروه=پاها · چتِ خصوصی=خودآگاهی · بقیه نگه‌داشته (ثبت‌شده، نه دورانداخته)
    # · ایمنی هرگز ساکت نمی‌شود · یک چیز، یک دکمه.
    "test_surface_policy.py",
    # ۲۰۲۶-۰۷-۲۸ — ریشهٔ «کارتِ ۶ساعته چهار بار در یک ساعت»: ۱۸ کادنس حالتِ
    # پنجره‌شان را در حافظه نگه می‌داشتند، پس هر بوت همه را بی‌قید شلیک می‌کرد.
    # آخرین چکِ این فایل جلوی برگشتنِ الگو را می‌گیرد، نه فقط شش نمونه را.
    "test_epoch_guard.py",
    # ⚠️ شانزدهمی عمداً نیامد: test_kill_seam_closer.py هم STOP-ORGANISM را نام
    # می‌برد و هم harness.setup ندارد — یعنی روی درختِ زنده می‌نویسد، دقیقاً تلهٔ
    # test_tg_power. تا ایزوله نشده اضافه‌اش نکن؛ اول harness بگیرد، بعد ثبت.
    # ۲۰۲۶-۰۷-۲۸ — بستهٔ `mining_os` (۳۲ تستِ سبزِ درون-بسته) از `88aaa29` تا امروز
    # **صفر صداکننده** داشت: هوکش هرگز کامیت نشد و ACTIVATION.md خطِ اشتباهی را
    # به‌عنوان محلِ اتصال اعلام می‌کرد. تست‌های خودِ بسته این را نمی‌دیدند چون همه
    # درون-بسته‌اند. این فایل call site را می‌سنجد نه شکلِ بسته را. script-native.
    "test_mining_os_wiring.py",
    # ۲۰۲۶-۰۷-۲۸ — اتاقِ چت (رأیِ مالک: «تو گروه یه جا رو بزار چت کنم … تعاملارو
    # چت‌گونه میخوام»). سه بند از چهار بندش دربارهٔ چیزی است که نباید بشود:
    # فلگ‌خاموش=بی‌اثر، مبهم=می‌پرسد، و هیچ فرمانِ خیالی تبلیغ نمی‌شود — همان
    # ۸ فرمانی که امروز صبح تبلیغ می‌شد و در هیچ باتی وجود نداشت.
    "test_chat_room.py",
    # ۲۰۲۶-۰۷-۲۸ — گاردِ برابریِ پاها (رأیِ مالک: «گروه و پاها همه‌رو اتصالات رو
    # کدنویسی کن»). چهار رجیستریِ مستقل وجود داشت که هیچ‌کدام دیگری را نمی‌دید،
    # و اختلافشان بی‌صدا بود: سه اندامِ ثبت‌شده هیچ راهی برای رسیدن نداشتند و
    # هیچ تستی قرمز نمی‌شد چون هر رجیستری **به‌تنهایی** سالم بود.
    "test_leg_parity.py",
    # ۲۰۲۶-۰۷-۲۸ — صدای پاها در گروه. ریشهٔ ۷ تاپیکِ خالی نبودِ نگاشت نبود؛
    # ارگانیسم فقط ۵ جریان تولید می‌کرد و هیچ‌کدام پا نبود. بیشترِ این تست
    # دربارهٔ **نفرستادن** است: خاموش، بی‌تغییر، لرزان، بی‌داده، بی‌اتاق.
    "test_leg_rooms.py",
    # ۲۰۲۶-۰۷-۲۸ — پل کلیدِ `keyboard` می‌خواند و روتر `reply_markup` می‌داد، پس
    # ۲۹ ردیف دکمه (queue ۱۰ · doctor ۶ · money ۵ · organs ۴ · school ۳ ·
    # heart ۱) بی‌صدا دور ریخته می‌شد. متن می‌رسید، دکمه‌ها نه، صفر خطا — و کلِ
    # مسیرِ رأیِ مالک از گروه روی همان دکمه‌هاست.
    "test_bridge_buttons.py",
    # ۲۰۲۶-۰۷-۲۸ ۱۹:۵۷ — یک پروبِ بدایزوله `power.stop_organism()` را روی درختِ
    # زنده صدا زد و ارگانیسم و مرکز ۳۰ دقیقه خوابیدند. گارد در خودِ `power.py`
    # نشست نه در تست، چون مهاجم پروبِ دست‌نویس بود نه تست. جهتِ failش عمداً
    # به‌سمتِ **اجازه** است: بستنِ ترمزِ اضطراریِ واقعی بدتر از نشانگرِ سرگردان.
    "test_power_isolation_guard.py",
    # ۲۰۲۶-۰۷-۲۸ — بستنِ حلقه‌های ذهن، بعد از ممیزیِ متخاصمِ ۱۱-ایجنتی که هر پنج
    # زیرسیستم را PARTIAL داد و هر ۶ نمرهٔ CREDIBLE را تنزل داد. الگوی واحدش:
    # «مکانیزم درست پیاده شده و دقیقاً در خطی که باید رفتار را عوض کند خاموش است».
    # هر پنج فایل جدا نوشته شد (مالکیتِ انحصاریِ فایل، بدونِ worktree چون مخزن
    # ~۴۴۰ فایلِ کامیت‌نشده دارد و worktree کدِ دیروز را می‌داد)، و هرکدام را یک
    # ایجنتِ دومِ مستقل با بازسازیِ کدِ قبل-از-فیکس راستی‌آزمایی کرد.
    # همه پشتِ فلگِ تازه و پیش‌فرض خاموش: فلگ‌خاموش = رفتارِ امروز، بایت‌به‌بایت.
    "test_selfknow_unknown_bridge.py",              # تصحیحِ مالک به شاخهٔ heuristic
    "test_selfknow_calibration.py",                 # اولین Brierِ واقعیِ سیستم
    "test_pain_calibration.py",                     # آستانهٔ درد از توزیعِ واقعی
    "test_consolidation_compress_and_recall.py",    # تثبیت: کپی → فشرده‌سازی
    "test_debate_owner_verdict.py",                 # رأیِ مالک ماندگار و بی‌تکرار
    # ۲۰۲۶-۰۷-۳۰ — هر دو plain-asserts اند (تابع‌های `t_*` + `harness.run`)، پس در
    # TESTS می‌آیند نه PYTEST_TESTS: زیرِ pytest صفر تست collect می‌شود ⇒ exit 5 ⇒
    # قرمزِ کاذبِ دائم. run_all هیچ glob/discovery ندارد ⇒ ثبت‌نشده = هرگز اجرا نشده.
    "test_hebbian_eventclock.py",                   # ساعتِ رخدادِ hebbian + سقفِ learned
    "test_watchdog_stall.py",                       # استالِ حلقه + احیای باصدا
    # ۲۰۲۶-۰۷-۳۱ — موجِ «اتصال، نه اندامِ نو» (سندِ OCTOPUS-VS-FRONTIER): پنج
    # فایل، همه plain-asserts (تابع‌های t_ + harness.run) ⇒ در TESTS، نه PYTEST.
    "test_action_durability.py",     # دفترِ idempotency/nonce ِ persisted؛ replay=NOOP؛
                                     # همین تست باگِ split/rsplit ِ CONFLICT را رو کرد
    "test_retrieval_router.py",      # حافظه در نقطهٔ تصمیم — فقط narrowing، هرگز مجوز
    "test_mission_kernel.py",        # پروندهٔ واحدِ مأموریت: timeline/resume/fsck، فقط‌خواندنی
    "test_state_write_retry.py",     # ریشهٔ VQ-STATE-WRITE-001: retry ِ os.replace + breadcrumb
    "test_action_schema_drift.py",   # دو کپیِ اعتبارسنجِ action-request — گاردِ drift
    # ۲۰۲۶-۰۷-۳۱ — اتاقِ کنترلِ پاها. دو فایلِ اول ۰۷-۳۰ نوشته شده بودند و در
    # **هیچ** لیستی نبودند (همان تلهٔ مستندِ بالا: تست ساخته شد، به رانر وصل
    # نشد). هر سه قبل از ثبت جدا اجرا و سبز شدند (۱۸/۱۸ · ۷/۷ · ۱۵/۱۵).
    "test_tg_leg_tasks.py",         # مدلِ Task ِ گروه: ۴ وضعیت، کارت، رسید
    "test_tg_group_is_legs_only.py",  # گروه legs-only: جریانِ هسته‌ای هرگز در گروه
    "test_tg_leg_commands.py",      # ۹ فرمانِ طبیعی + رفعِ مانع با ریپلای + گزارشِ روزانه
    # ۲۰۲۶-۰۷-۳۱ — اسکنِ عمیقِ تلگرام ۹ سوییتِ سبزِ دیگر را هم ثبت‌نشده یافت؛
    # از جمله test_tg_callback_emitter_parity که **دقیقاً گاردِ کارتِ مرده**
    # است و هرگز نمی‌دوید. هر ۹ تا قبل از ثبت جدا اجرا و سبز شدند.
    # (test_mining_leg عمداً ثبت نشد — ImportError ِ واقعیِ پیش‌موجود:
    # `MiningLeg` دیگر در legs/mining_leg.py نیست؛ فیکسش کارِ جداست.
    # test_studio_telegram هم self-skip است: ماژولش در worktree ِ Project-F است.)
    "test_tg_callback_emitter_parity.py",   # هر verb ِ ساخته‌شده حتماً route می‌شود
    "test_tg_input_surface_policy.py",      # گیتِ ورودی: outer/inner × DM/group
    "test_tg_surface_router.py",            # stream → (client, chat, topic)
    "test_tg_canonical_access_model.py",    # مدلِ دسترسیِ مصوب
    "test_tg_client_contract.py",           # قراردادِ کلاینتِ دو-باتی
    "test_capability_manifest_registry.py", # کاتالوگِ قابلیت‌ها
    "test_tg_hold_policy.py",               # ماشینِ حالتِ HOLD (VQ-TG-HOLD-001)
    "test_tg_route_seam.py",                # درزِ _route_send
    "test_tg_build_surface.py",             # سطحِ «بساز:» + حلقهٔ ساختِ خود
    # ۲۰۲۶-۰۷-۳۱ — حلقهٔ عملیاتی (برنچ claude/operational-loop-agi-566734):
    "test_state_write_loudness.py",              # VQ-STATE-WRITE-001: شکستِ نوشتن باصدا
    "test_mission_approval_and_receipt_critic.py",  # کارتِ A3 → صفِ مالک + منتقدِ رسید
    "test_verdict_feedback_loop.py",             # حکمِ مالک → توکن‌ها → تصمیمِ بعدی
    "test_mission_reconcile_step1.py",           # گذارِ قانونیِ Genome + واژگانِ ۱۲→۶
    # ۲۰۲۶-۰۷-۳۱ — موجِ یکپارچه‌سازی:
    "test_ledger_reanchor_2026_07_31.py",   # رگرسیونِ ترمیمِ زنجیرهٔ ledger (genesis تازه)
    "test_tg_send_receipt_schema.py",       # رسیدِ ارسال: bot_role+surface+state سه‌حالتی (gate 8)
    "test_redact_before_archive.py",        # redact قبل از hold (boundary-3: نشت در آرشیو)
    "test_tg_409_rival_poller.py",           # تشخیصِ pollerِ رقیب روی باتِ مرکز (boundary-12)
    "test_flag_load_shortfall.py",             # پیکربندیِ نصفه سرِ boot داد بزند (فروپاشیِ ۰۹:۰۷)
    "test_tg_poll_health.py",                # گوشِ مرده دیده شود: هر دورِ getUpdates ثبت + هشدارِ کوری
    "test_tg_voice_worker.py",               # ویسِ کند روی نخِ کارگر، نه روی حلقهٔ poll
    "test_tg_model_cache.py",                 # مدل یک‌بار بار شود، نه به‌ازای هر ویس
    "test_tg_voice_keep_audio.py",           # صوت فقط با فلگِ صریحِ تشخیص می‌ماند
    # ۲۰۲۶-۰۷-۳۱ — ساختِ ۴موجهٔ منشورِ UI تلگرام (۸ لِین + لِینِ سیم‌کشی):
    "test_tg_menu_contract.py",             # منوی DM ≤۱۰ ِ scope-دار + تک‌نویسندهٔ منوی inner
    "test_tg_callback_answer.py",           # هیچ تپی بی‌answer نمی‌ماند (مرگِ spinner)
    "test_tg_group_allowlist_policy.py",    # گیتِ گروه deny-by-default + گیتِ callback
    "test_tg_send_receipts.py",             # رسیدِ سه‌حالتی state/bot_role/surface در هر مسیر
    "test_tg_capture.py",                   # capture یک‌ژسته → vault (رأی ۹-۱۰)
    "test_tg_reminders.py",                 # یادآوریِ NL + سکوتِ ۲۳-۷ (رأی ۶/۸)
    "test_tg_brief.py",                     # بریفِ صبح/شب + لینکِ تاپیک (رأی ۱۱)
    "test_tg_ask_vault.py",                 # سؤال-از-vault با منبع (رأی ۹)
    "test_miniapp_gateway.py",              # گیتِ initData ِ Mini App (رأی ۲۲)
    "test_tg_leg_activation.py",            # قالبِ پای فعال‌شونده + گاردِ صفر-template
    "test_tg_weekly_review.py",             # مرورِ هفتگیِ شنبه (رأی ۱۲ + §۹)
    "test_tg_question_budget.py",           # بودجهٔ ۳۰-سؤال/هفته (رأی ۲۴)
    "test_tg_wiring_w2.py",                 # سیم‌کشیِ سریالِ همهٔ ماژول‌ها در center
    # ۲۰۲۶-۰۸-۰۱ — موجِ «هر وعده واقعی شود» (ویس، ارسالِ لید، بودجه‌ها، یتیم‌ها):
    "test_tg_wiring_w3.py",                 # سیم‌کشیِ دورِ دوم (ویس/بودجه/سؤال/یتیم)
    "test_tg_transcribe.py",                # نردبانِ متن‌سازیِ ویس + صداقتِ شکست
    "test_tg_notify_budget.py",             # سقفِ ۵ اعلانِ قطع‌کننده (منشور §۳)
    "test_tg_question_producers.py",        # اختاپوس واقعاً سؤال می‌سازد (رأی ۲۴)
    "test_tg_send_log_stats.py",            # خطِ آمارِ ضدِاسپم در پالس
    "test_tg_orphans_wired.py",             # سه ماژولِ ساخته‌شده که حالا صداکننده دارند
    "test_mail_credentials.py",             # اعتبارِ SMTP: هرگز خودِ راز را برنمی‌گرداند
    "test_tg_owner_readiness.py",           # چک‌لیستِ آمادگیِ مالک (فقط‌خواندنی)
    "test_tg_acceptance_journey.py",        # سفرِ ۶ساعتهٔ پذیرش (تستِ خودِ هارنس)
    "test_lead_pipeline.py",                # حلقهٔ لید: کشف→تحقیق→پیش‌نویس→گیر/کارت (رأی ۱۳)
    "test_lead_send_cap.py",                # سقفِ ۱۰/روز (رأی ARM ِ مالک ۰۷-۳۱) دو-لایه
    "test_lead_outbound_transport.py",      # transport ِ SMTP: بی‌creds=NOT_ARMED صادق
    # ۲۰۲۶-۰۸-۰۱ — سه شکافِ پیش از مسلح‌سازیِ لید + پروبِ دریافت.
    # ثبت عمداً مرکزی است: پنج لِینِ موازی حق نداشتند run_all را دست بزنند،
    # چون تصادمِ همین فایل امروز یک deploy را متوقف کرد.
    "test_lead_send_notify.py",            # GAP-1: ایمیلِ رفته دیگر بی‌صدا نمی‌رود (فلگ default-off)
    "test_lead_price_in_email.py",         # GAP-2: کوت بدونِ عدد کوت نیست
    "test_funnel_sent.py",                 # GAP-3: /funnel «فرستاده شد» را هم نشان می‌دهد
    "test_tg_receive_probe.py",            # پروبِ سلامتِ دریافت (رأیِ مالک ۰۸-۰۱، توکن فقط از env)
    # union از لِینِ موازی (ماینینگ/پول) — این هفت ثبت در درختِ زنده بودند
    # (پنج stage-شده، دو نه) و deploy درست حاضر نشد رویشان ff بزند. ثبت
    # افزایشی است و هر هفت فایل روی دیسک‌اند، پس union نه انتخاب.
         ]
# تست‌های خارج از _ops/tests/ (path tuyệtق)
EXTRA_TESTS = [HERE.parents[1] / "07 - Knowledge" / "Time-Architecture" / "test_fusion_sim.py",
               HERE.parents[1] / "07 - Knowledge" / "school-memory" / "test_curriculum.py",
               # ۲۰۲۶-۰۷-۳۱ — تست‌های unified_control (ثبت‌نشده = هرگز اجرا نشده):
               HERE.parent / "unified_control" / "tests" / "test_snapshot_staleness.py",
               HERE.parent / "unified_control" / "tests" / "test_snapshot_linkage.py",
               # ۲۰۲۶-۰۷-۳۱ — اعتبارسنجِ قراردادِ تلگرام (تا امروز صداکننده‌ نداشت).
               HERE.parent / "telegram_contract" / "validate_contract.py"]

# این فایل‌ها pytest-style هستند (fixtureهای monkeypatch/tmp_path) و اجرای مستقیمشان
# سبزِ دروغین می‌دهد. run_all باید واقعاً pytest را اجرا کند.
PYTEST_TESTS = {
    "test_ziman_leg.py", "test_ziman_phase2.py",
    # 2026-07-16 (audit R-04): test_ziman_wiring/biology پیش‌تر در TESTS بودند ولی نه در این
    # set → run_all آن‌ها را direct-run می‌کرد (بدونِ __main__ → صفر assert → green-lie:
    # exit 0 در حالی که زیرِ pytest واقعاً اجرا/اثبات می‌شوند). هر دو فایلِ pytest-style
    # (fixtureِ monkeypatch/tmp_path) هستند؛ این‌جا ثبت شدند تا واقعاً اجرا شوند.
    "test_ziman_wiring.py", "test_ziman_biology.py",
    "test_cartographer_leg.py", "test_cartographer_wiring.py",
    "test_blocker_fixes_2026_07_22.py",   # pytest-native (monkeypatch fixtures)
    # ۲۰۲۶-۰۷-۲۸ — همان green-lie، دوازده روز بعد. `test_synapse_sense.py`
    # pytest-style است (صفر تابعِ `t_`، صفر رانرِ `__main__`)، پس direct-run
    # صفر assert می‌دود و `exit 0` می‌دهد. زیرِ pytest **۲۰ تست، همه سبز** —
    # یعنی بیست تستِ سالم در سوئیت شمرده می‌شدند و هرگز اجرا نمی‌شدند.
    #
    # روشِ پیدا شدنش مهم‌تر از خودش است: چکِ **ساختاری** (وجودِ `__main__`) این
    # را نگرفت و ۵۰ کاذب داد. تنها چیزی که گرفت، اجرای **تجربیِ** هر ۳۶۶ فایلِ
    # غیرpytest و نگه‌داشتنِ آن‌هایی بود که `exit 0` با **صفر خروجی** می‌دهند.
    # اگر روزی دوباره شک کردی، همان را اجرا کن نه grep.
    "test_synapse_sense.py",
    # ۲۰۲۶-۰۸-۰۱ — سومین تکرارِ همان green-lie، این بار Mining (رأیِ مالک: گزینهٔ الف).
    # `test_mining_wiring.py` در `TESTS` بود ولی نه این‌جا → direct-run، صفر assert،
    # `exit 0`. زیرِ pytest واقعیتش **۶ قرمز / ۴ سبز** است.
    #
    # نکتهٔ تلخ: ممیزیِ R-04 (۰۷-۱۶) همین فایل را «phantomِ عمداً کنارگذاشته» ثبت
    # کرده بود (کامنتِ داخلِ `TESTS`)، ولی جاروی یتیم‌ها (۰۷-۲۰) آن را به‌عنوان
    # «سبزِ روی‌دیسک» برگرداند — چون معیارِ سبزبودن را از همان direct-runِ معیوب
    # پرسید. یعنی دروغِ سبز باعثِ ثبتِ خودش شد. اگر جاروی بعدی هم همان را بپرسد،
    # دوباره برمی‌گردد؛ معیار باید pytest باشد نه exit code ِ اجرای مستقیم.
    #
    # ثبت این‌جا سوییت را **صادقانه قرمز** می‌کند: ۵ قرمز `AttributeError` است
    # (`wiring.make_mining_leg`/`mining_beat` وجود ندارند — Mining با قراردادِ
    # `_BUSINESS_LEGS_SPEC` ساخته شد، نه الگوی کارخانه‌ای) و ۱ قرمزِ واقعیِ رندر
    # (تلمتریِ `mining_os` به دایجست وصل نشده). تفصیل و دو تصمیمِ باقی‌مانده:
    # `00 - Inbox/AGENT_QUESTIONS.md` — ورودیِ ۲۰۲۶-۰۸-۰۱.
    "test_mining_wiring.py",
}

# ۲۰۲۶-۰۷-۳۰ — «قرمزِ کاذبِ ۱۲۰». پاسِ اولِ سوییت بدونِ capture اجرا می‌شد، پس هر
# ~۳۶۶ فرزند کنسولِ مشترکِ والد را ارث می‌بردند. زیرِ بار، فرزندی که سالم است و
# `exit 0` می‌دهد در **flushِ پایانیِ مفسر** شکست می‌خورد و ۱۲۰ برمی‌گرداند؛ رانر
# ۱۲۰ را عیناً مثلِ AssertionError می‌شمرد. شواهدِ روی دیسک در `_flaky`:
#     ۳۳ × exit(1)=120 exit(2)=0   ← ۳۳ تستِ سالم که در یک اجرا قرمز شمرده شدند
#      ۶ × exit(1)=1   exit(2)=1   ← قرمزِ واقعی و پایدار
#      ۲ × exit(1)=1   exit(2)=0   ← لرزشِ واقعی (حکمِ تست بود، نه محیط)
# و هر `failed` غیرخالی `revoke_capability()` را صدا می‌زند.
#
# ⚠️ ۱۲۰ **مبهم** است، نه بی‌ضرر. تصحیحِ ۲۰۲۶-۰۷-۳۰ (بازبینیِ متخاصم، اثباتِ
# تجربی): وقتی `Py_FinalizeEx()` شکست می‌خورد، مفسر exitcode را با ۱۲۰
# **بازنویسی** می‌کند — یعنی حکمِ واقعی را دور می‌ریزد، نه اینکه جای حکمِ غایب
# بنشیند. پروبِ چهارحالته زیرِ sinkِ شکسته: exit(0)→120 · exit(1)→120 ·
# raise AssertionError→120 · exit(3)→120. پس «۱۲۰ دیدم ⇒ تست سالم بود» غلط است؛
# یک AssertionErrorِ واقعی هم همین کد را می‌دهد.
# نتیجهٔ عملی: از این کد **نمی‌توان** به سالم‌بودنِ تست رسید. تشخیصِ درست باید
# stdout/stderr ِ پاسِ اول را برای شاهدِ شکست (Traceback/AssertionError/FAILED)
# بسنجد — که hunkِ capture ِ همین کامیت آن را در دسترس گذاشت.
INFRA_EXIT_CODES = frozenset({120})   # کدِ مفسر — **مبهم**؛ به‌تنهایی حکم نیست


def is_infra_false_red(first_rc: int, retry_rc: int) -> bool:
    """**فقط برچسب‌گذاریِ تشخیصی — هیچ تصمیمِ scoring به این تابع بند نیست.**


    True یعنی «شاید artifactِ کنسول باشد»، نه «تست سالم است». پاک‌کردنِ برچسب از
    `failed` بر پایهٔ این تابع در ۲۰۲۶-۰۷-۳۰ **عمداً غیرفعال شد**: با retryِ سبز،
    بچه‌ای که AssertionError داده بود و flushش شکسته بود به‌غلط PASS/MARK می‌گرفت
    ⇒ fail-OPEN روی گیتِ capability/پول. رانر fail-closed می‌مانَد.
    """
    return retry_rc == 0 and first_rc in INFRA_EXIT_CODES


if __name__ == "__main__":
    failed = []
    for t in TESTS + EXTRA_TESTS:
        p = HERE / t          # نام‌های نسبیِ TESTS → _ops/tests؛ EXTRA_TESTSِ absolute دست‌نخورده می‌ماند
        label = p.name
        print(f"\n── {label} " + "─" * (60 - len(label)))
        cmd = ([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(p)]
               if label in PYTEST_TESTS else
               [sys.executable, "-X", "utf8", str(p)])
        # capture در **پاسِ اول** هم لازم است: هر فرزند به لولهٔ اختصاصیِ خودش
        # flush می‌کند، نه به کنسولِ مشترکِ والد — ریشهٔ ۱۲۰ همین اشتراک بود.
        # والد خروجی را روی همان جریانِ اصلی بازپخش می‌کند تا لاگ کم‌ نشود.
        r = subprocess.run(cmd, cwd=str(p.parent), timeout=300,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.stdout:
            sys.stdout.write(r.stdout)
        if r.stderr:
            sys.stderr.write(r.stderr)   # unittest پیشرفتش را روی stderr می‌نویسد
        sys.stdout.flush()
        sys.stderr.flush()
        if r.returncode != 0:
            failed.append(label)   # پیش‌فرضِ fail-closed؛ فقط artifactِ محیط پاکش می‌کند
            # ۲۰۲۶-۰۷-۲۸ — تشخیصِ لرزش. الگوی ثبت‌شده: ~۴۰٪ اجراها **یک** تستِ
            # متفاوت قرمز می‌شود که تنها اجرا شود سبز است. چهار فرضیه (ارگانیسمِ
            # زنده، پروسهٔ معلق، قفلِ ۳ثانیه‌ای، بار) هیچ‌کدام اثبات نشد — چون
            # تنها چیزی که از هر اجرا می‌ماند **نامِ تست** است، نه شواهدش.
            #
            # پس به‌جای فرضیهٔ پنجم: همان تست بلافاصله دوباره و **با خروجیِ
            # کامل** اجرا می‌شود. اگر بارِ دوم سبز شد، لرزش تأیید می‌شود و
            # خروجیِ قرمز روی دیسک می‌ماند تا دفعهٔ بعد حدس نزنیم.
            try:
                _d = HERE / "_flaky"
                _d.mkdir(exist_ok=True)
                _r2 = subprocess.run(cmd, cwd=str(p.parent), timeout=300,
                                     capture_output=True, text=True,
                                     encoding="utf-8", errors="replace")
                _tag = "سبز-بارِ-دوم" if _r2.returncode == 0 else "قرمزِ-پایدار"
                if is_infra_false_red(r.returncode, _r2.returncode):
                    # ۲۰۲۶-۰۷-۳۰ — پاک‌کردنِ برچسب **عمداً غیرفعال شد** (بازبینیِ متخاصم).
                    # فرضِ «۱۲۰ هرگز حکمِ تست نیست» غلط است: اگر Py_FinalizeEx شکست
                    # بخورد، مفسر exitcode را با ۱۲۰ **بازنویسی** می‌کند — پس exit(1)
                    # و حتی AssertionError هم ۱۲۰ می‌شوند. اثباتِ end-to-end: بچه‌ای
                    # که AssertionError می‌دهد و flushش می‌شکند، با retryِ سبز به‌غلط
                    # MARK می‌گرفت ⇒ **fail-OPEN روی گیتِ پول** (بدتر از باگی که
                    # می‌خواست ببندد). تا تصمیمِ مالک: فقط مشاهده ثبت می‌شود و برچسب
                    # در failed می‌ماند (fail-closed). رفعِ درست = سنجشِ stdout/stderr
                    # ِ پاسِ اول برای شاهدِ شکست، که حالا capture می‌شود.
                    _tag += (f" · مشکوک به artifactِ کنسول (exit {r.returncode}) — "
                             "برچسب نگه داشته شد (fail-closed)")
                (_d / f"{label}.txt").write_text(
                    f"# {label} · {_tag}\n"
                    f"# exit(1)={r.returncode} exit(2)={_r2.returncode}\n\n"
                    f"--- stdout ---\n{_r2.stdout}\n"
                    f"--- stderr ---\n{_r2.stderr}",
                    encoding="utf-8")
                print(f"   ↻ اجرای دوم: {_tag} → tests/_flaky/{label}.txt")
            except Exception as _e:  # noqa: BLE001 — تشخیص هرگز سوییت را نمی‌کشد
                print(f"   ↻ ثبتِ لرزش نشد: {type(_e).__name__}")
    print("\n" + "=" * 66)

    # A3: markerِ capability فقط با اجرای سبزِ کاملِ سوئیت نوشته می‌شود (با fingerprintِ کدِ پول)؛
    # هر شکست revokeش می‌کند (fail-closed). تنها یکی از سه شرطِ گیت است — به‌تنهایی هیچ باز نمی‌کند.
    # markerِ capability در همان درختی نوشته می‌شود که تست شد (REAL_VAULT)، نه vault زنده —
    # اجرای worktree هرگز marker/state درختِ زنده را refresh/revoke نمی‌کند.
    _rv = os.environ.get("REAL_VAULT")
    if _rv and not os.environ.get("ORG_ROOT"):
        os.environ["ORG_ROOT"] = _rv
    sys.path.insert(0, str(HERE.parent / "budget"))
    try:
        import capability_gate as _cg
    except Exception as _e:  # noqa: BLE001 — گزارشِ سوئیت نباید به import گره بخورد
        _cg = None
        print(f"(هشدار: capability_gate لود نشد، marker دست‌نخورده: {_e})")

    if failed:
        if _cg:
            _cg.revoke_capability()
        print(f"❌ شکست: {', '.join(failed)}  (capability revoked)")
        sys.exit(1)
    if _cg:
        _cg.mark_capability("green: " + ",".join(TESTS))
    print(f"✅ همهٔ {len(TESTS)} فایل تست سبز  (capability marker با fingerprint نوشته شد)")
