# Reporting Bugs

Use the GitHub `Bug report` issue form when Modwire behaves incorrectly.

## Good Bug Reports Include

- a short summary of what went wrong
- the affected area, such as architecture mapping, dependency graph reporting,
  shape policy, callable reports, or unused exports
- the smallest source snippet or fixture that reproduces the problem
- the actual output, traceback, graph edges, or violations
- the expected output
- Modwire, modwire-extraction, Python, and operating-system versions where relevant

## Examples of Bugs

- graph edges are missing, duplicated, or pointed at the wrong node
- an architecture policy returns the wrong violation
- shape, callable, or unused-export reports omit or misclassify source metadata
- package installation or distribution metadata is broken

Open a bug report at:

https://github.com/modwire/modwire/issues/new?template=bug_report.yml
