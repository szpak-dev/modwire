# Reports and public failures

## Report catalogue

Every analysis returns these reports in order:

| Identifier | Purpose |
| --- | --- |
| `architecture.map` | Classified modules, source files, and unclassified files. |
| `architecture.violations.flow` | Boundary, layer direction, cycle, and re-entry violations. |
| `architecture.violations.shape` | Structural rule violations grouped by shape realm. |
| `architecture.insights` | Non-gating implementation observations. |

The CLI treats flow and shape violations as a failed architecture check. Insights do
not become violations merely because they are present.

## Failure hierarchy

`ModwireError` is the base class for supported operational failures.

| Failure | Meaning |
| --- | --- |
| `ArchitectureError` | Invalid or unsupported architecture analysis state. |
| `UnknownFlowAnalyzerError` | Configuration names an unregistered flow analyzer. |
| `ExtractionError` | Source cannot be discovered, extracted, or parsed as requested. |
| `UnsupportedLanguageError` | No extractor is registered for the language. |
| `UnsupportedParserError` | No in-process parser is registered for the language. |
| `DuplicateIdentityError` | Two source items claim the same extracted identity. |
| `InvalidSourceRootError` | The requested source root is not a directory. |
| `SourceAccessError` | The operating system rejects source-tree access. |
| `SourceObservationInvalidatedError` | Source changed after its canonical observation. |
| `ExtractorUnavailableError` | A required external extractor runtime is unavailable. |
| `ExtractorResourceError` | A packaged extractor resource is missing or unreadable. |
| `ExtractorExecutionError` | The external extractor process exits unsuccessfully. |
| `ExtractorContractError` | Extractor output violates the runtime contract. |
| `CacheOwnershipError` | The requested path is not recognised as Modwire-owned cache state. |
| `CacheAccessError` | The operating system rejects cache access. |
| `InitializationError` | Project initialization cannot complete. |
| `InvalidInitializationTargetError` | A generated target escapes its accepted project boundary. |
| `UnsupportedManifestFormatError` | No serializer owns the requested manifest format. |
| `InvalidImplementationManifestError` | Manifest content violates its canonical contract. |

More specific failures derive from their family and from `ModwireError`. Catch the
narrow type when recovery is operation-specific; catch `ModwireError` at a complete
Modwire boundary.
