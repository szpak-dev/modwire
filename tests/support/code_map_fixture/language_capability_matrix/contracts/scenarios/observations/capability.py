from typing import Annotated

from pydantic import Field

from .....fixture_root_model import FixtureRootModel
from .annotation import AnnotationObservation
from .assigned_values import AssignedValuesObservation
from .attribute import AttributeObservation
from .call import CallObservation
from .callable import CallableObservation
from .declaration import DeclarationObservation
from .declaration_relation import DeclarationRelationObservation
from .dependency import DependencyObservation
from .empty_source import EmptySourceObservation
from .exact_span import ExactSpanObservation
from .modifier import ModifierObservation
from .namespace import NamespaceObservation
from .parameter import ParameterObservation
from .parameter_kind import ParameterKindObservation
from .source import SourceObservation
from .span_owner import SpanOwnerObservation
from .type_reference import TypeReferenceObservation
from .type_slot import TypeSlotObservation


class CapabilityObservation(
    FixtureRootModel[
        Annotated[
            SourceObservation
            | EmptySourceObservation
            | DeclarationObservation
            | CallableObservation
            | CallObservation
            | ParameterObservation
            | ParameterKindObservation
            | TypeReferenceObservation
            | TypeSlotObservation
            | AnnotationObservation
            | ModifierObservation
            | AttributeObservation
            | AssignedValuesObservation
            | DeclarationRelationObservation
            | NamespaceObservation
            | DependencyObservation
            | ExactSpanObservation
            | SpanOwnerObservation,
            Field(discriminator="kind"),
        ]
    ]
):
    pass
