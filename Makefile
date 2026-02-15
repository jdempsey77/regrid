# ReGrid — quick venv + install + test (no feature targets)
.PHONY: venv install install-verify test test-e2e test-all test-quick help clean

help:
	@echo "ReGrid dev targets:"
	@echo "  make venv         - create .venv (then: source .venv/bin/activate)"
	@echo "  make install      - pip install -e \".[test]\" (run after activate)"
	@echo "  make install-verify - pip install -e \".[test,verify]\" (includes rtree, scipy)"
	@echo "  make test         - pytest tests/ -v (all tests)"
	@echo "  make test-e2e     - pytest tests/test_e2e.py -v (end-to-end only)"
	@echo "  make test-quick   - pytest tests/ -v -m \"not slow\" (fast tests only)"
	@echo "  make test-all     - run all tests including verify"
	@echo "  make clean        - remove debug/, out/, .pytest_cache/"
	@echo "  regrid --help     - after install, run CLI"

venv:
	python -m venv .venv
	@echo "Run: source .venv/bin/activate  (Windows: .venv\\Scripts\\activate)"

install:
	pip install -e ".[test]"

install-verify:
	pip install -e ".[test,verify]"

test:
	pytest tests/ -v --tb=short

test-e2e:
	pytest tests/test_e2e.py -v --tb=short

test-quick:
	pytest tests/ -v --tb=short -m "not slow"

test-all: install-verify
	pytest tests/ -v --tb=short

clean:
	rm -rf debug/ out/ .pytest_cache/ src/regrid.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
