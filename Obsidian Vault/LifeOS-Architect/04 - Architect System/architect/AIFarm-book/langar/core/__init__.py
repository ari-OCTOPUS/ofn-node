"""core — هسته‌ی مرکزیِ شناخت و ارتباط (HumanCore)."""

from .human_core import HumanCore
from .mental_model import MentalModel
from .communication import CommunicationManager, CommunicationStyle
from .self_improver import SelfImprover

__all__ = ["HumanCore", "MentalModel", "CommunicationManager",
           "CommunicationStyle", "SelfImprover"]
