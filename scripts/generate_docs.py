from pathlib import Path

from modwire import create_runtime
from modwire.cli.documentation.application import DocumentationApplication

if __name__ == "__main__":
    with create_runtime(Path.cwd()) as runtime:
        raise SystemExit(runtime.get(DocumentationApplication).run())
