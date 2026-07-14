# Brushline -- Makefile for VPS operations
# Usage: make <target>
# Run from /srv/brushline/code on the VPS

VENV    := /srv/brushline/venv
PYTHON  := $(VENV)/bin/python
SERVICE := brushline

.PHONY: start stop restart status logs kill unkill spend test check eval

start:
	systemctl start $(SERVICE)
	@echo "Started. Check: make logs"

stop:
	systemctl stop $(SERVICE)

restart:
	systemctl restart $(SERVICE)

status:
	systemctl status $(SERVICE) --no-pager

logs:
	journalctl -u $(SERVICE) -f --no-hostname

kill:
	touch /srv/brushline/data/KILL_SWITCH
	@echo "KILL SWITCH ACTIVATED -- all external actions halted"

unkill:
	rm -f /srv/brushline/data/KILL_SWITCH
	@echo "Kill switch cleared -- system resumed"

spend:
	$(PYTHON) -c "from src import governance; import json; print(json.dumps(governance.get_spend_status(), indent=2))"

check:
	$(PYTHON) -c "from src.config import config; m = config.validate(); print('MISSING:', m) if m else print('Config OK'); print('Serper key set:', bool(config.SERPER_API_KEY)); print('Telegram token set:', bool(config.TELEGRAM_BOT_TOKEN)); print('Chat IDs:', config.ALLOWED_OPERATOR_CHAT_IDS)"

test:
	@set -e; for t in tests/test_phase*.py; do echo "== $$t"; $(PYTHON) $$t; done
	$(PYTHON) evals/run_eval.py

test-pytest:
	$(VENV)/bin/pytest tests/ -v

eval:
	$(PYTHON) evals/run_eval.py
