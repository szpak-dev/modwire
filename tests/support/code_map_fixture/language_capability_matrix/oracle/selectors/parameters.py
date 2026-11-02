from typing import Literal

from modwire.application import CodeMap, DeclarationIdentity, SourceParameter

from ....fixture_model import FixtureModel
from ..identities import FixtureSourceIdentities
from ..missing import MissingFactObservation
from ..observation import PublicFactObservation


class ParameterListSelector(FixtureModel):
    kind: Literal["parameter_list"]
    callable: DeclarationIdentity

    def parameters(self, code_map: CodeMap) -> tuple[SourceParameter, ...]:
        return next(
            callable_.parameters
            for callable_ in code_map.extraction.files[self.callable.source_id].canonical_callables()
            if callable_.declaration_id == self.callable
        )

    def read_expected(self, code_map: CodeMap) -> PublicFactObservation:
        return PublicFactObservation(self.parameters(code_map))

    def read_actual(self, code_map: CodeMap, identities: FixtureSourceIdentities) -> PublicFactObservation:
        source = code_map.extraction.files[identities.authored(self.callable.source_id)]
        callables = tuple(
            callable_
            for callable_ in source.canonical_callables()
            if identities.declaration(callable_.declaration_id) == self.callable
        )
        if not callables:
            return PublicFactObservation(MissingFactObservation())
        return PublicFactObservation(callables[0].parameters)
