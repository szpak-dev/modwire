DEV_DIR := .dev
DIST_DIR := $(DEV_DIR)/dist
PROJECT_ROOT := $(CURDIR)
PHP_EXTRACTOR_DIR := src/modwire/cli/resources/extractors/php
PHP_EXTRACTOR_WORK_DIR := $(DEV_DIR)/native/php
TYPESCRIPT_EXTRACTOR_DIR := src/modwire/cli/resources/extractors/typescript
TYPESCRIPT_EXTRACTOR_WORK_DIR := $(DEV_DIR)/native/typescript

export COMPOSER_CACHE_DIR := $(PROJECT_ROOT)/$(DEV_DIR)/cache/composer
export npm_config_cache := $(PROJECT_ROOT)/$(DEV_DIR)/cache/npm
export PYTHONPYCACHEPREFIX := $(PROJECT_ROOT)/$(DEV_DIR)/cache/python
export UV_CACHE_DIR := $(PROJECT_ROOT)/$(DEV_DIR)/cache/uv

.PHONY: architecture build ci docs-check format format-check lint native-check package-check php-check python-ci test type-check typescript-check

format:
	uv run ruff format src tests scripts

format-check:
	uv run ruff format --check src tests scripts

lint:
	uv run ruff check src tests scripts

type-check:
	uv run pyright src/modwire

test:
	uv run pytest

docs-check:
	uv run python scripts/generate_docs.py --check

architecture:
	uv run modwire report --language python --summary

build:
	rm -rf $(DIST_DIR)
	uv build --out-dir $(DIST_DIR)

package-check: build
	uv run twine check $(DIST_DIR)/*

typescript-check:
	rm -rf $(TYPESCRIPT_EXTRACTOR_WORK_DIR)
	mkdir -p $(TYPESCRIPT_EXTRACTOR_WORK_DIR)
	cp $(TYPESCRIPT_EXTRACTOR_DIR)/package.json $(TYPESCRIPT_EXTRACTOR_DIR)/package-lock.json $(TYPESCRIPT_EXTRACTOR_DIR)/build.mjs $(TYPESCRIPT_EXTRACTOR_DIR)/script.ts $(TYPESCRIPT_EXTRACTOR_DIR)/tsconfig.json $(TYPESCRIPT_EXTRACTOR_WORK_DIR)
	cd $(TYPESCRIPT_EXTRACTOR_WORK_DIR) && npm ci && npm run check && npm run build
	cmp $(TYPESCRIPT_EXTRACTOR_WORK_DIR)/script.js $(TYPESCRIPT_EXTRACTOR_DIR)/script.js

php-check:
	rm -rf $(PHP_EXTRACTOR_WORK_DIR)
	mkdir -p $(PHP_EXTRACTOR_WORK_DIR)
	cp $(PHP_EXTRACTOR_DIR)/composer.json $(PHP_EXTRACTOR_DIR)/composer.lock $(PHP_EXTRACTOR_DIR)/build.php $(PHP_EXTRACTOR_DIR)/script.src.php $(PHP_EXTRACTOR_WORK_DIR)
	composer --working-dir=$(PHP_EXTRACTOR_WORK_DIR) install --no-interaction --no-progress --prefer-dist
	composer --working-dir=$(PHP_EXTRACTOR_WORK_DIR) check
	composer --working-dir=$(PHP_EXTRACTOR_WORK_DIR) build
	cmp $(PHP_EXTRACTOR_WORK_DIR)/script.php $(PHP_EXTRACTOR_DIR)/script.php

native-check: typescript-check php-check

python-ci: format-check lint type-check test docs-check architecture package-check

ci: python-ci native-check
