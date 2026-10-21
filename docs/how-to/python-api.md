# Use Modwire through the Python API

Use `modwire.application` when another tool needs extraction, queries, architecture
reports, cache diagnostics, or an implementation manifest without parsing CLI
output.

## Extract and analyse source

Create the public application and validate configuration before analysis. This
example runs against the same Python source used by the tutorial:

```{literalinclude} ../_examples/python_api.py
:language: python
```

`generate_queryable_map` performs filesystem work through Modwire's CLI boundary
and returns a `QueryableCodeMap`. The example queries files and tracked dependencies,
selects a report by its public metadata, and asserts the observable violation count
without reaching into extractor internals. The repository test suite executes this
file, so its configuration, public imports, and expected result cannot drift as
unchecked prose.

## Reuse cached extraction and reports

Supply explicit cache ownership:

```python
from modwire.application import CacheOptions

cache = CacheOptions(
    directory=".modwire/cache",
    namespace="documentation-example",
    max_bytes=512 * 1024 * 1024,
)
cached_map = application.generate_queryable_map_cached_with_diagnostics(
    "python",
    ".",
    policy,
    cache,
)
cached_reports = application.analyze_cached_with_diagnostics(
    cached_map.value,
    config,
    cache,
)
```

Each `CachedResult` contains the value and one `CacheOutcome` per applicable stage.
The outcomes expose counts and reuse state, never cache keys or source contents.

## Publish an implementation manifest

An implementation manifest records observed source facts and provenance. It does not
claim that the implementation satisfies an intended architecture.

```python
code_map = application.generate_map("python", ".", policy)
manifest_format = application.implementation_manifest_formats()[0]
document = application.implementation_manifest(code_map, manifest_format)
manifest = application.read_implementation_manifest(document)

assert code_map.schema_version == 11
assert manifest_format.id == "canonical-json"
assert manifest.schema_version == 8
assert document.verify_digest()

with open("implementation-manifest.json", "w", encoding="utf-8") as target:
    target.write(document.payload)
```

`read_implementation_manifest` validates canonical content and the declared digest
before returning the typed manifest. Inspect
`manifest.producer.relationship_capabilities` before treating an empty relationship
family as evidence of absence.
