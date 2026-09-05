# Modwire

Consolidation workspace for **modwire-extraction**, **modwire-architecture**, and **modwire-cli**.

Start with [HANDOFF.md](HANDOFF.md) and the [consolidation epic](https://github.com/modwire/modwire/issues/1).
This checkout currently contains planning and handoff material; the source packages have not yet been merged.

The next task is [confirming baselines and package mapping](https://github.com/modwire/modwire/issues/2), followed by the [mechanical local merge](https://github.com/modwire/modwire/issues/3).

The merge must preserve behavior, wire every service through Wireup, combine the legacy `.modwire` configurations, and produce the expected architecture map and passing health checks. The CLI remains part of the unified package, with clean `pipx` installation verified before transfer.

After local verification, transfer this repository to `szpak-dev/modwire` and establish the organization Project. Performance improvements and Enclosure dependency upgrades are linked follow-up work.

[Planning diagrams](docs/planning/diagrams/README.md) · [Pinned source baselines](docs/planning/baselines.json)
