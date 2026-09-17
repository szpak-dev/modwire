# Migrating from Modwire 4 to 5

Modwire 5 makes Core an in-memory architecture engine. Callers own filesystem
discovery, configuration loading, code extraction, and generated-file output.

## Architecture reports

Pass an already extracted `QueryableCodeMap` to Core:

```python
from modwire import ArchitectureConfig, Modwire
from modwire_extraction import QueryableCodeMap


def architecture_reports(code_map: QueryableCodeMap):
    return Modwire().architecture(ArchitectureConfig()).report(code_map)
```

Replace these Modwire 4 APIs:

| Modwire 4 | Modwire 5 |
| --- | --- |
| `Modwire().extract(root, language)` | Extract externally and inject a `QueryableCodeMap`. |
| `ArchitectureApplication.report(root, language)` | `ArchitectureApplication.report(code_map)` |
| `QueryableCodeMapReader.read(root, language)` | Removed from Core. |
| `CodePackageWriter.write(package, destination)` | Removed from Core; callers own output. |

## Configuration and serialization

Core retains `from_json`, `to_json`, `from_yaml`, `to_yaml`, `from_dict`, and
`to_dict`. The path-based `load_json`, `save_json`, `load_yaml`, and `save_yaml`
helpers are removed. Read or write files outside Core and pass strings or
dictionaries to Core.

`ModwireConfig.load_dir()` is also removed. Callers read and combine
configuration before constructing the strict in-memory config.

## Dependency graphs and boundaries

Modwire 5 requires `modwire-extraction>=2,<3`. Graph nodes are tracked file IDs;
resolved edges target tracked files, while external and unresolved edges retain
their specifier and explicit resolution state without entering boundary checks.

Boundary rules are closed allowlists:

- same-module tracked dependencies are allowed;
- a tracked cross-module dependency must match an explicit `allow` target;
- external and unresolved edges are ignored by module policy;
- tracked files without a configured module tag produce an unclassified
  violation;
- duplicate tag names remain invalid, while each file may intentionally match
  several distinct tags and realms.
