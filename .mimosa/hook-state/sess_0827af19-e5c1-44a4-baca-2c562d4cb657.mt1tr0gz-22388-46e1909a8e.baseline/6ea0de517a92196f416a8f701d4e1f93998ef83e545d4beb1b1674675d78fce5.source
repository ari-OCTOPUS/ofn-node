"""
Research-Spec Compiler
======================
Turns a raw research *idea* into an *executable, falsifiable spec* and
enforces the five hard gates that separate real research from prose:

    no metric          -> useless
    no falsifiability  -> pseudo-research
    no api_contract    -> not connectable
    no mvp             -> not runnable
    no decision_rule   -> no closure

Zero required dependencies (stdlib only). PyYAML is used if present so specs
can be authored in YAML; otherwise use the .json mirrors.
"""

__version__ = "0.1.0"

from .model import CANONICAL_FIELDS, load_spec, dump_spec, SpecError
from .validator import validate, Report, Gate
from .harness import Condition, run_ablation, decide, check_failure, run_spec

__all__ = [
    "CANONICAL_FIELDS",
    "load_spec",
    "dump_spec",
    "SpecError",
    "validate",
    "Report",
    "Gate",
    "Condition",
    "run_ablation",
    "decide",
    "check_failure",
    "run_spec",
    "__version__",
]
