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

The Python requirement comes from the Modwire package. The Node.js range comes from
the bundled TypeScript extractor's package metadata. The PHP extractor uses PHP 8.1
syntax; its bundled `nikic/php-parser` library has a lower PHP 7.4 floor, which does
not lower the executable extractor requirement. Node.js and PHP must be available
on `PATH`; Modwire reports an unavailable runtime as a public failure.

## Fact-capability coverage

`Supported` means the extractor declares complete support for the fact family it
publishes. `Partial` means the extractor deliberately publishes only the stated
subset. `Unsupported` means consumers must not infer that fact from an empty result.

| Capability | Python | TypeScript | PHP |
| --- | --- | --- | --- |
| sources | Supported | Supported | Supported |
| symbols | Supported | Supported | Supported |
| callables | Supported | Supported | Supported |
| parameters | Supported | Supported | Supported |
| annotations | Partial | Partial | Partial |
| modifiers | Partial | Partial | Partial |
| attributes | Supported | Supported | Supported |
| assigned_values | Supported | Unsupported | Unsupported |
| inheritance | Supported | Supported | Supported |
| namespaces | Unsupported | Unsupported | Unsupported |
| declaration_kinds | Supported | Supported | Supported |
| composition | Partial | Partial | Partial |
| dependencies | Supported | Supported | Supported |
| spans | Partial | Partial | Partial |

The exact explanations travel with every public `CodeMap` in
`code_map.producer.capabilities`. In particular:

- annotations are declared types plus selected decorators or attributes; arbitrary
  annotations are not evaluated;
- modifiers normalize visibility and member or callable kind rather than preserving
  every language keyword;
- Python assigned values distinguish calls, references, literals, unresolved
  expressions, and unassigned declarations; TypeScript and PHP do not yet extract
  assigned-value evidence;
- namespace extraction is explicitly unsupported until a language extractor publishes
  authored package, namespace, or module declarations;
- declaration kinds distinguish the exact shared class, abstract-class, interface,
  function, callable, and value categories currently emitted by each extractor;
- composition currently records class extension and implementation evidence without
  inferring language- or framework-specific mixin semantics;
- callable spans are exact, while other symbols expose line counts.

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
