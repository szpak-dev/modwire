DEV_DIR := .dev
BUILD_DIR := $(DEV_DIR)/build
DIST_DIR := $(DEV_DIR)/dist
EGG_INFO_DIR := src/modwire.egg-info
PROJECT_ROOT := $(CURDIR)

export PYTHONPYCACHEPREFIX := $(PROJECT_ROOT)/$(DEV_DIR)/cache/python
export UV_CACHE_DIR := $(PROJECT_ROOT)/$(DEV_DIR)/cache/uv

.PHONY: big-projects build ci docs docs-check extractor-check format format-check host-check lint package-check scan-benchmark scan-benchmark-fixture test type-check

format:
	uv run ruff format src tests scripts

format-check:
	uv run ruff format --check src tests scripts

lint:
	uv run ruff check src tests scripts

type-check:
	uv run pyright src/modwire

test:
	mkdir -p $(DEV_DIR)/testing
	uv run pytest

big-projects:
	uv run python -m tests.extraction.big_projects.run

scan-benchmark-fixture:
	uv run python -m tests.extraction.scan_benchmark.prepare --root .dev/benchmarks/scan-project --source-template "$(SCAN_BENCHMARK_SOURCE)"

scan-benchmark:
	uv run python -m tests.extraction.scan_benchmark.run --root .dev/benchmarks/scan-project --language "$(SCAN_BENCHMARK_LANGUAGE)" --excluded-pattern 'example_excluded/**'

docs-check:
	uv run python scripts/generate_docs.py --check

docs:
	uv run python scripts/generate_docs.py

build:
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(EGG_INFO_DIR)
	uv build --out-dir $(DIST_DIR)

package-check: build
	uv run twine check $(DIST_DIR)/*

extractor-check:
	python3 scripts/check_extractors.py

host-check: format-check lint type-check test docs-check package-check

ci: host-check extractor-check
