.PHONY: verify

verify:
	uv run ruff check src tests
	uv run pytest
	uv build
	uv run twine check dist/*
