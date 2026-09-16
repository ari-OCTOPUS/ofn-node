# NBB Control Plane — developer entrypoints.
# Windows users without make: use scripts/gate.ps1 (same steps).

PY ?= python

.PHONY: install test gate-0 demo clean

install:
	$(PY) -m pip install -e .[dev,api]

test:
	$(PY) -m pytest

# Phase 0 gate: full suite green + kernel purity proven by the import-lint test.
gate-0:
	$(PY) -m pytest
	$(PY) -m pytest tests/test_import_lint.py -q

demo:
	$(PY) run.py

clean:
	$(PY) -c "import shutil; shutil.rmtree('outputs', ignore_errors=True)"
