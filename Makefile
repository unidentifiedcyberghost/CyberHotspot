PYTHON ?= python3
PIP := $(PYTHON) -m pip

.PHONY: install dev test lint run-gui doctor clean

install:
	$(PIP) install -e ".[qr]"

dev:
	$(PIP) install -e ".[qr,dev]"

test:
	$(PYTHON) -m pytest

lint:
	ruff check cyberhotspot tests

run-gui:
	$(PYTHON) -m cyberhotspot.gui

doctor:
	$(PYTHON) -m cyberhotspot.cli doctor

clean:
	rm -rf build dist *.egg-info .pytest_cache
