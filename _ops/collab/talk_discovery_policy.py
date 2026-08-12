#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""talk_discovery_policy.py — legacy Talk Discovery policy API.

Prefer ADR-033 `policy.talk_gate` / `policy.policy_gate` for new call sites.
Collaborator may produce draft responses. Chat input stays untrusted.
EXTERNAL_SEND / harvest / CRM / policy mutation stay hard-forbidden even with approval.
Episodic *semantic* writes need owner_approval_id; content-free digests are not this action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TalkAction(str, Enum):
    RESPOND_DRAFT = "respond_draft"
    RETRIEVE_CONTEXT = "retrieve_context"
    WRITE_EPISODIC_MEMORY = "write_episodic_memory"
    WRITE_SEMANTIC_MEMORY = "write_semantic_memory"
    EXTERNAL_SEND = "external_send"
    ENABLE_HARVEST = "enable_harvest"
    CRM_MUTATION = "crm_mutation"
    POLICY_MUTATION = "policy_mutation"


@dataclass(frozen=True)
class TalkDecision:
    allowed: bool
    reason: str
    requires_owner_approval: bool = False


class TalkDiscoveryPolicy:
    READ_ONLY_ALLOWED = {
        TalkAction.RESPOND_DRAFT,
        TalkAction.RETRIEVE_CONTEXT,
    }

    OWNER_APPROVAL_ONLY = {
        TalkAction.WRITE_EPISODIC_MEMORY,
    }

    FORBIDDEN = {
        TalkAction.WRITE_SEMANTIC_MEMORY,
        TalkAction.EXTERNAL_SEND,
        TalkAction.ENABLE_HARVEST,
        TalkAction.CRM_MUTATION,
        TalkAction.POLICY_MUTATION,
    }

    POLICY_VERSION = "talk-discovery-policy.v1"

    def decide(
        self,
        action: TalkAction,
        *,
        collab_enabled: bool,
        untrusted_instruction: bool,
        owner_approval_id: str | None,
    ) -> TalkDecision:
        if not collab_enabled:
            return TalkDecision(False, "collaborator disabled")

        if action in self.FORBIDDEN:
            return TalkDecision(False, "hard forbidden for talk-discovery")

        if untrusted_instruction and action != TalkAction.RESPOND_DRAFT:
            return TalkDecision(
                False, "untrusted content cannot authorize state change"
            )

        if action in self.OWNER_APPROVAL_ONLY:
            if not owner_approval_id:
                return TalkDecision(False, "owner approval absent", True)
            return TalkDecision(True, "approved episodic-memory write", True)

        if action in self.READ_ONLY_ALLOWED:
            return TalkDecision(True, "read-only draft path")

        return TalkDecision(False, "unknown action: fail closed")
