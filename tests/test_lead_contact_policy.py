from __future__ import annotations

import os
import sqlite3
import tempfile
import threading

from ofn.adapters.lead_store import LeadStore, MIGRATIONS

NOW = "2026-08-26T10:00:00Z"
LATER = "2026-08-27T10:00:00Z"
TENANT = "lead"


def _create(store: LeadStore, suffix: str = "1", **extra) -> str:
    data = {
        "lead_id": f"policy-{suffix}",
        "source": "test",
        "source_ref": suffix,
        "customer_name": "Contact Policy Fixture",
        "phone": f"04120000{int(suffix):02d}",
        "email": f"fixture{suffix}@example.test",
    }
    data.update(extra)
    out = store.create_lead(TENANT, data, now_iso=NOW)
    assert out["ok"]
    return out["lead"]["lead_id"]


def _allow(store: LeadStore, lead_id: str, channels=("sms", "email")) -> dict:
    return store.set_contact_policy(
        TENANT,
        lead_id,
        legal_basis="explicit_consent",
        channel_scope=channels,
        proof_digest="sha256:proof-fixture",
        reason="fixture evidence",
        now_iso=NOW,
    )


class TestContactPolicy:
    def setup_method(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = self.temp.name
        self.store = LeadStore(os.path.join(self.directory, "lead.sqlite"))
        self.lead_id = _create(self.store)

    def teardown_method(self):
        self.store.close()
        self.temp.cleanup()

    def test_no_policy_fails_closed_and_public_contact_is_not_consent(self):
        lead = self.store.get(TENANT, self.lead_id)
        assert lead["phone"] and lead["email"]
        verdict = self.store.contact_allowed(TENANT, self.lead_id, "sms")
        assert verdict["allowed"] is False
        assert verdict["rule"] == "contact:policy-missing"

    def test_each_scoped_channel_is_allowed_independently(self):
        out = _allow(self.store, self.lead_id, ("sms", "email", "phone"))
        assert out["ok"]
        for channel in ("sms", "email", "phone"):
            verdict = self.store.contact_allowed(TENANT, self.lead_id, channel)
            assert verdict == {
                "allowed": True,
                "rule": "contact:allowed",
                "channel": channel,
                "legal_basis": "explicit_consent",
            }

    def test_wrong_channel_or_missing_matching_contact_fails_closed(self):
        assert _allow(self.store, self.lead_id, ("email",))["ok"]
        wrong = self.store.contact_allowed(TENANT, self.lead_id, "sms")
        assert not wrong["allowed"]
        assert wrong["rule"] == "contact:channel-not-scoped"

        no_email = _create(self.store, "2", email="")
        assert _allow(self.store, no_email, ("email",))["ok"]
        missing = self.store.contact_allowed(TENANT, no_email, "email")
        assert not missing["allowed"]
        assert missing["rule"] == "contact:contact-missing"

    def test_blank_proof_and_unknown_legal_basis_are_refused(self):
        blank = self.store.set_contact_policy(
            TENANT, self.lead_id, legal_basis="explicit_consent",
            channel_scope=["sms"], proof_digest="   ", now_iso=NOW,
        )
        assert not blank["ok"]
        assert blank["rule"] == "contact:proof-missing"
        unknown = self.store.set_contact_policy(
            TENANT, self.lead_id, legal_basis="public_contact",
            channel_scope=["sms"], proof_digest="digest", now_iso=NOW,
        )
        assert not unknown["ok"]
        assert unknown["rule"] == "contact:invalid-legal-basis"
        assert self.store.get_contact_policy(TENANT, self.lead_id) is None

    def test_revoke_after_allow_blocks_and_cannot_be_reauthorized(self):
        assert _allow(self.store, self.lead_id)["ok"]
        assert self.store.contact_allowed(TENANT, self.lead_id, "sms")["allowed"]
        revoked = self.store.revoke_contact_policy(
            TENANT, self.lead_id, at_iso=LATER, reason="consent withdrawn",
        )
        assert revoked["ok"]
        verdict = self.store.contact_allowed(TENANT, self.lead_id, "sms")
        assert not verdict["allowed"]
        assert verdict["rule"] == "contact:revoked"

        rewrite = _allow(self.store, self.lead_id)
        assert rewrite["ok"]
        persisted = rewrite["policy"]
        assert persisted["do_not_contact"] is True
        assert persisted["revoked_at"] == LATER
        assert self.store.contact_allowed(TENANT, self.lead_id, "sms")["allowed"] is False

    def test_opt_out_is_permanent_even_without_prior_policy(self):
        out = self.store.record_opt_out(
            TENANT, self.lead_id, at_iso=NOW, reason="stop all contact",
        )
        assert out["ok"]
        policy = out["policy"]
        assert policy["do_not_contact"] is True
        assert policy["opted_out_at"] == NOW
        assert policy["proof_digest"]
        assert policy["channel_scope"] == []
        assert self.store.contact_allowed(TENANT, self.lead_id, "email")["allowed"] is False

        assert _allow(self.store, self.lead_id)["ok"]
        policy = self.store.get_contact_policy(TENANT, self.lead_id)
        assert policy["do_not_contact"] is True
        assert policy["opted_out_at"] == NOW

    def test_tenant_scope_is_enforced(self):
        assert _allow(self.store, self.lead_id)["ok"]
        assert self.store.get_contact_policy("other", self.lead_id) is None
        verdict = self.store.contact_allowed("other", self.lead_id, "sms")
        assert not verdict["allowed"]
        assert verdict["rule"] == "contact:lead-missing"

    def test_policy_is_bound_to_the_scoped_channel_fingerprint(self):
        assert _allow(self.store, self.lead_id, ("sms", "email"))["ok"]
        original = self.store.get_contact_policy(TENANT, self.lead_id)
        assert self.store.contact_allowed(TENANT, self.lead_id, "sms")["allowed"]

        changed_phone = self.store.update_lead(
            TENANT, self.lead_id, {"phone": "0499000000"}, now_iso=LATER,
        )
        assert changed_phone["ok"]
        sms = self.store.contact_allowed(TENANT, self.lead_id, "sms")
        assert not sms["allowed"]
        assert sms["rule"] == "contact:fingerprint-changed"
        # Email evidence stays bound to the unchanged email rather than being
        # invalidated by an unrelated phone edit.
        assert self.store.contact_allowed(TENANT, self.lead_id, "email")["allowed"]

        changed_email = self.store.update_lead(
            TENANT, self.lead_id, {"email": "new-contact@example.test"},
            now_iso=LATER,
        )
        assert changed_email["ok"]
        email = self.store.contact_allowed(TENANT, self.lead_id, "email")
        assert not email["allowed"]
        assert email["rule"] == "contact:fingerprint-changed"
        # The evidence row itself remains an immutable statement about the old
        # fingerprints until an explicit fresh policy replaces it.
        stale = self.store.get_contact_policy(TENANT, self.lead_id)
        assert stale["contact_phone_hash"] == original["contact_phone_hash"]
        assert stale["contact_email_hash"] == original["contact_email_hash"]

        refreshed = self.store.set_contact_policy(
            TENANT, self.lead_id, legal_basis="explicit_consent",
            channel_scope=["sms", "email"],
            proof_digest="sha256:fresh-proof-for-new-contact", now_iso=LATER,
        )
        assert refreshed["ok"]
        assert self.store.contact_allowed(TENANT, self.lead_id, "sms")["allowed"]
        assert self.store.contact_allowed(TENANT, self.lead_id, "email")["allowed"]

    def test_policy_stores_hashes_and_digests_not_raw_contact(self):
        assert _allow(self.store, self.lead_id)["ok"]
        row = self.store._conn.execute(
            "SELECT * FROM lead_contact_policy WHERE tenant_id=? AND lead_id=?",
            (TENANT, self.lead_id),
        ).fetchone()
        serialized = "|".join(str(value) for value in row)
        assert "0412000001" not in serialized
        assert "fixture1@example.test" not in serialized
        assert row["contact_phone_hash"]
        assert row["contact_email_hash"]
        columns = {item[1] for item in self.store._conn.execute(
            "PRAGMA table_info(lead_contact_policy)"
        )}
        assert "phone" not in columns
        assert "email" not in columns


class TestFollowUpIntegrity:
    def setup_method(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = self.temp.name
        self.path = os.path.join(self.directory, "lead.sqlite")
        self.store = LeadStore(self.path)
        self.lead_id = _create(self.store)

    def teardown_method(self):
        self.store.close()
        self.temp.cleanup()

    def test_second_follow_up_is_rejected_at_hard_cap(self):
        first = self.store.record_follow_up(TENANT, self.lead_id, at_iso=NOW)
        second = self.store.record_follow_up(TENANT, self.lead_id, at_iso=LATER)
        assert first["ok"]
        assert not second["ok"]
        assert second["rule"] == "follow-up:hard-cap"
        lead = self.store.get(TENANT, self.lead_id)
        assert lead["follow_up_count"] == 1
        assert lead["last_follow_up_at"] == NOW

    def test_concurrent_callers_cannot_both_claim_follow_up(self):
        barrier = threading.Barrier(2)
        results: list[dict] = []
        errors: list[BaseException] = []

        def claim():
            other = LeadStore(self.path)
            try:
                barrier.wait()
                results.append(other.record_follow_up(
                    TENANT, self.lead_id, at_iso=NOW,
                ))
            except BaseException as exc:  # surface thread failures to the test
                errors.append(exc)
            finally:
                other.close()

        threads = [threading.Thread(target=claim) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert not errors
        assert sum(bool(result["ok"]) for result in results) == 1
        assert self.store.get(TENANT, self.lead_id)["follow_up_count"] == 1


class TestDuplicateContactHashes:
    def setup_method(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = self.temp.name
        self.store = LeadStore(os.path.join(self.directory, "lead.sqlite"))

    def teardown_method(self):
        self.store.close()
        self.temp.cleanup()

    def test_phone_and_email_hashes_each_find_duplicates_without_cross_tenant_leak(self):
        first = _create(
            self.store, "1", phone="0412 345 678", email="same@example.test",
        )
        by_phone = _create(
            self.store, "2", phone="+61 412 345 678", email="other@example.test",
        )
        by_email = _create(
            self.store, "3", phone="0499999999", email="SAME@example.test",
        )
        self.store.create_lead("other", {
            "lead_id": "other-duplicate", "source": "test",
            "phone": "+61 412 345 678", "email": "same@example.test",
        }, now_iso=NOW)

        matches = self.store.has_duplicate_contact(TENANT, first, details=True)
        assert {item["lead_id"] for item in matches} == {by_phone, by_email}
        assert self.store.has_duplicate_contact(TENANT, first) is True
        assert self.store.has_duplicate_contact(TENANT, by_phone) is True


class TestLeadTransitionIntegrity:
    def setup_method(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = self.temp.name
        self.store = LeadStore(os.path.join(self.directory, "lead.sqlite"))
        self.lead_id = _create(self.store)

    def teardown_method(self):
        self.store.close()
        self.temp.cleanup()

    def test_generic_update_rejects_arbitrary_delivery_jumps_for_all_authorities(self):
        for status in ("contacted", "quoted", "won"):
            out = self.store.update_lead(
                TENANT, self.lead_id, {"status": status}, now_iso=NOW,
                authority="owner",
            )
            assert not out["ok"]
            assert out["rule"] == "lead:delivery-status-requires-dedicated-method"
        assert self.store.get(TENANT, self.lead_id)["status"] == "new"

    def test_create_cannot_claim_delivery_or_terminal_status(self):
        for index, requested in enumerate(
                ("contacted", "quoted", "won", "lost", "spam", "archived"),
                start=10):
            lead_id = _create(self.store, str(index), status=requested)
            assert self.store.get(TENANT, lead_id)["status"] == "new"

    def test_create_upsert_cannot_rewrite_existing_lifecycle_status(self):
        assert self.store.mark_delivered(
            TENANT, self.lead_id, kind="reply", at_iso=NOW,
        )["ok"]
        assert self.store.get(TENANT, self.lead_id)["status"] == "contacted"

        # Same id is an intake retry. Neither an explicit terminal status nor
        # the normalized new fallback may rewind the existing lifecycle.
        retried = self.store.create_lead(TENANT, {
            "lead_id": "policy-1", "source": "retry", "status": "won",
            "phone": "0412000001", "email": "fixture1@example.test",
        }, now_iso=LATER)
        assert retried["ok"]
        assert retried["lead"]["status"] == "contacted"

    def test_touch_contact_preserves_timestamp_without_changing_status(self):
        self.store.touch_contact(TENANT, self.lead_id, at_iso=NOW)
        lead = self.store.get(TENANT, self.lead_id)
        assert lead["last_contacted_at"] == NOW
        assert lead["status"] == "new"

    def test_delivery_receipt_methods_advance_truthfully(self):
        reply = self.store.mark_delivered(
            TENANT, self.lead_id, kind="reply", at_iso=NOW,
        )
        assert reply["ok"] and reply["transitioned"]
        assert reply["lead"]["status"] == "contacted"
        assert reply["lead"]["last_contacted_at"] == NOW

        quote = self.store.mark_delivered(
            TENANT, self.lead_id, kind="quote", at_iso=LATER,
        )
        assert quote["ok"] and quote["transitioned"]
        assert quote["lead"]["status"] == "quoted"
        assert quote["lead"]["last_contacted_at"] == LATER

        won = self.store.record_booked_revenue(
            TENANT, self.lead_id, amount_cents=100_00,
            booked_at=LATER, payment_ref_digest="sha256:payment",
        )
        assert won["ok"]
        assert won["lead"]["status"] == "won"

    def test_delivery_receipt_does_not_rewind_a_more_advanced_status(self):
        quote = self.store.mark_delivered(
            TENANT, self.lead_id, kind="quote", at_iso=NOW,
        )
        assert quote["ok"] and quote["lead"]["status"] == "quoted"
        late_reply = self.store.mark_delivered(
            TENANT, self.lead_id, kind="reply", at_iso=LATER,
        )
        assert late_reply["ok"] and not late_reply["transitioned"]
        assert late_reply["lead"]["status"] == "quoted"
        assert late_reply["lead"]["last_contacted_at"] == LATER

    def test_terminal_lock_and_owner_reopen_requires_reason(self):
        closed = self.store.update_lead(
            TENANT, self.lead_id, {"status": "lost"}, now_iso=NOW,
        )
        assert closed["ok"]
        partner = self.store.update_lead(
            TENANT, self.lead_id, {"status": "review"}, now_iso=LATER,
            authority="partner",
        )
        owner_generic = self.store.update_lead(
            TENANT, self.lead_id, {"status": "review"}, now_iso=LATER,
            authority="owner",
        )
        assert not partner["ok"] and partner["rule"] == "lead:terminal-locked"
        assert not owner_generic["ok"] and owner_generic["rule"] == "lead:terminal-locked"

        no_reason = self.store.owner_reopen_lead(
            TENANT, self.lead_id, reason=" ", now_iso=LATER,
        )
        non_owner = self.store.owner_reopen_lead(
            TENANT, self.lead_id, reason="customer returned", now_iso=LATER,
            authority="partner",
        )
        assert not no_reason["ok"]
        assert no_reason["rule"] == "lead:reopen-reason-required"
        assert not non_owner["ok"]
        assert non_owner["rule"] == "lead:owner-required"

        reopened = self.store.owner_reopen_lead(
            TENANT, self.lead_id, reason="customer requested a new review",
            now_iso=LATER,
        )
        assert reopened["ok"]
        assert reopened["lead"]["status"] == "review"
        assert reopened["lead"]["outcome_reason"] == "customer requested a new review"


class TestContactPolicyMigration:
    def test_old_database_migrates_idempotently_and_keeps_existing_rows(self, tmp_path):
        path = str(tmp_path / "legacy.sqlite")
        conn = sqlite3.connect(path)
        conn.execute(
            "CREATE TABLE painting_leads ("
            "lead_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL DEFAULT 'lead', "
            "source TEXT NOT NULL, source_ref TEXT NOT NULL DEFAULT '', "
            "customer_name TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '', "
            "email TEXT NOT NULL DEFAULT '', suburb TEXT NOT NULL DEFAULT '', "
            "distance_km REAL, job_type TEXT NOT NULL DEFAULT '', rooms TEXT NOT NULL DEFAULT '', "
            "budget_text TEXT NOT NULL DEFAULT '', message TEXT NOT NULL DEFAULT '', "
            "score INTEGER NOT NULL DEFAULT 0, temperature TEXT NOT NULL DEFAULT 'new', "
            "status TEXT NOT NULL DEFAULT 'new', next_action TEXT NOT NULL DEFAULT '', "
            "assigned_to TEXT NOT NULL DEFAULT '', tags_json TEXT NOT NULL DEFAULT '[]', "
            "notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO painting_leads "
            "(lead_id, tenant_id, source, phone, status, created_at, updated_at) "
            "VALUES ('lead:legacy-policy', 'lead', 'manual', '0412345678', "
            "'new', ?, ?)",
            (NOW, NOW),
        )
        conn.commit()
        conn.close()

        first = LeadStore(path)
        try:
            lead_columns = {row[1] for row in first._conn.execute(
                "PRAGMA table_info(painting_leads)"
            )}
            assert {"follow_up_count", "last_follow_up_at"} <= lead_columns
            tables = {row[0] for row in first._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            assert "lead_contact_policy" in tables
            assert first.get(TENANT, "lead:legacy-policy") is not None
            # Every migration is callable repeatedly inside an explicit unit of work.
            first._conn.execute("BEGIN IMMEDIATE")
            for migration in MIGRATIONS:
                migration(first._conn)
            first._conn.execute("COMMIT")
        finally:
            first.close()

        second = LeadStore(path)
        try:
            lead = second.get(TENANT, "lead:legacy-policy")
            assert lead["follow_up_count"] == 0
            assert lead["last_follow_up_at"] == ""
            assert second.get_contact_policy(TENANT, "lead:legacy-policy") is None
        finally:
            second.close()
