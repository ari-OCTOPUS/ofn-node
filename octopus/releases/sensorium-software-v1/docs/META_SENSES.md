# META_SENSES

092 anomaly: Shadow, MAD/CUSUM/rate/missing/invalid-transition/rules. No enforcement.
095 contradiction: Shadow, CON-R001..R014. Cannot overwrite source observations.
096 uncertainty: plugin ready, Registry v5 MANIFEST_ONLY.
097 novelty: plugin ready, novelty≠anomaly, Registry v5 MANIFEST_ONLY.
099 policy/safety: plugin ready, may propose DEGRADED/FAILED_SAFE, cannot act.
100 provenance: plugin ready, grades evidence quality only.

Cycles 092→092, 095→092, self-ingest of 096/097/100 are denied.
