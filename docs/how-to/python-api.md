# Use Modwire through the Python API

Use `modwire.application` when another tool needs extraction, queries, architecture
reports, cache diagnostics, or an implementation manifest without parsing CLI
output.

## Extract and analyse source

Create the public application and validate configuration before analysis:

```python
from modwire.application import ModwireApplication, ScanPolicy

application = ModwireApplication.create()
config = application.configure(
    {
        "boundaries": {
            "tags": [
                {"name": "feature", "match": "src/*/*"},
                {"name": "api", "match": "src/*/*/api"},
                {"name": "application", "match": "src/*/*/application"},
                {"name": "infrastructure", "match": "src/*/*/infrastructure"},
                {"name": "domain", "match": "src/*/*/domain"},
            ],
            "rules": [
                {
                    "source": "feature",
                    "disallow": ["feature"],
                    "allow_same_match": True,
                }
            ],
            "flow": {
                "module_tag": "feature",
                "layers": ["api", "application", "infrastructure", "domain"],
                "analyzers": ["module-boundaries", "no-cycles", "no-reentry"],
            },
        },
        "shape": {
            "realms": [
                {
                    "name": "source",
                    "match": "src",
                    "shape": {"max_classes_per_file": 1},
                }
            ]
        },
    }
)
policy = ScanPolicy(excluded_patterns=("generated/**", ".venv/**"))
code_map = application.generate_queryable_map("python", ".", policy)
reports = application.analyze(code_map, config)
```

`generate_queryable_map` performs filesystem work through Modwire's CLI boundary and
returns a `QueryableCodeMap`. Query declarations or dependencies without reaching
into extractor internals:

```python
source_files = code_map.files().count()
classes = code_map.classes().count()
tracked_dependencies = code_map.tracked_dependency_edges().count()
```

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

assert manifest_format.id == "canonical-json"
assert document.verify_digest()

with open("implementation-manifest.json", "w", encoding="utf-8") as target:
    target.write(document.payload)
```

Read a received document with `read_implementation_manifest`. It validates canonical
content and the declared digest before returning the typed manifest.
