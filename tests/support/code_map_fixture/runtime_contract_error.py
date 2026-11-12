from .fixture_contract_error import FixtureContractError
from .runtime_violation import RuntimeViolation


class RuntimeContractError(FixtureContractError):
    def __init__(self, violation: RuntimeViolation, runtime: str, expected: str, actual: str) -> None:
        self.violation = violation
        self.runtime = runtime
        self.expected = expected
        self.actual = actual
        super().__init__(f"Runtime {runtime} violates {violation.value}: expected {expected}; observed {actual}")
