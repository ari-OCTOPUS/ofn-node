"""research — منطقِ پژوهشِ مهاجرت‌داده‌شده به بک‌اند (فاز ۲)."""

from .engine import run_research
from .brain import get_brain
from .search_providers import get_search_provider
from . import constitution, source_quality

__all__ = ["run_research", "get_brain", "get_search_provider",
           "constitution", "source_quality"]
