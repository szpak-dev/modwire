# Glossary

Modwire uses familiar architecture words in specific ways. These definitions keep
configuration, reports, and design discussion aligned.

## Analyzer

A named architecture check executed by the flow report. Modwire provides
`module-boundaries`, `backward-flow`, `no-cycles`, and `no-reentry`.

## Architecture configuration

The validated `architecture.yaml` document containing source exclusions, boundary
tags and rules, dependency flow configuration, and shape realms.

## Architecture map

A report that groups extracted source under module identities derived from the
configured `module_tag`. It also lists source that no configured module captures.

## Bounded context

A business or domain boundary with coherent ownership, language, and model. Modwire
favours source trees where a stable path segment represents this boundary. A bounded
context is mapped with tags and boundary rules; it is not a synonym for a realm.

## Boundary rule

A rule controlling dependencies from one source tag to other tags. `disallow`
defines closed targets, `allow` names explicit exceptions, and `allow_same_match`
permits collaboration inside one wildcard capture.

## Cache namespace

A caller-chosen name that isolates one set of Modwire-owned cache entries from other
callers or workflows. It is not a cache key.

## Code map

The immutable, typed, language-neutral result of source extraction. It contains
source files, declarations, relations, dependency evidence, producer identity, and
extraction metrics for one language.

## Dependency flow

The direction and paths of dependencies between classified source. Flow analyzers
check allowed boundaries, layer order, cycles, and module re-entry.

## Excluded pattern

A glob removing matching paths from a scope. Root `excluded_patterns` affect CLI
source traversal. Boundary tag and shape realm exclusions affect only their
architectural classification.

## Extractor

The language-specific boundary that translates Python, PHP, TypeScript, or Java source
into the shared code model. Extractors retain explicit runtime and capability
identity.

## Feature

A cohesive slice of behaviour inside a bounded context. In the preferred Modwire
convention, a stable path segment identifies the feature and a module tag captures
it. Teams that use the word “module” for this unit can map the same structure.

## Glob capture

The path value matched by wildcard segments such as `*` or `**`. Modwire uses the
captured value to distinguish repeated contexts, features, or modules described by
one tag pattern.

## Implementation manifest

A deterministic, provenance-bearing document containing implementation facts
observed by Modwire. It describes what exists in source; it does not claim that the
source conforms to an intended architecture.

## Layer

A named architectural role inside a feature or module, such as `api`, `application`,
`infrastructure`, or `domain`. Its position in a realm's `layers` list defines the
allowed dependency direction for `backward-flow`.

## Module

The unit used by dependency flow analysis. A realm's `module_tag` selects the tag,
and that tag's glob capture supplies each module identity. Under the preferred
convention, a module usually corresponds to a feature inside a bounded context.

## Polyglot

A source system containing more than one programming language. Modwire supports
Python, PHP, TypeScript, and Java through the same code model and architecture vocabulary.
Each extraction or CLI report still selects one language explicitly.

## Queryable code map

A `CodeMap` with typed queries for files, declarations, calls, imports, and incoming,
outgoing, tracked, or external dependencies.

## Realm

A named dependency analysis scope under `boundaries.flow.realms`. A realm selects a
`module_tag` and layer order for one architectural area. It can separate backend and
frontend conventions, for example. A realm is not a bounded context, feature, module,
or layer and does not define their hierarchy.

## Relationship inventory

The extractor-declared completeness of authored static declaration, member, or
dependency relationship evidence. Complete inventory makes absence trustworthy only
inside that family boundary. It does not include runtime calls, reflection,
framework wiring, or other unobserved behavior.

## Report

A typed architecture analysis result. Modwire returns the architecture map, flow
violations, shape violations, and non-gating insights in a stable order.

## Scan policy

Caller-owned source traversal settings: excluded patterns and whether filesystem
symlinks are followed. The CLI derives exclusions from `architecture.yaml` and does
not follow symlinks.

## Shape realm

A named path scope under `shape.realms` with structural limits for matching source.
It is separate from a dependency analysis realm. A shape realm may target a context,
feature family, layer, adapter, or any other cohesive source scope.

## Source observation

One complete, immutable canonical inventory for a language, source root, and scan
policy. It exposes a source-manifest identity and can be reused for cached map
generation when the observed files have not changed.

## Standalone tag

A tag whose matches participate in boundary analysis without being grouped as
modules. Public entry points and composition roots are common examples.

## Tag

A configured name and glob pattern that gives matching source an architectural role.
Tags can overlap: one file may belong to its bounded context, feature, and layer tags
at the same time.
