# Identity, cache reuse, and failure

A fast architecture report is useless if it silently reuses results for different
source. Modwire's cache starts from identity rather than timestamps or caller-provided
keys.

## Source identity comes first

A source observation records one complete canonical inventory for a selected
language and scan policy. Its identity changes when an included file is added,
removed, renamed, or edited. Excluded descendants are deliberately unobserved.

Cached map generation also accounts for the extractor descriptor, capabilities,
batch contract, installed Modwire version, observed external runtime, and executable
entrypoint content. The cache identity for a report adds the effective architecture
configuration.

Callers choose a cache directory, namespace, and capacity. They do not choose cache
keys or provide source hashes.

## Reuse is observable

Diagnostic API variants return `CachedResult` values. Each result includes a
`CacheOutcome` for applicable stages such as extraction, code map generation, and
reports. Counts distinguish hits, misses, invalidated entries, computed values, and
stored values. They do not disclose source contents or internal keys.

A reusable `SourceObservation` lets a caller establish identity and then generate a
map from that exact observation. Modwire validates that the source did not drift in
between. Changed source fails explicitly instead of producing a map assembled from
different moments.

## Expected failures are typed

All supported operational failures derive from `ModwireError`.

Modwire does not convert a missing runtime, unreadable source, invalid configuration,
corrupt manifest, or changed observation into an empty success. CLI commands render
the failure and return a nonzero status. Python callers can catch the narrow public
failure type that matches the operation.

Cache corruption is different from source ambiguity. A corrupt owned cache entry can
be invalidated and recomputed because the source remains authoritative. Invalid or
ambiguous source evidence stays visible.
