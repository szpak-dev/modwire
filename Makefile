DEV_DIR := .dev
BUILD_DIR := $(DEV_DIR)/build
DIST_DIR := $(DEV_DIR)/dist
EGG_INFO_DIR := src/modwire.egg-info
PROJECT_ROOT := $(CURDIR)
BIG_PROJECT_ARGS ?=
RUBY_VERSION := 4.0.7
PRISM_VERSION := 1.9.0
RUBY_RUNTIME_DIR := $(DEV_DIR)/runtimes/ruby-$(RUBY_VERSION)

export PYTHONPYCACHEPREFIX := $(PROJECT_ROOT)/$(DEV_DIR)/cache/python
export UV_CACHE_DIR := $(PROJECT_ROOT)/$(DEV_DIR)/cache/uv

.PHONY: big-projects build cache-benchmark ci docs docs-check docs-linkcheck docs-links docs-lock extractor-check format format-check host-check lint package-check report-benchmark ruby-runtime scan-benchmark scan-benchmark-fixture test type-check

format:
	uv run ruff format src tests scripts

format-check:
	uv run ruff format --check src tests scripts

lint:
	uv run ruff check src tests scripts

type-check:
	uv run pyright src/modwire

test: ruby-runtime docs-links
	mkdir -p $(DEV_DIR)/testing
	PATH="$(PROJECT_ROOT)/$(RUBY_RUNTIME_DIR)/bin:$$PATH" uv run pytest

ruby-runtime:
	@if $(RUBY_RUNTIME_DIR)/bin/ruby -rprism -e 'abort unless RUBY_VERSION == "$(RUBY_VERSION)" && Prism::VERSION == "$(PRISM_VERSION)"' >/dev/null 2>&1; then \
		:; \
	elif ruby -rprism -e 'abort unless RUBY_VERSION == "$(RUBY_VERSION)" && Prism::VERSION == "$(PRISM_VERSION)"' >/dev/null 2>&1; then \
		:; \
	elif command -v ruby-install >/dev/null 2>&1; then \
		ruby-install --no-install-deps --no-reinstall ruby $(RUBY_VERSION) --install-dir "$(PROJECT_ROOT)/$(RUBY_RUNTIME_DIR)"; \
		"$(PROJECT_ROOT)/$(RUBY_RUNTIME_DIR)/bin/gem" install prism --version $(PRISM_VERSION) --no-document; \
	else \
		echo "Ruby $(RUBY_VERSION) with Prism $(PRISM_VERSION) is required; install ruby-install or provide the pinned runtime on PATH." >&2; \
		exit 1; \
	fi

big-projects:
	uv run python -u -m tests.extraction.big_projects.run $(BIG_PROJECT_ARGS)

scan-benchmark-fixture:
	uv run python -m tests.extraction.scan_benchmark.prepare --root .dev/benchmarks/scan-project --source-template "$(SCAN_BENCHMARK_SOURCE)"

scan-benchmark:
	uv run python -m tests.extraction.scan_benchmark.run --root .dev/benchmarks/scan-project --language "$(SCAN_BENCHMARK_LANGUAGE)" --excluded-pattern 'example_excluded/**'

cache-benchmark:
	uv run python -m scripts.benchmarks.cache.run --root "$(CACHE_BENCHMARK_ROOT)" --language "$(CACHE_BENCHMARK_LANGUAGE)" --cache-directory .dev/benchmarks/cache --incremental-source "$(CACHE_BENCHMARK_SOURCE)" --replacement-source "$(CACHE_BENCHMARK_REPLACEMENT)"

report-benchmark:
	uv run python -m scripts.benchmarks.report.run --root "$(REPORT_BENCHMARK_ROOT)" --language "$(REPORT_BENCHMARK_LANGUAGE)" --cache-directory "$(REPORT_BENCHMARK_CACHE)" --cache-namespace "$(REPORT_BENCHMARK_NAMESPACE)"

docs-check: docs-links
	PYTHONPATH=src uv run --isolated --locked --with-requirements docs/requirements.lock sphinx-build -W --keep-going -E -a -b html docs docs/_build/html

docs:
	PYTHONPATH=src uv run --isolated --locked --with-requirements docs/requirements.lock sphinx-build -b html docs docs/_build/html

docs-links:
	uv run --isolated --no-project --python 3.12 python scripts/check_docs_links.py

docs-linkcheck:
	PYTHONPATH=src uv run --isolated --locked --with-requirements docs/requirements.lock sphinx-build -W --keep-going -E -a -b linkcheck docs docs/_build/linkcheck

docs-lock:
	uv pip compile --python-version 3.12 --universal --output-file docs/requirements.lock docs/requirements.in

build:
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(EGG_INFO_DIR)
	uv build --out-dir $(DIST_DIR)

package-check: build
	uv run twine check $(DIST_DIR)/*

extractor-check: ruby-runtime
	PATH="$(PROJECT_ROOT)/$(RUBY_RUNTIME_DIR)/bin:$$PATH" python3 scripts/check_extractors.py

host-check: format-check lint type-check test docs-check package-check

ci: host-check extractor-check
