# Modwire

**Polyglot architecture checks, one model.**

Modwire extracts Python, PHP, and TypeScript into the same typed, language-neutral
code model. It then checks explicit architecture rules for each language's source
set.

Modwire favours systems whose source tree makes the architecture visible:

```text
<bounded-context>/<feature-or-module>/<layer>/...
```

Glob patterns map that convention onto a real repository. Boundary, dependency flow,
cycle, re-entry, and shape checks keep it consistent as the system changes.

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
```

Each report run selects one language. The architecture vocabulary and rules stay the
same across all three.

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
- [Contributing](docs/how-to/contributing.md)

The documentation site covers the complete first workflow, configuration, caching,
implementation manifests, failure contracts, and the supported Python surface.

## Development

```console
uv sync --all-groups --locked
make host-check
```

Build the documentation alone with `make docs-check`. Generated HTML is written to
`docs/_build/html` and remains outside source control.

Report defects and documentation gaps through the
[Modwire issue tracker](https://github.com/szpak-dev/modwire/issues).
