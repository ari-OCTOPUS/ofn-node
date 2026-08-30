# -*- coding: utf-8 -*-
"""_ops.identity -- Zero-Trust identity and capability enforcement (EQUIP G7).

Vertical slice: agent identity registry, capability tokens bound to task/action/
resource/duration, and a policy enforcement point (PEP) that validates tool calls
before execution.

Design principles:
  - deny-by-default (no token = no access)
  - capability token bound to agent_id + task_id + action + resource + duration
  - token reuse and confused-deputy resistant (nonce, expiry, HMAC)
  - MCP tool discovery != permission
  - tool arguments policy-checked before execution
  - all deny/escalation attempts audit-logged
  - separate "who is the agent" from "on whose behalf"

stdlib-only. No network. No external writes beyond audit log.
"""
