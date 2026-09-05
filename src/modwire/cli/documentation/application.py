import argparse
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from modwire.cli.documentation.services.documentation_generator import DocumentationGenerator


@injectable()
@dataclass(frozen=True)
class DocumentationApplication:
    """Update or validate the generated README class reference."""

    generator: DocumentationGenerator

    def run(self) -> int:
        """Run the documentation command from the process argument vector."""
        parser = argparse.ArgumentParser(description="Generate README class reference documentation.")
        parser.add_argument("--check", action="store_true", help="Fail instead of updating stale documentation.")
        arguments = parser.parse_args()
        readme = Path.cwd() / "README.md"
        if self.generator.update(readme, arguments.check):
            return 0
        if arguments.check:
            print("Generated documentation is stale. Run `make docs` and commit the result.")
            return 1
        return 0
