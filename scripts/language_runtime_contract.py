import sys
from collections.abc import Sequence
from pathlib import Path

from tests.support.code_map_fixture.fixture_contract import PolyglotFixtureContract


class LanguageRuntimeContractCommand:
    def __init__(self, repository: Path) -> None:
        self.contract = PolyglotFixtureContract(repository)

    def write_github_output(self, output: Path) -> None:
        with output.open(mode="a", encoding="utf-8") as stream:
            stream.write(f"contract={self.contract.runtime_document()}\n")

    def run(self, arguments: Sequence[str]) -> None:
        if len(arguments) == 2 and arguments[0] == "export":
            self.write_github_output(Path(arguments[1]))
        elif tuple(arguments) == ("install-packages",):
            self.contract.install_runtime_packages()
        else:
            raise ValueError("expected export OUTPUT or install-packages")


if __name__ == "__main__":
    LanguageRuntimeContractCommand(Path(__file__).resolve().parents[1]).run(sys.argv[1:])
