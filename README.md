# Modwire

Consolidation workspace for **modwire-extraction**, **modwire-architecture**, and **modwire-cli**.

Start with the [Modwire board](https://github.com/orgs/szpak-dev/projects/13) and the [consolidation epic](https://github.com/szpak-dev/modwire/issues/1).

The merge must preserve behavior, wire every service through Wireup, combine the legacy `.modwire` configurations, and produce the expected architecture map and passing health checks. The CLI remains part of the unified package, with clean `pipx` installation verified before transfer.

Enclosure MCP is the single source of truth for project guidance, architecture and diagrams; the local docs are bootstrap context and synchronized exports. The consolidation also evaluates how agents use Enclosure for a new, demanding project.

After the local merge, package/CLI verification and usable Enclosure project management with the canonical diagrams and real architecture/health evidence, **stop for the user's explicit acceptance of the local implementation**. Publication, performance improvements and Enclosure dependency upgrades are later work requiring a subsequent instruction. Current blockers live in the native issue graph and organization boards.

[Planning diagrams](docs/planning/diagrams/README.md) · [Pinned source baselines](docs/planning/baselines.json)

<!-- generated:public-api:start -->
## Command reference

Provide `modwire init` for setup and `modwire report` for architecture feedback.

Existing `modwire --language <language>` automation continues to run reports.

| Command | Purpose |
| --- | --- |
| `modwire init` | Create `.modwire/` guidance and a strict architecture template. |
| `modwire report --language <language>` | Analyse the configured project and render violations. |
| `modwire --language <language>` | Backwards-compatible form of `report`. |

Use `--summary` with `report` to render module-to-layer membership without files.
<!-- generated:public-api:end -->
