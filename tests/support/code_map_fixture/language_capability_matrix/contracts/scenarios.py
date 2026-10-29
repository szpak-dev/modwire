from typing import Annotated, Literal

from pydantic import Field

from modwire.application import (
    FactCapability,
    RelationshipFamily,
    SourceCallableKind,
    SourceCallResolution,
    SourceDeclarationRelationKind,
    SourceDependencyResolution,
    SourceMemberKind,
    SourceNamespaceKind,
    SourceParameterKind,
    SourceSymbolKind,
    SourceTypeAbsent,
    SourceTypeReference,
    SourceTypeUnsupported,
)

from ...model import FixtureModel, FixtureRootModel
from ..values import (
    AnnotationExpression,
    AuthoredModifier,
    ClaimState,
    FixtureRole,
    Identifier,
    QualifiedName,
    RelationshipAspect,
    RepositorySourcePath,
    ScenarioId,
    SourceLine,
    SourcePosition,
    TypeSlotRole,
)


class SourceObservation(FixtureModel):
    kind: Literal["source"]
    relative_path: RepositorySourcePath


class DeclarationObservation(FixtureModel):
    kind: Literal["declaration"]
    qualified_name: QualifiedName
    declaration_kind: SourceSymbolKind


class CallableObservation(FixtureModel):
    kind: Literal["callable"]
    qualified_name: QualifiedName
    callable_kind: SourceCallableKind


class CallObservation(FixtureModel):
    kind: Literal["call"]
    owner: QualifiedName
    target: QualifiedName
    resolution: SourceCallResolution


class ParameterObservation(FixtureModel):
    kind: Literal["parameter"]
    owner: QualifiedName
    name: Identifier
    position: SourcePosition
    parameter_kind: SourceParameterKind
    has_default: bool


class ParameterKindObservation(FixtureModel):
    kind: Literal["parameter_kinds"]
    present: tuple[SourceParameterKind, ...]


class TypeReferenceObservation(FixtureModel):
    kind: Literal["type_reference"]
    owner: QualifiedName
    role: TypeSlotRole
    position: SourcePosition
    type: SourceTypeAbsent | SourceTypeReference | SourceTypeUnsupported


class TypeSlotObservation(FixtureModel):
    kind: Literal["type_slot"]
    owner: QualifiedName
    role: TypeSlotRole
    position: SourcePosition


class AnnotationObservation(FixtureModel):
    kind: Literal["annotation"]
    owner: QualifiedName
    expression: AnnotationExpression


class ModifierObservation(FixtureModel):
    kind: Literal["modifier"]
    owner: QualifiedName
    modifier: AuthoredModifier


class AttributeObservation(FixtureModel):
    kind: Literal["attribute"]
    owner: QualifiedName
    name: Identifier
    member_kind: SourceMemberKind


class AssignedValuePartitionObservation(FixtureModel):
    kind: Literal["assigned_value_partition"]
    owner: QualifiedName
    absent: tuple[Identifier, ...]
    literal: tuple[Identifier, ...]
    reference: tuple[Identifier, ...]
    call: tuple[Identifier, ...]
    unresolved: tuple[Identifier, ...]


class DeclarationRelationObservation(FixtureModel):
    kind: Literal["declaration_relation"]
    source: QualifiedName
    relation: SourceDeclarationRelationKind
    target: QualifiedName


class NamespaceObservation(FixtureModel):
    kind: Literal["namespace"]
    qualified_name: QualifiedName
    namespace_kind: SourceNamespaceKind


class DependencyObservation(FixtureModel):
    kind: Literal["dependency"]
    source: RepositorySourcePath
    target: Identifier
    resolution: SourceDependencyResolution


class ExactSpanObservation(FixtureModel):
    kind: Literal["exact_span"]
    owner: QualifiedName
    start: SourceLine
    end: SourceLine


class SpanOwnerObservation(FixtureModel):
    kind: Literal["span_owner"]
    owner: QualifiedName


class CapabilityObservation(
    FixtureRootModel[
        Annotated[
            SourceObservation
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
            | AssignedValuePartitionObservation
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


class RelationshipObservation(
    FixtureRootModel[
        Annotated[
            DeclarationRelationObservation | AttributeObservation | DependencyObservation,
            Field(discriminator="kind"),
        ]
    ]
):
    pass


class CapabilityClaim(FixtureModel):
    kind: Literal["capability"]
    capability: FactCapability
    state: ClaimState
    observation: CapabilityObservation


class RelationshipClaim(FixtureModel):
    kind: Literal["relationship"]
    relationship: RelationshipFamily
    aspect: RelationshipAspect
    state: ClaimState
    observation: RelationshipObservation


class ScenarioClaim(FixtureRootModel[Annotated[CapabilityClaim | RelationshipClaim, Field(discriminator="kind")]]):
    pass


class CapabilityScenario(FixtureModel):
    name: ScenarioId
    fixture: FixtureRole
    source: RepositorySourcePath
    claims: tuple[ScenarioClaim, ...] = Field(min_length=1)
