from pathlib import Path


ROOT = Path("/home/ari/ofn")


changes = {
    ROOT / "ofn/run.py": [
        (
            """    # Metadata-only OFN seams. Payload-returning reads (owner_queue,
    # recent_events) and mutation-prone projections are deliberately absent.
""",
            """    # Metadata-only OFN seams. Raw payload-returning reads (owner_queue,
    # recent_events) and mutation-prone projections remain deliberately absent.
""",
        ),
        (
            """        "ledger_summary": node.owner_ledger_summary,
    }
    try:
""",
            """        "ledger_summary": node.owner_ledger_summary,
    }
    owner_queue_metadata = getattr(node, "owner_queue_metadata", None)
    if callable(owner_queue_metadata):
        reads["owner_queue_metadata"] = owner_queue_metadata

    try:
""",
        ),
    ],
    ROOT / "ofn/node.py": [
        (
            """                })
        return out

    def _owner_business(self, tenant: TenantId | str, *,
""",
            """                })
        return out

    def owner_queue_metadata(self) -> list[dict]:
        \"\"\"Metadata-only view of the existing owner approval queue.

        ``owner_queue`` remains the command surface's payload-bearing read.
        Cockpit V2 receives this allowlisted derivative so adding a read
        projection cannot disclose customer text or create another queue.
        \"\"\"
        out: list[dict] = []
        for row in self.owner_queue():
            native_id = row.get("id")
            tenant = row.get("tenant")
            idempotency_key = None
            if isinstance(native_id, str) and isinstance(tenant, str):
                prefix = f"{tenant}:"
                if native_id.startswith(prefix) and len(native_id) > len(prefix):
                    idempotency_key = native_id[len(prefix):]
            out.append({
                "native_id": native_id,
                "idempotency_key": idempotency_key,
                "tenant": tenant,
                "state": (
                    "held" if row.get("held") is True else "pending_owner"
                ),
                "risk": row.get("tier"),
                "created_at": row.get("created_at"),
            })
        return out

    def _owner_business(self, tenant: TenantId | str, *,
""",
        ),
    ],
    ROOT / "ofn/adapters/cockpit_v2_read_model.py": [
        (
            """    "owner_money": "money",
}
""",
            """    "owner_money": "money",
    "owner_queue_metadata": "owner_queue_metadata",
}
""",
        ),
        (
            """        rows = sorted(candidates.values(), key=self._queue_sort_key, reverse=True)
        return rows, readable_count > 0, complete and not ctx.incomplete

    @staticmethod
    def _filter_queue(
""",
            """        rows = sorted(candidates.values(), key=self._queue_sort_key, reverse=True)
        return rows, readable_count > 0, complete and not ctx.incomplete

    @staticmethod
    def _owner_queue_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
        return (row.get("created_at") or "", row.get("id") or "")

    @staticmethod
    def _project_owner_queue_row(
        value: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        native_id = _safe_token(value.get("native_id"), maximum=128)
        tenant = _safe_token(value.get("tenant"), maximum=64)
        idempotency_key = _safe_token(
            value.get("idempotency_key"), maximum=128
        )
        state = _safe_token(value.get("state"), maximum=64)
        risk = _safe_token(value.get("risk"), maximum=32)
        created_at = _timestamp(value.get("created_at"))

        if native_id is None or tenant is None:
            return None
        prefix = f"{tenant}:"
        if not native_id.startswith(prefix) or len(native_id) <= len(prefix):
            return None
        if (
            idempotency_key is not None
            and native_id != f"{tenant}:{idempotency_key}"
        ):
            return None

        truth = LIVE_VERIFIED
        if None in (idempotency_key, state, risk, created_at):
            truth = UNKNOWN
        return {
            "id": f"business:{native_id}",
            "source_kind": "business_outbox",
            "native_id": native_id,
            "idempotency_key": idempotency_key,
            "tenant": tenant,
            "state": state,
            "risk": risk,
            "created_at": created_at,
            "truth": truth,
        }

    def _collect_owner_queue(
        self, ctx: _Context
    ) -> tuple[list[dict[str, Any]] | None, bool]:
        value = self._callback(
            "owner_queue_metadata", ctx, expected=True
        )
        if value is None:
            return None, False
        source_id = "ofn_owner_queue_metadata"
        if not isinstance(value, (list, tuple)):
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None, False

        candidates: dict[str, dict[str, Any]] = {}
        had_input = bool(value)
        for index, raw in enumerate(value):
            if index >= MAX_ROWS:
                ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                break
            try:
                ctx.budget.spend(rows=1, work=1)
            except _BudgetExceeded:
                ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                break
            if not isinstance(raw, Mapping):
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                continue
            row = self._project_owner_queue_row(raw)
            if row is None:
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                continue
            previous = candidates.get(row["native_id"])
            if previous is not None:
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                continue
            candidates[row["native_id"]] = row

        if had_input and not candidates:
            return None, False
        rows = sorted(
            candidates.values(), key=self._owner_queue_sort_key, reverse=True
        )
        return rows, True

    @staticmethod
    def _filter_queue(
""",
        ),
        (
            """        self._mesh_root_source(ctx)
        rows, available, complete = self._collect_queue(ctx)
        filtered = self._filter_queue(rows, normalized)
""",
            """        self._mesh_root_source(ctx)
        rows, available, complete = self._collect_queue(ctx)
        owner_items, owner_available = self._collect_owner_queue(ctx)
        filtered = self._filter_queue(rows, normalized)
""",
        ),
        (
            """        total = len(filtered) if complete else None
        data = {
            "items": page,
            "limit": normalized["limit"],
            "next_cursor": next_cursor,
            "total": total,
        }
        if not available:
            status = "unavailable"
        elif ctx.warnings or not complete:
            status = "degraded"
        else:
            status = "ok"
""",
            """        total = len(filtered) if complete else None
        data = {
            "items": page,
            "owner_items": owner_items,
            "limit": normalized["limit"],
            "next_cursor": next_cursor,
            "total": total,
        }
        if not available and not owner_available:
            status = "unavailable"
        elif (
            ctx.warnings or not complete or not available or not owner_available
        ):
            status = "degraded"
        else:
            status = "ok"
""",
        ),
    ],
}


rendered = {}
for path, replacements in changes.items():
    text = path.read_text(encoding="utf-8")
    for index, (old, new) in enumerate(replacements, 1):
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"{path}: replacement {index} expected one match, found {count}"
            )
        text = text.replace(old, new, 1)
    rendered[path] = text

for path, text in rendered.items():
    path.write_text(text, encoding="utf-8")
    print(path)
