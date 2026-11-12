from typing import Self

from pydantic import model_validator

from modwire.application import SourceParameter, SourceSignature, SourceTypeReference

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
    owners: dict[QualifiedName, QualifiedName]
    parameters: dict[QualifiedName, tuple[SourceParameter, ...]]
    returns: dict[QualifiedName, SourceTypeReference]
    gaps: dict[Identifier, str]

    @model_validator(mode="after")
    def validate_targets(self) -> Self:
        callables = {item.qualified_name.value for item in self.callables}
        declarations = {item.qualified_name.value for item in self.declarations}
        selected = {name.value for name in (*self.owners, *self.parameters, *self.returns)}
        if not selected <= callables:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "selected callable")
        if not {owner.value for owner in self.owners.values()} <= declarations:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "selected owner")
        if not {span.owner.value for span in self.spans} <= {owner.value for owner in self.owners}:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "owner at authored span")
        if not {owner.value for owner in self.signatures} <= declarations:
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "signature owner")
        if any(not requirement.strip() for requirement in self.gaps.values()):
            raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, "empty source requirement")
        return self
