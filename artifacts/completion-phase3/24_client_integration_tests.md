# Client integration tests

Ran against an ephemeral `serve(..., port=0)` and tempfile DB, not the live `organism.db`.

Command:

```text
python3 -m unittest ofn.organism.tests.test_checkpoint_watcher ofn.organism.tests.test_get_purity_and_lan ofn.organism.tests.test_memory_gate ofn.organism.tests.test_kernel ofn.organism.tests.test_life ofn.organism.tests.test_raise ofn.organism.tests.test_learn -q
```

Result: `Ran 74 tests ... OK`

Coverage:

- soak-equivalent GET `/health` without token on loopback
- GET `/api/v1/organism` with and without token
- 401 is not retried
- GET cognitive state delta is 0 under `OCTOPUS_GET_PURE=1`
- GET `/api/v1/eval` is 405

Gateway and afferent do not call 8090; they were not restarted.
