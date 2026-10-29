# Language support and limits

Modwire applies one architecture vocabulary to one language source set per report.
The common model does not mean that every parser emits every fact with identical
completeness. This page states the runtime contract and the capability differences.

## Runtime and source support

| Language | Extractor identity | Source extensions | Required runtime | Repository CI coverage |
| --- | --- | --- | --- | --- |
| Python | `modwire.python.ast` version 2 | `.py` | Python 3.12 or newer | Python 3.12, 3.13, and 3.14 |
| TypeScript | `modwire.typescript.ts-morph` version 2 | `.ts`, `.tsx`, `.js`, `.jsx` | Node.js 20 or 22 and newer | Node.js 20 for extractor-resource checks |
| PHP | `modwire.php.php-parser` version 2 | `.php` | PHP 8.1 or newer | Runner-provided PHP; the workflow does not pin a version |
| Java | `modwire.java.javaparser` version 1 | `.java` | Java 17 or newer | Temurin 17 for extractor-resource checks |
| Ruby | `modwire.ruby.prism` version 1 | `.rb` | Ruby 4.0.x with Prism 1.9.x | Ruby 4.0.7 and Prism 1.9.0 |

The Python requirement comes from the Modwire package. The Node.js range comes from
the bundled TypeScript extractor's package metadata. The PHP extractor uses PHP 8.1
syntax; its bundled `nikic/php-parser` library has a lower PHP 7.4 floor, which does
not lower the executable extractor requirement. Node.js and PHP must be available
on `PATH`. The Java extractor uses JavaParser Core in Java 25 syntax mode without
JavaSymbolSolver and runs as a bundled executable JAR. Java must also be available
on `PATH`. The Ruby extractor runs a bundled script against Prism without loading the
analysed application. Ruby and Prism must satisfy their declared version ranges.
Modwire reports an unavailable or incompatible runtime as a public failure.

## Fact-capability coverage

`Supported` means the extractor declares complete support for the fact family it
publishes. `Partial` means the extractor deliberately publishes only the stated
subset. `Unsupported` means consumers must not infer that fact from an empty result.

The executable authority is the repository-root
[`language-capabilities.yaml`](../../language-capabilities.yaml). It owns every
language/capability status, explanation, exact public evidence observation, and
source-backed limitation. Tests load that file directly and require all capability
cells in canonical order, so this page deliberately does not copy the matrix.

The same statuses and explanations travel with every public `CodeMap` in
`code_map.producer.capabilities`.

## Relationship-capability coverage

Relationship coverage separates semantic understanding from inventory completeness.
`Supported` inventory means an empty result is trustworthy inside the stated static
family boundary. Semantic support can remain partial when Modwire preserves every
authored fact but cannot resolve its complete runtime meaning.

The same root
[`language-capabilities.yaml`](../../language-capabilities.yaml) owns every
language/family semantics status, inventory status, explanation, exact public
evidence observation, and limitation. The values travel in
`code_map.producer.relationship_capabilities`.

The inventory boundary contains authored declaration relations, static member and
callable references, assigned values when supported, and authored source
dependencies. It does not contain runtime calls, reflection, dynamic loading,
dependency-injection wiring, generated behavior, or framework conventions. An empty
relationship family is not evidence of absence unless its inventory status is
`Supported`.

## Deliberate boundaries

- A report selects exactly one language. Modwire does not construct cross-language
  dependency edges in one report.
- Modwire checks declared rules against statically extracted facts. It does not
  infer the intended architecture or observe runtime calls.
- Glob tags are explicit project configuration, not framework conventions guessed
  from directory names.
- An implementation manifest records observed facts and provenance. It does not
  certify compliance with an architecture.
- The caller owns installation and lifecycle of required external runtimes.
