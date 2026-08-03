"""Storage contract tests: append-only ledger, CAS budget, and the two real bug classes."""

import threading

import pytest

pytestmark = pytest.mark.l1

from nbb_cp.adapters.storage.memory import MemoryBudgetStore, MemoryLedgerStore
from nbb_cp.adapters.storage.sqlite import SqliteBudgetStore, SqliteLedgerStore
from nbb_cp.kernel import budget as budget_math
from nbb_cp.kernel.domain import BudgetState, Money
from nbb_cp.kernel.errors import CapExceededError, ConcurrencyConflictError
from nbb_cp.kernel.events import EventKind, verify_chain


@pytest.fixture(params=["memory", "sqlite"])
def stores(request, tmp_path):
    if request.param == "memory":
        return MemoryLedgerStore(), MemoryBudgetStore(BudgetState(cap=Money(1000)))
    path = tmp_path / "nbb.db"
    return SqliteLedgerStore(path), SqliteBudgetStore(path, BudgetState(cap=Money(1000)))


class TestLedgerContract:
    def test_append_and_verify_roundtrip(self, stores):
        ledger, _ = stores
        for i in range(5):
            ledger.append(f"t{i}", EventKind.PROPOSAL, {"i": i, "note": "سلام"})
        events = ledger.read_all()
        assert len(events) == 5
        verify_chain(events)  # raises on any break

    def test_head_tracks_last_event(self, stores):
        ledger, _ = stores
        assert ledger.head() is None
        ledger.append("t0", EventKind.KILL, {"by": "armin"})
        assert ledger.head().kind is EventKind.KILL

    def test_unicode_payload_survives_roundtrip(self, stores):
        ledger, _ = stores
        ledger.append("t0", EventKind.REVENUE, {"note": "درآمد تأییدشده", "amount_cents": 10})
        assert ledger.read_all()[0].payload["note"] == "درآمد تأییدشده"

    def test_concurrent_appends_never_fork_history(self, stores):
        ledger, _ = stores
        errors = []

        def writer(n):
            try:
                for i in range(10):
                    ledger.append(f"t{n}-{i}", EventKind.SPEND, {"organ_id": "a", "n": n, "i": i})
            except Exception as exc:  # noqa: BLE001 - collecting for assertion
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        events = ledger.read_all()
        assert len(events) == 40
        verify_chain(events)  # one linear history, no forks, no gaps


class TestBudgetCas:
    def test_stale_version_write_rejected(self, stores):
        _, budget = stores
        state = budget.get()
        first = budget_math.reserve(state, Money(100))
        budget.compare_and_swap(state.version, first)
        # A second writer still holding the old state must lose, not double-spend.
        stale = budget_math.reserve(state, Money(100))
        with pytest.raises(ConcurrencyConflictError):
            budget.compare_and_swap(state.version, stale)

    def test_racing_reservations_conserve_every_landed_reservation(self, stores):
        # NOTE: the previous assertion (`committed <= cap`) was tautological — it can
        # never fail for ANY store, because reserve() cap-checks before the store sees
        # the state and lost updates only make committed *lower*. The real guarantee is
        # conservation: committed must equal the number of CAS calls that actually
        # landed, times the amount. A non-atomic CAS loses updates and fails this.
        _, budget = stores
        landed = []  # one marker per successful compare_and_swap (list.append is GIL-atomic)

        def reserver():
            for _ in range(50):
                state = budget.get()
                try:
                    new_state = budget_math.reserve(state, Money(10))
                except CapExceededError:
                    return  # no headroom left; stop cleanly
                try:
                    budget.compare_and_swap(state.version, new_state)
                    landed.append(1)
                except ConcurrencyConflictError:
                    continue  # lost the race: re-read and retry

        threads = [threading.Thread(target=reserver) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        final = budget.get()
        assert final.committed.cents == len(landed) * 10, (
            f"{len(landed)} reservations landed but committed={final.committed.cents}c "
            f"— a lost update double-spent headroom"
        )
        assert final.committed.cents <= final.cap.cents  # INV-1 still holds

    def test_get_reflects_last_cas(self, stores):
        _, budget = stores
        state = budget.get()
        new_state = budget_math.reserve(state, Money(250))
        budget.compare_and_swap(state.version, new_state)
        assert budget.get().committed.cents == 250
        assert budget.get().version == state.version + 1
