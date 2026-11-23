from typing import Self

from pydantic import model_validator

from modwire.application import (
    DeclarationFamily,
    DeclarationIdentity,
    FileInventoryCoverage,
    MemberInventoryCoverage,
    SourceDeclarationRelation,
    SourceExport,
    SourceParameter,
    SourcePlacement,
    SourceSignature,
    SourceTypeAbsent,
    SourceTypeReference,
    SourceTypeUnsupported,
    SourceUnresolvedMethod,
)

from ...fixture_model import FixtureModel
from ...scenario_contract_error import ScenarioContractError
from ...scenario_violation import ScenarioViolation
from ..contracts.scenarios.observations.attribute import AttributeObservation
from ..contracts.scenarios.observations.callable import CallableObservation
from ..contracts.scenarios.observations.declaration import DeclarationObservation
from ..contracts.scenarios.observations.exact_span import ExactSpanObservation
from ..contracts.scenarios.observations.namespace import NamespaceObservation
from ..values.names.identifier import Identifier
from ..values.names.qualified_name import QualifiedName


class SourceFactExpectation(FixtureModel):
    declarations: tuple[DeclarationObservation, ...]
    callables: tuple[CallableObservation, ...]
    attributes: tuple[AttributeObservation, ...]
    namespaces: tuple[NamespaceObservation, ...]
    signatures: dict[QualifiedName, tuple[SourceSignature, ...]]
    spans: tuple[ExactSpanObservation, ...]
    owners: tuple[tuple[DeclarationIdentity, DeclarationIdentity], ...]
    unresolved_methods: tuple[SourceUnresolvedMethod, ...]
    parameters: dict[QualifiedName, tuple[SourceParameter, ...]]
    returns: dict[QualifiedName, SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported]
    placements: tuple[tuple[DeclarationIdentity, SourcePlacement], ...]
    exports: tuple[SourceExport, ...]
    relations: tuple[SourceDeclarationRelation, ...]
    inventory: FileInventoryCoverage
    member_inventories: tuple[tuple[DeclarationIdentity, MemberInventoryCoverage], ...]
    gaps: dict[Identifier, str]

    @model_validator(mode="after")
    def validate_targets(self) -> Self:
        callables = {item.qualified_name.value for item in self.callables}
        declarations = {item.qualified_name.value for item in self.declarations}
        selected = {name.value for name in (*self.parameters, *self.returns)}
        if not selected <= callables:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "selected callable")
        members = {
            identity
            for identity, _ in self.placements
            if identity.family in (DeclarationFamily.METHOD, DeclarationFamily.PROPERTY)
        }
        owners = {identity for identity, _ in self.member_inventories}
        unresolved = {method.declaration_id for method in self.unresolved_methods}
        if (
            not unresolved <= members
            or {member for member, _ in self.owners} != members - unresolved
            or len(self.owners) != len(members - unresolved)
            or not {owner for _, owner in self.owners} <= owners
        ):
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "selected owner")
        if not {span.owner.value for span in self.spans} <= callables:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "owner at authored span")
        if not {owner.value for owner in self.signatures} <= declarations:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "signature owner")
        if any(not requirement.strip() for requirement in self.gaps.values()):
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "empty source requirement")
        return self
