# MP-05 — Register the ruling record in DECISIONS O-5 (OPEN)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

Seven rulings and the P0 gate were answered on 2026-08-31 and captured in a
status file on a side branch, but the canonical decision register on `main`
still ends at the surgery-series entries and contains no O-5 section. The
source document points O-5 at a vault file, so the record currently has two
candidate homes and no authoritative one.

## Forbidden

Rewriting an existing decision. Paraphrasing an owner sentence. Choosing the
file location. Publishing vault content.

## Steps

1. Report both candidate homes: the surgery `DECISIONS.md` on `main`, and the
   vault reference named in the revenue map. State which is reachable from this
   host and which is not.
2. Report every ruling with its verbatim owner sentence, its date, and what it
   opened or closed. Mark the two partial rulings explicitly.
3. ASK Q1: does O-5 live in the repository decision register on `main`, in the
   vault with an export later, or in both with one marked mirror?
4. ASK Q2: are the partial rulings (4 and 6) recorded as `PARTIAL` or split
   into answered and open sub-rulings?
5. ASK Q3: does registering O-5 supersede the side-branch status file, or do
   both stand with a pointer?
6. Write only into the location the owner named. Preserve every prior entry
   byte-for-byte.

## Expected output

An O-5 section containing one row per ruling: id, verbatim answer, date, opened,
still-open, and evidence link. Plus a receipt listing the questions and answers.

## Done when

Exactly one authoritative O-5 location exists, and every other copy is labelled
a mirror.
