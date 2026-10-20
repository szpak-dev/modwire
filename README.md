# Modwire

> **Your architecture already has rules. Modwire makes them enforceable.**

Modwire turns intended boundaries into executable checks across Python, PHP,
TypeScript, and Java. When a dependency points backward, code crosses a boundary, a cycle
appears, or the source layout drifts, Modwire reports the violation before the
architecture becomes tribal knowledge.

*Polyglot architecture checks, one model.*

Modwire favours systems whose source tree makes bounded contexts, features or
modules, and layers visible. Glob patterns map that convention onto a real
repository. Boundary, dependency flow, cycle, re-entry, and shape checks keep it
consistent as the system changes.

## Installation

Modwire requires Python 3.12 or newer.

```console
python -m pip install modwire
```

## Quickstart

Create the project-local configuration, then run the reports for each language in
the repository:

```console
modwire init
modwire report --language python --summary
modwire report --language typescript --summary
modwire report --language php --summary
modwire report --language java --summary
```

Each report run selects one language. The architecture vocabulary and rules stay the
same across all four.

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
- [Explanation](docs/explanation/index.md)
- [Architecture](docs/architecture/index.md)
- [Technical reference](docs/reference/index.md)
- [Language support and limits](docs/reference/language-support.md)
- [Recorded evidence](docs/reference/evidence.md)
- [Contributing](docs/how-to/contributing.md)

The documentation site covers the complete first workflow, configuration, caching,
implementation manifests, failure contracts, language capability differences,
recorded extraction evidence, and the supported Python surface.

## Development

```console
uv sync --all-groups --locked
make host-check
```

Build the documentation alone with `make docs-check`. Generated HTML is written to
`docs/_build/html` and remains outside source control.

Report defects and documentation gaps through the
[Modwire issue tracker](https://github.com/szpak-dev/modwire/issues).
