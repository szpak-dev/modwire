# Workspace handoff — 2026-09-05

## Start here

Open `~/Projects/modwire` in VS Code. Its `origin` is `https://github.com/modwire/modwire.git`.
The user chose a fresh repository; all three source repositories remain intact.

**Current work:** [issue #2](https://github.com/modwire/modwire/issues/2) preflight is documented in [preflight.md](docs/planning/preflight.md) on local branch `issue-2-preflight`; record its completion before starting [issue #3's mechanical local merge](https://github.com/modwire/modwire/issues/3) on a separate local branch. Follow issues one at a time; the user authorizes correcting their wording and blockers when necessary.
Do not restart a broad strategy or portfolio discussion. Do not make caching, organization transfer or Projects setup prerequisites for the local merge.

## User clarification — local acceptance and Enclosure authority

The user clarified on 2026-09-05 that the immediate destination is a **reviewable local implementation**, merging extraction, architecture and CLI into one package and managing that project through Enclosure MCP. **Stop there for the user's explicit acceptance.** The later epic roadmap does not authorize automatic transfer, publication, organization Projects setup, performance work or Enclosure runtime upgrades. Subsequent work needs a further instruction after acceptance.

Enclosure MCP is the **single source of truth** for project operating guidance, architecture and diagrams. The three diagrams exported under `docs/planning/diagrams/` must remain available in Enclosure under their existing IDs. Update canonical diagrams through MCP, then refresh the local exports and provenance. GitHub supplies the actual issue/blocker graph; reconcile it into Enclosure, subject to the user's acceptance gate. Local files are bootstrap context or exports, not a competing authority.

The acceptance package must include:

- The local merge diff and immutable source/package mapping, preserving behavior and Wireup-only service construction.
- Package, CLI, clean distribution installation and pipx verification, plus a nonempty architecture map covering all three components with preserved effective constraints and passing Enclosure health.
- A real workspace registration/binding and usable operating guidance through Enclosure MCP; registration by itself is insufficient.
- The canonical planning diagrams, with retrievable source/snapshots, validation and revision evidence matching refreshed docs exports. Clearly distinguish proposals from accepted implementation contracts.
- An agent workflow record showing how Enclosure was used from bootstrap through demanding changes: context/guidance retrieval, diagram discovery and updates, configuration migration, registration, checks, failures and recovery. Successful receipts without usable content do not pass retrieval checks.
- Exact completed and failed/unrun checks, remaining blockers, and the concrete local implementation presented for acceptance. Never describe an incomplete gate as accepted.

## Latest instruction review — 2026-09-05

### Subsequent #2 preflight and branch protection

The user explicitly directed implementation to start, issues to be followed one at a time (editable when necessary), and work to use local branches with protected `main`. Created `issue-2-preflight` preserving the prior instruction changes. [preflight.md](docs/planning/preflight.md) records the exact mapping, Python >=3.12, local version 8.0.0.dev0, preserved import packages/resources, unified Wireup boundary and configuration migration requirements.

Verified all three canonical remote tag commits with host-mode `git ls-remote`, including peeled annotated tags; they match `baselines.json`. Inspected pinned Git archives: 116 Python source files, 15 test modules, helper/template resources and legacy configuration. `git diff --check` passed. Package tests are not part of this documentation preflight and have not run. No source repositories were changed.

Applied and read back GitHub `main` protection: one approving PR review, stale approvals dismissed, resolved conversations and linear history required, admin enforcement enabled, force pushes and deletion disabled. No required status checks were invented: the repository currently has no Actions workflows. Add real verified CI check names when those workflows are introduced. No implementation was pushed.

The earlier review below is historical; its no-source-merge and MCP retrieval findings remain applicable until #3 supplies newer evidence.

Read this handoff, local instructions, diagram exports/provenance, live epic #1, preflight #2, merge #3 and Enclosure diagram presentation issue #151. The live merge issue is blocked by #2. Source consolidation has not started; the next implementation issue remains #2, followed by #3.

Actual MCP verification:

- `get_workspace_context(root, task)` was called once for this task and returned `status: error`, HTTP 404, `Resource not found`. The workspace remains unregistered; no placeholder configuration was created.
- `get_diagram_set` identified set `GkVyr2XEdDAWxCdSJaLu4X` but returned `status: incomplete`, `reason: presentation_incomplete`, with no follow-ups.
- Individual `get_diagram` calls identified all three exported diagrams at the manifest revisions: `pRWegQjSZXEvfwWEoCxZzq` 19, `HUhdthFrEjBoLtZLtTrn4D` 43 and `PBLeM6dFuqQrawEuKFUGG9` 24. Each returned `status: incomplete`, without source, snapshot, draft/validation state or continuation. IDs/revisions match; content parity is **not reverified**.
- `find_diagram_set_diagrams`, `get_diagram_kind(flowchart)` and a scoped `get_diagram_set_diagram` also returned incomplete presentations without follow-ups. `find_record_categories`, `find_records` and `search_records` did the same, preventing discovery/readback of canonical operating guidance.

These are Enclosure MCP usability blockers, consistent with existing presentation work under [#148](https://github.com/szpak-dev/enclosure/issues/148), [#151](https://github.com/szpak-dev/enclosure/issues/151) and [#152](https://github.com/szpak-dev/enclosure/issues/152). Do not infer an empty collection from an incomplete response. The user's clarified acceptance contract is recorded locally pending reconciliation into canonical Enclosure guidance and diagrams when retrieval is usable; no canonical update or synchronization is claimed. GitHub issues were read, not edited, and still omit this explicit user acceptance checkpoint.

This instruction review changed documentation only. No package tests, build, pipx, architecture map or project health checks were run because the checkout still has no merged source/configuration. The bootstrap verification below is historical, not current MCP retrieval evidence.

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
3. **Wireup constructs every service and resolves all collaborators. No manual service instances or fallback construction paths.** Canonical preflight corrected the bootstrap assumption: only CLI declares Wireup at the pinned releases. Architecture 7.0.0 and Extraction 2.1.1 both have manual composition that must be migrated rather than grandfathered in.
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

Local preflight → merge → CLI/pipx verification and usable Enclosure project management/diagrams/health → **STOP: user acceptance of the local implementation**. The later roadmap, only after acceptance and a subsequent instruction, includes remaining Enclosure impact checks → transfer to `szpak-dev/modwire` → organization Project → management handoff.
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

The full epic completes when consolidation, transfer and management are verified; this is broader than the immediate local acceptance checkpoint. The linked performance and integrated-runtime delivery work is not falsely completed with it.

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
These are planning proposals, not accepted implementation contracts. Their original M/E ordering predates the user's local-merge/transfer/Projects decision; current issue dependencies supersede it, subject to the explicit user acceptance checkpoint above. Exported notes capture CLI inclusion, Wireup-only services and architecture configuration/health gates but still need the new acceptance checkpoint reconciled through MCP. Update the diagrams from Enclosure MCP before implementing changed structural contracts. See the latest instruction review for the current retrieval blocker.

## Before leaving this workspace

Record the last completed issue/commit, actual tests and map/health receipts, changed configuration and remaining blockers. Keep GitHub issues and Enclosure guidance aligned. Do not claim a successful merge or healthy architecture based on an empty bootstrap tree.
