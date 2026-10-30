from typing import Literal, Self

from pydantic import model_validator

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName
from .assigned_attribute import AssignedAttributeExpectation


class AssignedValuesObservation(FixtureModel):
    kind: Literal["assigned_values"]
    owner: QualifiedName
    attributes: tuple[AssignedAttributeExpectation, ...]

    @model_validator(mode="after")
    def validate_attributes(self) -> Self:
        names = tuple(attribute.name for attribute in self.attributes)
        if len(set(names)) != len(names):
            raise ValueError("assigned-value attribute names contain duplicates")
        return self
