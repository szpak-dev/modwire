# Workspace handoff — 2026-09-05

## Start here

Open `~/Projects/modwire` in VS Code. Its `origin` is `https://github.com/modwire/modwire.git`.
The user chose a fresh repository; all three source repositories remain intact.

**Current work:** issue #2 is CLOSED at local commit `dd2a2593a7033de8013ed7fca6721fd68eee5eb0`. Issue #3 is the only active issue, on local branch `issue-3-local-consolidation`; implementation is uncommitted and unpushed. The original repositories are untouched. The merge is NOT complete. Follow issues one at a time; do not start #4 until #3 is complete.
Do not restart a broad strategy or portfolio discussion. Do not make caching, organization transfer or Projects setup prerequisites for the local merge.

## Latest checkpoint — testing guidance retrieval diagnosis

This checkpoint supersedes the older implementation notes below. Issue #3 remains active, local and uncommitted; the consolidation is not complete.

The latest completed implementation verification ran `uv run modwire report --language python --summary` in host mode and exited **0**, with `Architecture checks passed.` Receipt: `.dev/modwire-report-summary.txt`. Coverage verification found 207 retained Python source files: architecture 91, CLI 47, extraction 22, shared 46, plus the root executable entrypoint. Every retained source has tags and exactly one shape realm; no files are unclassified. Receipt: `.dev/architecture-coverage.json`. Twelve direct boundary cases passed. Python parser output matched the pinned implementation on 209 source files; all 11 TypeScript/PHP assets matched SHA-256 hashes (`.dev/parser-preservation-latest.json`). Ruff passed; strict Pyright still reports one upstream pydantic-yaml unknown annotation. These checks predate this read-only Enclosure diagnosis.

User-approved configuration changes: explicitly exclude tests/tooling/build artifacts, the empty root package marker and generated version file from the source report. Preserve public contracts with narrow entrypoint, shared-model nullability/default-argument and startup configuration exceptions. Shared has no facade; shared services are directly injectable. CLI/extraction now coordinate through facades; SourceReader is owned by CLI, and extraction consumes supplied data. InitializationApplication coordinates ResourcesApplication. Glob matching is now a shared service, used for scan exclusions, map tags and shape realms. Legacy allow-list exceptions to broad disallow rules remain supported; the intermediate disallow-precedence change was reverted to preserve the existing documented contract.

The user now explicitly authorizes **rewriting tests**, superseding the earlier instruction to leave tests alone. Requirements: read canonical Enclosure testing records first; class-based tests split into packages; balanced shared/context/module base classes; explicit public API imports enforced by boundary rules; Wireup implementation details must not leak to consumers, including consumers using Wireup themselves. No tests have been rewritten since this instruction. Work was paused when the user emphasized the testing records are crucial.

Read-only diagnosis established why MCP retrieval fails:

- `search_records` with broad and focused testing queries returns `presentation_incomplete`; record/category listing does too. This is not an empty-search result.
- The running `enclosure-mcp` container (`9orky/enclosure:latest`) is healthy. Its logs show the underlying `/api/records/search-results` calls returning HTTP 200.
- Inspected the running image's package resources: template families are only `core`, `projects`, `shared`. The `records/search_records.md.jinja` and `.json.jinja` pair is absent. Local Enclosure source likewise has no records templates.
- `PackagePresentationTemplateRepository.find()` raises `PresentationTemplateNotFound` for an operation without a template pair; `PresentationService.present()` catches it and emits the generic incomplete receipt. The exception is not logged there. This is missing MCP presentation implementation, tracked by open Enclosure #152, rather than a failed search backend or a limit/query issue.
- Read-only REST search on the same local Enclosure server succeeded and recovered actual record references. Receipt: `.dev/enclosure-testing-search-rest.json`. Relevant records: `AxTPtEU9S9mt54z6yjEAi2` — “The Fortress Siege & the Meticulous Auntie”; `tzMYbAN4rHxGYTEji6yRqF` — “Behavioral verification”; `gEcPX6tnLPhirrM4aBXMB2` — “Sirenity verification”.
- Direct MCP `get_record` for the first two IDs confirmed their titles but still omitted their content with `presentation_incomplete`. Full guidance content has not yet been read. REST discovery is a documented diagnostic workaround, not successful MCP retrieval or management acceptance.
- The first workspace-context call for the Enclosure checkout was made for this read-only diagnosis and returned `presentation_budget_exceeded`, a separate presentation issue. No Enclosure source, records, runtime configuration, container image or database was changed.

Next: recover and read the canonical testing record contents, then resume the public API/test hierarchy work within issue #3. Enclosure MCP presentation and project-registration/management verification remain acceptance blockers. Do not move to #4 or claim the merge complete.

## Active implementation instructions and state

Latest user steering supersedes the historical mechanical-only plan below:

- Architecture, CLI and extraction use named injectable `facade.py` services. Context facades coordinate with other context facades. Module `application.py` services coordinate within the same context; module services are private. **Shared is the explicit user exception: it has no facade and exposes injectable shared services to every context/module.** Named facades exist; remaining implementation violations are still being resolved. Do not weaken the architecture configuration or exclude violating implementation to obtain a passing report.
- Use glob tags and proper exclusions for contexts/modules, not enumerated context/module names. `.modwire/architecture.yaml` has seven generic role tags plus the explicit shared exception tag. Realm-specific rules allow facade coordination, application coordination within a context, model exchange and direct shared-service injection. Shape constraints and all four flow analyzers remain enabled. This is a working configuration with real failing reports, NOT accepted healthy configuration.
- The previous instruction to leave tests unchanged has been superseded by the latest testing rewrite request above. The rewrite is paused pending canonical guidance retrieval; historical test receipts are not current success.
- The user deleted the invented public root `create_runtime` helper and rejected local dependency type stubs. Keep `src/modwire/__init__.py` empty. `typings/` and `stubPath` are removed; do not recreate them or test-facing runtime wrappers. CLI startup currently calls Wireup directly. The interim `RuntimeScope`/`RuntimeFactory` abstractions were deleted too. Tests/conftest and verification/docs scripts still reference the removed helper; they intentionally await the later verification phase.
- Only CLI performs filesystem/process I/O. Architecture receives typed `ArchitectureConfig` objects. Extraction's Python parser accepts source text; extraction orchestration currently uses an abstract `SourceReader` implemented by CLI. This boundary still needs alignment with the newly specified facade hierarchy.
- Source imports are module-level and explicit, with no wildcard imports, postponed-annotation future imports, `Protocol`, staticmethods or classmethods. Comments are restricted to public API documentation. Frozen dataclasses represent injectable services with typed fields; DTOs inherit the one shared Pydantic `ValueModel`. Ordinary values may be constructed directly; services must be discovered/constructed/injected by Wireup.
- All local caches, dumps and build outputs are in `.dev/`. Add automatic formatting as `make format`, and eventually `make ci` as the central complete gate, with CI/release workflows matching the pinned package repos. These Makefile/workflow tasks remain unfinished.

Current source structure is `src/modwire/{architecture,cli,extraction,shared}` with the requested module names. Legacy layers/modules/projects applications were retired. Native TypeScript/PHP helpers are preserved byte-for-byte in `cli/resources/extractors/`; Python syntax parsing stays in `extraction/extractors/services/`. The user initially objected to moving native helpers, then accepted that filesystem/process responsibilities can belong to CLI. No helper files were deleted. Source inventories in `source-imports.json` still describe an earlier layout and need reconciliation; do not present them as a current complete mapping.

Recent implementation corrections: runtime wiring removed from shared; resource asset DTOs moved from initialization to resources; Console injected into each renderer rather than passed through a DTO; fake shape union aliases removed in favor of real Pydantic base types; generic source-item results share a typed base; an injectable glob matcher owned by architecture/map now handles `*`, `**`, `?`, and character classes for both map and shape matching. The original tag matcher only supported entire-segment `*`. Direct checks confirmed context/module captures and exclusions.

Historical verification before the user's latest source changes:

- 45 tests passed on Python 3.12. These include the migrated 41 baseline tests plus filesystem/import/service checks. Do not update them now or claim they pass against the current root API.
- Direct comparison against pinned extraction/architecture implementations matched code maps, dependency graphs, all report contents and catalogs for Python/TypeScript/PHP fixtures. Only documented report model module paths were normalized (`report-model-migration.json`). Python parser output matched 200 then-current Python source files. All 11 native TypeScript/PHP helper files matched pinned SHA-256 hashes. Raw receipts are in `.dev/baseline-parity.json` and `.dev/parser-corpus.json`.
- Wheel and sdist built and passed Twine; the wheel installed in an isolated Python 3.14 environment with a working CLI. This predates the latest facade work and is not final package acceptance.
- Ruff passed. Strict full-package Pyright reached one error from pydantic-yaml's unannotated `**json_kwargs`; the user rejected the stub workaround. Retain the failure until addressed appropriately; do not add ignores or stubs to fake green.
- Verified original extraction filesystem behavior directly with `git show 71808b1a924e1c496ddf19914ab3a577fe946228`: `ModwireExtraction` resolved roots, `SourceExtractor` checked/walked directories and ran subprocesses, and the Python helper read files. The pinned original was NOT filesystem agnostic end-to-end.

Latest actual production command: host-mode `UV_CACHE_DIR=$PWD/.dev/cache/uv PYTHONPYCACHEPREFIX=$PWD/.dev/cache/pycache uv run modwire report --language python --summary`. It executed after removing SharedFacade and produced a nonempty real map covering architecture/extraction/CLI/shared, but exited **1** with remaining module-boundary and strict shape violations. Latest output: `.dev/modwire-report-summary.txt`; the earlier full report is `.dev/modwire-report.txt`. The latest summary reports no cycle/reentry violations. No successful health is claimed.

Latest implementation and direct verification:

- Fixed ModuleBoundaryAnalyzer evaluating overlapping context/module realms as a union: each realm now checks its own module identity. A shared context match cannot bypass module rules. Explicit disallow wins over matching allow rules. BoundaryRule has an optional realm selector; invalid realm references are rejected by configuration validation. Missing classification on one end no longer silently permits an edge.
- Moved map reporting into report/services/MapReportCollector and report/models; MapApplication now exposes map loading. ReportApplication injects MapApplication. Moved PathMatcher/GlobPathMatcher to architecture/map. The single Pydantic ValueModel is now shared/values/models/value_model.py.
- MapApplication and BoundariesApplication obtain typed boundary configuration from ConfigApplication and pass values to their private services. Those services no longer inject ConfigApplication across module boundaries.
- SharedFacade was explicitly rejected by the user and deleted. Do not recreate it. Consumers may inject shared services directly.
- Twelve direct cases using auto-discovered Wireup services passed, including same-module access, denied private cross-module access, permitted same-context applications, denied cross-context applications, facade coordination and direct shared-service access. Scratch check and receipt: `.dev/check_boundary_enforcement.py`, `.dev/boundary-enforcement.json`. No tracked tests were changed or run.
- Ruff source checks/format passed. Strict Pyright still exits 1 with the single upstream pydantic-yaml unknown **json_kwargs annotation, now reported at shared/values/models/value_model.py. No stub or suppression added.
- Remaining source boundary violations include CLI startup reaching PipelineApplication, InitializationService reaching ResourcesApplication, BatchSourceReader reaching extraction internals and PythonParserCommand reaching PythonParser across contexts. Tests/scripts/root files remain reported as unclassified; they were not excluded to manufacture success. Strict shape violations include optional arguments/properties and CLI startup's top-level function.
- Enclosure rechecked after these structural/rule changes: find_project_by_root remains 404; get_diagram_set remains presentation_incomplete without content/continuations. Health is unrun because registration/guidance is still blocked.

Enclosure remains unregistered (find-by-root 404). Discovery succeeded for Python/uv. Canonical diagram set retrieval remains `presentation_incomplete` with no usable content/continuations. No canonical diagrams or project registration were mutated. Do not invent scaffolding/record IDs or permissive rules. Registration, usable guidance/diagrams and Enclosure health remain acceptance blockers.

Next: finish the remaining CLI/extraction and private-module coordination violations without changing parser behavior; re-run `uv run modwire report --language python --summary`. Named facades and independent realm enforcement are implemented, with shared explicitly exempt from facade access. Preserve strict rules and report failures. Continue #3; do not move to #4, push, publish, transfer or request acceptance yet.

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
