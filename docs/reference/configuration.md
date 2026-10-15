# Architecture configuration

`architecture.yaml` contains one `ArchitectureConfig` document. Unknown fields are
rejected.

## Root fields

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `excluded_patterns` | list of strings | `[]` | Project-relative source patterns excluded before CLI extraction. |
| `boundaries` | mapping | empty | Tags, boundary rules, and dependency flow analysis. |
| `shape` | mapping | required | One or more shape realms. |

## Boundary tags

Each `boundaries.tags` item contains:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `name` | non-empty string | required | Unique tag name. |
| `match` | non-empty string | required | Case-sensitive, path-segment glob. |
| `excluded_patterns` | list of strings | `[]` | Matches omitted from this tag. |

Supported glob syntax includes `*`, `**`, `?`, character sets such as `[ab]`, and
negated sets such as `[!a]`. Paths are normalised to `/`. Directory matches include
their descendants.

## Boundary rules

Each `boundaries.rules` item contains:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `source` | tag name | required | Tag whose outgoing dependencies are checked. |
| `realm` | realm name | empty | Restrict the rule to one realm under `boundaries.flow`. |
| `disallow` | list of tag names | `[]` | Target tags rejected by the rule. |
| `allow` | list of tag names | `[]` | Explicit target-tag exceptions. |
| `allow_same_match` | boolean | `false` | Allow dependencies within one wildcard capture. |

Tag names must be unique. A non-empty rule realm must name a realm under
`boundaries.flow`.

## Flow

`boundaries.flow` contains:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `module_tag` | tag name | empty | Tag whose wildcard capture identifies modules. |
| `layers` | list of tag names | `[]` | Dependency direction, ordered from entry toward core. |
| `realms` | list | `[]` | Named module-tag and layer overrides. |
| `standalone_tags` | list of tag names | `[]` | Classified nodes outside module capture. |
| `analyzers` | list of names | all registered | Flow analyzers to run. |

Each realm has `name`, `module_tag`, and `layers`. Non-empty realm names and analyzer
names must be unique.

Registered analyzers are:

- `module-boundaries`
- `backward-flow`
- `no-cycles`
- `no-reentry`

## Shape realms

`shape.realms` requires at least one item. Realm names must be unique.

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `name` | non-empty string | required | Shape scope identifier. |
| `match` | non-empty string | required | Source-tree glob. |
| `excluded_patterns` | list of strings | `[]` | Matches omitted from this shape realm. |
| `shape` | mapping | strict defaults | Structural rules for matching files. |

Numeric limits accept `-1` to disable the rule:

- `max_classes_per_file`
- `max_interfaces_per_file`
- `max_types_per_file`
- `max_abstract_classes_per_file`
- `max_functions_per_file`
- `max_variables_per_file`
- `max_methods_per_class`
- `max_declared_args`
- `max_function_lines`
- `max_method_lines`
- `max_class_lines`

The first four, method count, argument count, and line limits default to `-1`.
`max_functions_per_file` and `max_variables_per_file` default to `0`.

Boolean and vocabulary rules are:

| Field | Default |
| --- | --- |
| `allow_optional_function_args` | `false` |
| `allow_optional_method_args` | `false` |
| `allow_optional_class_properties` | `false` |
| `allow_import_aliases` | `false` |
| `require_joined_imports` | `true` |
| `allowed_import_crossing_types` | `[module, symbol]` |

Read [The Modwire architecture convention](../convention.md) before choosing scopes
and limits. The schema tells you what is valid; the convention explains what keeps a
large system coherent.
