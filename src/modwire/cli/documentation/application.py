from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from .services.documentation_generator import DocumentationGenerator


@injectable()
@dataclass(frozen=True)
class DocumentationApplication:
    generator: DocumentationGenerator

    def generate(self, readme: Path, check: bool) -> int:
        if self.generator.update(readme, check):
            return 0
        if check:
            print("Generated documentation is stale. Run `make docs` and commit the result.")
            return 1
        return 0
