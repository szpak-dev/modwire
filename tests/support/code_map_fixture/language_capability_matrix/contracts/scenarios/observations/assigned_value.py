from pydantic import Field

from modwire.application import SourceAssignedValueKind

from .....fixture_model import FixtureModel


class AssignedValueExpectation(FixtureModel):
    kind: SourceAssignedValueKind
    expression: str = Field(strict=True)
    reference: str = Field(strict=True)
