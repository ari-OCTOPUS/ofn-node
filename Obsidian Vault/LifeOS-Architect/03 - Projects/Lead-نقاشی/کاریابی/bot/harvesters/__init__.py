"""Harvesters — deterministic scrapers/fetchers for known channels."""
from harvesters.base import Harvester
from harvesters.planning_alerts import PlanningAlertsHarvester
from harvesters.austender import AusTenderHarvester
from harvesters.estimate_one import EstimateOneHarvester

ALL: list[type[Harvester]] = [
    PlanningAlertsHarvester,
    AusTenderHarvester,
    EstimateOneHarvester,
]
