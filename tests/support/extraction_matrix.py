import hashlib
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from modwire.application import CodeValidationError, ModwireApplication

from .code_map_fixture.claim_result import ClaimResult
from .code_map_fixture.conclusion import Conclusion
from .code_map_fixture.discrepancy import Discrepancy
from .code_map_fixture.fixture_contract import PolyglotFixtureContract
from .code_map_fixture.fixture_contract_error import FixtureContractError
from .matrix_invocation_error import MatrixInvocationError


class ExtractionMatrixCommand:
    def __init__(self, application: ModwireApplication) -> None:
        self.application = application

    def run(self, arguments: Sequence[str]) -> int:
        if len(arguments) != 2:
            raise MatrixInvocationError(len(arguments))
        repository = Path(arguments[0]).resolve()
        output = Path(arguments[1])
        try:
            contract = PolyglotFixtureContract(repository)
            contract.validate_inventories()
        except (FixtureContractError, CodeValidationError, ValidationError) as error:
            failure = ClaimResult(
                subject="matrix document or fixture inventory",
                expected="a complete validated matrix",
                actual=str(error),
                discrepancies=(Discrepancy.INVALID_EVIDENCE,),
                conclusions=(Conclusion.CONTRACT,),
                owner_issue=95,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(failure.model_dump_json(indent=2) + "\n", encoding="utf-8")
            print(f"Matrix input failed: {failure.actual}")
            return 2
        revision = subprocess.run(
            ("git", "rev-parse", "HEAD"), cwd=repository, capture_output=True, text=True, check=True
        ).stdout.strip()
        paths = subprocess.run(
            ("git", "ls-files", "-co", "--exclude-standard", "-z"),
            cwd=repository,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split("\0")
        digest = hashlib.sha256()
        for path in sorted(set(paths) - {""}):
            file = repository / path
            if file.is_file():
                digest.update(path.encode() + b"\0" + file.read_bytes() + b"\0")
        report = contract.assess(self.application, revision, digest.hexdigest())
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(report.table())
        return 0 if report.regression_passes else 1


if __name__ == "__main__":
    sys.exit(ExtractionMatrixCommand(ModwireApplication.create()).run(sys.argv[1:]))
