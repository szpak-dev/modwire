# Language support and limits

Modwire applies one architecture vocabulary to one language source set per report.
The common model does not mean that every parser emits every fact with identical
completeness. This page states the runtime contract and the capability differences.

## Runtime and source support

| Language | Registered extractor descriptor | Source extensions | Required runtime | Repository CI coverage |
| --- | --- | --- | --- | --- |
| Python | [modwire.python.ast](../../src/modwire/extraction/extractors/python/extractor.py) | `.py` | Python 3.12 or newer | [Workflow Python matrix](../../.github/workflows/ci.yml) and [extractor runtime pin](../../language-capabilities/contracts/python.yaml) |
| TypeScript | [modwire.typescript.ts-morph](../../src/modwire/extraction/extractors/typescript/extractor.py) | `.ts`, `.tsx`, `.js`, `.jsx` | Node.js 20 or 22 and newer | [Matrix runtime pin](../../language-capabilities/contracts/typescript.yaml) |
| PHP | [modwire.php.php-parser](../../src/modwire/extraction/extractors/php/extractor.py) | `.php` | PHP 8.1 or newer | [Matrix runtime pin](../../language-capabilities/contracts/php.yaml) |
| Java | [modwire.java.javaparser](../../src/modwire/extraction/extractors/java/extractor.py) | `.java` | Java 17 or newer | [Matrix runtime pin](../../language-capabilities/contracts/java.yaml) |
| Ruby | [modwire.ruby.prism](../../src/modwire/extraction/extractors/ruby/extractor.py) | `.rb` | Ruby 4.0.x with Prism 1.9.x | [Matrix runtime and Prism pins](../../language-capabilities/contracts/ruby.yaml) |

The linked descriptors own each extractor's identity and structural version.
Both values accompany every public CodeMap in `producer.extractor`.

Both CI jobs obtain exact external runtime and package versions from the root
capability index through the runtime-contract export. The package job selects
Python versions from its workflow matrix; the extractor job uses the Python pin.

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

The root index also selects the shared
[scenario catalog](../../language-capabilities/scenarios/catalog.yaml). Its typed
documents assemble expected public `CodeMap` observations for the reference shop,
capability fixtures, and implementation-manifest inputs. Each language binds every
scenario to its authored source files through explicit mappings. Language variants
preserve differences in observed facts. Source observations live in separate files;
shared producer metadata is defined once in the catalog.

Native scenario bindings compare complete source observations and dependency evidence,
including ordered parameter counts, names, kinds, defaults, and recursive types.
The common reference compares mapped classes and callables with normalized dependency
topology. It omits unmapped methods and language-specific properties, signatures,
functions, values, calls, annotations, imports, and source spans; it normalizes types,
paths, hashes, and metadata, and collapses equivalent topology edges. Capability and
relationship selectors must agree with the catalog before extraction runs. Missing
bindings, unbound expected facts, and unreferenced data files are rejected. The source
fixtures remain authored language programs; the catalog defines their expected public
observations.

Duplicate object fields are rejected in both YAML contracts and JSON source observations.

The index declares complete fixture collections and their non-source resources.
Every fixture source belongs to exactly one scenario binding; extra files and empty
directories fail inventory validation. Native dependency comparisons account for every
raw edge; both comparison modes reject endpoints outside the owned sources.
Manifest parameter selectors read
their expected name, kind, and default state from the same canonical source facts.
Every binding checks the original producer's complete capability and relationship
coverage against its language contract and its extractor descriptor against the
published registry before normalization. Raw artifact paths must agree with their
source identities. Reference parameter
aliases derive their canonical callable owner from the callable mappings. Projection
rejects inconsistent graph node identities and constructs a typed result directly.
Scenario bindings contain only canonical fact references. Their exact values include
absence and unsupported states in the public model; unused scenario evidence labels
and repeated reference selections are not stored. Each atomic capability or
relationship claim has one scenario owner and a valid evidence role.

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
