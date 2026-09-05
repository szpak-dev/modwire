# modwire-cli

Python 3.12+ CLI for Modwire architecture reports.

## Structure

- `__main__.py`: argument parsing and dependency-container lifecycle.
- `facade.py`: load config, extract code, request reports, run the output pipeline.
- `pipeline/steps/`: independently rendered report sections, ordered by Wireup qualifiers.
- `.modwire/architecture.yaml`: strict `ArchitectureConfig` input; unknown fields must remain invalid.

## Working rules

- Preserve `modwire --language <language>` report behavior unless a change explicitly replaces it.
- Keep CLI options at the boundary; put behavior in injected services/facades.
- Add subprocess-level coverage for every user-facing command in `tests/test_cli.py`.
