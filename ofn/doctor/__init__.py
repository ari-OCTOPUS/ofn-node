#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ofn.doctor — Lane LB: the self-completing doctor (read-only diagnosis,
falsifiable prescriptions, self-backlog, proposal destiny, verifiable receipts).

Charter: organs diagnose and propose; they do not patch or promote themselves
(LAB-DOCTOR-CONTRACT.yaml, principle). The round over a source vault is
strictly read-only; changes travel PR or owner ruling only.
"""
from .receipts import ReceiptLog, sha256_file, sha256_text
from .round import DoctorRound, Finding, RoundResult, SourceNotFoundError, tree_hash
from .backlog import SelfBacklog, BACKLOG_FIELDS
from .destiny import DestinyEngine, Proposal, Decision, OUTCOMES
from .contract_map import REQUIREMENTS, requirement_stats, validate_experiment
from .prescription import validate_prescription

__version__ = "0.1.0"
