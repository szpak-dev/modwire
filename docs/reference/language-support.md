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

| Capability | Python | TypeScript | PHP | Java | Ruby |
| --- | --- | --- | --- | --- | --- |
| sources | Supported | Supported | Supported | Supported | Supported |
| symbols | Supported | Supported | Supported | Supported | Partial |
| callables | Supported | Supported | Supported | Supported | Partial |
| calls | Supported | Supported | Supported | Supported | Partial |
| parameters | Supported | Supported | Supported | Supported | Partial |
| annotations | Partial | Partial | Partial | Partial | Unsupported |
| modifiers | Partial | Partial | Partial | Partial | Partial |
| attributes | Supported | Supported | Supported | Supported | Unsupported |
| assigned_values | Supported | Unsupported | Unsupported | Unsupported | Unsupported |
| inheritance | Supported | Supported | Supported | Supported | Supported |
| namespaces | Unsupported | Unsupported | Unsupported | Supported | Partial |
| declaration_kinds | Supported | Supported | Supported | Supported | Supported |
| composition | Unsupported | Partial | Partial | Partial | Partial |
| dependencies | Supported | Supported | Supported | Partial | Partial |
| spans | Partial | Partial | Partial | Partial | Partial |

The exact explanations travel with every public `CodeMap` in
`code_map.producer.capabilities`. In particular:

- annotations are declared types plus selected decorators or attributes; arbitrary
  annotations are not evaluated;
- modifiers normalize visibility and member or callable kind rather than preserving
  every language keyword;
- Python assigned values distinguish calls, references, literals, unresolved
  expressions, and unassigned declarations; TypeScript, PHP, Java, and Ruby do not yet
  extract assigned-value evidence;
- Java publishes authored package declarations and Ruby publishes authored module
  declarations; namespace extraction remains unsupported for Python, TypeScript, and PHP;
- declaration kinds distinguish the exact shared class, abstract-class, interface,
  function, callable, and value categories currently emitted by each extractor;
- inheritance records authored class extension; composition records implementation,
  trait, include, prepend, and singleton-extension evidence when the language adapter
  can distinguish those forms. Python base expressions remain inheritance evidence, and
  no distinct Python composition relation is classified;
- callable spans are exact, while other symbols expose line counts.

## Relationship-capability coverage

Relationship coverage separates semantic understanding from inventory completeness.
`Supported` inventory means an empty result is trustworthy inside the stated static
family boundary. Semantic support can remain partial when Modwire preserves every
authored fact but cannot resolve its complete runtime meaning.

| Family | Required fact evidence | Python | TypeScript | PHP | Java | Ruby |
| --- | --- | --- | --- | --- | --- | --- |
| declaration | symbols, inheritance, declaration kinds, composition | Partial / Supported | Partial / Supported | Partial / Partial | Partial / Partial | Partial / Partial |
| member | symbols, callables, calls, parameters, annotations, modifiers, attributes, assigned values, declaration kinds | Partial / Supported | Partial / Partial | Partial / Partial | Partial / Partial | Partial / Partial |
| dependency | sources, dependencies | Supported / Supported | Supported / Supported | Supported / Supported | Partial / Partial | Partial / Partial |

Each language cell is `semantics / inventory`. The exact statuses, evidence
requirements, and explanations travel in
`code_map.producer.relationship_capabilities`. Every extractor classifies every
family through the same shared contract.

The inventory boundary contains authored declaration relations, static member and
callable references, assigned values when supported, and authored source
dependencies. It does not contain runtime calls, reflection, dynamic loading,
dependency-injection wiring, generated behavior, or framework conventions. An empty
relationship family is not evidence of absence unless its inventory status is
`Supported`.

Java exact imports resolve when the target declaration is present in the same source
set. Wildcard imports, implicit same-package dependencies, classpath or framework
inference, generated code, and annotation-processor effects remain unresolved. Local
calls resolve only when one same-file target is unambiguous; overloads, arbitrary
receivers, inherited calls, and cross-file calls remain unresolved. Sealed declarations
retain their underlying class or interface kind, but `permits` relations are not yet
published.

Ruby publishes statically named classes, modules, constants, instance methods,
singleton methods, constructors, parameters, superclass clauses, and literal
`include`, `prepend`, and `extend` sites. Reopened declarations remain separate
authored sites rather than being merged. Literal `require` and `require_relative`
loads are normalized; dynamic loading, refinements, metaprogramming, unresolved
constant semantics, load-path inference, Rails conventions, and Zeitwerk autoloading
are not inferred. Method and constant aliases are not emitted as new declarations.
Same-file calls resolve only when one static target is unambiguous.

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
