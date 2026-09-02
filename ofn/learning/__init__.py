#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ofn.learning — shadow-only economic learning loop (owner order 2026-09-02).

OBSERVE → VERIFY RECEIPT → LINK ACTION CHAIN → SCORE OUTCOME →
EXTRACT LESSON → PROPOSE EXPERIMENT → HUMAN-GATED PR → OBSIDIAN RECEIPT.

This package observes and learns; it never sends, never authorizes, never
merges, never touches production models, and never writes spine events.
"""
from .receipts import PaymentReceipt, ReceiptVerifier
from .chain import ActionChain, ActionChainLinker
from .scorer import OutcomeScore, OutcomeScorer
from .lessons import Lesson, LessonExtractor
from .experiments import Experiment, ExperimentProposer, Proposal
from .ledger import EconomicLearningLedger

__version__ = "0.1.0"
