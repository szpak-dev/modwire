# Modwire

Consolidation workspace for **modwire-extraction**, **modwire-architecture**, and **modwire-cli**.

Start with [HANDOFF.md](HANDOFF.md) and the [consolidation epic](https://github.com/modwire/modwire/issues/1).
This checkout currently contains planning and handoff material; the source packages have not yet been merged.

The next task is [confirming baselines and package mapping](https://github.com/modwire/modwire/issues/2), followed by the [mechanical local merge](https://github.com/modwire/modwire/issues/3).

The merge must preserve behavior, wire every service through Wireup, combine the legacy `.modwire` configurations, and produce the expected architecture map and passing health checks. The CLI remains part of the unified package, with clean `pipx` installation verified before transfer.

Enclosure MCP is the single source of truth for project guidance, architecture and diagrams; the local docs are bootstrap context and synchronized exports. The consolidation also evaluates how agents use Enclosure for a new, demanding project.

After the local merge, package/CLI verification and usable Enclosure project management with the canonical diagrams and real architecture/health evidence, **stop for the user's explicit acceptance of the local implementation**. Repository transfer, organization Projects setup, publication, performance improvements and Enclosure dependency upgrades are later work requiring a subsequent instruction. See the handoff for current MCP retrieval blockers.

[Planning diagrams](docs/planning/diagrams/README.md) · [Pinned source baselines](docs/planning/baselines.json)
