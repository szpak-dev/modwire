# Configure and run architecture reports

Use this procedure to add Modwire to an existing repository and run the architecture
checks for each source language.

## Initialize the repository

From the repository root, run:

```console
modwire init
```

The command creates `.modwire/architecture.yaml`, an index, and concise working
guidance. It also creates `AGENTS.md` at the project root. Existing files are
preserved. Use `modwire init --force` only when you intend to replace generated
assets.

Use another configuration directory when `.modwire` is not suitable:

```console
modwire init --dot-dir config/modwire
```

Pass the same directory to later commands.

## Adapt the architecture convention

Open `architecture.yaml` and map the repository's stable directory convention.
Modwire favours this hierarchy:

```text
<bounded-context>/<feature-or-module>/<layer>/...
```

Name those concepts with boundary tags, configure feature or module tags as the
`module_tag` of realms under `boundaries.flow`, and apply shape rules to the smallest
useful source-tree scope. The complete
reasoning and examples are in
[The Modwire architecture convention](../architecture/convention.md). Exact fields are listed in
the [configuration reference](../reference/configuration.md).

## Run one report per language

Select the source language explicitly:

```console
modwire report --language python
modwire report --language typescript
modwire report --language php
```

Python ships with its extractor runtime. TypeScript requires Node.js on `PATH`; PHP
requires PHP on `PATH`.

Use `--summary` to omit individual files from a successful architecture map:

```console
modwire report --language python --summary
```

Use `--architecture-root` when the governed source tree is not the current directory:

```console
modwire report --language python --architecture-root packages/orders
```

Use `--dot-dir` when the configuration is stored elsewhere:

```console
modwire report --language python --dot-dir config/modwire
```

A clean report exits with status `0`. A reported architecture violation exits with
status `1` and names the failed rule and relevant source path or dependency path.
