import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from modwire.cli import CliFacade
from tests.support.service_test import ServiceTestCase


class CliTestCase(ServiceTestCase):
    def run_cli(self, arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        return self.run_cli_with_environment(arguments, os.environ)

    def run_cli_with_environment(
        self, arguments: tuple[str, ...], environment: Mapping[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(Path(sys.executable).with_name("modwire")), *arguments],
            cwd=self.workspace, env=environment, check=False, capture_output=True, text=True,
        )

    def cli(self) -> CliFacade:
        return self.service(CliFacade, self.example_configuration())

    def write_project(self, function_limit: int) -> None:
        self.write_files({
            "src/example.py": "def example() -> None:\n    pass\n",
            ".modwire/architecture.yaml": (
                "boundaries:\n  tags:\n    - {name: example-package, match: src}\n"
                "  flow:\n    module_tag: example-package\n"
                "shape:\n  realms:\n    - name: example-source\n      match: src\n"
                f"      shape:\n        max_functions_per_file: {function_limit}\n"
            ),
        })
