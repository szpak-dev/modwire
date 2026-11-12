from .fixture_contract_error import FixtureContractError
from .scenario_violation import ScenarioViolation


class ScenarioContractError(FixtureContractError):
    def __init__(self, violation: ScenarioViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Scenario contract violates {violation.value}: {subject}")
