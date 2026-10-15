# Command-line interface

## `modwire init`

Create project-local configuration and guidance.

| Option | Default | Meaning |
| --- | --- | --- |
| `--dot-dir` | `.modwire` | Configuration and generated guidance directory. |
| `--force` | off | Replace existing generated assets. |

Without `--force`, existing targets are preserved and missing targets are created.

## `modwire report`

Extract one language and render the configured architecture reports.

| Option | Default | Meaning |
| --- | --- | --- |
| `--language` | required | `python`, `typescript`, or `php`. |
| `--dot-dir` | `.modwire` | Directory containing `architecture.yaml`. |
| `--architecture-root` | `.` | Source root governed by the configuration. |
| `--summary` | off | Omit individual files from the architecture map. |
| `--cache-directory` | `.modwire/cache` | Persistent cache directory. |
| `--cache-namespace` | `default` | Isolated cache namespace. |
| `--cache-max-bytes` | `536870912` | Maximum owned cache size in bytes. |
| `--no-cache` | off | Disable persistent cache reuse for this report. |

Exit status `0` means every configured architecture check passed. Exit status `1`
means a report found violations or the operation failed. Invalid command syntax is
reported by the argument parser with status `2`.

For compatibility, arguments beginning with report options are treated as a report
command. Prefer the explicit `modwire report` form in new automation.

## `modwire cache-clear`

Clear one Modwire-owned cache namespace.

| Option | Default | Meaning |
| --- | --- | --- |
| `--dot-dir` | `.modwire` | Project configuration directory. |
| `--cache-directory` | `.modwire/cache` | Persistent cache directory. |
| `--cache-namespace` | `default` | Namespace to clear. |
| `--cache-max-bytes` | `536870912` | Cache ownership configuration. |
