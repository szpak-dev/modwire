# Target-language ownership

Modwire is hosted and distributed as a Python package. References to Python versions, Python packaging, type checking,
and Python-based development commands are host concerns rather than analyzed-language behavior.

All analyzed-language facts belong to extractor-owned locations:

- `src/modwire/extraction/extractors/services/` owns extractor registration, target identity, file extensions, runtime
  commands, parser selection, and batch policy.
- `src/modwire/extraction/extractors/resources/` owns parser programs, dependency manifests, generated executables,
  and build adapters.
- `tests/fixtures/languages/` and extractor integration tests own language-specific validation inputs.
- `tests/extraction/big_projects/projects.json` owns pinned language-specific production fixtures.

Shared code, dependency resolution, architecture analysis, traversal, consumer verification, benchmarks, and CI
orchestration must not contain supported-language tables, runtime commands, extension tables, or language-selection
branches. Callers select a registered extractor explicitly.

## Shared contract version 2

The class-level `CodeMap.schema_version` is `2` while the existing serialized envelope remains stable. Callable kinds
are `function`, `instance_method`, `type_method`, `static_method`,
`constructor`, `callable_value`, and `anonymous`. Parameter kinds are `positional`, `variadic_positional`,
`named_only`, and `variadic_named`.

Version 1 serialized maps used extractor-specific callable and parameter vocabulary. They are not accepted as version
2 values. Regenerate them from their source with the same registered extractor; persistent reuse does not yet exist,
so there is no cache migration or silent compatibility alias.

## Adding an extractor

Add one automatic Wireup `SourceExtractor` registration, its extractor-owned resources and optional `build.py`
adapter, and extractor integration fixtures. Package data and the generic build runner discover those resources without
changes to shared services, CLI traversal, architecture analysis, the top-level Makefile, or CI orchestration.
