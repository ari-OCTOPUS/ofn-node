"""Harvesters — deterministic fetchers for known channels.

EstimateOneHarvester exists but is NOT in ALL: it needs Playwright or a paid
plan to get past Cloudflare (see its docstring). Re-add once enabled.
"""
from harvesters.base import Harvester
from harvesters.planning_alerts import PlanningAlertsHarvester
from harvesters.austender import AusTenderHarvester
from harvesters.nsw_etendering import NswEtenderingHarvester

ALL: list[type[Harvester]] = [
    PlanningAlertsHarvester,
    AusTenderHarvester,
    NswEtenderingHarvester,
]
