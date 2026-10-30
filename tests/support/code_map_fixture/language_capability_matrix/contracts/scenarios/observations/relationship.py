from typing import Annotated

from pydantic import Field

from .....fixture_root_model import FixtureRootModel
from .assigned_values import AssignedValuesObservation
from .attribute import AttributeObservation
from .call import CallObservation
from .declaration_relation import DeclarationRelationObservation
from .dependency import DependencyObservation


class RelationshipObservation(
    FixtureRootModel[
        Annotated[
            DeclarationRelationObservation
            | AttributeObservation
            | DependencyObservation
            | CallObservation
            | AssignedValuesObservation,
            Field(discriminator="kind"),
        ]
    ]
):
    pass
