# Modwire

Modwire extracts source code into a typed code map and evaluates that map against
explicit architecture rules. It provides a Python API and a command-line interface
for extraction, implementation manifests, architecture reports, and project setup.

## Installation

Modwire requires Python 3.12 or newer.

```console
python -m pip install modwire
```

## Quickstart

Create the project-local configuration, then run the reports for one registered
source language:

```console
modwire init
modwire report --language python --summary
```

The supported Python interface is exported by `modwire.application`:

```python
from modwire.application import ModwireApplication, ScanPolicy

application = ModwireApplication.create()
code_map = application.generate_queryable_map(
    "python",
    ".",
    ScanPolicy(excluded_patterns=(".git/**", ".venv/**")),
)
```

## Documentation

- [Documentation entrance](docs/index.md)
- [Tutorials](docs/tutorials/index.md)
- [How-to guides](docs/how-to/index.md)
- [Architecture](docs/architecture.md)
- [Python API reference](docs/reference/api.md)
- [Contributing](docs/contributing.md)

The documentation site explains the architecture and generates API reference from
the supported Python surface.

## Development

```console
uv sync --all-groups --locked
make host-check
```

Build the documentation alone with `make docs-check`. Generated HTML is written to
`docs/_build/html` and remains outside source control.

Report defects and documentation gaps through the
[Modwire issue tracker](https://github.com/szpak-dev/modwire/issues).
