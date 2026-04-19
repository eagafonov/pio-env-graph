VENV = .venv
BIN = $(VENV)/bin

.PHONY: lint format test

$(VENV):
	python3 -m venv $(VENV)
	$(BIN)/pip install -e .
	$(BIN)/pip install -r requirements-dev.txt

lint: $(VENV)
	$(BIN)/black --check src/ tests/
	$(BIN)/flake8 src/ tests/

format: $(VENV)
	$(BIN)/black src/ tests/

test: $(VENV)
	$(BIN)/pytest
