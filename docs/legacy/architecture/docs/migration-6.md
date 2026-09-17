# Migrating from Modwire to Modwire Architecture

`modwire-architecture` is the successor distribution for architecture analysis.
It is a breaking package-identity migration: GitHub redirects the renamed
repository, but PyPI and Python imports do not provide a compatibility shim.

## Install and import

```bash
python -m pip uninstall modwire
python -m pip install 'modwire-architecture>=6,<7'
```

```python
# Before
from modwire import ArchitectureConfig, Modwire

# After
from modwire_architecture import ArchitectureConfig, Modwire
```

Update any deeper imports by replacing the root namespace
`modwire` with `modwire_architecture`. The package's behavior remains unchanged
by this identity migration: callers do not change logic, configuration,
inputs, outputs, reports, or runtime capabilities.

## Release history

Existing `modwire` PyPI releases and the repository's `v1.0.0` through
`v5.0.0` tags remain historical. The first release of the new distribution is
`modwire-architecture==6.0.0`, published from the preserved repository history
at tag `v6.0.0`.
