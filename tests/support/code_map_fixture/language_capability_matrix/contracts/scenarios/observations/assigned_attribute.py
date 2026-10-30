from pydantic import Field

from .....fixture_model import FixtureModel
from ....values.names.identifier import Identifier
from .assigned_value import AssignedValueExpectation


class AssignedAttributeExpectation(FixtureModel):
    name: Identifier
    values: tuple[AssignedValueExpectation, ...] = Field(min_length=1)
