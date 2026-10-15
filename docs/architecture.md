# Architecture

Modwire separates language-specific source extraction from language-neutral
architecture analysis. Applications use `ModwireApplication`; the command-line layer
coordinates filesystem access, extractor processes, configuration, reporting, and the
persistent cache.

## Processing flow

1. The CLI observes the requested source tree using an explicit `ScanPolicy`.
2. A registered extractor translates source files into Modwire's shared code model.
3. Modwire assembles the extracted declarations and relations into a `CodeMap`.
4. Architecture rules evaluate a `QueryableCodeMap` and produce report nodes.
5. Optional caches reuse extraction, code-map, and report results only when their
   source and configuration identities still match.

## Component boundaries

- `modwire.application` publishes the supported Python interface.
- `modwire.extraction` owns language registration and conversion into the shared code
  model.
- `modwire.shared` owns the language-neutral values exchanged between extraction,
  architecture analysis, caching, and implementation manifests.
- `modwire.architecture` owns configuration, rules, analysis, and reports.
- `modwire.implementation` serializes observed implementation facts with their source
  provenance.
- `modwire.cli` owns filesystem and process interaction, extractor transport, project
  initialization, rendering, and persistent cache storage.
