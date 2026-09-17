# modwire-cli

The command-line interface for the Modwire ecosystem.

## Install

```sh
pip install modwire-cli
```

## Usage

```sh
modwire init
modwire report --language python
```

By default, Modwire reads its configuration from `.modwire/architecture.yaml`
and analyses the current directory. Override either path when needed:

```sh
modwire report --language typescript --dot-dir path/to/.modwire --architecture-root path/to/source
```

Use `--summary` for a compact module → layer map that omits individual source files:

```sh
modwire report --language python --summary
```

The original option-only command remains supported for existing automation:

```sh
modwire --language python
```

To check this repository's architecture:

```sh
uv run modwire report --language python
```

<!-- generated:public-api:start -->
## Command reference

Provide `modwire init` for setup and `modwire report` for architecture feedback.

Existing `modwire --language <language>` automation continues to run reports.

| Command | Purpose |
| --- | --- |
| `modwire init` | Create `.modwire/` guidance and a strict architecture template. |
| `modwire report --language <language>` | Analyse the configured project and render violations. |
| `modwire --language <language>` | Backwards-compatible form of `report`. |

Use `--summary` with `report` to render module-to-layer membership without files.
<!-- generated:public-api:end -->

## Development

```sh
uv sync --all-groups
uv run pytest
uv run ruff check .
uv build
```

The README command reference is generated from the public CLI docstring:

```sh
make docs
make verify
```
