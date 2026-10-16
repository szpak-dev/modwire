# Architecture

Modwire separates language-specific source extraction from language-neutral
architecture analysis. Applications use `ModwireApplication`; the command-line layer
coordinates filesystem access, extractor processes, configuration, reporting, and the
persistent cache.

The [Modwire architecture convention](convention.md) describes the architecture
Modwire favours in a user's system. This page describes Modwire itself.

## Architecture authority

The canonical authorities are **ModwireApplication Tree, revision 5**, and
**ModwireApplication UML, revision 15**, in the project architecture record. The
component view below is a reader-oriented projection of those accepted diagrams,
not a second architecture definition. If prose and a canonical diagram diverge,
the diagram governs and the prose must be corrected.

```text
CLI and Python consumers
└── modwire.application
    └── ModwireApplication
        ├── ArchitectureFacade     configuration, analysis, report catalog
        ├── CliFacade              filesystem, processes, cache, CLI workflow
        ├── ExtractionFacade       extractor registration and code-map assembly
        └── ImplementationFacade   implementation-manifest formats and documents
             │
             └── modwire.shared    typed language-neutral contracts
```

The public object is the composition boundary. Consumers use
`modwire.application`; the facades organize internal responsibility without asking
consumers to construct or import internal services.

## Processing flow

1. The CLI observes the requested source tree using an explicit `ScanPolicy`.
2. A registered extractor translates source files into Modwire's shared code model.
3. Modwire assembles the extracted declarations and relations into a `CodeMap`.
4. Architecture rules evaluate a `QueryableCodeMap` and produce report nodes.
5. Optional caches reuse extraction, code map, and report results only when their
   source and configuration identities still match.

Each extraction and report operation selects one language. Python, PHP, and
TypeScript therefore retain exact extractor provenance while publishing the same
shared code contracts.

## Internal component boundaries

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

`ModwireApplication.create()` composes these boundaries through Wireup. A consuming
application receives one public object and does not need to assemble internal
services or depend on their packages.
