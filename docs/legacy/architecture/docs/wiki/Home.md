# Modwire Wiki

Modwire Architecture provides typed architecture analysis over code maps produced
by `modwire-extraction`. Presentation and hypermedia integrations belong to
sibling packages.

## Start Here

- README describes the package boundaries, model taxonomy, and ecosystem
  projects.
- [Reporting bugs](Reporting-bugs.md)
- [Requesting features](Requesting-features.md)
- [Development checks](Development-checks.md)

## Useful Project Links

- Repository: https://github.com/modwire/modwire-architecture
- Issues: https://github.com/modwire/modwire-architecture/issues
- Bug report form: https://github.com/modwire/modwire-architecture/issues/new?template=bug_report.yml
- Feature request form: https://github.com/modwire/modwire-architecture/issues/new?template=feature_request.yml

## Code Maps

Pass an already extracted `QueryableCodeMap` and an explicit
`ArchitectureConfig` to `Modwire().architecture(config).report(code_map)` or
`ArchitectureApplication.standard(config).report(code_map)`. Callers own path
discovery, configuration loading, generated files, and terminal commands.
