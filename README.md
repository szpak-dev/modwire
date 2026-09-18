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

### `discover`

Discover supported source languages beneath a root using the caller's scan policy.

### `generate_map`

Extract source files for one language and return their code map.

### `generate_queryable_map`

Extract source files and return a queryable code map.

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

## `ScanPolicy`

Caller-owned filesystem traversal policy with explicit exclusions and opt-in symlink following.
