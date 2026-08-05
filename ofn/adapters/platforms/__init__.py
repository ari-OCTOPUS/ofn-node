"""Platform adapters package.

Each module here is one outside service. The package is imported lazily by
the node; nothing here runs at import time, and nothing here publishes for
real until the OwnerRelease switch is wired (M5) and the relevant WIRE
flag is on — which the project's hard rules keep off by default.
"""
