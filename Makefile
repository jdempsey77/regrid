# ReGrid — quick venv + install + test (no feature targets)
.PHONY: venv install test help

help:
	@echo "ReGrid dev targets:"
	@echo "  make venv    - create .venv (then: source .venv/bin/activate)"
	@echo "  make install - pip install -e \".[test]\" (run after activate)"
	@echo "  make test    - pytest tests/ -v"
	@echo "  regrid --help - after install, run CLI"

venv:
	python -m venv .venv
	@echo "Run: source .venv/bin/activate  (Windows: .venv\\Scripts\\activate)"

install:
	pip install -e ".[test]"

test:
	pytest tests/ -v --tb=short
