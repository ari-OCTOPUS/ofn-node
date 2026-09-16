import pytest

pytestmark = pytest.mark.l0

from nbb_cp.kernel.budget import headroom, release, reserve
from nbb_cp.kernel.domain import BudgetState, Money
from nbb_cp.kernel.errors import CapExceededError, FailClosedError

STATE = BudgetState(cap=Money(1000))


class TestReserve:
    def test_reserve_within_cap(self):
        new = reserve(STATE, Money(400))
        assert new.committed == Money(400)

    def test_reserve_to_exact_cap_allowed(self):
        new = reserve(STATE, Money(1000))
        assert headroom(new) == Money(0)

    def test_reserve_past_cap_rejected(self):
        with pytest.raises(CapExceededError):
            reserve(STATE, Money(1001))

    def test_reserve_past_cap_from_partial_state_rejected(self):
        partial = reserve(STATE, Money(900))
        with pytest.raises(CapExceededError):
            reserve(partial, Money(101))

    def test_reserve_zero_rejected(self):
        with pytest.raises(FailClosedError):
            reserve(STATE, Money(0))

    def test_version_bumps_on_reserve(self):
        assert reserve(STATE, Money(1)).version == STATE.version + 1

    def test_original_state_untouched(self):
        reserve(STATE, Money(500))
        assert STATE.committed == Money(0)


class TestRelease:
    def test_release_returns_headroom(self):
        state = reserve(STATE, Money(500))
        state = release(state, Money(200))
        assert state.committed == Money(300)

    def test_release_more_than_committed_rejected(self):
        state = reserve(STATE, Money(100))
        with pytest.raises(FailClosedError):
            release(state, Money(101))

    def test_version_bumps_on_release(self):
        state = reserve(STATE, Money(100))
        assert release(state, Money(50)).version == state.version + 1
