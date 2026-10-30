import sys
from pathlib import Path

from tests.support.code_map_fixture.fixture_contract import PolyglotFixtureContract


class LanguageRuntimeContractCommand:
    def __init__(self, repository: Path) -> None:
        self.contract = PolyglotFixtureContract(repository)

    def write_github_output(self, output: Path) -> None:
        with output.open(mode="a", encoding="utf-8") as stream:
            stream.write(f"contract={self.contract.runtime_document()}\n")


if __name__ == "__main__":
    LanguageRuntimeContractCommand(Path(__file__).resolve().parents[1]).write_github_output(Path(sys.argv[1]))
