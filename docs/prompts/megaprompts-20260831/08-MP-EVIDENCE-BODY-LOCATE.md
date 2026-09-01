# MP-08 — Locate the evidence body before any verdict (BLOCKED)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

The canonical manifest records the observatory implementation, the strategy
module and the live-store verifier as not found at the current head, classifies
the situation as body-not-on-this-host, and marks both Brier values
not-reproduced with the resolved sample count not reproducible. A separate risk
entry accepts this as a gap rather than a defect. Consequently no measurement
quality verdict can be issued from this host, and merging code does not create
the missing body. Every attempt so far has produced a verdict from the wrong
host.

## Forbidden

Issuing any statistical verdict. Reconstructing a strategy, verifier or
database by copying formulas or values out of documentation. Emitting a
not-found result as a critical finding when the file is simply on another host.
Opening a database in write mode. Treating a listening loopback port as proof
that a tunnel or a service is alive.

## Steps

1. Search the current host exhaustively for the three named artefacts and for
   the evidence database. Report absolute paths or `absent`, with the search
   command and its hash.
2. If absent, emit exactly `BODY=not_on_this_host`. `NONE` is permitted only
   after a read-only open of a real file where no candidate formula reproduces
   the stored hash.
3. Report which hosts are candidates for holding the body, based only on written
   evidence, and state the evidence for each candidate.
4. ASK Q1: which host holds the evidence store, and how does this session reach
   it — or is the answer that it must be run there instead?
5. ASK Q2: if the body is unrecoverable, does the rebuild start from a versioned
   fixture with independent producer/scorer/verifier boundaries, or is the
   measurement dimension formally recorded as absent?
6. ASK Q3: the two documented states of the hash formula conflict across the
   same day — which timestamp is authoritative?
7. ASK Q4: does the sample-count threshold discrepancy get resolved by the dated
   amendment, or by re-deriving it from the checker?
8. Do not touch loopback ports. Do not build a bundle.

## Expected output

`docs/octopus-surgery/receipts/BODY-LOCATE-<date>.yaml` with per-artefact
presence, the `BODY=` verdict, candidate hosts with evidence, and the four
answers.

## Done when

The body is located on a named host, or the measurement dimension is formally
recorded as absent by owner ruling. Neither outcome is chosen by the agent.
