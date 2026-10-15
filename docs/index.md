# Modwire

**Polyglot architecture checks, one model.**

Modwire extracts Python, PHP, and TypeScript into the same typed, language-neutral
code model. It evaluates each language's source set against explicit architecture
rules.

Three ideas shape the tool:

1. Python, PHP, and TypeScript share one architecture vocabulary.
2. Bounded contexts contain features or modules, which follow explicit layers.
3. Boundary, dependency flow, cycle, re-entry, and shape rules make that convention
   executable.

Modwire does not infer an architecture from naming folklore. Glob patterns map the
source tree to concepts you name, and reports show where the implementation stops
matching them.

Start with [Check a polyglot project](tutorials/check-a-polyglot-project.md). Read
[The Modwire architecture convention](architecture/convention.md) before adapting the generated
configuration. Use the [how-to guides](how-to/index.md) for a specific task and the
[reference](reference/index.md) for exact contracts. The [glossary](reference/glossary.md)
defines Modwire's architecture and runtime vocabulary.
