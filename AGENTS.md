Read `HANDOFF.md` and the [current epic](https://github.com/modwire/modwire/issues/1) before starting work.

**User acceptance gate:** finish the local extraction + architecture + CLI consolidation, its verification, and real Enclosure project management, then stop and present the implementation for the user's explicit acceptance. Transfer, publication, Projects setup and later delivery work require a subsequent instruction after acceptance; the epic's longer roadmap is not authorization to continue automatically.

**Enclosure MCP is the single source of truth** for project operating guidance, architecture and diagrams. Local guidance and `docs/planning/diagrams/` are bootstrap material or synchronized exports, not independent authorities. Preserve the existing canonical diagram IDs and verify source, snapshots, validation and revisions through MCP. Record unavailable/incomplete retrieval as a blocker; do not substitute an export or a successful receipt for a verified MCP read.

Call Enclosure `get_workspace_context(root, task)` once at the first task in this workspace. Bootstrap found this workspace unregistered. If it is still unregistered, use this handoff and the linked issue until the real source/configuration is ready for registration; never create empty or permissive rules to manufacture healthy status.

- Consolidate extraction, architecture and CLI locally first. Preserve the source repositories and immutable revision provenance.
- Follow GitHub issues sequentially, with one implementation issue active at a time; update issue wording/blockers when findings require it. Implement on local issue branches, preserving unrelated changes. Keep `main` protected and do not push or merge the local implementation before user acceptance.
- Keep the initial merge mechanical and behavior-preserving. Service wiring is mandatory: Wireup constructs every service and resolves every collaborator. No manual service instances or fallback construction paths. Ordinary immutable data/value construction is distinct from service construction.
- Bring legacy `.modwire` shape/boundary configurations and relevant guidance with the source. Remap source roots, patterns, tags and realms deliberately; preserve constraints and explain conflicts. Never weaken rules or exclude source simply to pass.
- Verify the expected nonempty architecture map, all three components' coverage, package checks and Enclosure health before calling the merge complete. Check health after structural, public API, DI or architecture-rule changes.
- Keep caching/performance work separate from the initial merge. Keep `modwire-hex` separate.
- Read the actual GitHub issue and its blockers. The current issue graph supersedes provisional M/E ordering in the earlier diagrams, subject to the user's local acceptance gate. Reconcile issue ordering into Enclosure guidance and diagrams; do not maintain competing project contracts.
- Treat this consolidation as an evaluation of agent use of Enclosure on a new, demanding project. Record bootstrap/context retrieval, guidance and diagram discovery, configuration migration, registration/binding, health checks, and failures or workarounds. Registration alone is not proof that project management through MCP works.
- After an ambiguous mutation failure, verify state before retrying. Preserve unrelated changes and report failed or unrun checks.
- Run GitHub and environment-sensitive CLI/uv commands in host-equivalent mode.
- Update the handoff with completed work, exact verification, remaining blockers and the next issue before leaving the workspace.
