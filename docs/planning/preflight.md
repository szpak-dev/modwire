# Issue #2 — pinned source and package mapping

Verified on 2026-09-05 against the canonical remote tags with `git ls-remote` and local Git objects at the exact peeled commits. Temporary `git archive` exports were used for inspection; sibling working trees and histories were not changed.

| Repository | Tag | Immutable source commit | Python modules in source |
| --- | --- | --- | ---: |
| modwire/modwire-extraction | v2.1.1 | 71808b1a924e1c496ddf19914ab3a577fe946228 | 19 |
| modwire/modwire-architecture | v7.0.0 | c1ed25b1e71c5d800450a50a72906529947268fc | 68 |
| modwire/modwire-cli | v2.0.0 | 67f76cfa63ddfaf6114ca9168939a315bf94948e | 29 |

## Distribution and import mapping

One distribution, `modwire`, will contain the existing import packages unchanged in location and identity:

| Source path | Local destination | Public contract retained |
| --- | --- | --- |
| Extraction `src/modwire_extraction/` | `src/modwire_extraction/` | `ModwireExtraction`, `QueryableCodeMap`, all existing submodule imports and CodeMap/data identities |
| Architecture `src/modwire_architecture/` | `src/modwire_architecture/` | `Modwire`, `ArchitectureConfig`, shared models, report classes and existing submodule imports |
| CLI `src/modwire_cli/` | `src/modwire_cli/` | `modwire_cli.cli:main`, init/report/legacy arguments, output and exit statuses |
| New unified composition entry | `src/modwire/` | Explicit Wireup runtime/composition API for all three components |
| Extraction tests and fixtures | `tests/extraction/` | Public API and parser/identity behavior checks; relative fixture paths retained |
| Architecture tests and fixtures | `tests/architecture/` | Reports, boundaries, shape, models and import migration checks |
| CLI tests and fixtures | `tests/cli/` | Functional init/report and filesystem safety checks; test imports remapped if necessary |
| Component docs and release metadata | `docs/legacy/<component>/` | Original README, license, manifests, guidance and relevant documentation with provenance |

No package source is renamed to a nested `modwire.*` namespace. In particular, there must not be duplicated or compatibility-copy CodeMap/model classes. Dependencies on `modwire-extraction` and `modwire-architecture` are removed from the unified manifest because their modules ship in the same wheel. Installing this candidate should use a clean environment, avoiding overlapping files from the three legacy distributions.

The Python minimum is **3.12**, the existing Architecture and CLI minimum (Extraction alone supported 3.11). The local, unpublished candidate version is **8.0.0.dev0**, explicitly identifying the consolidation and required composition migration beyond Architecture 7. This is not a release approval. Unified package URLs point to `modwire/modwire`; the license remains MIT with original notices preserved. Name ownership and trusted publisher configuration must be verified before any future publication; they are not prerequisites for a local build.

Runtime dependency union: `pydantic>=2.12`, `pydantic-yaml>=1.7`, `rich>=13`, and `wireup>=2.12.0`. A resolved lockfile will capture the actual verification environment. Development tooling retains pytest, build, Ruff, Pyright and Twine as relevant to the inherited checks.

## Resources

Keep all helper files at their current import-relative paths. Extraction's TypeScript directory contains `script.ts`, bundled `script.js`, `build.mjs`, `package.json`, `package-lock.json` and `tsconfig.json`. Its PHP directory contains `script.php`, `script.src.php`, `build.php`, `composer.json` and `composer.lock`. The Python parser script remains a packaged Python module. Preserve Architecture and CLI `py.typed` markers, and every `modwire_cli/resources/init/*` template. Build wheel and sdist with these files; validate resources after clean installation. Node and PHP remain runtime prerequisites for their respective languages; rebuilding helper bundles is separate from using the shipped scripts.

## Composition boundary

All service creation and collaborator resolution will go through one explicit Wireup composition boundary in the unified package. It owns container creation, discovery/registration, lifetimes, runtime value bindings and ordered analyzer/resolver/reporter collections. Service modules declare their dependencies. CLI entry points and supported library runtime entry points resolve their roots from this boundary. No manually built service passed to `instance`, service factory that calls a constructor, or exception/default fallback is allowed. Ordinary configuration, paths, immutable results and value collections are distinct from services.

Canonical inspection corrects the bootstrap handoff: **only CLI declares Wireup at these releases**. Architecture 7.0.0 and Extraction 2.1.1 both require migration. Known service construction sites include:

- Extraction's language loader and queryable-map facade.
- Architecture's `standard_*` composition helpers, `ArchitectureApplication.standard`, map loader/TagMatcher, analyzers, collectors and resolvers.
- CLI's `main = CommandLine()`, `Console()` instance binding, extraction and Architecture facade construction, initialization service and documentation commands.

Preserve parser algorithms, identities, report ordering and observable CLI behavior. Service constructor signatures and composition helpers may change where needed to enforce injection; document the supported runtime API and migrate call sites/tests explicitly. Public data imports and their class identity must remain stable. Compatibility entry points may resolve through Wireup, but cannot keep a second manual composition path. Inventory and verify all remaining constructors during #3 rather than assume decorators alone prove compliance.

## Architecture configuration and guidance

Preserve original configurations as provenance before remapping their effective copies:

- Architecture: `.modwire/boundaries.yaml` and `.modwire/shape.yaml`. Boundary tags currently assume a component-relative root; the module tag, layer patterns, backward-flow, no-cycles and no-reentry checks must be deliberately remapped. Shape allows unlimited class/interface/type counts but zero top-level functions. Existing source/composition conflicts must be reported and resolved, not hidden.
- CLI: `.modwire/architecture.yaml`, `.modwire/INDEX.md`, `.modwire/docs/`, and root `AGENTS.md`. Normalize the combined envelope into the effective shape/boundary documents. Preserve its package shape limits and module-boundaries/no-cycles/no-reentry checks; remap test/script roots when moved.
- Extraction: the pinned tree contains **no `.modwire` files**. Add explicit, meaningful coverage reflecting its source structure; do not exclude it or apply an empty configuration.

The unified architecture root is the repository root. Use distinct component tags/realms and preserved component-specific constraints, with deliberate governance of the new composition boundary. Keep docs/legacy provenance distinct from executable source. Verification must demonstrate source coverage and expected dependencies for all three components, nonempty matches, package architecture checks and Enclosure health. Specific conflicting patterns and inherited violations belong in #3's migration evidence.

Imported guidance remains historical where it conflicts with the user's current instructions: preserve local unrelated changes; Enclosure MCP is SSOT; keep work local and sequential by issue; stop for acceptance after the local implementation and verification. No history rewrite, transfer, publication, performance/caching change, broad redesign or `modwire-hex` merge is included.

## Verification and transition

All three remote tags match `baselines.json`; annotated Extraction/CLI tags were compared using their peeled commit values. Pinned tree inspection verified 116 Python source modules, the resource inventory, current manifests, 15 test modules, and the legacy configuration/guidance paths. No package tests are claimed by this documentation preflight. Canonical Enclosure registration and MCP retrieval remain blocked by [Enclosure #173](https://github.com/szpak-dev/enclosure/issues/173).

Once this mapping is recorded on #2 and that issue is complete, work proceeds to #3 alone. #4's dedicated pipx/CLI acceptance follows #3. The final local acceptance checkpoint requires both, plus usable Enclosure project guidance, canonical diagrams and health evidence.
