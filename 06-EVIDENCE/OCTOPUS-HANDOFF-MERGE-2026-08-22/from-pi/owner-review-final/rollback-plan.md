# rollback-plan

Doctor script backup:

```
cp /var/lib/octopus/state/config-history/octopus_doctor_readonly.py.pre-honest-checks /opt/octopus/scripts/octopus_doctor_readonly.py
```

backup sha256: `sha256:4dc4458efc681169771594a3532033fb65da250fb6ca6d7efac6393886b4ea76`

Shadow candidate is unused by live WM. Removing it does not change live predictions:

```
# optional; live services do not import these files
# rm /opt/octopus/cognition/src/octopus_cognition/world_model/interaction_candidate.py
```

Do not restart services. Do not reboot. Do not restore unsigned GAP-002 (signature already verified).
Do not copy private keys.
