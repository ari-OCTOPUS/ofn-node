import pytest

pytestmark = pytest.mark.l0

from nbb_cp.kernel.errors import HumanVerdictRequiredError, IllegalTransitionError
from nbb_cp.kernel.lifecycle import LifecycleState as S
from nbb_cp.kernel.lifecycle import transition


class TestLadder:
    def test_active_to_throttled(self):
        assert transition(S.ACTIVE, S.THROTTLED) is S.THROTTLED

    def test_throttled_to_dormant(self):
        assert transition(S.THROTTLED, S.DORMANT) is S.DORMANT

    def test_dormancy_is_reversible(self):
        assert transition(S.DORMANT, S.THROTTLED) is S.THROTTLED
        assert transition(S.THROTTLED, S.ACTIVE) is S.ACTIVE

    def test_ladder_never_jumps_down(self):
        with pytest.raises(IllegalTransitionError):
            transition(S.ACTIVE, S.DORMANT)

    def test_ladder_never_jumps_to_extinct(self):
        with pytest.raises(IllegalTransitionError):
            transition(S.ACTIVE, S.EXTINCT, human_approved=True)

    def test_noop_transition_is_fine(self):
        assert transition(S.ACTIVE, S.ACTIVE) is S.ACTIVE


class TestExtinction:
    def test_extinction_without_human_rejected(self):
        with pytest.raises(HumanVerdictRequiredError):
            transition(S.DORMANT, S.EXTINCT)

    def test_extinction_with_human_allowed(self):
        assert transition(S.DORMANT, S.EXTINCT, human_approved=True) is S.EXTINCT

    def test_extinct_is_absorbing(self):
        with pytest.raises(IllegalTransitionError):
            transition(S.EXTINCT, S.DORMANT, human_approved=True)
