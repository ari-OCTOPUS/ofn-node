# L7 handoff — NATS_LEAF_MIRROR EventEnvelope PR

Owner vote correction: NATS_LEAF_MIRROR supersedes LOCAL_CRDT.

PR target: rebase https://github.com/ari-OCTOPUS/ofn-node/pull/238
Branch: cursor/event-envelope-local-crdt-3830 (contents retargeted; name historical)

Publish notes: additive EventEnvelope + disabled nats leaf/mirror init JSON.
Do not enable. Do not cut over writers. Do not edit FROZEN.lock.
