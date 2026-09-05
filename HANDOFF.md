# Workspace handoff — 2026-09-05

## Start here

Open `~/Projects/modwire` in VS Code. Its `origin` is `https://github.com/modwire/modwire.git`.
The user chose a fresh repository; all three source repositories remain intact.

**Next action:** read [issue #2](https://github.com/modwire/modwire/issues/2), confirm the pinned source/package mapping, then perform [issue #3's mechanical local merge](https://github.com/modwire/modwire/issues/3).
Do not restart a broad strategy or portfolio discussion. Do not make caching, organization transfer or Projects setup prerequisites for the local merge.

## Completed in bootstrap

- Created `modwire/modwire` and cloned it into the user-created local folder.
- Created [epic #1](https://github.com/modwire/modwire/issues/1), its completion tasks and linked release work; assigned new issues to `9orky`.
- Added native GitHub sub-issue and blocker relationships as well as readable issue links.
- Reused Enclosure's existing [MCP presentation epic #148](https://github.com/szpak-dev/enclosure/issues/148), including diagram #151 and record #152.
- Saved valid Enclosure planning diagrams and exported their source/snapshots with provenance below.

**Not yet done:** no source package consolidation, package publication, performance implementation, organization transfer, GitHub Project setup, actual merged architecture map or healthy merged-project claim. Modwire was unregistered in Enclosure at bootstrap. No package tests were run because this is a documentation-only bootstrap.

## Non-negotiable merge requirements

1. Merge **extraction + architecture + CLI**. `modwire-hex` remains a separate consumer.
2. Keep the merge local and mechanical: source/package moves, dependency consolidation, required import and wiring adjustments. Preserve observable behavior.
3. **Wireup constructs every service and resolves all collaborators. No manual service instances or fallback construction paths.** Architecture and CLI declare Wireup; Extraction's current manifest does not, and its manual facade composition must be migrated rather than grandfathered in.
4. Merge the legacy `.modwire` configurations and relevant guidance along with source. Produce one reviewed effective shape/boundary configuration with correct roots/patterns/realms and preserved constraints.
5. Verify a nonempty architecture map covering all three components and expected dependencies. Stale roots, unmatched patterns or excluded source must not create a false healthy result.
6. Register/bind the real merged workspace in Enclosure with the actual configuration; attach package/CLI checks and passing architecture/health evidence before calling the merge complete. Never loosen rules merely to pass.
7. Preserve the `modwire` console entry point and verify clean wheel/sdist installation plus `pipx` smoke tests; document Node/PHP prerequisites where relevant.
8. Preserve original repositories/releases and record immutable provenance. A Git-history rewrite is not required for this local mechanical merge.

## Source baselines and configuration

Use canonical tagged commits, not arbitrary contents of sibling checkouts. The local Architecture checkout inspected during planning differs from its published API.

| Source | Release | Commit |
| --- | --- | --- |
| `modwire/modwire-extraction` | `v2.1.1` | [`71808b1a924e`](https://github.com/modwire/modwire-extraction/commit/71808b1a924e1c496ddf19914ab3a577fe946228) |
| `modwire/modwire-architecture` | `v7.0.0` | [`c1ed25b1e71c`](https://github.com/modwire/modwire-architecture/commit/c1ed25b1e71c5d800450a50a72906529947268fc) |
| `modwire/modwire-cli` | `v2.0.0` | [`67f76cfa63dd`](https://github.com/modwire/modwire-cli/commit/67f76cfa63ddfaf6114ca9168939a315bf94948e) |

Legacy configuration paths verified at those commits:

- Architecture: `.modwire/boundaries.yaml` and `.modwire/shape.yaml`.
- CLI: `.modwire/architecture.yaml`, `.modwire/INDEX.md`, and `.modwire/docs/` (architecture, rules, testing, workflow and project guidance).
- Extraction: no `.modwire` files exist at the inspected release. Define deliberate coverage for it in the combined configuration; do not assume absent rules mean the component should be ungoverned.

The split and combined configuration shapes differ. Normalize envelopes and remap paths/tag/realm names; do not concatenate YAML or silently select the weaker conflicting rule. See [baselines.json](docs/planning/baselines.json) for exact source provenance.

## Issue order

Local preflight → merge → CLI/pipx and Enclosure impact checks → transfer to `szpak-dev/modwire` → organization Project → management handoff.
The following native blockers and linked issues govern the current order:

| Issue | Work | Blocked by |
| --- | --- | --- |
| [modwire/modwire#2](https://github.com/modwire/modwire/issues/2) | Confirm baselines and package mapping for the mechanical local merge | None |
| [szpak-dev/enclosure#157](https://github.com/szpak-dev/enclosure/issues/157) | Measure Enclosure migration impact against the mechanically merged Modwire package | [modwire/modwire#3](https://github.com/modwire/modwire/issues/3) |
| [modwire/modwire#3](https://github.com/modwire/modwire/issues/3) | Mechanically merge extraction, architecture and CLI into the local Modwire package | [modwire/modwire#2](https://github.com/modwire/modwire/issues/2) |
| [modwire/modwire#4](https://github.com/modwire/modwire/issues/4) | Preserve the unified modwire CLI and verify clean pipx installation | [modwire/modwire#3](https://github.com/modwire/modwire/issues/3) |
| [modwire/modwire#5](https://github.com/modwire/modwire/issues/5) | Transfer verified Modwire to szpak-dev/modwire and verify integrations | [modwire/modwire#4](https://github.com/modwire/modwire/issues/4), [szpak-dev/enclosure#157](https://github.com/szpak-dev/enclosure/issues/157) |
| [modwire/modwire#6](https://github.com/modwire/modwire/issues/6) | Establish szpak-dev Projects views for the coordinated release train | [modwire/modwire#5](https://github.com/modwire/modwire/issues/5) |
| [modwire/modwire#7](https://github.com/modwire/modwire/issues/7) | Verify consolidation handoff and close the management epic with evidence | [modwire/modwire#6](https://github.com/modwire/modwire/issues/6) |
| [modwire/modwire#8](https://github.com/modwire/modwire/issues/8) | Prune excluded paths before traversal and establish Docker scan benchmarks | [modwire/modwire#3](https://github.com/modwire/modwire/issues/3) |
| [modwire/modwire#9](https://github.com/modwire/modwire/issues/9) | Add correct incremental extraction and architecture analysis reuse | [modwire/modwire#8](https://github.com/modwire/modwire/issues/8) |
| [szpak-dev/enclosure#158](https://github.com/szpak-dev/enclosure/issues/158) | Adopt unified Modwire with scan policy and Docker cache integration | [szpak-dev/enclosure#157](https://github.com/szpak-dev/enclosure/issues/157), [modwire/modwire#9](https://github.com/modwire/modwire/issues/9), [modwire/modwire#5](https://github.com/modwire/modwire/issues/5) |
| [szpak-dev/enclosure#159](https://github.com/szpak-dev/enclosure/issues/159) | Upgrade Sirenity to 7.1 and expose discoverable pagination through MCP | None |
| [szpak-dev/enclosure#160](https://github.com/szpak-dev/enclosure/issues/160) | Upgrade Mermaiden to 6 with verified persisted-snapshot migration | None |
| [szpak-dev/enclosure#161](https://github.com/szpak-dev/enclosure/issues/161) | Verify and deliver the coordinated Modwire and Enclosure release train | [szpak-dev/enclosure#158](https://github.com/szpak-dev/enclosure/issues/158), [szpak-dev/enclosure#159](https://github.com/szpak-dev/enclosure/issues/159), [szpak-dev/enclosure#160](https://github.com/szpak-dev/enclosure/issues/160), [szpak-dev/enclosure#148](https://github.com/szpak-dev/enclosure/issues/148), [modwire/modwire#7](https://github.com/modwire/modwire/issues/7) |

The epic completes when consolidation, transfer and management are verified. The linked performance and integrated-runtime delivery work is not falsely completed with it.

## Findings to preserve

- Extraction 2.1.1 `_discover_source_files` calls `_count_source_files` on excluded directories, which still walks them. Prune before descent; do not reintroduce traversal to report excluded-file counts. Docker impact is not yet benchmarked.
- Enclosure directly uses Modwire in three source files and two dependency entries. Its impact report must distinguish simple dependency/import changes from scan/cache integration and verification.
- Healthy architecture reports did not guarantee usable MCP: context overflow and incomplete empty-collection/detail presentations were observed. Existing MCP work must prove required retrieval and continuations through MCP.
- Diagram revisions originally saved invalid draft snapshots with empty source. The diagrams are now valid with saved source; verify `draft`, validation and source availability, not revision increments alone.
- The current flowchart configuration schema exposes only `wrap`; direction is separately emitted as `flowchart TD`. Do not invent unavailable configuration fields.

## Enclosure upgrades and release gates

Enclosure currently pins Sirenity 7.0.3 and Mermaiden 5.2.3. The reviewed release targets are Sirenity 7.1.0 and Mermaiden 6.0.0; recheck upstream before implementation.

Sirenity requires verified intermediate/final-page continuation through REST, Siren and MCP. Mermaiden 6 rejects v2 snapshots: inventory, back up, convert/recreate and prove restore before pin/rollout changes. These planning snapshots also require migration. Image rollback alone cannot restore migrated data.

The later release train verifies native/Docker cold, warm and edited-source behavior; report parity; cache invalidation/recovery; clean distribution installation; MCP retrieval; and persisted-diagram recovery. Publish stable Modwire before locking/rebuilding/retesting and releasing Enclosure.

## Diagram authority and scope updates

Enclosure diagram set: `GkVyr2XEdDAWxCdSJaLu4X`. See [diagram exports and provenance](docs/planning/diagrams/README.md).
These are planning proposals, not accepted implementation contracts. Their original M/E ordering predates the user's local-merge/transfer/Projects decision; current issue dependencies supersede it. Notes now capture CLI inclusion, Wireup-only services and architecture configuration/health gates. Update the diagrams from Enclosure MCP before implementing changed structural contracts.

## Before leaving this workspace

Record the last completed issue/commit, actual tests and map/health receipts, changed configuration and remaining blockers. Keep GitHub issues and Enclosure guidance aligned. Do not claim a successful merge or healthy architecture based on an empty bootstrap tree.
