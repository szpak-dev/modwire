# Recorded evidence

Modwire keeps evidence revision-scoped. The records below answer two different
questions: whether complete source roots were extracted, and whether directory
pruning reduced work in one controlled fixture. They do not support a general
performance claim.

## Production-project extraction

On 2026-09-21, revision
`619f47c3caa8a86cfa9b7e0c1583f85120bc9aea` ran
`ModwireApplication.generate_map` once over nine pinned production source roots.
All 8,601 discovered files were built into 8,601 modules. No excluded patterns were
used.

| Language/project | Pinned source root | Files and modules built | Recorded seconds |
| --- | --- | ---: | ---: |
| Python / transformers | `src/transformers` | 2,823 | 130.629 |
| Python / django | `django` | 908 | 10.051 |
| Python / ansible | `lib/ansible` | 583 | 6.492 |
| TypeScript / VS Code | `src/vs/editor` | 858 | 16.059 |
| TypeScript / TypeScript | `src` | 709 | 11.238 |
| TypeScript / Angular | `packages/core/src` | 409 | 2.987 |
| PHP / Laravel | `src` | 1,644 | 10.267 |
| PHP / Symfony Console | `src/Symfony/Component/Console` | 359 | 1.920 |
| PHP / Composer | `src` | 308 | 2.257 |

The recorded total was 191.9 seconds. Because this was one repetition and the
record does not identify its environment, it is extraction-completeness evidence,
not a benchmark or a portable timing promise. The authoritative inputs and values
are in the [production extraction record](../../tests/extraction/big_projects/results.json)
and its [pinned project manifest](../../tests/extraction/big_projects/projects.json).

## Controlled traversal benchmark

The 2026-09-21 traversal record compares baseline revision
`a201fc0054d49e4206c6ef81b9c3c9d231f511d4` with pruned revision
`619f47c3caa8a86cfa9b7e0c1583f85120bc9aea` on Darwin 25.5.0 arm64 with
Python 3.12.11.

The fixture contained 100 included Python files and 100 excluded directories with
100,000 excluded Python files. Fixture creation was outside the timed operation.
Both revisions extracted the same 100 included files over five repetitions.

| Revision behavior | Median seconds | Observed excluded files | Pruned directories |
| --- | ---: | ---: | ---: |
| Recursive baseline | 0.995345 | 100,000 | not recorded |
| Directory pruning | 0.374147 | 0 | 1 |

For this fixture, the recorded median speedup was 2.66x and the reduction was
62.4%. This result measures native `ModwireApplication.generate_map` traversal only;
it is not Docker, Enclosure, service-latency, or whole-project performance evidence.
See the [complete benchmark record](../../tests/extraction/scan_benchmark/results.json)
for the runs, method, and interpretation.

## Reproduce the operations

Production-project extraction clones the pinned public revisions and can consume
substantial time and network capacity:

```console
make big-projects BIG_PROJECT_ARGS="--repeat 1"
```

The controlled benchmark runner is available through `make scan-benchmark` after a
fixture has been prepared with `make scan-benchmark-fixture`. Compare results only
when the input fixture, public operation, repetitions, and environment are recorded
together.
