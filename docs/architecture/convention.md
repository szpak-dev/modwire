# The Modwire architecture convention

A directory tree can be tidy and still say nothing about the architecture. A folder
named `services` does not tell you which business boundary owns it, which feature it
serves, or which direction its dependencies may travel.

Modwire favours a stronger convention:

```text
<bounded-context>/<feature-or-module>/<layer>/...
```

The names vary between systems. The hierarchy matters. A bounded context owns a
coherent model and language. A feature or module owns a slice of behaviour inside
that context. A layer describes the role code plays inside the feature.

This convention is not hardcoded into Modwire. Glob patterns map it to the actual
source tree, which keeps the rule explicit and lets Python, PHP, TypeScript, Java, and
Ruby share the same architecture vocabulary.

The [glossary](../reference/glossary.md) distinguishes realms, bounded contexts, features,
modules, layers, tags, and shape realms.

## Start with bounded contexts

Suppose a repository contains sales and fulfilment contexts:

```text
src/
├── sales/
│   ├── orders/
│   └── pricing/
└── fulfilment/
    ├── shipping/
    └── inventory/
```

Capture the first directory below `src` as a context:

```yaml
boundaries:
  tags:
    - name: context
      match: src/*
```

The `*` captures one path segment. Files below `src/sales` belong to the `sales`
context; files below `src/fulfilment` belong to `fulfilment`. The capture lets
Modwire distinguish those bounded contexts instead of applying one undifferentiated
label to every match.

A bounded context is valuable because it gives change a clear owner. A dependency
crossing from fulfilment into sales is then visible as an architectural decision,
not merely an import between two files.

Protect that ownership with a closed-context rule:

```yaml
boundaries:
  rules:
    - source: context
      disallow: [context]
      allow_same_match: true
```

Code may collaborate inside one captured context. A dependency into another context
fails unless a more specific allowed tag names the intended public contract. This
keeps cross-context integration explicit without teaching Modwire business semantics.

## Put features or modules inside the context

Capture the next path segment as the feature or module:

```yaml
boundaries:
  tags:
    - name: context
      match: src/*
    - name: feature
      match: src/*/*
```

`src/sales/orders` and `src/sales/pricing` become separate feature captures. This is
where Modwire becomes especially useful: the same boundary rule can protect every
feature discovered through the convention.

```yaml
  rules:
    - source: feature
      disallow: [feature]
      allow_same_match: true
```

The rule rejects dependencies between distinct feature captures while allowing code
inside one feature to collaborate. Add named exceptions deliberately, usually for a
shared contract or an explicit public facade:

```yaml
  tags:
    - name: shared
      match: src/shared

  rules:
    - source: feature
      disallow: [feature]
      allow: [shared]
      allow_same_match: true
```

The important part is not that every feature is isolated forever. The important
part is that crossing a feature boundary requires a visible rule.

## Make layers directional

Inside each feature, use stable layer names:

```text
src/sales/orders/api/
src/sales/orders/application/
src/sales/orders/infrastructure/
src/sales/orders/domain/
```

Tag the layers and order them from entry point toward the core:

```yaml
boundaries:
  tags:
    - {name: feature, match: "src/*/*"}
    - {name: api, match: "src/*/*/api"}
    - {name: application, match: "src/*/*/application"}
    - {name: infrastructure, match: "src/*/*/infrastructure"}
    - {name: domain, match: "src/*/*/domain"}

  flow:
    module_tag: feature
    layers: [api, application, infrastructure, domain]
    analyzers: [module-boundaries, backward-flow, no-cycles, no-reentry]
```

`backward-flow` rejects a dependency that moves against the declared order.
`no-cycles` rejects cyclic module dependencies. `no-reentry` rejects a dependency
path that leaves a feature and later enters it again. Together they protect more
than a folder layout: they protect the direction of collaboration.

Layers only help when they carry a stable meaning. Do not add a layer because a
framework generated a directory. Name the role that should constrain dependencies.

## Use realms when conventions differ

A polyglot repository may contain different but equally deliberate structures. A
backend might use `api → application → infrastructure → domain`, while a frontend
uses `page → state → component`.

Model them as separate realms:

```yaml
boundaries:
  tags:
    - {name: backend-context, match: "src/backend/*"}
    - {name: backend-feature, match: "src/backend/*/*"}
    - {name: api, match: "src/backend/*/*/api"}
    - {name: application, match: "src/backend/*/*/application"}
    - {name: infrastructure, match: "src/backend/*/*/infrastructure"}
    - {name: domain, match: "src/backend/*/*/domain"}
    - {name: frontend-context, match: "src/frontend/*"}
    - {name: frontend-feature, match: "src/frontend/*/*"}
    - {name: page, match: "src/frontend/*/*/page"}
    - {name: state, match: "src/frontend/*/*/state"}
    - {name: component, match: "src/frontend/*/*/component"}

  flow:
    realms:
      - name: backend
        module_tag: backend-feature
        layers: [api, application, infrastructure, domain]
      - name: frontend
        module_tag: frontend-feature
        layers: [page, state, component]
    analyzers: [module-boundaries, backward-flow, no-cycles, no-reentry]
```

Realms prevent one layer vocabulary from being stretched until it means nothing.
They also let the same Modwire configuration govern Python backend source and
TypeScript frontend source one language report at a time.

## Use glob captures deliberately

The [configuration reference](../reference/configuration.md) defines the
supported glob syntax, path normalisation, and descendant matching behaviour.

Use `**` carefully. A broad recursive capture can collapse architectural levels that
should remain distinct. Prefer one `*` for each convention level when the path has a
stable context, feature, and layer structure.

When source should still be extracted but omitted from one tag or shape realm, use a
local exclusion. [Control source scope and persistent cache](../how-to/cache-and-scope.md)
shows how local exclusions differ from exclusions applied before extraction.

## Apply shape where ownership is clear

Boundary rules constrain relationships. Shape rules constrain the source inside a
shape realm:

```yaml
shape:
  realms:
    - name: feature-source
      match: src/*/*
      excluded_patterns:
        - src/*/*/generated/**
      shape:
        max_classes_per_file: 1
        max_methods_per_class: 10
```

The [configuration reference](../reference/configuration.md) lists every shape rule,
its default, and how to disable numeric limits. Configure each shape realm according
to its actual role.

Shape rules work best when their shape realm has one architectural purpose. A domain
model, an integration adapter, and a generated client rarely deserve identical
limits.

## Treat the convention as a design decision

Modwire can map another source layout. That flexibility is an escape hatch for real
systems, not a reason to abandon convention. A stable context → feature/module →
layer hierarchy makes ownership visible to people, imports, and tools at the same
time.

When a new feature fits the existing paths, the existing rules govern it
automatically. That is the payoff: architectural consistency stops depending on
someone remembering to add another special case.
