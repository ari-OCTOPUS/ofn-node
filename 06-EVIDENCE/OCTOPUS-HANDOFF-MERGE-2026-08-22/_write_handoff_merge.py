import json
from pathlib import Path

dest = Path(r'F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22')
merged = dest / 'merged'
merged.mkdir(parents=True, exist_ok=True)
from_pi = dest / 'from-pi'

handoff = json.loads((from_pi / 'LAPTOP-AGENT-HANDOFF.json').read_text(encoding='utf-8'))
owner = json.loads((from_pi / 'OWNER_REVIEW_DECISION.json').read_text(encoding='utf-8'))
doctor = json.loads((from_pi / 'doctor-latest.json').read_text(encoding='utf-8'))

local_state = {
  "schema": "octopus.local-state-card.v1",
  "written_at_local": "2026-08-22T19:15:00+10:00",
  "timezone": "Australia/Sydney (UTC+10)",
  "board": {
    "hostname": "DietPi",
    "board_id": handoff.get('board', {}).get('board_id'),
    "ip": "192.168.0.182",
    "boot_id": "4dbf4819-c7dc-4224-bb3b-2650f9d2aa6c",
    "uptime_observed": "4 days, 22:46 (observed 2026-08-22T19:13+10)"
  },
  "services_active_observed": [
    "octopus-sensorium", "octopus-stability", "nats-server",
    "octopus-reflex", "octopus-world-model", "octopus-skill-tracker",
    "octopus-metacontrol", "dropbear"
  ],
  "listeners": {
    "mqtt_1883": "CLOSED_NO_LISTENER_OBSERVED",
    "stability_9101": "LOOPBACK_ONLY_PER_HANDOFF_CONTRACT (LAN open auth may be pending runbook)"
  },
  "wave0": "KEEP_LOCKED",
  "readiness_profile": "WAVE0_OBSERVE_ONLY",
  "actuator_authority": "NONE",
  "reflex_armed": False,
  "doctor_live_status": doctor.get('status'),
  "doctor_blocking_failed_ids": doctor.get('blocking_failed_ids'),
  "doctor_run_id": doctor.get('run_id'),
  "doctor_timestamp_utc": doctor.get('timestamp'),
  "sot_note": "LOCAL-STATE-CARD + CHG receipts under 06-EVIDENCE are SoT for live Pi metrics. Narrative alone is not evidence.",
  "receipt_refs": [
    "06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22/SOAK-POST-ABD-ACK.json",
    "06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-C-NATS-2026-08-22/RECEIPT-CHG-C-ACK.json",
    "06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/from-pi/doctor-latest.json"
  ]
}
(merged / 'LOCAL-STATE-CARD.json').write_text(json.dumps(local_state, indent=2) + '\n', encoding='utf-8')

live = dict(handoff.get('live', {}))
live['updated_note'] = "2026-08-22: readiness still WAVE0_OBSERVE_ONLY; ABD+C PASS does not change observe-only / locked actuators"
live['mqtt_1883'] = "CLOSED"
live['actuator_authority'] = "NONE"

gap001 = dict(handoff.get('gap001', {}))
gap001['merge_note'] = "Aug17 OWNER_REVIEW listed gap_001_open as FAIL — SUPERSEDED by this handoff TESTED_PASS + later ABD soak PASS"

gap002 = dict(handoff.get('gap002', {}))
gap002['merge_note'] = "Doctor latest may still flag gap002_registry; treat as open doctor check, not ABD+C failure. Checkpoint/registry settle remains laptop sign path."

stability = dict(handoff.get('stability', {}))
stability['lan_9101_auth'] = "OCTOPUS-ORANGEPI-LAN-9101-20260822 file-auth exists; runbook/execute may be pending; do not assume LAN open"

do_not = list(dict.fromkeys(list(handoff.get('do_not', [])) + [
  "unlock WAVE0 / arm reflex / open MQTT 1883 without explicit owner execute that is separate from file-auth",
  "delete OWNER_REVIEW narrative — equal value; archive and merge only",
  "git add -A",
  "export or rewrite keys"
]))

owner_merged = {
  "schema": "octopus.owner-review-decision.merged.v1",
  "written_at_local": "2026-08-22T19:15:00+10:00",
  "timezone": "Australia/Sydney (UTC+10)",
  "merge_policy": "EQUAL_VALUE_INTEGRATE_NOT_DELETE",
  "owner_authorization": "OCTOPUS-HANDOFF-MERGE-2026-08-22",
  "sources": {
    "owner_review_decision_aug17": {
      "path_live_pi": "/var/lib/octopus/state/OWNER_REVIEW_DECISION.json",
      "archive": "archive/OWNER_REVIEW_DECISION.json",
      "written_at": owner.get('written_at')
    },
    "owner_review_pack": "archive/owner-review/",
    "owner_review_final_pack": "archive/owner-review-final/",
    "laptop_agent_handoff_aug17": {
      "path_live_pi": "/var/lib/octopus/state/LAPTOP-AGENT-HANDOFF.json",
      "archive": "archive/LAPTOP-AGENT-HANDOFF.json",
      "written_at": handoff.get('written_at')
    },
    "doctor_latest": {
      "path_live_pi": "/var/lib/octopus/state/doctor/latest.json",
      "archive": "archive/doctor-latest.json",
      "run_id": doctor.get('run_id'),
      "status": doctor.get('status')
    }
  },
  "preserved_from_owner_review_aug17": {
    "decision": owner.get('decision'),
    "current_wave": owner.get('current_wave'),
    "actuator_authority": owner.get('actuator_authority'),
    "executed_actions": owner.get('executed_actions'),
    "planner_invocations": owner.get('planner_invocations'),
    "authority_changed": owner.get('authority_changed'),
    "oa_t7_created": owner.get('oa_t7_created'),
    "oa_a0_created": owner.get('oa_a0_created'),
    "hardware_touched": owner.get('hardware_touched'),
    "candidate_wired_to_live": owner.get('candidate_wired_to_live'),
    "do_not_call_audit_head_seq_266": owner.get('do_not_call_audit_head_seq_266'),
    "narrative_rule": "Narrative is not evidence (see archive/owner-review/NARRATIVE_NOT_EVIDENCE.md)"
  },
  "superseded_claims": [
    {
      "claim": "doctor FAIL with blocking gap_001_open + gap002_registry as live operational posture",
      "was": {"doctor": "FAIL", "blocking_failed": owner.get('blocking_failed'), "as_of": "2026-08-17"},
      "now": "Aug17 gap_001_open SUPERSEDED: handoff recorded gap001 TESTED_PASS post-reboot; ABD soak PASS 2026-08-22. gap002_registry may still appear in doctor checks — doctor artifact pending registry/checkpoint settle, NOT ABD+C failure.",
      "evidence": [
        "from-pi/LAPTOP-AGENT-HANDOFF.json gap001.status=TESTED_PASS",
        "06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22/SOAK-POST-ABD-ACK.json result=PASS",
        "06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-C-NATS-2026-08-22/RECEIPT-CHG-C-ACK.json result=C1_PASS_C2_NOT_NEEDED"
      ]
    },
    {
      "claim": "ready_for_bounded_transition / next_action still blocked solely by Aug17 GAP-001 maintenance window",
      "was": owner.get('next_action'),
      "now": "Operational CHG ABD+C (C1) PASS. WAVE0 remains KEEP_LOCKED by owner posture, not by Aug17 gap_001_open.",
      "evidence": ["SOAK-POST-ABD-ACK.json", "RECEIPT-CHG-C-ACK.json wave0=LOCKED"]
    }
  ],
  "live_current_truth": {
    "decision": "KEEP_WAVE0_LOCKED",
    "current_wave": "WAVE0_OBSERVE_ONLY",
    "actuator_authority": "NONE",
    "mqtt_1883": "CLOSED",
    "abd_c_status": "PASS (CHG-A/B/D soak PASS; CHG-C C1_PASS_C2_NOT_NEEDED)",
    "chg_e": "AUTHORIZED_FILE_ONLY may be pending sensoriom runbook",
    "doctor_torch_lan9101": "AUTHORIZED_FILE_ONLY may be pending runbooks; mutate_device false on laptop auth files",
    "keys": "IN_PLACE_OK; export/rewrite FORBIDDEN",
    "money_webhook_work_pump": "laptop SoT; Pi N/A; Center restart deferred until Phase-3 green",
    "phase3": {
      "CONTROL_URL_canonical": "https://cp.master-painting.com",
      "ofn_gates_chg": "DONE on Board2",
      "prove": "pending (Cloudflare 530 observed on healthz/pull)"
    },
    "executed_actions": 0,
    "planner_invocations": 0,
    "hardware_touched": False,
    "ready_for_bounded_actuator_transition": False
  },
  "doctor_live_vs_receipts": {
    "doctor_latest_status": doctor.get('status'),
    "doctor_blocking_failed_ids": doctor.get('blocking_failed_ids'),
    "interpretation": "Doctor may still report FAIL/gap002_registry. That does NOT override ABD+C PASS receipts or KEEP_WAVE0_LOCKED. Do not issue OA-T7 / unlock from doctor FAIL alone."
  }
}
(merged / 'OWNER_REVIEW_DECISION.merged-2026-08-22.json').write_text(json.dumps(owner_merged, indent=2) + '\n', encoding='utf-8')

handoff_merged = {
  "schema": "octopus.laptop-agent.handoff.merged.v1",
  "written_at_local": "2026-08-22T19:15:00+10:00",
  "timezone": "Australia/Sydney (UTC+10)",
  "merge_policy": "EQUAL_VALUE_WITH_OWNER_REVIEW",
  "owner_authorization": "OCTOPUS-HANDOFF-MERGE-2026-08-22",
  "supersedes_narrative_only": "archive/LAPTOP-AGENT-HANDOFF.json (Aug17) — archived, not deleted",
  "board": handoff.get('board'),
  "live": live,
  "milestone": handoff.get('milestone'),
  "gap001": gap001,
  "gap002": gap002,
  "registry": handoff.get('registry'),
  "fusion_s1": handoff.get('fusion_s1'),
  "stability": stability,
  "reflex_a0": handoff.get('reflex_a0'),
  "cognition": handoff.get('cognition'),
  "owner_review_merged": {
    "decision": "KEEP_WAVE0_LOCKED",
    "equal_value_with": "OWNER_REVIEW_DECISION + owner-review packs",
    "merged_doc": "merged/OWNER_REVIEW_DECISION.merged-2026-08-22.json",
    "narrative_not_evidence": True
  },
  "chg_rollout_2026_08_22": {
    "ABD": "PASS (SOAK-POST-ABD-ACK)",
    "C": "C1_PASS_C2_NOT_NEEDED; wave0 LOCKED",
    "E": "authorized file-only; may be pending",
    "torch": "authorized file-only; may be pending",
    "doctor_autopatch": "companion readonly rerun authorized; auto-patch still forbidden on Pi unless separate grant"
  },
  "do_not": do_not,
  "laptop_agent_playbook_delta_2026_08_22": [
    "Read merged CURRENT-TRUTH.md in this package before acting",
    "Treat LOCAL-STATE-CARD.json + CHG receipts as SoT for live Pi metrics",
    "WAVE0 remains KEEP_LOCKED; MQTT 1883 CLOSED; actuator_authority=NONE",
    "Money/webhook/work_pump: laptop SoT; Pi N/A; defer Center restart until Phase-3 green",
    "Phase-3 CONTROL_URL canonical https://cp.master-painting.com; OFN gates CHG done on Board2; prove still pending",
    "Keys: use in-place only; export/rewrite forbidden",
    "Do not treat Aug17 OWNER_REVIEW doctor FAIL gaps as current operational blockers where receipts show PASS"
  ],
  "preserved_valuable_from_aug17_handoff": {
    "ssh_facts": handoff.get('board', {}).get('ssh'),
    "playbook": handoff.get('laptop_agent_playbook'),
    "do_not_list": handoff.get('do_not'),
    "stability_tunnel_contract": handoff.get('stability'),
    "reflex_advisory": handoff.get('reflex_a0'),
    "inbound_paths": {
      "to_laptop": "/var/lib/octopus/inbound/TO-LAPTOP/",
      "signed_registry": "/var/lib/octopus/inbound/SIGNED-REGISTRY-BUNDLE/",
      "signed_checkpoint": "/var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/"
    }
  }
}
(merged / 'LAPTOP-AGENT-HANDOFF.merged-2026-08-22.json').write_text(json.dumps(handoff_merged, indent=2) + '\n', encoding='utf-8')

print('OK')
for p in sorted(merged.glob('*')):
    print(p.name, p.stat().st_size)
