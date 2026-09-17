# Modwire Architecture

Modwire Architecture is the typed architecture library for the Modwire ecosystem.
It analyzes extracted code maps in memory without owning extraction, presentation,
hypermedia, filesystem, or command-line orchestration.

```python
from modwire_architecture import ArchitectureConfig, Modwire
from modwire_extraction import QueryableCodeMap


def analyze(code_map: QueryableCodeMap):
    return Modwire().architecture(ArchitectureConfig()).report(code_map)
```

Install the library with:

```bash
python -m pip install 'modwire-architecture>=7,<8'
```

Core accepts in-memory configuration and an already extracted code map. Callers
own source discovery, configuration loading, and output handling.

## Shape realms

Shape rules are configured through one or more required realms. A realm matches
source IDs with its own glob and is independent of architecture-boundary tags.
Each realm's `shape` object uses the standard shape-rule defaults; specify only
the values that differ for that realm.

```yaml
architecture:
  shape:
    realms:
      - name: project
        match: "*"
        shape:
          max_function_lines: 40

      - name: tests
        match: tests/*
        shape:
          max_functions_per_file: -1
          allow_optional_function_args: true
```

A source matching multiple realms is evaluated under each realm's rules.

## Package shape

- `modwire_architecture.architecture` — architecture maps, boundary policies, shape checks,
  insights, and typed reports.
- `modwire_architecture.code` — validated in-memory code-package values.
- `modwire_architecture.layers` — named layer contracts; orchestration remains to be defined.
- `modwire_architecture.modules` — named module contracts; orchestration remains to be defined.
- `modwire_architecture.projects` — project coordination contracts for modules and layers;
  orchestration remains to be defined.
- `modwire_architecture.shared.config` — immutable, validated configuration contracts.
- `modwire_architecture.shared.report` — architecture report contracts and metadata.

Scaffolding and glossary functionality are not part of this package. Agent
composes Architecture, Mermaid, and Siren through their published interfaces.

## Ecosystem

The ecosystem provides independently released building blocks:

- [modwire-extraction](https://github.com/modwire/modwire-extraction) — canonical
  code extraction. Follow its [Trustworthy Foundation](https://github.com/modwire/modwire-extraction/milestone/2),
  [Canonical Symbol Model v2](https://github.com/modwire/modwire-extraction/milestone/1),
  and [Extensible Production Platform](https://github.com/modwire/modwire-extraction/milestone/3)
  milestones.
- [modwire-siren](https://github.com/modwire/modwire-siren) — typed Siren and
  OpenAPI integration. See [Siren integration improvements](https://github.com/modwire/modwire-siren/milestone/1).
- [modwire-mermaid](https://github.com/modwire/modwire-mermaid) — typed,
  deterministic Mermaid source. See [Package improvements](https://github.com/modwire/modwire-mermaid/milestone/1).

Architecture depends only on Extraction. Agent composes Architecture, Mermaid,
and Siren as separate published packages.

The architecture work here tracks the
[Standalone Architecture Package](https://github.com/modwire/modwire-architecture/milestone/7)
milestone.
Package-identity guidance is available in
[Migrating from Modwire to Modwire Architecture](docs/migration-6.md).
The historical [Modwire 4 to 5 migration](docs/migration-5.md) remains available
for existing `modwire` consumers.

## Model contracts

Public value objects derive from one of three Pydantic bases:
`ModwireModel`, `ModwireConfigModel`, or `ModwireReportModel`. They are frozen,
reject unknown fields, validate defaults, normalize surrounding string
values through domain validators, and provide dictionary, JSON, and YAML
round-trip helpers without filesystem orchestration.

## Development

```bash
uv sync --all-groups
uv run pytest
uv run ruff check src tests
uv build
```
