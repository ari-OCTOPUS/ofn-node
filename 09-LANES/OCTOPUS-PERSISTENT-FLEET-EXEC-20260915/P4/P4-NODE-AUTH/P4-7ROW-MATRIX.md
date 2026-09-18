# P4 7-row role matrix receipt

stamp_utc: 2026-09-15T03:44:56Z
method: mesh_ssh ?? fingerprint: `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as`
ARCH: 8b0a5e03??? ?? SEC: db62b335??? ?? schema: 47d76eeb???

| node_id | bind_role | auth_status | lease_eligible | commander | may_authorize | notes |
|---|---|---|---|---|---|---|
| 138 | commander | OK | False | True | False | sole commander / issuer |
| 180 | quality_restore_copy_RO | OK | False | False | False | quality + restore_copy_RO ??? never commander |
| 182 | lab_witness | OK | False | False | False | lab_witness ??? lease false |
| 100 | knowledge_retrieve | OK | True | False | False | knowledge_retrieve |
| 160 | knowledge_prep | OK | True | False | False | knowledge_prep |
| 193 | model_infer | OK | True | False | False | model_infer (not T3 model-server service) |
| 114 | eval_batch | OK | True | False | False | eval_batch |

HOLD customer_send ?? STOP before P5 ?? no dual-commander
