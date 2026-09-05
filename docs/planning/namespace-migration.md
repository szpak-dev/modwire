# Unified namespace — user correction during issue #3

The user explicitly chose `src/modwire/{architecture,extraction,cli}`. This supersedes the preserved split import-package layout in issue #2's historical preflight. The distribution remains `modwire`.

| Old import | New import |
| --- | --- |
| `modwire_architecture` | `modwire.architecture` |
| `modwire_extraction` | `modwire.extraction` |
| `modwire_cli` | `modwire.cli` |

All retained submodules follow the same prefix substitution. There are no duplicated model classes or old namespace copies. Resources move with their owning package; package-data, runtime lookups, CLI entrypoint, tests and workflows must use the new paths. The CLI command remains `modwire`.

The user also retired Architecture's `layers`, `modules` and `projects` applications and their unused shared configuration models. Pinned originals remain in the original repositories; `removed-modules.json` records the retired source paths before the namespace move.

Downstream consumers, including Enclosure, need the import prefix migration plus the explicit Wireup runtime composition API. This is a deliberate API change, separate from parser/report behavior preservation. No downstream deployment is implied by the local implementation.

CI/release workflows are part of #3. All caches, local artifacts and diagnostic dumps go to gitignored `.dev/`.
