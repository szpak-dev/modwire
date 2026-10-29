from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from modwire.application import (
    SourceCallableKind,
    SourceCallResolution,
    SourceDeclarationRelationKind,
    SourceDependencyResolution,
    SourceMemberKind,
    SourceNamespaceKind,
    SourceParameterKind,
    SourceSymbolKind,
)

from ...model import FixtureModel, FixtureRootModel
from ..values import (
    ClaimState,
    Identifier,
    ManifestChange,
    ManifestScenarioId,
    QualifiedName,
    RepositoryPath,
    RepositorySourcePath,
    SourcePosition,
)


class ManifestSourceObservation(FixtureModel):
    kind: Literal["source"]
    relative_path: RepositorySourcePath


class ManifestNamespaceObservation(FixtureModel):
    kind: Literal["namespace"]
    qualified_name: QualifiedName
    namespace_kind: SourceNamespaceKind


class ManifestSymbolObservation(FixtureModel):
    kind: Literal["symbol"]
    qualified_name: QualifiedName
    symbol_kind: SourceSymbolKind


class ManifestCallableObservation(FixtureModel):
    kind: Literal["callable"]
    qualified_name: QualifiedName
    callable_kind: SourceCallableKind


class ManifestParameterObservation(FixtureModel):
    kind: Literal["parameter"]
    owner: QualifiedName
    name: Identifier
    position: SourcePosition
    parameter_kind: SourceParameterKind
    has_default: bool


class ManifestAttributeObservation(FixtureModel):
    kind: Literal["attribute"]
    owner: QualifiedName
    name: Identifier
    member_kind: SourceMemberKind


class ManifestCallObservation(FixtureModel):
    kind: Literal["call"]
    owner: QualifiedName
    target: QualifiedName
    resolution: SourceCallResolution


class ManifestDeclarationRelationObservation(FixtureModel):
    kind: Literal["declaration_relation"]
    source: QualifiedName
    relation: SourceDeclarationRelationKind
    target: QualifiedName


class ManifestDependencyObservation(FixtureModel):
    kind: Literal["dependency"]
    source: RepositorySourcePath
    target: Identifier
    resolution: SourceDependencyResolution


class ManifestObservation(
    FixtureRootModel[
        Annotated[
            ManifestSourceObservation
            | ManifestNamespaceObservation
            | ManifestSymbolObservation
            | ManifestCallableObservation
            | ManifestParameterObservation
            | ManifestAttributeObservation
            | ManifestCallObservation
            | ManifestDeclarationRelationObservation
            | ManifestDependencyObservation,
            Field(discriminator="kind"),
        ]
    ]
):
    pass


class ManifestClaim(FixtureModel):
    state: ClaimState
    observation: ManifestObservation


class ManifestScenario(FixtureModel):
    name: ManifestScenarioId
    source: RepositorySourcePath
    claims: tuple[ManifestClaim, ...] = Field(min_length=1)


class ManifestTransition(FixtureModel):
    before: ManifestScenarioId
    after: ManifestScenarioId
    changes: tuple[ManifestChange, ...] = Field(min_length=1)


class ManifestContract(FixtureModel):
    root: RepositoryPath
    scenarios: tuple[ManifestScenario, ...] = Field(min_length=1)
    transitions: tuple[ManifestTransition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        names = tuple(scenario.name for scenario in self.scenarios)
        sources = tuple(scenario.source.value for scenario in self.scenarios)
        if len(set(names)) != len(names):
            raise ValueError("manifest scenario names contain duplicates")
        if len(set(sources)) != len(sources):
            raise ValueError("manifest scenario sources contain duplicates")
        for scenario in self.scenarios:
            if scenario.source.value.parts[0] != scenario.name.value:
                raise ValueError("manifest source is outside its named scenario")
        for transition in self.transitions:
            if transition.before not in names or transition.after not in names:
                raise ValueError("manifest transition names an undeclared scenario")
            if transition.before == transition.after:
                raise ValueError("manifest transition must change scenario")
        return self
