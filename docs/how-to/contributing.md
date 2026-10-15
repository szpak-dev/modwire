# Contributing

Install the locked development environment and run the repository checks before
proposing a change:

```console
uv sync --all-groups --locked
make host-check
```

Documentation changes must also keep `make docs-check` warning-free. Regenerate the
documentation dependency lock with `make docs-lock` after changing
`docs/requirements.in`.
