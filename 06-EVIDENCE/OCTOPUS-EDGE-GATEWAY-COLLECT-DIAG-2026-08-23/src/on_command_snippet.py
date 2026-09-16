    async def _on_command(self, msg) -> None:  # noqa: ANN001
        try:
            body = json.loads(msg.data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.audit.append("command_rejected", reason="invalid_json")
            return
        name = str(body.get("command", ""))
        if name in FORBIDDEN_COMMANDS:
            self.audit.append("command_forbidden", command=name, sender=body.get("sender_id"))
            return
        required = REQUIRED_COMMAND_FIELDS
        if any(k not in body for k in required):
            self.audit.append("command_rejected", reason="unsigned_or_incomplete", command=name)
            return
        if name not in ALLOWED_COMMANDS:
            self.audit.append("command_rejected", reason="not_allowlisted", command=name)
            return

        # Stage2D: readonly diagnostics may execute without command-trust root.
        # Signature is required as a field but NOT cryptographically verified until trust root binds.
        if name in ("COLLECT_DIAGNOSTICS", "REQUEST_DIAGNOSTIC"):
            from octopus_sensorium.edge_gateway.collect_diagnostics import collect_diagnostics

            params = body.get("params") if isinstance(body.get("params"), dict) else {}
            request_id = str(body.get("request_id") or body.get("nonce") or "")
            result = collect_diagnostics(
                request_id=request_id,
                params=params,
                sender_id=str(body.get("sender_id") or ""),
                write_evidence=True,
            )
            self.audit.append(
                "command_diagnostics",
                command=name,
                status=result.get("status"),
                request_id=request_id,
                signature_verify="UNVERIFIED_NO_COMMAND_TRUST_ROOT",
            )
            payload = json.dumps(result, separators=(",", ":")).encode("utf-8")
            reply = getattr(msg, "reply", None) or ""
            if reply:
                await self.nc.publish(reply, payload)
            else:
                await self.nc.publish(
                    f"octopus.sensorium.diagnostics.{request_id or 'unknown'}",
                    payload,
                )
            return

        # Wave 0: all other allowlisted commands stay deferred without trust root.
        self.audit.append("command_deferred", command=name, reason="command_trust_root_not_bound")
