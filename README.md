# Modwire

## `ModwireApplication`

Public entry point for source discovery, extraction, architecture analysis, and the Modwire CLI.

### `create`

Create an isolated application with all services resolved through Wireup.

### `configure`

Validate architecture configuration values.

### `catalog`

Return the available architecture reports.

### `analyze`

Analyze a code map with a validated architecture configuration.

### `analyze_cached`

Analyze a code map, reusing reports for an exact map and configuration identity.

### `analyze_cached_with_diagnostics`

Analyze a code map and report the public outcome of report-cache reuse.

### `discover`

Discover supported source languages beneath a root using the caller's scan policy.

### `generate_map`

Extract one language and return its code map with honest scan metrics.

``files_excluded`` counts only source files encountered and excluded directly.
``directories_pruned`` counts directories rejected before descent; their
descendants are deliberately unobserved and are not included in file counts.

### `generate_queryable_map`

Extract source files and return a queryable code map.

### `generate_map_cached`

Return a code map with content-addressed source and complete-manifest reuse.

### `generate_map_cached_with_diagnostics`

Return a code map and public outcomes for extraction and complete-map reuse.

### `generate_queryable_map_cached`

Return a queryable code map with content-addressed persistent reuse.

### `generate_queryable_map_cached_with_diagnostics`

Return a queryable code map and public outcomes for every applicable cache stage.

### `clear_cache`

Clear only the Modwire-owned directory for one cache namespace.

### `load_configuration`

Load and validate an architecture configuration from a directory.

### `initialize`

Create project-local Modwire configuration and agent guidance.

### `generate_documentation`

Generate this README from the published interface docstrings, or check that it is current.

### `run_extractor`

Run the native extractor transport for one supported language.

### `run`

Run the Modwire command line interface and return its process status.

## `CacheStage`

Public stages reported by cached Modwire operations.

## `CacheOutcome`

Content-safe lifecycle counts for one stage of a cached operation.

Extraction counts describe current source records. Code-map and report counts
describe one entry. Invalidated entries are also misses. Diagnostics include
the configured namespace but never cache keys, source identities, or content.

## `CachedResult`

A cached operation value together with one outcome per applicable stage.

### `outcome`

Return the outcome for one applicable cache stage.

## `CacheOptions`

Generic persistent-cache settings supplied by a caller.

## `ScanPolicy`

Caller-owned filesystem traversal policy with explicit exclusions and opt-in symlink following.
