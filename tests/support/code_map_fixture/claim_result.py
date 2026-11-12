from pydantic import Field

from .conclusion import Conclusion
from .discrepancy import Discrepancy
from .fixture_model import FixtureModel


class ClaimResult(FixtureModel):
    subject: str
    expected: str
    actual: str
    discrepancies: tuple[Discrepancy, ...]
    conclusions: tuple[Conclusion, ...]
    owner_issue: int = Field(gt=0)

    @property
    def satisfied(self) -> bool:
        return not self.discrepancies

    def with_evidence(self, subject: str, expected: str, actual: str) -> "ClaimResult":
        return ClaimResult(
            subject=subject,
            expected=expected,
            actual=actual,
            discrepancies=self.discrepancies,
            conclusions=self.conclusions,
            owner_issue=self.owner_issue,
        )
