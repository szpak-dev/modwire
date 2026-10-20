# One model across four languages

Python, PHP, TypeScript, and Java disagree about syntax, runtime, and type systems. An
architecture rule should not need three unrelated meanings of “module dependency”
because of that.

Modwire places language-specific work at the extraction boundary. Each extractor
observes source files and publishes the same typed concepts: files, declarations,
members, imports, calls, assigned values, and dependency relations. Architecture
analysis consumes that shared code model rather than parser output.

## What the common model enables

One architecture configuration can name contexts, features, modules, and layers for
all supported languages. The CLI still analyses one language at a time, which keeps
source inventories and extractor provenance explicit. The resulting reports use the
same rule identifiers and structural vocabulary.

The model also supports implementation manifests. A manifest serializes observed
facts with their source and extractor provenance in deterministic canonical JSON.
It can tell another system what Modwire observed. It cannot decide what the
architecture was intended to be.

The producer also declares relationship coverage through one language-neutral
contract. Declaration, member, and dependency families each state their required
fact evidence, semantic support, and inventory support. Complete inventory makes an
empty family trustworthy only inside its documented static boundary; it does not
turn runtime or framework inference into source evidence.

## Where language differences remain

A common model does not pretend the languages are identical. Extractor capability
coverage records which fact families a language can publish, while relationship
coverage independently records semantic and inventory support. Every extractor uses
the same contracts and declares its own truthful statuses. Unresolved or unsupported
syntax remains explicit rather than being guessed into a convenient shape.

External runtimes remain operational dependencies. Python extraction runs with
Modwire, while TypeScript needs Node.js, PHP needs PHP, and Java needs a Java 17 or
newer runtime. A missing runtime is an
extractor failure, not an empty code map.

This separation keeps architecture rules portable without hiding the evidence they
depend on.
