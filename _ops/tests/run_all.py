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
         "test_chrono_heartbeat.py", "test_chrono_langar.py",
         "test_telegram_channel.py", "test_telegram_group_allowlist.py",
         "test_leg.py", "test_doctor.py",
         "test_phase5.py", "test_spectral.py", "test_chamber.py",
         "test_calibration.py", "test_box.py", "test_evolution.py",
         "test_box_b134.py", "test_sensory.py", "test_rhythm.py",
         "test_cockpit.py", "test_project_f.py", "test_studio_telegram.py",
         "test_live_loop.py", "test_proposal_buttons.py", "test_dual_brain.py", "test_acquisition.py",
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
         "test_rfc_sweep.py", "test_consolidation_distinguish.py", "test_gate_sweep.py",
         "test_latent_space.py", "test_encoders.py", "test_consolidation_latent.py",
         "test_bcm_forgetting.py", "test_sparse_filter.py", "test_chamber_temperature.py",
         "test_fisher.py", "test_telegram_rfc_router.py",
         "test_cockpit_v2.py",
         "test_heart_math.py", "test_heart_producers.py",
         "test_heart_control.py", "test_heart_loop.py", "test_heart_work.py",
         "test_needs_nudge.py", "test_cortex.py", "test_live_cockpit.py",
         "test_telegram_poll_e2e.py", "test_self_improve.py",
         "test_p0_security_fixes.py", "test_httpauth.py", "test_go_live.py",
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
         "test_tg_api.py", "test_tg_render.py", "test_tg_center.py",
         "test_tg_power.py",   # 2026-07-17: مرکزِ فرماندهی (مکثِ تک‌پا + ردهٔ قدرتِ دوکلیک)
         "test_code_autonomy.py",
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
         "test_accountant.py", "test_txn_store.py", "test_attributor.py",
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
         ]
# تست‌های خارج از _ops/tests/ (path tuyệtق)
EXTRA_TESTS = [HERE.parents[1] / "07 - Knowledge" / "Time-Architecture" / "test_fusion_sim.py",
               HERE.parents[1] / "07 - Knowledge" / "school-memory" / "test_curriculum.py"]

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
}

if __name__ == "__main__":
    failed = []
    for t in TESTS + EXTRA_TESTS:
        p = HERE / t          # نام‌های نسبیِ TESTS → _ops/tests؛ EXTRA_TESTSِ absolute دست‌نخورده می‌ماند
        label = p.name
        print(f"\n── {label} " + "─" * (60 - len(label)))
        cmd = ([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(p)]
               if label in PYTEST_TESTS else
               [sys.executable, "-X", "utf8", str(p)])
        r = subprocess.run(cmd, cwd=str(p.parent), timeout=300)
        if r.returncode != 0:
            failed.append(label)
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
