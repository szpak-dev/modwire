from typing import Literal

from modwire.application import CodeMap, FileId

from ....fixture_model import FixtureModel
from ..fact_selector_kind import FactSelectorKind
from ..identities import FixtureSourceIdentities
from ..observation import PublicFactObservation


class SourceFileSelector(FixtureModel):
    kind: Literal[FactSelectorKind.SOURCE_FILE]
    source: FileId

    def read_expected(self, code_map: CodeMap) -> PublicFactObservation:
        return PublicFactObservation(code_map.extraction.files[self.source])

    def read_actual(self, code_map: CodeMap, identities: FixtureSourceIdentities) -> PublicFactObservation:
        return PublicFactObservation(identities.source(code_map.extraction.files[identities.authored(self.source)]))
