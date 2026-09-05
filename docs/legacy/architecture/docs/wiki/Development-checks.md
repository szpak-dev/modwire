# Development Checks

Run these checks before opening a pull request:

```bash
uv sync --all-groups
uv run ruff check src tests
uv run pytest
uv build
uv run twine check dist/*
```

This page is the canonical local-check list; README and contributor guidance
link here to avoid release-process drift.

The CI workflow currently validates:

- Python 3.12, 3.13, and 3.14
- Ruff static checks and the unit test suite
- package build and distribution metadata

CI delegates these checks to the reusable
[`python-package.yml`](../../.github/workflows/python-package.yml) workflow.
Packaging and tests do not require a pre-existing `.dev` directory; caches are
disposable and use their tool defaults.
