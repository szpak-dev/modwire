from pydantic import Field

from modwire.application import SourceAssignedValue

from .....fixture_model import FixtureModel
from ....values.names.identifier import Identifier


class AssignedAttributeExpectation(FixtureModel):
    name: Identifier
    values: tuple[SourceAssignedValue, ...] = Field(min_length=1)
