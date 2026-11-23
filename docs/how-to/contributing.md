# Contributing

Use the runtimes pinned in [the language contracts](../../language-capabilities.yaml).
For Ruby's rejection test, also install the version in
[`runtime.rejected_versions`](../../language-capabilities/contracts/ruby.yaml) and set
`MODWIRE_TEST_REJECTED_RUBY` to its absolute executable path. Keep the supported
Ruby on `PATH`; CI provisions both versions from that contract.

Install the locked development environment and run the repository checks before
proposing a change:

```console
uv sync --all-groups --locked
make host-check
```

Documentation changes must also keep `make docs-check` warning-free. Regenerate the
documentation dependency lock with `make docs-lock` after changing
`docs/requirements.in`.
