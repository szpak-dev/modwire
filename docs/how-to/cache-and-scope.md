# Control source scope and persistent cache

Use exclusions to keep generated or irrelevant source outside the analysis. Use
cache options to keep repeated reports fast without changing their meaning.

## Exclude source paths

Add project-relative patterns at the top of `architecture.yaml`:

```yaml
excluded_patterns:
  - .git/**
  - generated/**
  - vendor/**
```

For CLI reports, these patterns prune matching source paths before extraction. A
directory excluded before traversal does not contribute file counts because Modwire
does not inspect its descendants.

Boundary tags and shape realms each have their own `excluded_patterns`. Those
exclusions refine classification or shape evaluation after extraction:

```yaml
boundaries:
  tags:
    - name: feature
      match: src/*/*
      excluded_patterns:
        - src/*/*.py

shape:
  realms:
    - name: production
      match: src
      excluded_patterns:
        - src/generated/**
      shape:
        max_classes_per_file: 1
```

Use top-level exclusions when a path should not be read. Use tag or shape exclusions
when Modwire should still extract the source but omit it from one architectural
classification.

## Choose a cache namespace

CLI reports use `.modwire/cache`, the `default` namespace, and a 512 MiB size limit
unless you override them:

```console
modwire report \
  --language python \
  --cache-directory .cache/modwire \
  --cache-namespace pull-request \
  --cache-max-bytes 268435456
```

Namespaces isolate callers or workflows that should not manage one another's cache
entries. The cache remains content-addressed: source, extractor runtime, complete
source set, and effective configuration identities decide whether reuse is valid.

Run once without persistent reuse when measuring cold behaviour or checking cache
independence:

```console
modwire report --language python --no-cache
```

Clear only one namespace with matching options:

```console
modwire cache-clear \
  --cache-directory .cache/modwire \
  --cache-namespace pull-request \
  --cache-max-bytes 268435456
```

Modwire refuses to treat an arbitrary directory as owned cache state. Clearing a
namespace removes only the Modwire-owned directory for that namespace.
